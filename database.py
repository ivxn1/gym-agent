import os
import json
import logging
from datetime import date, timedelta
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _client = create_client(url, key)
    return _client


# ── Users ──────────────────────────────────────────────────────────────────

def get_user(telegram_id: int) -> Optional[dict]:
    try:
        res = get_client().table("users").select("*").eq("telegram_id", telegram_id).single().execute()
        return res.data
    except Exception:
        return None


def upsert_user(telegram_id: int, name: str) -> dict:
    client = get_client()
    existing = get_user(telegram_id)
    if existing:
        return existing
    data = {"telegram_id": telegram_id, "name": name, "level": 1, "xp": 0, "streak": 0, "difficulty": "beginner"}
    res = client.table("users").insert(data).execute()
    return res.data[0]


def update_user(telegram_id: int, **fields) -> dict:
    res = get_client().table("users").update(fields).eq("telegram_id", telegram_id).execute()
    return res.data[0] if res.data else {}


def add_xp(telegram_id: int, xp_amount: int) -> dict:
    user = get_user(telegram_id)
    if not user:
        return {}
    new_xp = user["xp"] + xp_amount
    new_level = user["level"]
    # Level thresholds: 100xp per level, increasing by 50 each level
    xp_for_next = 100 + (new_level - 1) * 50
    leveled_up = False
    while new_xp >= xp_for_next:
        new_xp -= xp_for_next
        new_level += 1
        xp_for_next = 100 + (new_level - 1) * 50
        leveled_up = True
    return update_user(telegram_id, xp=new_xp, level=new_level), leveled_up


def update_streak(telegram_id: int) -> int:
    user = get_user(telegram_id)
    if not user:
        return 0
    today = date.today()
    # Check if worked out yesterday
    yesterday = today - timedelta(days=1)
    res = get_client().table("workout_logs") \
        .select("log_date") \
        .eq("user_id", user["id"]) \
        .eq("log_date", str(yesterday)) \
        .eq("completed", True) \
        .limit(1).execute()
    if res.data:
        new_streak = user["streak"] + 1
    else:
        new_streak = 1
    update_user(telegram_id, streak=new_streak)
    return new_streak


# ── Workout Logs ───────────────────────────────────────────────────────────

def log_exercise(user_id: int, exercise_name: str, completed: bool, xp_earned: int = 0):
    today = str(date.today())
    client = get_client()
    existing = client.table("workout_logs") \
        .select("id") \
        .eq("user_id", user_id) \
        .eq("log_date", today) \
        .eq("exercise_name", exercise_name) \
        .execute()
    if existing.data:
        client.table("workout_logs").update({"completed": completed, "xp_earned": xp_earned}) \
            .eq("id", existing.data[0]["id"]).execute()
    else:
        client.table("workout_logs").insert({
            "user_id": user_id,
            "log_date": today,
            "exercise_name": exercise_name,
            "completed": completed,
            "xp_earned": xp_earned,
        }).execute()


def get_today_logs(user_id: int) -> list:
    res = get_client().table("workout_logs") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("log_date", str(date.today())).execute()
    return res.data or []


def get_week_logs(user_id: int, week_start: date) -> list:
    week_end = week_start + timedelta(days=6)
    res = get_client().table("workout_logs") \
        .select("*") \
        .eq("user_id", user_id) \
        .gte("log_date", str(week_start)) \
        .lte("log_date", str(week_end)).execute()
    return res.data or []


# ── User State ─────────────────────────────────────────────────────────────

def get_user_state(user_id: int) -> dict:
    try:
        res = get_client().table("user_state").select("*").eq("user_id", user_id).single().execute()
        return res.data
    except Exception:
        # Create default state
        data = {
            "user_id": user_id,
            "conversation_history": [],
            "workout_sent_today": False,
            "reminder_sent_today": False,
            "last_workout_message_id": None,
        }
        get_client().table("user_state").insert(data).execute()
        return data


def update_user_state(user_id: int, **fields):
    client = get_client()
    state = get_user_state(user_id)
    client.table("user_state").update(fields).eq("user_id", user_id).execute()


def append_conversation(user_id: int, role: str, content: str):
    state = get_user_state(user_id)
    history = state.get("conversation_history") or []
    history.append({"role": role, "content": content})
    # Keep last 20 messages
    if len(history) > 20:
        history = history[-20:]
    update_user_state(user_id, conversation_history=history)


def reset_daily_state():
    """Called at midnight to reset daily flags for all users."""
    get_client().table("user_state").update({
        "workout_sent_today": False,
        "reminder_sent_today": False,
    }).neq("user_id", 0).execute()


# ── Weekly Stats ───────────────────────────────────────────────────────────

def upsert_weekly_stats(user_id: int, week_start: date, **fields):
    client = get_client()
    existing = client.table("weekly_stats") \
        .select("id") \
        .eq("user_id", user_id) \
        .eq("week_start", str(week_start)).execute()
    if existing.data:
        client.table("weekly_stats").update(fields).eq("id", existing.data[0]["id"]).execute()
    else:
        client.table("weekly_stats").insert({"user_id": user_id, "week_start": str(week_start), **fields}).execute()


def get_weekly_stats(user_id: int, week_start: date) -> Optional[dict]:
    try:
        res = get_client().table("weekly_stats") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("week_start", str(week_start)).single().execute()
        return res.data
    except Exception:
        return None


def get_all_active_users() -> list:
    res = get_client().table("users").select("*").execute()
    return res.data or []
