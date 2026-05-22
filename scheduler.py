import logging
import asyncio
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

import database as db
import telegram_client as tg
from agent import check_and_adapt_difficulty

logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone("Europe/Sofia")


async def job_send_daily_workouts():
    """08:00 Sofia — send workout to all users."""
    logger.info("Running job: send_daily_workouts")
    db.reset_daily_state()
    users = db.get_all_active_users()
    for user in users:
        try:
            await tg.send_daily_workout(user["telegram_id"])
            await asyncio.sleep(0.1)  # gentle rate-limit
        except Exception as e:
            logger.error("Error sending workout to %s: %s", user["telegram_id"], e)


async def job_send_reminders():
    """17:00 Sofia — remind users who haven't started."""
    logger.info("Running job: send_reminders")
    users = db.get_all_active_users()
    for user in users:
        try:
            state = db.get_user_state(user["id"])
            if not state:
                continue
            # Only remind if workout was sent but nothing completed yet
            if not state.get("workout_sent_today"):
                continue
            if state.get("reminder_sent_today"):
                continue
            today_logs = db.get_today_logs(user["id"])
            any_done = any(l["completed"] for l in today_logs)
            if not any_done:
                await tg.send_reminder(user["telegram_id"])
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error("Error sending reminder to %s: %s", user["telegram_id"], e)


async def job_weekly_report():
    """Sunday 20:00 Sofia — send weekly summary."""
    logger.info("Running job: weekly_report")
    users = db.get_all_active_users()
    for user in users:
        try:
            await tg.send_weekly_report(user["telegram_id"])
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error("Error sending weekly report to %s: %s", user["telegram_id"], e)


async def job_auto_adapt_difficulty():
    """Sunday 21:00 Sofia — auto-adjust difficulty based on 2-week performance."""
    logger.info("Running job: auto_adapt_difficulty")
    users = db.get_all_active_users()
    for user in users:
        try:
            new_diff = await check_and_adapt_difficulty(user["telegram_id"])
            if new_diff:
                await tg.send_message(
                    user["telegram_id"],
                    f"📈 <b>Трудността е автоматично увеличена!</b>\n\n"
                    f"Тренираш редовно последните 2 седмици — браво! "
                    f"От следващата седмица минаваш на ниво <b>{new_diff.capitalize()}</b>. 💪"
                )
        except Exception as e:
            logger.error("Error adapting difficulty for %s: %s", user["telegram_id"], e)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    # Daily workout — 08:00 Sofia
    scheduler.add_job(
        job_send_daily_workouts,
        CronTrigger(hour=8, minute=0, timezone=TIMEZONE),
        id="daily_workout",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Afternoon reminder — 17:00 Sofia
    scheduler.add_job(
        job_send_reminders,
        CronTrigger(hour=17, minute=0, timezone=TIMEZONE),
        id="afternoon_reminder",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Weekly report — Sunday 20:00 Sofia
    scheduler.add_job(
        job_weekly_report,
        CronTrigger(day_of_week="sun", hour=20, minute=0, timezone=TIMEZONE),
        id="weekly_report",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # Auto-adapt difficulty — Sunday 21:00 Sofia
    scheduler.add_job(
        job_auto_adapt_difficulty,
        CronTrigger(day_of_week="sun", hour=21, minute=0, timezone=TIMEZONE),
        id="auto_adapt",
        replace_existing=True,
        misfire_grace_time=600,
    )

    return scheduler
