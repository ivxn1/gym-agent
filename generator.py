"""AI-powered workout generator with equipment/preference filtering and fallback to workouts.py."""
import asyncio
import logging
import os
from typing import Optional

import anthropic

from models import WorkoutPlan, Exercise
from workouts import get_workout_plan, get_quick_workout

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-haiku-4-5-20251001"

WEEKDAY_TO_CATEGORY: dict[int, str] = {
    0: "hiit_core",
    1: "strength",
    2: "recovery",
    3: "hiit_core",
    4: "strength",
    5: "recovery",
}

CATEGORY_LABELS: dict[str, str] = {
    "hiit_core": "HIIT + Core",
    "strength": "Сила с ластици",
    "recovery": "Лека активност",
}

CATEGORY_FALLBACK_KEY: dict[str, str] = {
    "hiit_core": "hiit",
    "strength": "strength_bands",
    "recovery": "stretching",
}

_DIFFICULTY_PARAMS: dict[str, dict] = {
    "beginner":     {"min": 5, "max": 7,  "xp": 8},
    "intermediate": {"min": 7, "max": 9,  "xp": 12},
    "advanced":     {"min": 8, "max": 10, "xp": 18},
}

_BUILD_WORKOUT_TOOL = {
    "name": "build_workout",
    "description": "Output a structured workout plan.",
    "input_schema": {
        "type": "object",
        "properties": {
            "day_type": {"type": "string", "description": "Bulgarian workout type label"},
            "estimated_duration": {"type": "string", "description": "e.g. '35 мин'"},
            "estimated_calories": {"type": "integer"},
            "exercises": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":               {"type": "string", "description": "Exercise name in English"},
                        "sets":               {"type": "integer"},
                        "reps":               {"type": "string"},
                        "duration":           {"type": "string", "description": "e.g. '30 сек'"},
                        "rest":               {"type": "string"},
                        "xp":                 {"type": "integer", "description": "8 easy / 12 medium / 18 hard"},
                        "youtube_query":      {"type": "string", "description": "English YouTube search query"},
                        "required_equipment": {
                            "type": "string",
                            "enum": [
                                "treadmill", "jump_rope", "resistance_band", "bodyweight",
                                "dumbbells", "barbell", "kettlebell", "pull_up_bar", "mat", "none",
                            ],
                        },
                    },
                    "required": ["name", "xp", "youtube_query", "required_equipment"],
                },
            },
        },
        "required": ["day_type", "estimated_duration", "estimated_calories", "exercises"],
    },
}


async def generate_workout(
    user: dict, category: str, difficulty: str, preferences: dict
) -> tuple[WorkoutPlan, str]:
    """Generate a personalized workout. Returns (plan, source). Never raises."""
    try:
        plan = await asyncio.wait_for(
            _call_ai(user, category, difficulty, preferences),
            timeout=20.0,
        )
        if plan:
            return plan, "ai"
    except asyncio.TimeoutError:
        logger.warning("generate_workout timeout for user %s", user.get("telegram_id"))
    except Exception as e:
        logger.error("generate_workout error for user %s: %s", user.get("telegram_id"), e)
    return _fallback_plan(category, difficulty), "fallback"


async def _call_ai(
    user: dict, category: str, difficulty: str, preferences: dict
) -> Optional[WorkoutPlan]:
    equipment       = preferences.get("equipment")       or ["treadmill", "jump_rope", "resistance_band", "bodyweight"]
    goals           = preferences.get("goals")           or ["general_fitness"]
    target_muscles  = preferences.get("target_muscles")  or []
    exclusions      = preferences.get("exclusions")      or []
    session_minutes = preferences.get("session_minutes") or 35

    params    = _DIFFICULTY_PARAMS.get(difficulty, _DIFFICULTY_PARAMS["beginner"])
    cat_label = CATEGORY_LABELS.get(category, category)

    lines = [
        f"Build a {cat_label} workout for a {difficulty}-level athlete.",
        f"Session duration: ~{session_minutes} minutes. Number of exercises: {params['min']}–{params['max']}.",
        f"ONLY use this equipment (no substitutions): {', '.join(equipment)}.",
        f"Goals: {', '.join(goals)}.",
    ]
    if target_muscles:
        lines.append(f"Emphasise these muscle groups: {', '.join(target_muscles)}.")
    if exclusions:
        lines.append(
            f"STRICTLY EXCLUDE any exercise involving: {', '.join(exclusions)}. "
            "Check both the exercise name and youtube_query."
        )
    lines += [
        f"Set xp={params['xp']} for every exercise.",
        "Exercise names in English. day_type label in Bulgarian.",
    ]
    if category == "hiit_core":
        lines.append("High-energy intervals + core work, brief rest periods.")
    elif category == "strength":
        lines.append("Resistance training: compound + isolation moves.")
    elif category == "recovery":
        lines.append("Light mobility, stretching, low intensity, full range of motion.")

    response = await asyncio.to_thread(
        _client.messages.create,
        model=MODEL,
        max_tokens=2048,
        tools=[_BUILD_WORKOUT_TOOL],
        tool_choice={"type": "tool", "name": "build_workout"},
        messages=[{"role": "user", "content": "\n".join(lines)}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "build_workout":
            return _validate(block.input, equipment, exclusions, difficulty, params)
    return None


def _validate(
    data: dict, equipment: list, exclusions: list, difficulty: str, params: dict
) -> Optional[WorkoutPlan]:
    valid: list[Exercise] = []
    for ex in data.get("exercises", []):
        req   = ex.get("required_equipment", "none")
        name  = ex.get("name", "")
        query = ex.get("youtube_query", "")

        if req not in ("none", "bodyweight") and req not in equipment:
            logger.debug("Dropping %s — needs %s not in equipment", name, req)
            continue

        if any(e.lower() in name.lower() or e.lower() in query.lower() for e in exclusions):
            logger.debug("Dropping %s — matches exclusion", name)
            continue

        xp_raw = ex.get("xp", params["xp"])
        xp = 8 if xp_raw <= 9 else (12 if xp_raw <= 14 else 18)

        valid.append(Exercise(
            name=name,
            sets=ex.get("sets"),
            reps=str(ex["reps"]) if ex.get("reps") is not None else None,
            duration=ex.get("duration"),
            rest=ex.get("rest"),
            xp=xp,
            youtube_query=query,
        ))

    if len(valid) < params["min"]:
        logger.warning("Only %d valid exercises after filtering (min %d)", len(valid), params["min"])
        return None

    return WorkoutPlan(
        day_type=data.get("day_type", "Тренировка"),
        exercises=valid,
        estimated_duration=data.get("estimated_duration", f"{params['min'] * 5} мин"),
        estimated_calories=data.get("estimated_calories", 250),
        difficulty=difficulty,
    )


def _fallback_plan(category: str, difficulty: str) -> WorkoutPlan:
    key  = CATEGORY_FALLBACK_KEY.get(category, "hiit")
    plan = get_quick_workout(key)
    if plan:
        return plan
    plan = get_workout_plan(0, difficulty or "beginner")
    if plan:
        return plan
    return WorkoutPlan(
        day_type="Тренировка",
        exercises=[
            Exercise(name="Push-ups",          sets=3, reps="10",     xp=8, youtube_query="push ups tutorial"),
            Exercise(name="Bodyweight Squats",  sets=3, reps="15",     xp=8, youtube_query="bodyweight squats"),
            Exercise(name="Plank",              duration="30 сек",     xp=8, youtube_query="plank exercise form"),
            Exercise(name="Mountain Climbers",  duration="30 сек",     xp=8, youtube_query="mountain climbers"),
            Exercise(name="Jumping Jacks",      duration="30 сек",     xp=8, youtube_query="jumping jacks"),
        ],
        estimated_duration="20 мин",
        estimated_calories=150,
        difficulty=difficulty or "beginner",
    )
