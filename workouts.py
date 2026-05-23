"""Static workout library. Difficulty scales sets/reps at runtime."""
from models import Exercise, WorkoutPlan

# XP values
XP_EASY = 8
XP_MEDIUM = 12
XP_HARD = 18

WORKOUT_LIBRARY: dict[str, dict[str, WorkoutPlan]] = {
    # ── Monday — Cardio HIIT + Core (variant A) ────────────────────────────
    "cardio_hiit_a": {
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
    # ── Tuesday — Силова тренировка (variant A) ────────────────────────────
    "strength_a": {
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
    # ── Wednesday — Лека активност (variant A) ─────────────────────────────
    "recovery_a": {
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
    # ── Thursday — Cardio HIIT + Core (variant B) ──────────────────────────
    "cardio_hiit_b": {
        "beginner": WorkoutPlan(
            day_type="Кардио HIIT + Core",
            exercises=[
                Exercise(name="Skater Hops", duration="30 сек", rest="15 сек", xp=XP_EASY, youtube_query="skater hops"),
                Exercise(name="Squat to Knee Drive", sets=3, reps="10", rest="30 сек", xp=XP_MEDIUM, youtube_query="squat knee drive"),
                Exercise(name="Mountain Climbers", duration="30 сек", rest="20 сек", xp=XP_MEDIUM, youtube_query="mountain climbers"),
                Exercise(name="Jump Rope", duration="45 сек", rest="20 сек", xp=XP_MEDIUM, youtube_query="jump rope"),
                Exercise(name="Side Plank", duration="20 сек на страна", rest="20 сек", xp=XP_MEDIUM, youtube_query="side plank"),
                Exercise(name="Bicycle Crunch", sets=3, reps="12", rest="25 сек", xp=XP_EASY, youtube_query="bicycle crunch"),
                Exercise(name="Flutter Kicks", sets=3, reps="20", rest="25 сек", xp=XP_EASY, youtube_query="flutter kicks"),
            ],
            estimated_duration="25 мин",
            estimated_calories=230,
            difficulty="beginner",
        ),
        "intermediate": WorkoutPlan(
            day_type="Кардио HIIT + Core",
            exercises=[
                Exercise(name="Skater Hops", duration="45 сек", rest="10 сек", xp=XP_MEDIUM, youtube_query="skater hops"),
                Exercise(name="Squat to Knee Drive", sets=4, reps="14", rest="20 сек", xp=XP_MEDIUM, youtube_query="squat knee drive"),
                Exercise(name="Tuck Jumps", sets=3, reps="10", rest="30 сек", xp=XP_HARD, youtube_query="tuck jumps"),
                Exercise(name="Jump Rope", duration="75 сек", rest="15 сек", xp=XP_MEDIUM, youtube_query="jump rope"),
                Exercise(name="Mountain Climbers", duration="45 сек", rest="15 сек", xp=XP_MEDIUM, youtube_query="mountain climbers"),
                Exercise(name="Side Plank", duration="40 сек на страна", rest="15 сек", xp=XP_MEDIUM, youtube_query="side plank"),
                Exercise(name="Bicycle Crunch", sets=4, reps="20", rest="20 сек", xp=XP_MEDIUM, youtube_query="bicycle crunch"),
                Exercise(name="V-Up", sets=3, reps="12", rest="25 сек", xp=XP_MEDIUM, youtube_query="v-up exercise"),
                Exercise(name="Flutter Kicks", sets=3, reps="30", rest="20 сек", xp=XP_EASY, youtube_query="flutter kicks"),
            ],
            estimated_duration="35 мин",
            estimated_calories=350,
            difficulty="intermediate",
        ),
        "advanced": WorkoutPlan(
            day_type="Кардио HIIT + Core",
            exercises=[
                Exercise(name="Tuck Jumps", sets=4, reps="15", rest="20 сек", xp=XP_HARD, youtube_query="tuck jumps"),
                Exercise(name="Skater Hops", duration="60 сек", rest="10 сек", xp=XP_MEDIUM, youtube_query="skater hops"),
                Exercise(name="Burpee Broad Jump", sets=4, reps="8", rest="25 сек", xp=XP_HARD, youtube_query="burpee broad jump"),
                Exercise(name="Jump Rope Double Unders", duration="60 сек", rest="20 сек", xp=XP_HARD, youtube_query="double unders jump rope"),
                Exercise(name="Mountain Climbers", duration="60 сек", rest="10 сек", xp=XP_MEDIUM, youtube_query="mountain climbers"),
                Exercise(name="Side Plank with Reach", duration="45 сек на страна", rest="15 сек", xp=XP_HARD, youtube_query="side plank reach"),
                Exercise(name="V-Up", sets=4, reps="18", rest="20 сек", xp=XP_MEDIUM, youtube_query="v-up exercise"),
                Exercise(name="Bicycle Crunch", sets=4, reps="30", rest="15 сек", xp=XP_MEDIUM, youtube_query="bicycle crunch"),
                Exercise(name="Hollow Body Hold", duration="40 сек", rest="20 сек", xp=XP_HARD, youtube_query="hollow body hold"),
            ],
            estimated_duration="45 мин",
            estimated_calories=470,
            difficulty="advanced",
        ),
    },
    # ── Friday — Силова тренировка (variant B) ─────────────────────────────
    "strength_b": {
        "beginner": WorkoutPlan(
            day_type="Сила — Ластици + Тяло",
            exercises=[
                Exercise(name="Sumo Squat", sets=3, reps="12", rest="40 сек", xp=XP_EASY, youtube_query="sumo squat"),
                Exercise(name="Incline Push Up", sets=3, reps="10", rest="40 сек", xp=XP_MEDIUM, youtube_query="incline push up"),
                Exercise(name="Resistance Band Pull Apart", sets=3, reps="12", rest="30 сек", xp=XP_EASY, youtube_query="band pull apart"),
                Exercise(name="Step-Up", sets=3, reps="10 на крак", rest="40 сек", xp=XP_MEDIUM, youtube_query="step up exercise"),
                Exercise(name="Resistance Band Lateral Raise", sets=3, reps="12", rest="30 сек", xp=XP_EASY, youtube_query="band lateral raise"),
                Exercise(name="Superman", sets=3, reps="12", rest="30 сек", xp=XP_EASY, youtube_query="superman exercise"),
            ],
            estimated_duration="30 мин",
            estimated_calories=200,
            difficulty="beginner",
        ),
        "intermediate": WorkoutPlan(
            day_type="Сила — Ластици + Тяло",
            exercises=[
                Exercise(name="Sumo Squat", sets=4, reps="15", rest="35 сек", xp=XP_MEDIUM, youtube_query="sumo squat"),
                Exercise(name="Decline Push Up", sets=4, reps="12", rest="40 сек", xp=XP_MEDIUM, youtube_query="decline push up"),
                Exercise(name="Resistance Band Face Pull", sets=4, reps="15", rest="30 сек", xp=XP_MEDIUM, youtube_query="band face pull"),
                Exercise(name="Step-Up", sets=4, reps="12 на крак", rest="35 сек", xp=XP_MEDIUM, youtube_query="step up exercise"),
                Exercise(name="Resistance Band Lateral Raise", sets=3, reps="15", rest="30 сек", xp=XP_EASY, youtube_query="band lateral raise"),
                Exercise(name="Single Leg Glute Bridge", sets=3, reps="12 на крак", rest="30 сек", xp=XP_MEDIUM, youtube_query="single leg glute bridge"),
                Exercise(name="Resistance Band Deadlift", sets=4, reps="15", rest="35 сек", xp=XP_MEDIUM, youtube_query="band deadlift"),
                Exercise(name="Superman", sets=3, reps="15", rest="25 сек", xp=XP_EASY, youtube_query="superman exercise"),
            ],
            estimated_duration="40 мин",
            estimated_calories=300,
            difficulty="intermediate",
        ),
        "advanced": WorkoutPlan(
            day_type="Сила — Ластици + Тяло",
            exercises=[
                Exercise(name="Pistol Squat (assisted)", sets=4, reps="6 на крак", rest="45 сек", xp=XP_HARD, youtube_query="assisted pistol squat"),
                Exercise(name="Decline Push Up", sets=4, reps="15", rest="35 сек", xp=XP_MEDIUM, youtube_query="decline push up"),
                Exercise(name="Resistance Band Face Pull", sets=4, reps="18", rest="25 сек", xp=XP_MEDIUM, youtube_query="band face pull"),
                Exercise(name="Bulgarian Split Squat", sets=4, reps="10 на крак", rest="40 сек", xp=XP_HARD, youtube_query="bulgarian split squat"),
                Exercise(name="Resistance Band Deadlift", sets=4, reps="18", rest="30 сек", xp=XP_MEDIUM, youtube_query="band deadlift"),
                Exercise(name="Single Leg Glute Bridge", sets=4, reps="15 на крак", rest="25 сек", xp=XP_MEDIUM, youtube_query="single leg glute bridge"),
                Exercise(name="Diamond Push Up", sets=3, reps="12", rest="35 сек", xp=XP_HARD, youtube_query="diamond push up"),
                Exercise(name="Superman Hold", duration="40 сек", rest="20 сек", xp=XP_MEDIUM, youtube_query="superman hold"),
            ],
            estimated_duration="50 мин",
            estimated_calories=380,
            difficulty="advanced",
        ),
    },
    # ── Saturday — Лека активност (variant B) ──────────────────────────────
    "recovery_b": {
        "beginner": WorkoutPlan(
            day_type="Лека активност + Мобилност",
            exercises=[
                Exercise(name="Jump Rope", duration="3 мин", rest="60 сек", xp=XP_EASY, youtube_query="jump rope"),
                Exercise(name="Standing Forward Fold", duration="45 сек", rest="—", xp=XP_EASY, youtube_query="standing forward fold stretch"),
                Exercise(name="Shoulder Rolls", sets=2, reps="12 на посока", rest="—", xp=XP_EASY, youtube_query="shoulder rolls mobility"),
                Exercise(name="Deep Squat Hold", duration="45 сек", rest="20 сек", xp=XP_EASY, youtube_query="deep squat hold"),
                Exercise(name="Cobra Stretch", duration="45 сек", rest="—", xp=XP_EASY, youtube_query="cobra stretch"),
                Exercise(name="Neck Stretch", sets=2, reps="20 сек на страна", rest="—", xp=XP_EASY, youtube_query="neck stretch"),
            ],
            estimated_duration="20 мин",
            estimated_calories=120,
            difficulty="beginner",
        ),
        "intermediate": WorkoutPlan(
            day_type="Лека активност + Мобилност",
            exercises=[
                Exercise(name="Jump Rope", duration="5 мин", rest="60 сек", xp=XP_EASY, youtube_query="jump rope"),
                Exercise(name="Deep Squat Hold", duration="60 сек", rest="20 сек", xp=XP_EASY, youtube_query="deep squat hold"),
                Exercise(name="Standing Forward Fold", duration="60 сек", rest="—", xp=XP_EASY, youtube_query="standing forward fold stretch"),
                Exercise(name="Thread the Needle", sets=3, reps="8 на страна", rest="15 сек", xp=XP_EASY, youtube_query="thread the needle stretch"),
                Exercise(name="Cobra to Down Dog", sets=3, reps="8", rest="20 сек", xp=XP_EASY, youtube_query="cobra to downward dog"),
                Exercise(name="90/90 Hip Switch", sets=3, reps="8 на страна", rest="15 сек", xp=XP_MEDIUM, youtube_query="90 90 hip switch"),
                Exercise(name="Foam Rolling (Гръб)", duration="3 мин", rest="—", xp=XP_EASY, youtube_query="foam rolling back"),
            ],
            estimated_duration="25 мин",
            estimated_calories=150,
            difficulty="intermediate",
        ),
        "advanced": WorkoutPlan(
            day_type="Лека активност + Мобилност",
            exercises=[
                Exercise(name="Jump Rope", duration="8 мин", rest="45 сек", xp=XP_MEDIUM, youtube_query="jump rope"),
                Exercise(name="Deep Squat Hold", duration="90 сек", rest="20 сек", xp=XP_EASY, youtube_query="deep squat hold"),
                Exercise(name="90/90 Hip Switch", sets=3, reps="12 на страна", rest="10 сек", xp=XP_MEDIUM, youtube_query="90 90 hip switch"),
                Exercise(name="Thread the Needle", sets=3, reps="10 на страна", rest="10 сек", xp=XP_EASY, youtube_query="thread the needle stretch"),
                Exercise(name="Cobra to Down Dog", sets=3, reps="12", rest="15 сек", xp=XP_EASY, youtube_query="cobra to downward dog"),
                Exercise(name="Jefferson Curl (леко)", sets=3, reps="8", rest="25 сек", xp=XP_MEDIUM, youtube_query="jefferson curl"),
                Exercise(name="Foam Rolling Full Body", duration="5 мин", rest="—", xp=XP_EASY, youtube_query="foam rolling"),
                Exercise(name="Wrist Mobility", sets=2, reps="10 на посока", rest="—", xp=XP_EASY, youtube_query="wrist mobility"),
            ],
            estimated_duration="30 мин",
            estimated_calories=180,
            difficulty="advanced",
        ),
    },
}

DAY_TO_WORKOUT = {
    0: "cardio_hiit_a",  # Monday
    1: "strength_a",     # Tuesday
    2: "recovery_a",     # Wednesday
    3: "cardio_hiit_b",  # Thursday
    4: "strength_b",     # Friday
    5: "recovery_b",     # Saturday
    6: None,             # Sunday — rest
}


def get_workout_plan(weekday: int, difficulty: str) -> WorkoutPlan | None:
    workout_key = DAY_TO_WORKOUT.get(weekday)
    if workout_key is None:
        return None
    plans = WORKOUT_LIBRARY.get(workout_key, {})
    return plans.get(difficulty) or plans.get("beginner")


# ─────────────────────────────────────────────────────────────────────────
# Quick on-demand workouts — chosen from the menu, equipment-focused.
# Not tied to a specific weekday.
# ─────────────────────────────────────────────────────────────────────────

QUICK_WORKOUTS: dict[str, WorkoutPlan] = {
    "running": WorkoutPlan(
        day_type="Бягане на пътека",
        exercises=[
            Exercise(name="Загрявка — Ходене", duration="3 мин", rest="—", xp=XP_EASY, youtube_query="treadmill warm up walk"),
            Exercise(name="Леко бягане", duration="5 мин", rest="—", xp=XP_MEDIUM, youtube_query="easy jog treadmill"),
            Exercise(name="Интервал — Бързо бягане", sets=5, reps="1 мин бързо + 1 мин ходене", rest="—", xp=XP_HARD, youtube_query="treadmill HIIT intervals"),
            Exercise(name="Cool-down — Ходене", duration="3 мин", rest="—", xp=XP_EASY, youtube_query="treadmill cool down walk"),
        ],
        estimated_duration="25 мин",
        estimated_calories=280,
        difficulty="intermediate",
    ),
    "jump_rope": WorkoutPlan(
        day_type="Въже за скачане — Интервали",
        exercises=[
            Exercise(name="Загрявка — Леки скокове", duration="60 сек", rest="30 сек", xp=XP_EASY, youtube_query="jump rope warm up"),
            Exercise(name="Двукраки скокове", sets=3, reps="60 сек", rest="30 сек", xp=XP_MEDIUM, youtube_query="jump rope basic"),
            Exercise(name="High Knee скокове", sets=3, reps="30 сек", rest="30 сек", xp=XP_MEDIUM, youtube_query="jump rope high knees"),
            Exercise(name="Boxer Skip (последователно)", sets=3, reps="45 сек", rest="20 сек", xp=XP_MEDIUM, youtube_query="boxer skip jump rope"),
            Exercise(name="Финал — Темп", duration="60 сек", rest="—", xp=XP_HARD, youtube_query="fast jump rope"),
        ],
        estimated_duration="15 мин",
        estimated_calories=180,
        difficulty="intermediate",
    ),
    "core": WorkoutPlan(
        day_type="Core тренировка",
        exercises=[
            Exercise(name="Plank", duration="45 сек", rest="20 сек", xp=XP_EASY, youtube_query="plank"),
            Exercise(name="Crunches", sets=3, reps="15", rest="25 сек", xp=XP_EASY, youtube_query="crunches"),
            Exercise(name="Russian Twist", sets=3, reps="20", rest="25 сек", xp=XP_MEDIUM, youtube_query="russian twist"),
            Exercise(name="Leg Raise", sets=3, reps="12", rest="25 сек", xp=XP_MEDIUM, youtube_query="leg raise"),
            Exercise(name="Dead Bug", sets=3, reps="10", rest="25 сек", xp=XP_MEDIUM, youtube_query="dead bug"),
            Exercise(name="Bird Dog", sets=3, reps="10 на страна", rest="20 сек", xp=XP_EASY, youtube_query="bird dog"),
            Exercise(name="Side Plank", duration="30 сек на страна", rest="20 сек", xp=XP_MEDIUM, youtube_query="side plank"),
        ],
        estimated_duration="18 мин",
        estimated_calories=140,
        difficulty="intermediate",
    ),
    "stretching": WorkoutPlan(
        day_type="Стречинг + Мобилност",
        exercises=[
            Exercise(name="World's Greatest Stretch", sets=2, reps="6 на страна", rest="—", xp=XP_EASY, youtube_query="world's greatest stretch"),
            Exercise(name="Hip Circles", sets=2, reps="10 на посока", rest="—", xp=XP_EASY, youtube_query="hip circles"),
            Exercise(name="Cat-Cow Stretch", sets=2, reps="10", rest="—", xp=XP_EASY, youtube_query="cat cow stretch"),
            Exercise(name="Pigeon Pose", duration="60 сек на страна", rest="—", xp=XP_EASY, youtube_query="pigeon pose stretch"),
            Exercise(name="Child's Pose", duration="90 сек", rest="—", xp=XP_EASY, youtube_query="child's pose stretch"),
            Exercise(name="Thoracic Rotation", sets=2, reps="10 на страна", rest="—", xp=XP_EASY, youtube_query="thoracic rotation"),
            Exercise(name="Foam Rolling (Цяло тяло)", duration="5 мин", rest="—", xp=XP_EASY, youtube_query="foam rolling"),
        ],
        estimated_duration="20 мин",
        estimated_calories=100,
        difficulty="beginner",
    ),
    "strength_bands": WorkoutPlan(
        day_type="Сила с ластици",
        exercises=[
            Exercise(name="Squat", sets=4, reps="12", rest="40 сек", xp=XP_MEDIUM, youtube_query="squat"),
            Exercise(name="Push Up", sets=4, reps="10", rest="40 сек", xp=XP_MEDIUM, youtube_query="push up"),
            Exercise(name="Resistance Band Row", sets=4, reps="12", rest="40 сек", xp=XP_MEDIUM, youtube_query="resistance band row"),
            Exercise(name="Resistance Band Overhead Press", sets=3, reps="12", rest="35 сек", xp=XP_MEDIUM, youtube_query="resistance band press"),
            Exercise(name="Hip Thrust", sets=3, reps="15", rest="30 сек", xp=XP_MEDIUM, youtube_query="hip thrust"),
            Exercise(name="Resistance Band Bicep Curl", sets=3, reps="15", rest="25 сек", xp=XP_EASY, youtube_query="resistance band curl"),
            Exercise(name="Lunge", sets=3, reps="10 на крак", rest="35 сек", xp=XP_MEDIUM, youtube_query="lunge"),
        ],
        estimated_duration="35 мин",
        estimated_calories=280,
        difficulty="intermediate",
    ),
    "hiit": WorkoutPlan(
        day_type="HIIT кардио",
        exercises=[
            Exercise(name="Jumping Jacks", duration="45 сек", rest="15 сек", xp=XP_EASY, youtube_query="jumping jacks"),
            Exercise(name="Burpees", sets=4, reps="8", rest="30 сек", xp=XP_HARD, youtube_query="burpees"),
            Exercise(name="High Knees", duration="45 сек", rest="15 сек", xp=XP_MEDIUM, youtube_query="high knees"),
            Exercise(name="Mountain Climbers", duration="45 сек", rest="15 сек", xp=XP_MEDIUM, youtube_query="mountain climbers"),
            Exercise(name="Jump Squat", sets=3, reps="12", rest="25 сек", xp=XP_HARD, youtube_query="jump squat"),
            Exercise(name="Plank to Push-Up", sets=3, reps="8", rest="25 сек", xp=XP_MEDIUM, youtube_query="plank to push up"),
        ],
        estimated_duration="22 мин",
        estimated_calories=260,
        difficulty="intermediate",
    ),
}


def get_quick_workout(key: str) -> WorkoutPlan | None:
    return QUICK_WORKOUTS.get(key)
