import re
import time
from datetime import timedelta

def parse_duration(duration_str: str) -> tuple[str, int]:
    """
    Parses a duration string like:
    - "3d"
    - "3 days"
    - "4d12h"
    - "4 days 12 hours"

    Returns:
        normalized_str (str): e.g. "3 days 12 hours"
        unix_end (int): current_time + duration in seconds

    Raises:
        ValueError: If invalid format or less than 1 day.
    """
    # Normalize for matching
    duration_str = duration_str.lower().replace(" ", "")

    # Match patterns like 4d, 4days, 4d12h, 4days12hours
    match = re.fullmatch(
        r"(?:(\d+)\s*d(?:ays?)?)?(?:(\d+)\s*h(?:ours?)?)?", duration_str
    )
    if not match:
        raise ValueError(
            "Invalid format. Examples: `3d`, `3 days`, `4d12h`, `4 days 12 hours`"
        )

    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0

    # No minutes allowed — must be at least 1 day
    if days == 0 and hours < 24:
        raise ValueError("Minimum duration is **1 day**.")

    total_seconds = timedelta(days=days, hours=hours).total_seconds()

    # Create human-readable normalized string
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    normalized_str = " ".join(parts)

    unix_end = int(time.time() + total_seconds)
    return normalized_str, unix_end
