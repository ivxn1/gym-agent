from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# Controlled vocabulary shared by preferences menu, generator prompt, and agent tools
EQUIPMENT_OPTIONS = [
    "treadmill", "jump_rope", "resistance_band", "bodyweight",
    "dumbbells", "barbell", "kettlebell", "pull_up_bar", "mat",
]
GOAL_OPTIONS = ["weight_loss", "muscle", "endurance", "flexibility", "general_fitness"]
MUSCLE_OPTIONS = ["chest", "back", "shoulders", "arms", "legs", "glutes", "core", "full_body"]


class User(BaseModel):
    telegram_id: int
    name: str
    level: int = 1
    xp: int = 0
    streak: int = 0
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    timezone: str = "Europe/Sofia"


class WorkoutLog(BaseModel):
    user_id: int
    log_date: date
    exercise_name: str
    completed: bool = False
    xp_earned: int = 0


class UserState(BaseModel):
    user_id: int
    conversation_history: list = []
    workout_sent_today: bool = False
    reminder_sent_today: bool = False
    last_workout_message_id: Optional[int] = None


class WeeklyStats(BaseModel):
    user_id: int
    week_start: date
    workouts_done: int = 0
    total_calories: int = 0
    personal_records: dict = {}
    total_xp_earned: int = 0


class Exercise(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[str] = None
    duration: Optional[str] = None
    rest: Optional[str] = None
    xp: int = 10
    youtube_query: str = ""


class WorkoutPlan(BaseModel):
    day_type: str
    exercises: list[Exercise]
    estimated_duration: str
    estimated_calories: int
    difficulty: str


class UserPreferences(BaseModel):
    user_id: int
    equipment: list = ["treadmill", "jump_rope", "resistance_band", "bodyweight"]
    goals: list = ["weight_loss", "muscle", "endurance"]
    target_muscles: list = []
    exclusions: list = []
    session_minutes: int = 35


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None
