# 💫━━━━━━━━━━━━━━━━━━
#   🌸 Scheduler Module 🌸
# 💫━━━━━━━━━━━━━━━━━━
import zoneinfo

from utils.loggers.espeon_log import espeon_log
from utils.schedules.helper import SchedulerManager

# 💫━━━━━━━━━━━━━━━━━━
#   🌸 Schedule Imports 🌸
# 💫━━━━━━━━━━━━━━━━━━
from .bingo_schedule import scheduled_bingo_opening

# 💫━━━━━━━━━━━━━━━━━━
#   🌸 Timezones & Scheduler Instance 🌸
# 💫━━━━━━━━━━━━━━━━━━
MANILA = zoneinfo.ZoneInfo("Asia/Manila")

# 🛠️ Create a SchedulerManager instance with Asia/Manila timezone
scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")


# 💫━━━━━━━━━━━━━━━━━━
#   🌸 Schedule Setup Function 🌸
# 💫━━━━━━━━━━━━━━━━━━
async def setup_scheduler(bot):
    """
    Set up scheduled tasks for the bot.
    """

    # 🌸 Bingo event opening on May 31 , 2026 12 PM Asia/Manila
    try:
        job = scheduler_manager.add_cron_job(
            func=scheduled_bingo_opening,
            name="bingo_opening_announcement",
            hour=12,
            minute=0,
            month=5,
            day_of_month=31,
            args=[bot],
            year=2026,  # Only runs in 2026
            timezone=MANILA,
        )
        espeon_log(
            "schedule_success",
            f"Scheduled Bingo opening announcement: {job.trigger}",
        )

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to schedule Bingo opening announcement: {e}",
            source="Scheduler Setup",
        )
    # Start the scheduler once to avoid duplicate-start runtime errors.
    if scheduler_manager.scheduler.running:
        espeon_log("schedule_success", "Scheduler already running. Skipping start().")
    else:
        scheduler_manager.start()
        espeon_log("schedule_success", "Scheduler started successfully.")

    # Attach the scheduler manager to the bot for later access
    bot.scheduler_manager = scheduler_manager
