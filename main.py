import os
import logging
import sentry_sdk
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from scheduler import create_scheduler
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
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)

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

    # Start scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(title="Gym Agent", lifespan=lifespan)


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


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
    except Exception as e:
        logger.exception("Unhandled error in webhook: %s", e)
        if sentry_dsn:
            sentry_sdk.capture_exception(e)

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

    # ── /start ─────────────────────────────────────────────────────────────
    if text == "/start":
        db.upsert_user(telegram_id, first_name)
        await tg.send_message(
            chat_id,
            f"👋 Здравей, <b>{first_name}</b>!\n\n"
            "Аз съм твоят личен фитнес агент. Всяка сутрин в <b>08:00</b> ще ти изпращам "
            "тренировката за деня с интерактивен checklist.\n\n"
            "📅 Програма:\n"
            "• Пон/Чет — Кардио HIIT + Core\n"
            "• Вт/Пет — Сила с ластици\n"
            "• Ср/Съб — Лека активност\n"
            "• Нед — Почивка\n\n"
            "Можеш да ми пишеш всяко време — ще ти помогна!\n\n"
            "⭐ <b>Level 1</b> | 🔥 Streak: 0 | XP: 0"
        )
        return

    # ── /stats ─────────────────────────────────────────────────────────────
    if text == "/stats":
        user = db.get_user(telegram_id)
        if user:
            await tg.send_message(
                chat_id,
                f"📊 <b>Твоята статистика</b>\n\n"
                f"⭐ Level: <b>{user['level']}</b>\n"
                f"✨ XP: <b>{user['xp']}</b>\n"
                f"🔥 Streak: <b>{user['streak']} дни</b>\n"
                f"📈 Трудност: <b>{user.get('difficulty', 'beginner').capitalize()}</b>",
            )
        return

    # ── /workout ───────────────────────────────────────────────────────────
    if text == "/workout":
        await tg.send_daily_workout(telegram_id)
        return

    # ── Free-text chat → Claude agent ─────────────────────────────────────
    reply = await ai.chat(telegram_id, text)
    await tg.send_message(chat_id, reply)
