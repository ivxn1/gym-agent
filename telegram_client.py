import os
import logging
import httpx
from datetime import date, timedelta

from workouts import get_workout_plan
from youtube import search_youtube
import database as db

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

DAYS_BG = ["Понеделник", "Вторник", "Сряда", "Четвъртък", "Петък", "Събота", "Неделя"]


async def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> dict | None:
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{BASE_URL}/sendMessage", json=payload)
            r.raise_for_status()
            return r.json().get("result")
    except Exception as e:
        logger.error("sendMessage error for %s: %s", chat_id, e)
        return None


async def edit_message_reply_markup(chat_id: int, message_id: int, reply_markup: dict):
    payload = {"chat_id": chat_id, "message_id": message_id, "reply_markup": reply_markup}
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{BASE_URL}/editMessageReplyMarkup", json=payload)
            r.raise_for_status()
    except Exception as e:
        logger.error("editMessageReplyMarkup error: %s", e)


async def answer_callback_query(callback_query_id: str, text: str = ""):
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            await c.post(f"{BASE_URL}/answerCallbackQuery", json={
                "callback_query_id": callback_query_id,
                "text": text,
                "show_alert": False,
            })
    except Exception as e:
        logger.warning("answerCallbackQuery error: %s", e)


async def set_webhook(webhook_url: str):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{BASE_URL}/setWebhook", json={"url": webhook_url, "drop_pending_updates": True})
        return r.json()


async def send_daily_workout(telegram_id: int):
    """Build and send the daily workout message with inline checklist buttons."""
    user = db.get_user(telegram_id)
    if not user:
        return

    today = date.today()
    weekday = today.weekday()

    if weekday == 6:
        # Sunday rest
        result = await send_message(
            telegram_id,
            "😴 <b>Неделя — Почивен ден!</b>\n\nОтпочини се добре. Утре започваме нова седмица 💪\n\n"
            f"🔥 Streak: <b>{user['streak']} дни</b> | ⭐ Level: <b>{user['level']}</b> | XP: <b>{user['xp']}</b>"
        )
        return

    difficulty = user.get("difficulty", "beginner")
    plan = get_workout_plan(weekday, difficulty)
    if not plan:
        return

    day_name = DAYS_BG[weekday]

    # Fetch YouTube links for all exercises
    yt_links = {}
    for ex in plan.exercises:
        yt_links[ex.name] = await search_youtube(ex.youtube_query or ex.name)

    # Build message text
    lines = [
        f"🏋️ <b>Тренировка за {day_name}</b> — {plan.day_type}",
        f"⏱ {plan.estimated_duration} | 🔥 ~{plan.estimated_calories} ккал | 📊 {difficulty.capitalize()}",
        "",
        "Натисни ✅ след всяко упражнение:",
        "",
    ]
    for i, ex in enumerate(plan.exercises, 1):
        detail = ""
        if ex.sets and ex.reps:
            detail = f"{ex.sets}×{ex.reps}"
        elif ex.duration:
            detail = ex.duration
        yt = yt_links.get(ex.name, "")
        lines.append(f"{i}. <b>{ex.name}</b> — {detail}  <a href='{yt}'>▶ видео</a>  (+{ex.xp} XP)")

    lines += [
        "",
        f"⭐ Level: <b>{user['level']}</b> | XP: <b>{user['xp']}</b> | 🔥 Streak: <b>{user['streak']}</b>",
    ]

    text = "\n".join(lines)

    # Inline keyboard — one button per exercise
    keyboard = []
    for ex in plan.exercises:
        keyboard.append([{
            "text": f"⬜ {ex.name}",
            "callback_data": f"done|{ex.name}|{ex.xp}",
        }])
    keyboard.append([{"text": "✅ Всичко готово!", "callback_data": "done|ALL|0"}])

    result = await send_message(telegram_id, text, reply_markup={"inline_keyboard": keyboard})
    if result:
        db.update_user_state(user["id"], workout_sent_today=True, last_workout_message_id=result.get("message_id"))


async def send_reminder(telegram_id: int):
    """Send afternoon reminder if nothing was checked off."""
    await send_message(
        telegram_id,
        "⏰ <b>Напомняне!</b>\n\nЕй, не съм видял тренировката ти за днес отметена. "
        "Само 20-45 минути и сте готово! 💪\n\nОтвори тренировката по-горе и цъкни упражненията.",
    )
    user = db.get_user(telegram_id)
    if user:
        db.update_user_state(user["id"], reminder_sent_today=True)


async def handle_exercise_callback(callback_query: dict) -> None:
    """Process inline button press when user marks an exercise as done."""
    cq_id = callback_query["id"]
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    telegram_id = callback_query["from"]["id"]
    data = callback_query.get("data", "")

    if not data.startswith("done|"):
        await answer_callback_query(cq_id)
        return

    parts = data.split("|", 2)
    if len(parts) < 3:
        await answer_callback_query(cq_id)
        return

    _, exercise_name, xp_str = parts
    xp_earned = int(xp_str) if xp_str.isdigit() else 10

    user = db.get_user(telegram_id)
    if not user:
        await answer_callback_query(cq_id, "Регистрирай се с /start")
        return

    if exercise_name == "ALL":
        # Mark all today's incomplete exercises
        today = date.today()
        weekday = today.weekday()
        plan = get_workout_plan(weekday, user.get("difficulty", "beginner"))
        if plan:
            for ex in plan.exercises:
                logs = db.get_today_logs(user["id"])
                done = {l["exercise_name"] for l in logs if l["completed"]}
                if ex.name not in done:
                    db.log_exercise(user["id"], ex.name, True, ex.xp)
                    result, leveled_up = db.add_xp(telegram_id, ex.xp)
        streak = db.update_streak(telegram_id)
        await answer_callback_query(cq_id, f"🎉 Невероятно! Streak: {streak} дни!")
        await send_message(chat_id, f"🏆 <b>Тренировката е завършена!</b>\n🔥 Streak: <b>{streak} дни</b>")
        return

    # Check if already marked
    logs = db.get_today_logs(user["id"])
    done_set = {l["exercise_name"] for l in logs if l["completed"]}
    if exercise_name in done_set:
        await answer_callback_query(cq_id, "Вече отметено! ✅")
        return

    db.log_exercise(user["id"], exercise_name, True, xp_earned)
    result_tuple = db.add_xp(telegram_id, xp_earned)
    leveled_up = result_tuple[1] if isinstance(result_tuple, tuple) else False

    # Update the inline button to show checkmark
    if message_id and chat_id:
        # Rebuild keyboard with this exercise checked
        today = date.today()
        weekday = today.weekday()
        plan = get_workout_plan(weekday, user.get("difficulty", "beginner"))
        updated_logs = db.get_today_logs(user["id"])
        done_set = {l["exercise_name"] for l in updated_logs if l["completed"]}

        if plan:
            keyboard = []
            for ex in plan.exercises:
                icon = "✅" if ex.name in done_set else "⬜"
                keyboard.append([{
                    "text": f"{icon} {ex.name}",
                    "callback_data": f"done|{ex.name}|{ex.xp}",
                }])
            keyboard.append([{"text": "✅ Всичко готово!", "callback_data": "done|ALL|0"}])
            await edit_message_reply_markup(chat_id, message_id, {"inline_keyboard": keyboard})

    fb = f"+{xp_earned} XP! 💪"
    if leveled_up:
        user_refreshed = db.get_user(telegram_id)
        fb += f"\n🎉 LEVEL UP! Сега си Level {user_refreshed['level']}!"
    await answer_callback_query(cq_id, fb)


async def send_weekly_report(telegram_id: int):
    """Send Sunday weekly summary."""
    user = db.get_user(telegram_id)
    if not user:
        return

    today = date.today()
    week_start = today - timedelta(days=today.weekday() + 1)  # last Monday
    logs = db.get_week_logs(user["id"], week_start)
    completed = [l for l in logs if l["completed"]]
    workouts_done = len(set(l["log_date"] for l in completed))
    total_xp = sum(l.get("xp_earned", 0) for l in completed)
    exercises_count = len(completed)

    # Estimate calories (rough: 60 per 10 mins, avg 35 min = 210 per session)
    estimated_calories = workouts_done * 260

    streak_emoji = "🔥" if user["streak"] >= 3 else "💪"

    lines = [
        "📊 <b>Седмичен отчет</b>",
        "",
        f"🗓 Тренировки: <b>{workouts_done}/6</b>",
        f"🏋️ Упражнения изпълнени: <b>{exercises_count}</b>",
        f"⭐ XP спечелени: <b>{total_xp}</b>",
        f"🔥 Калории (прибл.): <b>{estimated_calories} ккал</b>",
        f"{streak_emoji} Streak: <b>{user['streak']} дни</b>",
        f"📈 Level: <b>{user['level']}</b> | Трудност: <b>{user.get('difficulty', 'beginner').capitalize()}</b>",
        "",
    ]

    if workouts_done >= 5:
        lines.append("🏆 Страхотна седмица! Продължавай така!")
    elif workouts_done >= 3:
        lines.append("👍 Добра седмица! Следващата можем повече!")
    else:
        lines.append("💡 Тази седмица беше по-тежка — утре е нов старт!")

    lines.append("\nДовиждане до понеделник! 💪")

    await send_message(telegram_id, "\n".join(lines))


