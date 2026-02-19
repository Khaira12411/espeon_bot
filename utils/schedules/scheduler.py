# 💫━━━━━━━━━━━━━━━━━━
#   🌸 Scheduler Module 🌸
# 💫━━━━━━━━━━━━━━━━━━
import asyncio
import calendar
import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.loggers.espeon_log import espeon_log
from utils.schedules.helper import SchedulerManager

# 💫━━━━━━━━━━━━━━━━━━
#   🌸 Schedule Imports 🌸
# 💫━━━━━━━━━━━━━━━━━━
from .petal_lace_schedules import (
    scheduled_petal_lace_event_end,
    scheduled_petal_lace_opening,
    scheduled_petal_lace_shop_clear,
    reset_battle_roles
)

# 💫━━━━━━━━━━━━━━━━━━
#   🌸 Timezones & Scheduler Instance 🌸
# 💫━━━━━━━━━━━━━━━━━━
MANILA = zoneinfo.ZoneInfo("Asia/Manila")
NYC = zoneinfo.ZoneInfo("America/New_York")  # auto-handles EST/EDT

# 🛠️ Create a SchedulerManager instance with Asia/Manila timezone
scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")


# 💫━━━━━━━━━━━━━━━━━━
#   🌸 Schedule Setup Function 🌸
# 💫━━━━━━━━━━━━━━━━━━
async def setup_scheduler(bot):
    """
    Set up scheduled tasks for the bot.
    """

    # 🌸 Petal Lace Opening Announcement at Feb 27 at 1 pm Asia/Manila Time
    try:
        job = scheduler_manager.add_cron_job(
            func=scheduled_petal_lace_opening,
            name="petal_lace_opening_announcement",
            hour=13,
            minute=0,
            month=2,
            day_of_month=27,
            args=[bot],
            year=2026,  # Only runs in 2026
            timezone=MANILA,
        )
        espeon_log(
            "schedule_success",
            f"Scheduled Petal Lace opening announcement: {job.trigger}",
        )

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to schedule Petal Lace opening announcement: {e}",
            source="Scheduler Setup",
        )

    # 🌸 Reset battle roles everyday at 12:00 AM Est
    """try:
        job = scheduler_manager.add_cron_job(
            func=reset_battle_roles,
            name="daily_battle_role_reset",
            hour=0,
            minute=0,
            args=[bot],
            timezone=NYC,  # Use NYC timezone to auto-handle EST/EDT
        )
        espeon_log(
            "schedule_success",
            f"Scheduled daily battle role reset: {job.trigger}",
        )

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to schedule daily battle role reset: {e}",
            source="Scheduler Setup",
        )"""

    # Start the scheduler
    scheduler_manager.start()
    espeon_log("schedule_success", "Scheduler started successfully.")

    # Attach the scheduler manager to the bot for later access
    bot.scheduler_manager = scheduler_manager
