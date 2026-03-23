# from datetime import datetime
# import pytz

from datetime import datetime
from datetime import timedelta
import pytz

from config.petal_lace_settings import (
    POINT_MAP,
    SERVER_CURRENCY_EMOJI,
    SERVER_CURRENCY_NAME,
)


def is_event_active_now_manila():
    """
    Returns True if the current date and time in Asia/Manila timezone is between
    February 27, 1:00 PM and March 27, 1:00 PM (inclusive) of the current year.
    """
    tz = pytz.timezone("Asia/Manila")
    now = datetime.now(tz)
    year = now.year
    start = tz.localize(datetime(year, 2, 27, 12, 0, 0))
    end = tz.localize(datetime(year, 3, 27, 12, 0, 0))
    shop_close = tz.localize(datetime(year, 3, 30, 12, 0, 0))
    if now < start:
        return False, "Petal Lace shop is not yet open." , "shop_not_open"
    elif now > end:
        return False, "Petal Lace shop is closed." , "event_ended"
    elif now > shop_close:
        return False, "Petal Lace shop is closed and the event has ended.", "shop_closed"
    else:
        return True, None, "event_ongoing" # Shop is open


# Utility: Generate event points description from POINT_MAP
def generate_event_points_description():
    """
    Returns a formatted description string listing all event types and their point values.
    Example output:
        Shiny Event – 2 🍒
        Exclusive Event – 3 🍒
        ...
    """
    lines = []
    for key, value in POINT_MAP.items():
        context = value.get("context", key.replace("_", " ").title())
        points = value.get("points", 0)
        lines.append(f"{context} – {points} {SERVER_CURRENCY_EMOJI}")
    return "\n".join(lines)
