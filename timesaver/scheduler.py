"""Time range logic for scheduling blocks."""

from datetime import datetime, time


def parse_time(time_str: str) -> time:
    """Parse a time string in HH:MM format.

    Args:
        time_str: Time string in HH:MM format

    Returns:
        datetime.time object

    Raises:
        ValueError: If time string is invalid
    """
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {time_str}")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time values: {time_str}")
        return time(hour, minute)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid time format '{time_str}'. Use HH:MM format.") from e


def validate_time_format(time_str: str) -> bool:
    """Validate a time string is in HH:MM format.

    Args:
        time_str: Time string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        parse_time(time_str)
        return True
    except ValueError:
        return False


def is_time_in_range(
    current: time, start: time, end: time
) -> bool:
    """Check if current time is within the given range.

    Handles ranges that cross midnight (e.g., 22:00 to 06:00).

    Args:
        current: Current time to check
        start: Start of range
        end: End of range

    Returns:
        True if current time is within range
    """
    if start <= end:
        # Normal range (e.g., 09:00 to 17:00)
        return start <= current <= end
    else:
        # Range crosses midnight (e.g., 22:00 to 06:00)
        return current >= start or current <= end


def is_in_schedule(
    schedules: list[dict[str, str]], current_time: datetime | None = None
) -> bool:
    """Check if current time matches any schedule.

    Args:
        schedules: List of schedule dicts with 'start' and 'end' keys
        current_time: Optional datetime for testing (defaults to now)

    Returns:
        True if current time is within any schedule
    """
    if not schedules:
        # No schedules means always block (when enabled)
        return True

    if current_time is None:
        current_time = datetime.now()

    current = current_time.time()

    for schedule in schedules:
        start = parse_time(schedule["start"])
        end = parse_time(schedule["end"])
        if is_time_in_range(current, start, end):
            return True

    return False
