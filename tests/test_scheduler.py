"""Tests for scheduler module."""

from datetime import datetime, time

import pytest

from timesaver.scheduler import (
    is_in_schedule,
    is_time_in_range,
    parse_time,
    validate_time_format,
)


def test_parse_time_valid():
    """Test parsing valid time strings."""
    assert parse_time("09:00") == time(9, 0)
    assert parse_time("17:30") == time(17, 30)
    assert parse_time("00:00") == time(0, 0)
    assert parse_time("23:59") == time(23, 59)


def test_parse_time_invalid_format():
    """Test parsing invalid time formats."""
    with pytest.raises(ValueError) as exc_info:
        parse_time("invalid")
    assert "Invalid time format" in str(exc_info.value)


def test_parse_time_invalid_values():
    """Test parsing time with invalid values."""
    with pytest.raises(ValueError):
        parse_time("25:00")
    with pytest.raises(ValueError):
        parse_time("12:60")


def test_parse_time_invalid_format_no_colon():
    """Test parsing time without colon."""
    with pytest.raises(ValueError) as exc_info:
        parse_time("0900")
    assert "Invalid time format" in str(exc_info.value)


def test_validate_time_format():
    """Test time format validation."""
    assert validate_time_format("09:00") is True
    assert validate_time_format("17:30") is True
    assert validate_time_format("invalid") is False
    assert validate_time_format("25:00") is False


def test_is_time_in_range_normal():
    """Test time range check for normal ranges."""
    # 09:00 to 17:00
    start = time(9, 0)
    end = time(17, 0)

    assert is_time_in_range(time(9, 0), start, end) is True
    assert is_time_in_range(time(12, 0), start, end) is True
    assert is_time_in_range(time(17, 0), start, end) is True
    assert is_time_in_range(time(8, 59), start, end) is False
    assert is_time_in_range(time(17, 1), start, end) is False


def test_is_time_in_range_overnight():
    """Test time range check for ranges crossing midnight."""
    # 22:00 to 06:00
    start = time(22, 0)
    end = time(6, 0)

    assert is_time_in_range(time(22, 0), start, end) is True
    assert is_time_in_range(time(23, 30), start, end) is True
    assert is_time_in_range(time(0, 0), start, end) is True
    assert is_time_in_range(time(3, 0), start, end) is True
    assert is_time_in_range(time(6, 0), start, end) is True
    assert is_time_in_range(time(12, 0), start, end) is False
    assert is_time_in_range(time(21, 59), start, end) is False


def test_is_in_schedule_no_schedules():
    """Test that no schedules means always active."""
    assert is_in_schedule([]) is True


def test_is_in_schedule_in_range():
    """Test schedule check when in range."""
    schedules = [{"start": "00:00", "end": "23:59"}]
    assert is_in_schedule(schedules) is True


def test_is_in_schedule_specific_time():
    """Test schedule check with specific time."""
    schedules = [{"start": "09:00", "end": "17:00"}]

    # During work hours
    work_time = datetime(2024, 1, 1, 12, 0, 0)
    assert is_in_schedule(schedules, work_time) is True

    # Before work hours
    early_time = datetime(2024, 1, 1, 8, 0, 0)
    assert is_in_schedule(schedules, early_time) is False

    # After work hours
    late_time = datetime(2024, 1, 1, 18, 0, 0)
    assert is_in_schedule(schedules, late_time) is False


def test_is_in_schedule_multiple_schedules():
    """Test schedule check with multiple schedules."""
    schedules = [
        {"start": "09:00", "end": "12:00"},
        {"start": "13:00", "end": "17:00"},
    ]

    morning = datetime(2024, 1, 1, 10, 0, 0)
    assert is_in_schedule(schedules, morning) is True

    lunch = datetime(2024, 1, 1, 12, 30, 0)
    assert is_in_schedule(schedules, lunch) is False

    afternoon = datetime(2024, 1, 1, 15, 0, 0)
    assert is_in_schedule(schedules, afternoon) is True


def test_is_in_schedule_uses_current_time_when_none():
    """Test that is_in_schedule uses current time when not provided."""
    # This test just verifies the function runs without error
    schedules = [{"start": "00:00", "end": "23:59"}]
    result = is_in_schedule(schedules, None)
    assert result is True
