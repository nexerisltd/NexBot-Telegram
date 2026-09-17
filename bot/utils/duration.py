import re
from datetime import timedelta

_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}

_PATTERN = re.compile(r"^(\d+)([smhd])$")


def parse_duration(text: str) -> timedelta | None:
    """Parse strings like '30s', '10m', '2h', '1d' into a timedelta.

    Returns None if the string doesn't match the expected format.
    """
    if not text:
        return None
    match = _PATTERN.match(text.strip().lower())
    if not match:
        return None
    amount, unit = match.groups()
    seconds = int(amount) * _UNIT_SECONDS[unit]
    if seconds <= 0:
        return None
    return timedelta(seconds=seconds)


def format_duration(seconds: int) -> str:
    """Turn a second count back into a short human string, e.g. 3600 -> '1h'."""
    if seconds % 86400 == 0:
        return f"{seconds // 86400}d"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"
