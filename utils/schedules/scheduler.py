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

    # 🌸 Petal Lace Opening Announcement at Nov 30 1 PM Asia/Manila
    try:
        job = scheduler_manager.add_cron_job(
            func=scheduled_petal_lace_opening,
            name="petal_lace_opening_announcement",
            hour=13,
            minute=0,
            month=11,
            day_of_month=30,
            args=[bot],
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

    # 🌸 Event Close Dec 28th 1pm Asia/Manila
    try:
        job = scheduler_manager.add_cron_job(
            func=scheduled_petal_lace_event_end,
            name="petal_lace_closing_announcement",
            hour=13,
            minute=0,
            day_of_month=28,
            month=12,
            args=[bot],
            timezone=MANILA,
        )
        espeon_log(
            "schedule_success",
            f"Scheduled Petal Lace closing announcement: {job.trigger}",
        )

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to schedule Petal Lace closing announcement: {e}",
            source="Scheduler Setup",
        )

    # 🌸 Shop Clear Jan 4th 1pm Asia/Manila
    try:
        job = scheduler_manager.add_cron_job(
            func=scheduled_petal_lace_shop_clear,
            name="petal_lace_shop_clear",
            hour=13,
            minute=0,
            day_of_month=4,
            month=1,
            args=[bot],
            timezone=MANILA,
        )
        espeon_log(
            "schedule_success",
            f"Scheduled Petal Lace shop clear: {job.trigger}",
        )

    except Exception as e:
        espeon_log(
            "error",
            f"Failed to schedule Petal Lace shop clear: {e}",
            source="Scheduler Setup",
        )
    # Start the scheduler
    scheduler_manager.start()
    espeon_log("schedule_success", "Scheduler started successfully.")

    # Attach the scheduler manager to the bot for later access
    bot.scheduler_manager = scheduler_manager
