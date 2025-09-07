from typing import Optional
import re


def parse_compact_number(raw_number: str) -> Optional[int]:
    """
    Converts strings like '1k', '1.1k', '1 m', '1010k', '1.2b' to int.
    Returns None if invalid.
    """
    if not isinstance(raw_number, str):
        return None

    raw_number = raw_number.strip().lower()

    # Pattern: digits -> optional decimal -> optional space -> optional suffix k/m/b
    pattern = r"^(\d+(?:\.\d+)?)\s*([kmb])?$"
    match = re.fullmatch(pattern, raw_number)
    if not match:
        return None

    number_str, suffix = match.groups()

    try:
        number = float(number_str)
    except ValueError:
        return None

    if suffix == "k":
        number *= 1_000
    elif suffix == "m":
        number *= 1_000_000
    elif suffix == "b":
        number *= 1_000_000_000

    return int(number)
