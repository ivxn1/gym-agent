"""Static workout library. Difficulty scales sets/reps at runtime."""
from models import Exercise, WorkoutPlan

# XP values
XP_EASY = 8
XP_MEDIUM = 12
XP_HARD = 18

WORKOUT_LIBRARY: dict[str, dict[str, WorkoutPlan]] = {
    # ── Monday / Thursday — Cardio HIIT + Core ─────────────────────────────
    "cardio_hiit": {
        "beginner": WorkoutPlan(
            day_type="Кардио HIIT + Core",
            exercises=[
                Exercise(name="Jumping Jacks", duration="30 сек", rest="15 сек", xp=XP_EASY, youtube_query="jumping jacks"),
                Exercise(name="High Knees", duration="30 сек", rest="15 сек", xp=XP_EASY, youtube_query="high knees"),
                Exercise(name="Burpees", sets=3, reps="5", rest="45 сек", xp=XP_MEDIUM, youtube_query="burpees"),
                Exercise(name="Mountain Climbers", duration="30 сек", rest="20 сек", xp=XP_MEDIUM, youtube_query="mountain climbers"),
                Exercise(name="Plank", duration="30 сек", rest="30 сек", xp=XP_EASY, youtube_query="plank"),
                Exercise(name="Crunches", sets=3, reps="12", rest="30 сек", xp=XP_EASY, youtube_query="crunches"),
                Exercise(name="Leg Raise", sets=3, reps="8", rest="30 сек", xp=XP_MEDIUM, youtube_query="leg raise"),
            ],
            estimated_duration="25 мин",
            estimated_calories=220,
            difficulty="beginner",
        ),
        "intermediate": WorkoutPlan(
            day_type="Кардио HIIT + Core",
            exercises=[
                Exercise(name="Jumping Jacks", duration="45 сек", rest="10 сек", xp=XP_EASY, youtube_query="jumping jacks"),
                Exercise(name="High Knees", duration="45 сек", rest="10 сек", xp=XP_EASY, youtube_query="high knees"),
                Exercise(name="Burpees", sets=4, reps="8", rest="30 сек", xp=XP_MEDIUM, youtube_query="burpees"),
                Exercise(name="Mountain Climbers", duration="45 сек", rest="15 сек", xp=XP_MEDIUM, youtube_query="mountain climbers"),
                Exercise(name="Jump Rope", duration="60 сек", rest="20 сек", xp=XP_MEDIUM, youtube_query="jump rope"),
                Exercise(name="Plank", duration="45 сек", rest="20 сек", xp=XP_EASY, youtube_query="plank"),
                Exercise(name="Russian Twist", sets=3, reps="20", rest="30 сек", xp=XP_MEDIUM, youtube_query="russian twist"),
                Exercise(name="Leg Raise", sets=3, reps="12", rest="25 сек", xp=XP_MEDIUM, youtube_query="leg raise"),
                Exercise(name="Dead Bug", sets=3, reps="10", rest="30 сек", xp=XP_MEDIUM, youtube_query="dead bug"),
            ],
            estimated_duration="35 мин",
            estimated_calories=340,
            difficulty="intermediate",
        ),
        "advanced": WorkoutPlan(
            day_type="Кардио HIIT + Core",
            exercises=[
                Exercise(name="Burpees", sets=5, reps="10", rest="20 сек", xp=XP_HARD, youtube_query="burpees"),
                Exercise(name="Jump Rope", duration="90 сек", rest="15 сек", xp=XP_MEDIUM, youtube_query="jump rope"),
                Exercise(name="Mountain Climbers", duration="60 сек", rest="10 сек", xp=XP_MEDIUM, youtube_query="mountain climbers"),
                Exercise(name="High Knees", duration="60 сек", rest="10 сек", xp=XP_EASY, youtube_query="high knees"),
                Exercise(name="Plank", duration="60 сек", rest="15 сек", xp=XP_EASY, youtube_query="plank"),
                Exercise(name="Russian Twist", sets=4, reps="24", rest="20 сек", xp=XP_MEDIUM, youtube_query="russian twist"),
                Exercise(name="Leg Raise", sets=4, reps="15", rest="20 сек", xp=XP_MEDIUM, youtube_query="leg raise"),
                Exercise(name="Dead Bug", sets=4, reps="12", rest="25 сек", xp=XP_MEDIUM, youtube_query="dead bug"),
                Exercise(name="Hollow Body Hold", duration="30 сек", rest="20 сек", xp=XP_HARD, youtube_query="hollow body hold"),
            ],
            estimated_duration="45 мин",
            estimated_calories=460,
            difficulty="advanced",
        ),
    },
    # ── Tuesday / Friday — Силова тренировка ──────────────────────────────
    "strength": {
        "beginner": WorkoutPlan(
            day_type="Сила — Ластици + Тяло",
            exercises=[
                Exercise(name="Squat", sets=3, reps="10", rest="45 сек", xp=XP_EASY, youtube_query="squat"),
                Exercise(name="Push Up", sets=3, reps="8", rest="45 сек", xp=XP_MEDIUM, youtube_query="push up"),
                Exercise(name="Resistance Band Row", sets=3, reps="10", rest="45 сек", xp=XP_MEDIUM, youtube_query="resistance band row"),
                Exercise(name="Glute Bridge", sets=3, reps="12", rest="30 сек", xp=XP_EASY, youtube_query="glute bridge"),
                Exercise(name="Resistance Band Bicep Curl", sets=3, reps="10", rest="30 сек", xp=XP_EASY, youtube_query="resistance band curl"),
                Exercise(name="Lunge", sets=3, reps="8 на крак", rest="45 сек", xp=XP_MEDIUM, youtube_query="lunge"),
            ],
            estimated_duration="30 мин",
            estimated_calories=200,
            difficulty="beginner",
        ),
        "intermediate": WorkoutPlan(
            day_type="Сила — Ластици + Тяло",
            exercises=[
                Exercise(name="Squat", sets=4, reps="12", rest="40 сек", xp=XP_EASY, youtube_query="squat"),
                Exercise(name="Push Up", sets=4, reps="12", rest="40 сек", xp=XP_MEDIUM, youtube_query="push up"),
                Exercise(name="Resistance Band Row", sets=4, reps="12", rest="40 сек", xp=XP_MEDIUM, youtube_query="resistance band row"),
                Exercise(name="Hip Thrust", sets=4, reps="15", rest="35 сек", xp=XP_MEDIUM, youtube_query="hip thrust"),
                Exercise(name="Resistance Band Overhead Press", sets=3, reps="12", rest="40 сек", xp=XP_MEDIUM, youtube_query="resistance band press"),
                Exercise(name="Lunge", sets=3, reps="12 на крак", rest="40 сек", xp=XP_MEDIUM, youtube_query="lunge"),
                Exercise(name="Resistance Band Bicep Curl", sets=3, reps="15", rest="30 сек", xp=XP_EASY, youtube_query="resistance band curl"),
                Exercise(name="Tricep Dips", sets=3, reps="12", rest="30 сек", xp=XP_MEDIUM, youtube_query="tricep dips"),
            ],
            estimated_duration="40 мин",
            estimated_calories=300,
            difficulty="intermediate",
        ),
        "advanced": WorkoutPlan(
            day_type="Сила — Ластици + Тяло",
            exercises=[
                Exercise(name="Jump Squat", sets=4, reps="15", rest="30 сек", xp=XP_HARD, youtube_query="jump squat"),
                Exercise(name="Archer Push Up", sets=4, reps="8 на ръка", rest="40 сек", xp=XP_HARD, youtube_query="archer push up"),
                Exercise(name="Resistance Band Row", sets=4, reps="15", rest="30 сек", xp=XP_MEDIUM, youtube_query="resistance band row"),
                Exercise(name="Single Leg Hip Thrust", sets=4, reps="12 на крак", rest="35 сек", xp=XP_HARD, youtube_query="single leg hip thrust"),
                Exercise(name="Resistance Band Overhead Press", sets=4, reps="15", rest="30 сек", xp=XP_MEDIUM, youtube_query="resistance band press"),
                Exercise(name="Bulgarian Split Squat", sets=3, reps="10 на крак", rest="45 сек", xp=XP_HARD, youtube_query="bulgarian split squat"),
                Exercise(name="Resistance Band Curl", sets=4, reps="15", rest="25 сек", xp=XP_EASY, youtube_query="resistance band curl"),
                Exercise(name="Pike Push Up", sets=3, reps="10", rest="40 сек", xp=XP_HARD, youtube_query="pike push up"),
            ],
            estimated_duration="50 мин",
            estimated_calories=380,
            difficulty="advanced",
        ),
    },
    # ── Wednesday / Saturday — Лека активност ─────────────────────────────
    "active_recovery": {
        "beginner": WorkoutPlan(
            day_type="Лека активност + Мобилност",
            exercises=[
                Exercise(name="Jump Rope", duration="3 мин", rest="60 сек", xp=XP_EASY, youtube_query="jump rope"),
                Exercise(name="World's Greatest Stretch", sets=2, reps="5 на страна", rest="30 сек", xp=XP_EASY, youtube_query="world's greatest stretch"),
                Exercise(name="Hip Circles", sets=2, reps="10 на посока", rest="20 сек", xp=XP_EASY, youtube_query="hip circles"),
                Exercise(name="Inchworm", sets=2, reps="6", rest="30 сек", xp=XP_EASY, youtube_query="inchworm"),
                Exercise(name="Cat-Cow Stretch", sets=2, reps="10", rest="20 сек", xp=XP_EASY, youtube_query="cat cow stretch"),
                Exercise(name="Child's Pose", duration="60 сек", rest="—", xp=XP_EASY, youtube_query="child's pose stretch"),
            ],
            estimated_duration="20 мин",
            estimated_calories=120,
            difficulty="beginner",
        ),
        "intermediate": WorkoutPlan(
            day_type="Лека активност + Мобилност",
            exercises=[
                Exercise(name="Jump Rope", duration="5 мин", rest="60 сек", xp=XP_EASY, youtube_query="jump rope"),
                Exercise(name="World's Greatest Stretch", sets=3, reps="6 на страна", rest="20 сек", xp=XP_EASY, youtube_query="world's greatest stretch"),
                Exercise(name="Hip Circles", sets=3, reps="12 на посока", rest="15 сек", xp=XP_EASY, youtube_query="hip circles"),
                Exercise(name="Inchworm", sets=3, reps="8", rest="25 сек", xp=XP_EASY, youtube_query="inchworm"),
                Exercise(name="Foam Rolling (Legs)", duration="3 мин", rest="—", xp=XP_EASY, youtube_query="foam rolling"),
                Exercise(name="Pigeon Pose", duration="60 сек на страна", rest="—", xp=XP_EASY, youtube_query="pigeon pose stretch"),
                Exercise(name="Bird Dog", sets=3, reps="8 на страна", rest="20 сек", xp=XP_EASY, youtube_query="bird dog"),
            ],
            estimated_duration="25 мин",
            estimated_calories=150,
            difficulty="intermediate",
        ),
        "advanced": WorkoutPlan(
            day_type="Лека активност + Мобилност",
            exercises=[
                Exercise(name="Jump Rope", duration="8 мин", rest="45 сек", xp=XP_MEDIUM, youtube_query="jump rope"),
                Exercise(name="World's Greatest Stretch", sets=3, reps="8 на страна", rest="15 сек", xp=XP_EASY, youtube_query="world's greatest stretch"),
                Exercise(name="Hip Circles", sets=3, reps="15 на посока", rest="10 сек", xp=XP_EASY, youtube_query="hip circles"),
                Exercise(name="Inchworm", sets=3, reps="10", rest="20 сек", xp=XP_EASY, youtube_query="inchworm"),
                Exercise(name="Foam Rolling Full Body", duration="5 мин", rest="—", xp=XP_EASY, youtube_query="foam rolling"),
                Exercise(name="Cossack Squat", sets=3, reps="8 на страна", rest="25 сек", xp=XP_MEDIUM, youtube_query="cossack squat"),
                Exercise(name="Thoracic Rotation", sets=3, reps="10 на страна", rest="15 сек", xp=XP_EASY, youtube_query="thoracic rotation"),
                Exercise(name="Ankle Circles", sets=2, reps="15 на посока", rest="—", xp=XP_EASY, youtube_query="ankle mobility"),
            ],
            estimated_duration="30 мин",
            estimated_calories=180,
            difficulty="advanced",
        ),
    },
}

DAY_TO_WORKOUT = {
    0: "cardio_hiit",   # Monday
    1: "strength",      # Tuesday
    2: "active_recovery",  # Wednesday
    3: "cardio_hiit",   # Thursday
    4: "strength",      # Friday
    5: "active_recovery",  # Saturday
    6: None,            # Sunday — rest
}


def get_workout_plan(weekday: int, difficulty: str) -> WorkoutPlan | None:
    workout_key = DAY_TO_WORKOUT.get(weekday)
    if workout_key is None:
        return None
    plans = WORKOUT_LIBRARY.get(workout_key, {})
    return plans.get(difficulty) or plans.get("beginner")
