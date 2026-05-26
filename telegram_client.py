import os
import html
import logging
import httpx
from datetime import date, timedelta

from generator import generate_workout, WEEKDAY_TO_CATEGORY, CATEGORY_LABELS
from workouts import get_quick_workout
from youtube import search_youtube
from models import WorkoutPlan
import database as db

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

DAYS_BG = ["Понеделник", "Вторник", "Сряда", "Четвъртък", "Петък", "Събота", "Неделя"]

PERSISTENT_KEYBOARD = {
    "keyboard": [
        [{"text": "Днешна тренировка"}, {"text": "Меню"}],
        [{"text": "Статистика"}, {"text": "Настройки"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

# Labels for preferences menu
_EQUIPMENT_LABELS = {
    "treadmill":      "Пътека",
    "jump_rope":      "Въже",
    "resistance_band":"Ластик",
    "bodyweight":     "Само тяло",
    "dumbbells":      "Гири",
    "barbell":        "Щанга",
    "kettlebell":     "Гиря",
    "pull_up_bar":    "Лост",
    "mat":            "Постелка",
}
_GOAL_LABELS = {
    "weight_loss":    "Отслабване",
    "muscle":         "Мускули",
    "endurance":      "Издръжливост",
    "flexibility":    "Гъвкавост",
    "general_fitness":"Обща форма",
}
_MUSCLE_LABELS = {
    "chest":     "Гърди",
    "back":      "Гръб",
    "shoulders": "Рамене",
    "arms":      "Ръце",
    "legs":      "Крака",
    "glutes":    "Задник",
    "core":      "Core",
    "full_body": "Цяло тяло",
}

_QUICK_TO_CATEGORY = {
    "running":        "recovery",
    "jump_rope":      "hiit_core",
    "strength_bands": "strength",
    "hiit":           "hiit_core",
    "core":           "hiit_core",
    "stretching":     "recovery",
}
_QUICK_EQUIPMENT = {
    "running":        ["treadmill", "bodyweight"],
    "jump_rope":      ["jump_rope", "bodyweight"],
    "strength_bands": ["resistance_band", "bodyweight"],
    "core":           ["bodyweight", "mat"],
    "stretching":     ["bodyweight", "mat"],
}
_QUICK_LABELS = {
    "running":        "Бягане",
    "jump_rope":      "Въже за скачане",
    "strength_bands": "Сила с ластици",
    "hiit":           "HIIT кардио",
    "core":           "Core тренировка",
    "stretching":     "Стречинг",
}


# ── HTTP helpers ───────────────────────────────────────────────────────────

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


async def edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict | None = None):
    payload: dict = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{BASE_URL}/editMessageText", json=payload)
            r.raise_for_status()
    except Exception as e:
        logger.error("editMessageText error: %s", e)


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
    commands = [
        {"command": "workout",     "description": "Днешната тренировка"},
        {"command": "menu",        "description": "Меню с тренировки и трудност"},
        {"command": "stats",       "description": "Моята статистика"},
        {"command": "preferences", "description": "Настройки за тренировки"},
        {"command": "start",       "description": "Начало"},
    ]
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{BASE_URL}/setMyCommands", json={"commands": commands})
            return r.json()
    except Exception as e:
        logger.warning("setMyCommands error: %s", e)
        return None


# ── Workout rendering ──────────────────────────────────────────────────────

def _build_exercise_keyboard(plan: WorkoutPlan, plan_id: int, done_set: set) -> list:
    keyboard = []
    for idx, ex in enumerate(plan.exercises):
        mark = "[x]" if ex.name in done_set else "[ ]"
        keyboard.append([{"text": f"{mark} {ex.name}", "callback_data": f"done|{plan_id}|{idx}"}])
    keyboard.append([{"text": "Всичко готово!", "callback_data": f"done|{plan_id}|ALL"}])
    return keyboard


async def _render_workout(
    telegram_id: int,
    plan: WorkoutPlan,
    plan_id: int,
    header: str,
    mark_as_sent: bool = False,
) -> None:
    """Render a persisted workout plan as a Telegram message with inline checklist."""
    user = db.get_user(telegram_id)
    if not user:
        return

    yt_links: dict[str, str] = {}
    for ex in plan.exercises:
        yt_links[ex.name] = await search_youtube(ex.youtube_query or ex.name)

    lines = [
        header,
        f"{plan.estimated_duration} | ~{plan.estimated_calories} ккал | {plan.difficulty.capitalize()}",
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
        yt   = html.escape(yt_links.get(ex.name, ""), quote=True)
        name = html.escape(ex.name)
        lines.append(f'{i}. <b>{name}</b> — {detail}  <a href="{yt}">видео</a>  (+{ex.xp} XP)')

    lines += [
        "",
        f"Level: <b>{user['level']}</b> | XP: <b>{user['xp']}</b> | Streak: <b>{user['streak']} дни</b>",
    ]

    logs     = db.get_today_logs(user["id"])
    done_set = {l["exercise_name"] for l in logs if l["completed"]}
    keyboard = _build_exercise_keyboard(plan, plan_id, done_set)

    result = await send_message(telegram_id, "\n".join(lines), reply_markup={"inline_keyboard": keyboard})
    if result and mark_as_sent:
        db.update_user_state(
            user["id"],
            workout_sent_today=True,
            last_workout_message_id=result.get("message_id"),
        )


# ── Workout sending ────────────────────────────────────────────────────────

async def send_workout_for_day(telegram_id: int, weekday: int, mark_as_sent: bool = False) -> None:
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

    category_key = WEEKDAY_TO_CATEGORY.get(weekday)
    if not category_key:
        return

    today    = date.today()
    is_today = (weekday == today.weekday())

    # For today's scheduled send (mark_as_sent=True), reuse a cached plan
    if is_today and mark_as_sent:
        cached = db.get_today_plan(user["id"], category_key)
        if cached:
            plan = WorkoutPlan(**cached["plan"])
            day_name = DAYS_BG[weekday]
            header = f"<b>Тренировка {day_name}</b> — {plan.day_type}"
            await _render_workout(telegram_id, plan, cached["id"], header, mark_as_sent=True)
            return

    # Show generation notice only for interactive (user-initiated) requests
    if not mark_as_sent:
        await send_message(telegram_id, "Генерирам тренировка...")

    difficulty  = user.get("difficulty", "beginner")
    preferences = db.get_user_preferences(user["id"])
    plan, source = await generate_workout(user, category_key, difficulty, preferences)
    plan_id = db.save_generated_plan(user["id"], category_key, source, plan.model_dump())

    day_name = DAYS_BG[weekday]
    header   = f"<b>Тренировка {day_name}</b> — {plan.day_type}"
    await _render_workout(telegram_id, plan, plan_id, header, mark_as_sent=mark_as_sent)


async def send_daily_workout(telegram_id: int) -> None:
    """Send today's scheduled workout and mark it as sent."""
    today = date.today()
    await send_workout_for_day(telegram_id, today.weekday(), mark_as_sent=True)


async def send_quick_workout(telegram_id: int, quick_type: str) -> None:
    """Send an on-demand workout chosen from the menu, personalized via AI."""
    user = db.get_user(telegram_id)
    if not user:
        return

    category = _QUICK_TO_CATEGORY.get(quick_type)
    if not category:
        return

    preferences = db.get_user_preferences(user["id"])
    difficulty  = user.get("difficulty", "beginner")

    # Override equipment for type-specific quick workouts
    quick_prefs = dict(preferences)
    if quick_type in _QUICK_EQUIPMENT:
        quick_prefs["equipment"] = _QUICK_EQUIPMENT[quick_type]
    elif quick_type == "hiit":
        pass  # use user's own equipment

    await send_message(telegram_id, "Генерирам тренировка...")
    plan, source = await generate_workout(user, category, difficulty, quick_prefs)
    plan_id = db.save_generated_plan(user["id"], f"quick:{quick_type}", source, plan.model_dump())

    label  = _QUICK_LABELS.get(quick_type, plan.day_type)
    header = f"<b>{label}</b>"
    await _render_workout(telegram_id, plan, plan_id, header, mark_as_sent=False)


async def send_regenerated_today(telegram_id: int) -> None:
    """Generate a fresh workout for today (for 'give me another' requests)."""
    today   = date.today()
    weekday = today.weekday()
    if weekday == 6:
        await send_message(telegram_id, "Неделя е — почивен ден.")
        return

    user = db.get_user(telegram_id)
    if not user:
        return

    category_key = WEEKDAY_TO_CATEGORY.get(weekday)
    if not category_key:
        return

    difficulty  = user.get("difficulty", "beginner")
    preferences = db.get_user_preferences(user["id"])
    plan, source = await generate_workout(user, category_key, difficulty, preferences)
    plan_id = db.save_generated_plan(user["id"], category_key, source, plan.model_dump())

    day_name = DAYS_BG[weekday]
    header   = f"<b>Тренировка {day_name}</b> — {plan.day_type} (нова)"
    await _render_workout(telegram_id, plan, plan_id, header, mark_as_sent=False)


async def send_reminder(telegram_id: int) -> None:
    await send_message(
        telegram_id,
        "<b>Напомняне</b>\n\nТренировката за днес още не е отметена. "
        "20-45 минути са достатъчни. Отвори тренировката по-горе и започни.",
    )
    user = db.get_user(telegram_id)
    if user:
        db.update_user_state(user["id"], reminder_sent_today=True)


# ── Workout menu ───────────────────────────────────────────────────────────

async def send_workout_menu(chat_id: int) -> None:
    keyboard = [
        [{"text": "Днешната планирана тренировка", "callback_data": "menu|today"}],
        [
            {"text": "Бягане — пътека",   "callback_data": "menu|quick|running"},
            {"text": "Въже за скачане",   "callback_data": "menu|quick|jump_rope"},
        ],
        [
            {"text": "Сила с ластици",    "callback_data": "menu|quick|strength_bands"},
            {"text": "HIIT кардио",       "callback_data": "menu|quick|hiit"},
        ],
        [
            {"text": "Само Core",         "callback_data": "menu|quick|core"},
            {"text": "Стречинг / Мобилност", "callback_data": "menu|quick|stretching"},
        ],
        [
            {"text": "Виж друг ден",      "callback_data": "menu|days"},
            {"text": "Промени трудност",  "callback_data": "menu|diff_menu"},
        ],
    ]
    await send_message(
        chat_id,
        "<b>Какво ще тренираш сега?</b>\nИзбери според оборудването и времето, с което разполагаш.",
        reply_markup={"inline_keyboard": keyboard},
    )


async def send_day_picker(chat_id: int) -> None:
    keyboard = [
        [
            {"text": "Пон — HIIT", "callback_data": "menu|day|0"},
            {"text": "Вт — Сила",  "callback_data": "menu|day|1"},
        ],
        [
            {"text": "Ср — Лека",  "callback_data": "menu|day|2"},
            {"text": "Чет — HIIT", "callback_data": "menu|day|3"},
        ],
        [
            {"text": "Пет — Сила", "callback_data": "menu|day|4"},
            {"text": "Съб — Лека", "callback_data": "menu|day|5"},
        ],
        [{"text": "← Назад към менюто", "callback_data": "menu|back"}],
    ]
    await send_message(chat_id, "<b>Избери ден:</b>", reply_markup={"inline_keyboard": keyboard})


async def send_difficulty_menu(chat_id: int) -> None:
    keyboard = [
        [
            {"text": "По-лесно", "callback_data": "menu|diff|easier"},
            {"text": "По-трудно", "callback_data": "menu|diff|harder"},
        ],
        [{"text": "← Назад към менюто", "callback_data": "menu|back"}],
    ]
    await send_message(chat_id, "<b>Промени трудност:</b>", reply_markup={"inline_keyboard": keyboard})


# ── Preferences menu ───────────────────────────────────────────────────────

def _build_pref_main(prefs: dict) -> tuple[str, list]:
    mins        = prefs.get("session_minutes") or 35
    equip_names = [_EQUIPMENT_LABELS.get(e, e) for e in (prefs.get("equipment") or [])]
    goal_names  = [_GOAL_LABELS.get(g, g)      for g in (prefs.get("goals")     or [])]
    text = (
        "<b>Настройки за тренировки</b>\n\n"
        f"Оборудване: <i>{', '.join(equip_names) or '—'}</i>\n"
        f"Цели: <i>{', '.join(goal_names) or '—'}</i>\n"
        f"Продължителност: <i>{mins} мин</i>"
    )
    keyboard = [
        [
            {"text": "Оборудване",   "callback_data": "pref|sub|equip"},
            {"text": "Цели",         "callback_data": "pref|sub|goals"},
        ],
        [
            {"text": "Мускули",      "callback_data": "pref|sub|muscles"},
            {"text": f"{mins} мин →","callback_data": "pref|mins"},
        ],
        [{"text": "Изключени упражнения", "callback_data": "pref|sub|excl"}],
    ]
    return text, keyboard


def _build_pref_submenu(sub: str, prefs: dict) -> tuple[str, list]:
    if sub == "equip":
        owned = set(prefs.get("equipment") or [])
        text  = "<b>Оборудване</b>\n\nОтбележи с какво разполагаш:"
        items = list(_EQUIPMENT_LABELS.items())
        rows  = []
        for i in range(0, len(items), 2):
            row = []
            for key, label in items[i:i + 2]:
                mark = "✓" if key in owned else "○"
                row.append({"text": f"{mark} {label}", "callback_data": f"pref|equip|{key}"})
            rows.append(row)
        rows.append([{"text": "← Назад", "callback_data": "pref|main"}])
        return text, rows

    elif sub == "goals":
        owned = set(prefs.get("goals") or [])
        text  = "<b>Цели</b>\n\nИзбери своите цели:"
        items = list(_GOAL_LABELS.items())
        rows  = []
        for i in range(0, len(items), 2):
            row = []
            for key, label in items[i:i + 2]:
                mark = "✓" if key in owned else "○"
                row.append({"text": f"{mark} {label}", "callback_data": f"pref|goal|{key}"})
            rows.append(row)
        rows.append([{"text": "← Назад", "callback_data": "pref|main"}])
        return text, rows

    elif sub == "muscles":
        owned = set(prefs.get("target_muscles") or [])
        text  = "<b>Фокусирани мускули</b>\n\nИзбери мускулни групи за акцент:"
        items = list(_MUSCLE_LABELS.items())
        rows  = []
        for i in range(0, len(items), 2):
            row = []
            for key, label in items[i:i + 2]:
                mark = "✓" if key in owned else "○"
                row.append({"text": f"{mark} {label}", "callback_data": f"pref|muscle|{key}"})
            rows.append(row)
        rows.append([{"text": "← Назад", "callback_data": "pref|main"}])
        return text, rows

    elif sub == "excl":
        exclusions = prefs.get("exclusions") or []
        text = _build_excl_text(exclusions)
        rows = []
        for excl in exclusions:
            display = excl[:20]
            cb      = f"pref|excl|rm|{excl}"[:64]
            rows.append([{"text": f"Премахни: {display}", "callback_data": cb}])
        rows.append([{"text": "← Назад", "callback_data": "pref|main"}])
        return text, rows

    return "<b>Настройки</b>", [[{"text": "← Назад", "callback_data": "pref|main"}]]


def _build_excl_text(exclusions: list) -> str:
    if exclusions:
        return (
            f"<b>Изключени упражнения</b>\n\n"
            f"Изключени: <i>{', '.join(exclusions)}</i>\n\n"
            "За добавяне напиши в чата: \"имам контузия на <b>коляното</b>\""
        )
    return (
        "<b>Изключени упражнения</b>\n\n"
        "Няма изключени упражнения.\n\n"
        "За добавяне напиши в чата: \"имам контузия на <b>коляното</b>\""
    )


async def send_preferences_menu(telegram_id: int) -> None:
    user = db.get_user(telegram_id)
    if not user:
        await send_message(telegram_id, "Напиши /start за да се регистрираш.")
        return
    prefs = db.get_user_preferences(user["id"])
    text, keyboard = _build_pref_main(prefs)
    await send_message(telegram_id, text, reply_markup={"inline_keyboard": keyboard})


async def handle_pref_callback(callback_query: dict) -> None:
    cq_id      = callback_query["id"]
    message    = callback_query.get("message", {})
    chat_id    = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    telegram_id = callback_query["from"]["id"]
    data = callback_query.get("data", "")

    user = db.get_user(telegram_id)
    if not user:
        await answer_callback_query(cq_id, "Напиши /start")
        return

    await answer_callback_query(cq_id)

    parts = data.split("|")
    if len(parts) < 2:
        return
    cmd = parts[1]

    if cmd == "main":
        prefs = db.get_user_preferences(user["id"])
        text, keyboard = _build_pref_main(prefs)
        await edit_message(chat_id, message_id, text, {"inline_keyboard": keyboard})

    elif cmd == "sub" and len(parts) > 2:
        prefs = db.get_user_preferences(user["id"])
        text, keyboard = _build_pref_submenu(parts[2], prefs)
        await edit_message(chat_id, message_id, text, {"inline_keyboard": keyboard})

    elif cmd == "equip" and len(parts) > 2:
        item    = parts[2]
        prefs   = db.get_user_preferences(user["id"])
        current = list(prefs.get("equipment") or [])
        if item in current:
            current.remove(item)
        else:
            current.append(item)
        db.patch_user_preferences(user["id"], equipment=current)
        prefs["equipment"] = current
        _, keyboard = _build_pref_submenu("equip", prefs)
        await edit_message_reply_markup(chat_id, message_id, {"inline_keyboard": keyboard})

    elif cmd == "goal" and len(parts) > 2:
        item    = parts[2]
        prefs   = db.get_user_preferences(user["id"])
        current = list(prefs.get("goals") or [])
        if item in current:
            current.remove(item)
        else:
            current.append(item)
        db.patch_user_preferences(user["id"], goals=current)
        prefs["goals"] = current
        _, keyboard = _build_pref_submenu("goals", prefs)
        await edit_message_reply_markup(chat_id, message_id, {"inline_keyboard": keyboard})

    elif cmd == "muscle" and len(parts) > 2:
        item    = parts[2]
        prefs   = db.get_user_preferences(user["id"])
        current = list(prefs.get("target_muscles") or [])
        if item in current:
            current.remove(item)
        else:
            current.append(item)
        db.patch_user_preferences(user["id"], target_muscles=current)
        prefs["target_muscles"] = current
        _, keyboard = _build_pref_submenu("muscles", prefs)
        await edit_message_reply_markup(chat_id, message_id, {"inline_keyboard": keyboard})

    elif cmd == "excl" and len(parts) > 3 and parts[2] == "rm":
        item    = "|".join(parts[3:])
        prefs   = db.get_user_preferences(user["id"])
        current = list(prefs.get("exclusions") or [])
        if item in current:
            current.remove(item)
        db.patch_user_preferences(user["id"], exclusions=current)
        prefs["exclusions"] = current
        text, keyboard = _build_pref_submenu("excl", prefs)
        await edit_message(chat_id, message_id, text, {"inline_keyboard": keyboard})

    elif cmd == "mins":
        prefs   = db.get_user_preferences(user["id"])
        current = prefs.get("session_minutes") or 35
        options = [20, 30, 35, 45, 60]
        try:
            idx      = options.index(current)
            new_mins = options[(idx + 1) % len(options)]
        except ValueError:
            new_mins = 35
        db.patch_user_preferences(user["id"], session_minutes=new_mins)
        prefs["session_minutes"] = new_mins
        text, keyboard = _build_pref_main(prefs)
        await edit_message(chat_id, message_id, text, {"inline_keyboard": keyboard})


# ── Callback routing ───────────────────────────────────────────────────────

async def handle_menu_callback(callback_query: dict) -> None:
    cq_id      = callback_query["id"]
    chat_id    = callback_query["message"]["chat"]["id"]
    telegram_id = callback_query["from"]["id"]
    data = callback_query.get("data", "")

    parts  = data.split("|")
    action = parts[1] if len(parts) > 1 else ""

    if action == "today":
        await answer_callback_query(cq_id)
        await send_daily_workout(telegram_id)

    elif action == "quick" and len(parts) > 2:
        await answer_callback_query(cq_id)
        await send_quick_workout(telegram_id, parts[2])

    elif action == "days":
        await answer_callback_query(cq_id)
        await send_day_picker(chat_id)

    elif action == "diff_menu":
        await answer_callback_query(cq_id)
        await send_difficulty_menu(chat_id)

    elif action == "back":
        await answer_callback_query(cq_id)
        await send_workout_menu(chat_id)

    elif action == "day" and len(parts) > 2:
        await answer_callback_query(cq_id)
        await send_workout_for_day(telegram_id, int(parts[2]))

    elif action == "diff" and len(parts) > 2:
        direction = parts[2]
        user = db.get_user(telegram_id)
        if not user:
            await answer_callback_query(cq_id, "Напиши /start първо.")
            return
        levels = ["beginner", "intermediate", "advanced"]
        labels = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}
        idx    = levels.index(user.get("difficulty", "beginner"))
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
            await answer_callback_query(cq_id, f"Вече си на {labels[user.get('difficulty','beginner')]}.")

    else:
        await answer_callback_query(cq_id)


async def handle_exercise_callback(callback_query: dict) -> None:
    cq_id      = callback_query["id"]
    message    = callback_query.get("message", {})
    chat_id    = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    telegram_id = callback_query["from"]["id"]
    data = callback_query.get("data", "")

    if data.startswith("menu|"):
        await handle_menu_callback(callback_query)
        return

    if data.startswith("pref|"):
        await handle_pref_callback(callback_query)
        return

    if not data.startswith("done|"):
        await answer_callback_query(cq_id)
        return

    # Format: done|<plan_id>|<idx_or_ALL>
    parts = data.split("|", 2)
    if len(parts) < 3:
        await answer_callback_query(cq_id)
        return

    _, plan_id_str, idx_or_all = parts

    user = db.get_user(telegram_id)
    if not user:
        await answer_callback_query(cq_id, "Регистрирай се с /start")
        return

    try:
        plan_id = int(plan_id_str)
    except ValueError:
        await answer_callback_query(cq_id)
        return

    row = db.get_plan_by_id(plan_id, user["id"])
    if not row:
        await answer_callback_query(cq_id, "Планът не е намерен.")
        return

    plan = WorkoutPlan(**row["plan"])

    if idx_or_all == "ALL":
        logs     = db.get_today_logs(user["id"])
        done_set = {l["exercise_name"] for l in logs if l["completed"]}
        for ex in plan.exercises:
            if ex.name not in done_set:
                db.log_exercise(user["id"], ex.name, True, ex.xp)
                db.add_xp(telegram_id, ex.xp)
        streak = db.update_streak(telegram_id)

        updated_logs = db.get_today_logs(user["id"])
        done_set     = {l["exercise_name"] for l in updated_logs if l["completed"]}
        keyboard     = _build_exercise_keyboard(plan, plan_id, done_set)
        if message_id and chat_id:
            await edit_message_reply_markup(chat_id, message_id, {"inline_keyboard": keyboard})

        await answer_callback_query(cq_id, f"Тренировката е завършена! Streak: {streak} дни")
        await send_message(chat_id, f"<b>Тренировката е завършена.</b>\nStreak: <b>{streak} дни</b>")
        return

    try:
        idx = int(idx_or_all)
    except ValueError:
        await answer_callback_query(cq_id)
        return

    if idx < 0 or idx >= len(plan.exercises):
        await answer_callback_query(cq_id)
        return

    ex = plan.exercises[idx]

    logs     = db.get_today_logs(user["id"])
    done_set = {l["exercise_name"] for l in logs if l["completed"]}
    if ex.name in done_set:
        await answer_callback_query(cq_id, "Вече отметено.")
        return

    db.log_exercise(user["id"], ex.name, True, ex.xp)
    result_tuple = db.add_xp(telegram_id, ex.xp)
    leveled_up   = result_tuple[1] if isinstance(result_tuple, tuple) else False

    if message_id and chat_id:
        updated_logs = db.get_today_logs(user["id"])
        done_set     = {l["exercise_name"] for l in updated_logs if l["completed"]}
        keyboard     = _build_exercise_keyboard(plan, plan_id, done_set)
        await edit_message_reply_markup(chat_id, message_id, {"inline_keyboard": keyboard})

    fb = f"+{ex.xp} XP"
    if leveled_up:
        user_refreshed = db.get_user(telegram_id)
        fb += f" — Level up! Сега си Level {user_refreshed['level']}"
    await answer_callback_query(cq_id, fb)


# ── Weekly report ──────────────────────────────────────────────────────────

async def send_weekly_report(telegram_id: int) -> None:
    user = db.get_user(telegram_id)
    if not user:
        return

    today      = date.today()
    week_start = today - timedelta(days=today.weekday() + 1)  # last Monday
    logs       = db.get_week_logs(user["id"], week_start)
    completed  = [l for l in logs if l["completed"]]
    workouts_done   = len(set(l["log_date"] for l in completed))
    total_xp        = sum(l.get("xp_earned", 0) for l in completed)
    exercises_count = len(completed)
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
