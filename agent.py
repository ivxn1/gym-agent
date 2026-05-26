import os
import re
import json
import logging
from datetime import date, timedelta
import anthropic
import database as db
from workouts import get_workout_plan
from youtube import search_youtube
from models import EQUIPMENT_OPTIONS, GOAL_OPTIONS, MUSCLE_OPTIONS

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """Ти си личен фитнес треньор на потребителя в Telegram. Говориш на български.
Стил: директен, кратък — максимум 3-4 изречения. Без излишни емоджи — използвай най-много 1 на съобщение.
Форматиране: ВИНАГИ използвай Telegram HTML тагове — <b>удебелен</b> и <i>курсив</i>. НИКОГА НЕ използвай markdown синтаксис: ЗАБРАНЕНО е да пишеш **text** или *text* или __text__. Само HTML тагове.

Програма: понеделник/четвъртък — кардио HIIT + core, вторник/петък — сила с ластици и тежест на тялото, сряда/събота — лека активност + мобилност, неделя — почивка.
Тренировките са персонализирани с AI според настройките на потребителя (оборудване, цели, мускули, изключени упражнения).

Правила:
- Когато питат за тренировка за конкретен ден — ЗАДЪЛЖИТЕЛНО използвай инструмента get_workout_plan и изброй точните упражнения от резултата.
- Когато казват "беше лесно" или "искам по-тежко" — използвай adapt_difficulty(too_easy).
- Когато казват "пропуснах" или "не можах" — отговори без осъждане, използвай adapt_difficulty(missed_day).
- Когато питат как се прави упражнение — обясни с 2-3 ключови точки за техниката, без инструменти.
- Когато споменат оборудване, цели, мускули или контузии → използвай update_preferences.
- Когато питат за настройките си → използвай get_preferences.
- Когато искат нова/друга тренировка за днес → използвай regenerate_workout.
- НИКОГА не създавай текстово "меню" с emoji списъци. Ако питат какво можеш, кажи им да напишат /menu или /workout."""

TOOLS = [
    {
        "name": "get_workout_plan",
        "description": "Връща плана за тренировка за конкретен ден и ниво на трудност.",
        "input_schema": {
            "type": "object",
            "properties": {
                "weekday": {"type": "integer", "description": "Ден от седмицата (0=понеделник, 6=неделя)"},
                "difficulty": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
            },
            "required": ["weekday", "difficulty"],
        },
    },
    {
        "name": "save_workout_log",
        "description": "Записва изпълнено упражнение в базата данни.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "exercise_name": {"type": "string"},
                "completed": {"type": "boolean"},
                "xp_earned": {"type": "integer"},
            },
            "required": ["user_id", "exercise_name", "completed"],
        },
    },
    {
        "name": "adapt_difficulty",
        "description": "Адаптира трудността на тренировката спрямо feedback. Връща новото ниво.",
        "input_schema": {
            "type": "object",
            "properties": {
                "telegram_id": {"type": "integer"},
                "feedback": {"type": "string", "description": "too_easy, too_hard, или missed_day"},
            },
            "required": ["telegram_id", "feedback"],
        },
    },
    {
        "name": "get_weekly_stats",
        "description": "Взима седмичната статистика на потребителя.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "search_youtube",
        "description": "Търси YouTube видео за упражнение.",
        "input_schema": {
            "type": "object",
            "properties": {
                "exercise_name": {"type": "string"},
            },
            "required": ["exercise_name"],
        },
    },
    {
        "name": "get_preferences",
        "description": "Взима настройките на потребителя — оборудване, цели, мускули, изключени упражнения.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "update_preferences",
        "description": (
            "Обновява предпочитанията на потребителя. "
            "Използвай когато споменат оборудване, цели, мускули или контузии."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "add_equipment":    {"type": "array", "items": {"type": "string"},
                                     "description": f"Equipment keys to add: {EQUIPMENT_OPTIONS}"},
                "remove_equipment": {"type": "array", "items": {"type": "string"}},
                "set_goals":        {"type": "array", "items": {"type": "string"},
                                     "description": f"Replace goals list: {GOAL_OPTIONS}"},
                "add_exclusions":   {"type": "array", "items": {"type": "string"},
                                     "description": "Injury/movement keywords to exclude"},
                "remove_exclusions":{"type": "array", "items": {"type": "string"}},
                "session_minutes":  {"type": "integer", "description": "Session duration 15–120 min"},
            },
        },
    },
    {
        "name": "regenerate_workout",
        "description": "Генерира нова тренировка за днес и я изпраща. Използвай когато потребителят поиска друга тренировка.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


async def execute_tool(tool_name: str, tool_input: dict, context: dict) -> str:
    try:
        if tool_name == "get_workout_plan":
            plan = get_workout_plan(tool_input["weekday"], tool_input["difficulty"])
            if not plan:
                return json.dumps({"result": "Неделя е — почивен ден!"})
            return json.dumps({
                "day_type": plan.day_type,
                "exercises": [e.model_dump() for e in plan.exercises],
                "duration": plan.estimated_duration,
                "calories": plan.estimated_calories,
            })

        elif tool_name == "save_workout_log":
            db.log_exercise(
                user_id=tool_input["user_id"],
                exercise_name=tool_input["exercise_name"],
                completed=tool_input["completed"],
                xp_earned=tool_input.get("xp_earned", 10),
            )
            return json.dumps({"result": "saved"})

        elif tool_name == "adapt_difficulty":
            telegram_id = tool_input["telegram_id"]
            feedback = tool_input["feedback"]
            user = db.get_user(telegram_id)
            if not user:
                return json.dumps({"error": "user not found"})

            levels = ["beginner", "intermediate", "advanced"]
            current_idx = levels.index(user.get("difficulty", "beginner"))

            if feedback == "too_easy" and current_idx < 2:
                new_diff = levels[current_idx + 1]
                db.update_user(telegram_id, difficulty=new_diff)
                return json.dumps({"new_difficulty": new_diff, "message": "Трудността е увеличена!"})
            elif feedback == "too_hard" and current_idx > 0:
                new_diff = levels[current_idx - 1]
                db.update_user(telegram_id, difficulty=new_diff)
                return json.dumps({"new_difficulty": new_diff, "message": "Трудността е намалена."})
            elif feedback == "missed_day":
                return json.dumps({"new_difficulty": user["difficulty"], "message": "Без проблем, утре продължаваме!"})
            return json.dumps({"new_difficulty": user["difficulty"]})

        elif tool_name == "get_weekly_stats":
            user_id = tool_input["user_id"]
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            logs = db.get_week_logs(user_id, week_start)
            completed = [l for l in logs if l["completed"]]
            total_xp = sum(l.get("xp_earned", 0) for l in completed)
            workouts_done = len(set(l["log_date"] for l in completed))
            return json.dumps({
                "workouts_done": workouts_done,
                "exercises_completed": len(completed),
                "total_xp": total_xp,
                "week_start": str(week_start),
            })

        elif tool_name == "search_youtube":
            url = await search_youtube(tool_input["exercise_name"])
            return json.dumps({"url": url})

        elif tool_name == "get_preferences":
            user = context["user"]
            prefs = db.get_user_preferences(user["id"])
            return json.dumps({
                "equipment":      prefs.get("equipment", []),
                "goals":          prefs.get("goals", []),
                "target_muscles": prefs.get("target_muscles", []),
                "exclusions":     prefs.get("exclusions", []),
                "session_minutes":prefs.get("session_minutes", 35),
            })

        elif tool_name == "update_preferences":
            user   = context["user"]
            prefs  = db.get_user_preferences(user["id"])
            updates: dict = {}

            if "add_equipment" in tool_input:
                current = list(prefs.get("equipment") or [])
                for e in tool_input["add_equipment"]:
                    if e in EQUIPMENT_OPTIONS and e not in current:
                        current.append(e)
                updates["equipment"] = current

            if "remove_equipment" in tool_input:
                current = list(updates.get("equipment", prefs.get("equipment") or []))
                for e in tool_input["remove_equipment"]:
                    if e in current:
                        current.remove(e)
                updates["equipment"] = current

            if "set_goals" in tool_input:
                updates["goals"] = [g for g in tool_input["set_goals"] if g in GOAL_OPTIONS]

            if "add_exclusions" in tool_input:
                current = list(prefs.get("exclusions") or [])
                for e in tool_input["add_exclusions"]:
                    if e and e not in current:
                        current.append(e)
                updates["exclusions"] = current

            if "remove_exclusions" in tool_input:
                current = list(updates.get("exclusions", prefs.get("exclusions") or []))
                for e in tool_input["remove_exclusions"]:
                    if e in current:
                        current.remove(e)
                updates["exclusions"] = current

            if "session_minutes" in tool_input:
                mins = int(tool_input["session_minutes"])
                if 15 <= mins <= 120:
                    updates["session_minutes"] = mins

            if updates:
                db.patch_user_preferences(user["id"], **updates)
            return json.dumps({"result": "saved", "updated": list(updates.keys())})

        elif tool_name == "regenerate_workout":
            import telegram_client as tg
            await tg.send_regenerated_today(context["telegram_id"])
            return json.dumps({"result": "Генерирах нова тренировка за днес."})

    except Exception as e:
        logger.error("Tool %s error: %s", tool_name, e)
        return json.dumps({"error": str(e)})

    return json.dumps({"error": "unknown tool"})


async def chat(telegram_id: int, user_message: str) -> str:
    """Main agent loop — processes a message and returns a reply."""
    user = db.get_user(telegram_id)
    if not user:
        return "Не те намирам в системата. Моля напиши /start за да се регистрираш."

    state = db.get_user_state(user["id"])
    history = state.get("conversation_history") or []

    # Add user message to history
    history.append({"role": "user", "content": user_message})

    messages = history[-20:]  # Keep last 20

    # Agentic loop
    for _ in range(5):  # Max 5 tool-call iterations
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            # Process all tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await execute_tool(block.name, block.input, {"telegram_id": telegram_id, "user": user})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Append assistant response and tool results to messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            continue

        # End of loop — extract text
        reply = ""
        for block in response.content:
            if hasattr(block, "text"):
                reply += block.text

        # Save updated conversation history
        history.append({"role": "assistant", "content": reply})
        if len(history) > 20:
            history = history[-20:]
        db.update_user_state(user["id"], conversation_history=history)

        reply = _md_to_html(reply)
        return reply or "Не разбрах. Опитай пак!"

    return "Имах проблем с обработването на заявката. Опитай пак!"


def _md_to_html(text: str) -> str:
    """Convert any residual markdown to Telegram HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text, flags=re.DOTALL)
    text = re.sub(r'(?<![_])_([^_]+)_(?![_])', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


async def check_and_adapt_difficulty(telegram_id: int):
    """Check past 2-3 weeks of consistency and auto-adjust difficulty."""
    user = db.get_user(telegram_id)
    if not user:
        return

    today = date.today()
    # Check last 14 days
    logs_14 = []
    for i in range(14):
        d = today - timedelta(days=i + 1)
        week_start = d - timedelta(days=d.weekday())
        logs = db.get_week_logs(user["id"], week_start)
        logs_14.extend([l for l in logs if l["completed"]])

    # Count unique workout days
    workout_days = len(set(l["log_date"] for l in logs_14))
    levels = ["beginner", "intermediate", "advanced"]
    current_idx = levels.index(user.get("difficulty", "beginner"))

    # 10+ workout days in 14 days → upgrade difficulty
    if workout_days >= 10 and current_idx < 2:
        new_diff = levels[current_idx + 1]
        db.update_user(telegram_id, difficulty=new_diff)
        logger.info("Auto-upgraded %s to %s", telegram_id, new_diff)
        return new_diff

    return None
