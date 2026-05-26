import os
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from scheduler import create_scheduler, catch_up_on_startup
import database as db
import telegram_client as tg
import agent as ai

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Sentry ─────────────────────────────────────────────────────────────────
# DSN comes from the SENTRY_DSN fly secret. Fly injects FLY_* env vars
# automatically, which we use to tag environment and release.
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", os.environ.get("FLY_APP_NAME", "production")),
        release=os.environ.get("FLY_MACHINE_VERSION") or os.environ.get("FLY_IMAGE_REF"),
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
        # Capture logger.error()/logger.exception() as Sentry events,
        # and INFO+ as breadcrumbs for context leading up to an error.
        integrations=[LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)],
    )
    logger.info("Sentry initialised (env=%s)", os.environ.get("FLY_APP_NAME", "production"))
else:
    logger.warning("SENTRY_DSN not set — error tracking disabled")

# ── Telegram secret token for webhook security ─────────────────────────────
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
APP_URL = os.environ.get("APP_URL", "")  # e.g. https://gym-agent.fly.dev


# ── App lifecycle ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register webhook
    if APP_URL:
        webhook_url = f"{APP_URL}/webhook"
        result = await tg.set_webhook(webhook_url)
        logger.info("Webhook set: %s", result)

    # Register slash commands in Telegram UI
    cmd_result = await tg.set_bot_commands()
    logger.info("Bot commands set: %s", cmd_result)

    # Start scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started with jobs: %s", [j.id for j in scheduler.get_jobs()])

    # Send today's workout if we started up after 08:00 and missed the cron
    try:
        await catch_up_on_startup()
    except Exception as e:
        logger.error("Startup catch-up failed: %s", e)

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(title="Gym Agent", lifespan=lifespan)


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "sentry": bool(sentry_dsn)}


# ── Sentry verification — triggers a test error, then check your dashboard ──
@app.get("/debug/sentry")
async def debug_sentry():
    raise RuntimeError("Sentry test error — integration is working")


# ── Telegram webhook ───────────────────────────────────────────────────────
@app.post("/webhook")
async def webhook(request: Request):
    # Validate secret token
    if WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        await handle_update(update)
    except Exception:
        # LoggingIntegration forwards this to Sentry as an event.
        logger.exception("Unhandled error in webhook")

    # Always return 200 to Telegram
    return JSONResponse({"ok": True})


async def handle_update(update: dict):
    # ── Callback query (inline button press) ──────────────────────────────
    if "callback_query" in update:
        await tg.handle_exercise_callback(update["callback_query"])
        return

    # ── Regular message ────────────────────────────────────────────────────
    message = update.get("message")
    if not message:
        return

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()
    from_user = message.get("from", {})
    telegram_id = from_user.get("id")
    first_name = from_user.get("first_name", "Приятел")

    if not telegram_id or not text:
        return

    lower = text.lower().strip(" ?!.")

    # ── /start ─────────────────────────────────────────────────────────────
    if text == "/start":
        db.upsert_user(telegram_id, first_name)
        await tg.send_message(
            chat_id,
            f"Здравей, <b>{first_name}</b>.\n\n"
            "Всяка сутрин в <b>08:00</b> ще получаваш тренировката за деня с checklist.\n\n"
            "<b>Програма:</b>\n"
            "Пон/Чет — Кардио HIIT + Core\n"
            "Вт/Пет — Сила с ластици\n"
            "Ср/Съб — Лека активност\n"
            "Нед — Почивка\n\n"
            "Използвай бутоните долу или ми пиши свободно на български.",
            reply_markup=tg.PERSISTENT_KEYBOARD,
        )
        return

    # ── /stats or "Статистика" button ──────────────────────────────────────
    if text == "/stats" or lower == "статистика":
        user = db.get_user(telegram_id)
        if user:
            await tg.send_message(
                chat_id,
                f"<b>Статистика</b>\n\n"
                f"Level: <b>{user['level']}</b>\n"
                f"XP: <b>{user['xp']}</b>\n"
                f"Streak: <b>{user['streak']} дни</b>\n"
                f"Трудност: <b>{user.get('difficulty', 'beginner').capitalize()}</b>",
            )
        return

    # ── /workout or "Днешна тренировка" button ─────────────────────────────
    if text == "/workout" or lower in {"днешна тренировка", "тренировка"}:
        await tg.send_daily_workout(telegram_id)
        return

    # ── /menu, "Меню" button, or menu-like requests ───────────────────────
    menu_triggers = {
        "/menu", "меню", "menu", "опции", "options", "какво можеш", "помощ",
        "help", "/help", "commands", "команди",
    }
    if text == "/menu" or lower in menu_triggers:
        await tg.send_workout_menu(chat_id)
        return

    # ── /preferences or "Настройки" button ────────────────────────────────
    pref_triggers = {
        "/preferences", "настройки", "предпочитания", "preferences", "prefs",
    }
    if text == "/preferences" or lower in pref_triggers:
        await tg.send_preferences_menu(telegram_id)
        return

    # ── Free-text chat → Claude agent ─────────────────────────────────────
    reply = await ai.chat(telegram_id, text)
    await tg.send_message(chat_id, reply)
