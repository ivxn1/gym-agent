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
DAY_TYPES = {
    0: "HIIT + Core",
    1: "Сила",
    2: "Лека",
    3: "HIIT + Core",
    4: "Сила",
    5: "Лека",
    6: "Почивка",
}


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


async def set_bot_commands():
    """Register slash commands in Telegram UI (visible via the / button)."""
    commands = [
        {"command": "workout", "description": "Днешната тренировка"},
        {"command": "menu", "description": "Меню с тренировки и трудност"},
        {"command": "stats", "description": "Моята статистика"},
        {"command": "start", "description": "Начало"},
    ]
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{BASE_URL}/setMyCommands", json={"commands": commands})
            return r.json()
    except Exception as e:
        logger.warning("setMyCommands error: %s", e)
        return None


async def send_workout_menu(chat_id: int):
    """Send the workout selection menu."""
    keyboard = [
        [{"text": "Днешната тренировка", "callback_data": "menu|today"}],
        [
            {"text": "Пон — HIIT", "callback_data": "menu|day|0"},
            {"text": "Вт — Сила", "callback_data": "menu|day|1"},
            {"text": "Ср — Лека", "callback_data": "menu|day|2"},
        ],
        [
            {"text": "Чет — HIIT", "callback_data": "menu|day|3"},
            {"text": "Пет — Сила", "callback_data": "menu|day|4"},
            {"text": "Съб — Лека", "callback_data": "menu|day|5"},
        ],
        [
            {"text": "По-лесно", "callback_data": "menu|diff|easier"},
            {"text": "По-трудно", "callback_data": "menu|diff|harder"},
        ],
    ]
    await send_message(
        chat_id,
        "<b>Избери тренировка:</b>",
        reply_markup={"inline_keyboard": keyboard},
    )


async def send_workout_for_day(telegram_id: int, weekday: int, mark_as_sent: bool = False) -> None:
    """Build and send workout for a given weekday with inline checklist buttons."""
    user = db.get_user(telegram_id)
    if not user:
        return

    if weekday == 6:
        await send_message(
            telegram_id,
            f"<b>Неделя — Почивен ден.</b>\n\nОтпочини се. Утре започваме нова седмица.\n\n"
            f"Streak: <b>{user['streak']} дни</b> | Level: <b>{user['level']}</b>",
        )
        return

    difficulty = user.get("difficulty", "beginner")
    plan = get_workout_plan(weekday, difficulty)
    if not plan:
        return

    day_name = DAYS_BG[weekday]

    yt_links = {}
    for ex in plan.exercises:
        yt_links[ex.name] = await search_youtube(ex.youtube_query or ex.name)

    lines = [
        f"<b>Тренировка {day_name}</b> — {plan.day_type}",
        f"{plan.estimated_duration} | ~{plan.estimated_calories} ккал | {difficulty.capitalize()}",
        "",
        "Отбележи след всяко упражнение:",
        "",
    ]
    for i, ex in enumerate(plan.exercises, 1):
        if ex.sets and ex.reps:
            detail = f"{ex.sets}×{ex.reps}"
        elif ex.duration:
            detail = ex.duration
        else:
            detail = ""
        yt = yt_links.get(ex.name, "")
        lines.append(f"{i}. <b>{ex.name}</b> — {detail}  <a href='{yt}'>видео</a>  (+{ex.xp} XP)")

    lines += [
        "",
        f"Level: <b>{user['level']}</b> | XP: <b>{user['xp']}</b> | Streak: <b>{user['streak']} дни</b>",
    ]

    keyboard = []
    for ex in plan.exercises:
        keyboard.append([{"text": f"[ ] {ex.name}", "callback_data": f"done|{ex.name}|{ex.xp}"}])
    keyboard.append([{"text": "Всичко готово!", "callback_data": "done|ALL|0"}])

    result = await send_message(telegram_id, "\n".join(lines), reply_markup={"inline_keyboard": keyboard})
    if result and mark_as_sent:
        db.update_user_state(user["id"], workout_sent_today=True, last_workout_message_id=result.get("message_id"))


async def send_daily_workout(telegram_id: int):
    """Send today's workout and mark it as sent."""
    today = date.today()
    await send_workout_for_day(telegram_id, today.weekday(), mark_as_sent=True)


async def send_reminder(telegram_id: int):
    """Send afternoon reminder if nothing was checked off."""
    await send_message(
        telegram_id,
        "<b>Напомняне</b>\n\nТренировката за днес още не е отметена. "
        "20-45 минути са достатъчни. Отвори тренировката по-горе и започни.",
    )
    user = db.get_user(telegram_id)
    if user:
        db.update_user_state(user["id"], reminder_sent_today=True)


async def handle_menu_callback(callback_query: dict) -> None:
    """Handle workout menu selections."""
    cq_id = callback_query["id"]
    chat_id = callback_query["message"]["chat"]["id"]
    telegram_id = callback_query["from"]["id"]
    data = callback_query.get("data", "")

    parts = data.split("|")
    action = parts[1] if len(parts) > 1 else ""

    if action == "today":
        await answer_callback_query(cq_id)
        await send_daily_workout(telegram_id)

    elif action == "day" and len(parts) > 2:
        weekday = int(parts[2])
        await answer_callback_query(cq_id)
        await send_workout_for_day(telegram_id, weekday)

    elif action == "diff" and len(parts) > 2:
        direction = parts[2]
        user = db.get_user(telegram_id)
        if not user:
            await answer_callback_query(cq_id, "Напиши /start първо.")
            return
        levels = ["beginner", "intermediate", "advanced"]
        labels = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}
        idx = levels.index(user.get("difficulty", "beginner"))
        if direction == "easier" and idx > 0:
            new_diff = levels[idx - 1]
            db.update_user(telegram_id, difficulty=new_diff)
            await answer_callback_query(cq_id, f"Трудност намалена: {labels[new_diff]}")
            await send_message(chat_id, f"Трудността е сменена на <b>{labels[new_diff]}</b>.")
        elif direction == "harder" and idx < 2:
            new_diff = levels[idx + 1]
            db.update_user(telegram_id, difficulty=new_diff)
            await answer_callback_query(cq_id, f"Трудност увеличена: {labels[new_diff]}")
            await send_message(chat_id, f"Трудността е сменена на <b>{labels[new_diff]}</b>.")
        else:
            current_label = labels[user.get("difficulty", "beginner")]
            await answer_callback_query(cq_id, f"Вече си на {current_label}.")
    else:
        await answer_callback_query(cq_id)


async def handle_exercise_callback(callback_query: dict) -> None:
    """Process inline button press when user marks an exercise as done."""
    cq_id = callback_query["id"]
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    telegram_id = callback_query["from"]["id"]
    data = callback_query.get("data", "")

    if data.startswith("menu|"):
        await handle_menu_callback(callback_query)
        return

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
        today = date.today()
        weekday = today.weekday()
        plan = get_workout_plan(weekday, user.get("difficulty", "beginner"))
        if plan:
            for ex in plan.exercises:
                logs = db.get_today_logs(user["id"])
                done = {l["exercise_name"] for l in logs if l["completed"]}
                if ex.name not in done:
                    db.log_exercise(user["id"], ex.name, True, ex.xp)
                    db.add_xp(telegram_id, ex.xp)
        streak = db.update_streak(telegram_id)
        await answer_callback_query(cq_id, f"Тренировката е завършена! Streak: {streak} дни")
        await send_message(chat_id, f"<b>Тренировката е завършена.</b>\nStreak: <b>{streak} дни</b>")
        return

    # Check if already marked
    logs = db.get_today_logs(user["id"])
    done_set = {l["exercise_name"] for l in logs if l["completed"]}
    if exercise_name in done_set:
        await answer_callback_query(cq_id, "Вече отметено.")
        return

    db.log_exercise(user["id"], exercise_name, True, xp_earned)
    result_tuple = db.add_xp(telegram_id, xp_earned)
    leveled_up = result_tuple[1] if isinstance(result_tuple, tuple) else False

    # Rebuild keyboard with updated checkmarks
    if message_id and chat_id:
        today = date.today()
        weekday = today.weekday()
        plan = get_workout_plan(weekday, user.get("difficulty", "beginner"))
        updated_logs = db.get_today_logs(user["id"])
        done_set = {l["exercise_name"] for l in updated_logs if l["completed"]}

        if plan:
            keyboard = []
            for ex in plan.exercises:
                mark = "[x]" if ex.name in done_set else "[ ]"
                keyboard.append([{"text": f"{mark} {ex.name}", "callback_data": f"done|{ex.name}|{ex.xp}"}])
            keyboard.append([{"text": "Всичко готово!", "callback_data": "done|ALL|0"}])
            await edit_message_reply_markup(chat_id, message_id, {"inline_keyboard": keyboard})

    fb = f"+{xp_earned} XP"
    if leveled_up:
        user_refreshed = db.get_user(telegram_id)
        fb += f" — Level up! Сега си Level {user_refreshed['level']}"
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

    lines = [
        "<b>Седмичен отчет</b>",
        "",
        f"Тренировки: <b>{workouts_done}/6</b>",
        f"Упражнения: <b>{exercises_count}</b>",
        f"XP спечелени: <b>{total_xp}</b>",
        f"Калории (прибл.): <b>{estimated_calories} ккал</b>",
        f"Streak: <b>{user['streak']} дни</b>",
        f"Level: <b>{user['level']}</b> | Трудност: <b>{user.get('difficulty', 'beginner').capitalize()}</b>",
        "",
    ]

    if workouts_done >= 5:
        lines.append("Страхотна седмица. Продължавай така.")
    elif workouts_done >= 3:
        lines.append("Добра седмица. Следващата можем повече.")
    else:
        lines.append("Тази седмица беше по-тежка — утре е нов старт.")

    lines.append("\nДо понеделник.")

    await send_message(telegram_id, "\n".join(lines))


