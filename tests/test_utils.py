"""Tests for utility functions."""

from datetime import date, datetime

import pytest
import pytz
from icalendar import Event

from ics_calendar_mcp.utils import (
    parse_date,
    parse_datetime,
    format_event,
    format_event_short,
    format_recurring_event,
)


class TestParseDate:
    def test_valid_date(self):
        result = parse_date("2024-03-10")
        assert result == date(2024, 3, 10)

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            parse_date("10-03-2024")

    def test_invalid_date(self):
        with pytest.raises(ValueError):
            parse_date("2024-13-01")


class TestParseDatetime:
    def test_naive_datetime(self):
        dt = datetime(2024, 3, 10, 14, 30)
        result = parse_datetime(dt, "Europe/Warsaw")
        assert result.tzinfo is not None
        assert result.hour == 14

    def test_aware_datetime(self):
        tz = pytz.UTC
        dt = tz.localize(datetime(2024, 3, 10, 12, 0))
        result = parse_datetime(dt, "Europe/Warsaw")
        assert result.tzinfo is not None

    def test_date_only(self):
        d = date(2024, 3, 10)
        result = parse_datetime(d, "Europe/Warsaw")
        assert result.hour == 0
        assert result.minute == 0


class TestFormatEvent:
    def test_basic_event(self):
        event = Event()
        event.add("uid", "test-123")
        event.add("summary", "Team Meeting")
        event.add("dtstart", datetime(2024, 3, 10, 14, 0))
        event.add("dtend", datetime(2024, 3, 10, 15, 0))

        result = format_event(event, "Europe/Warsaw")

        assert result["uid"] == "test-123"
        assert result["summary"] == "Team Meeting"
        assert "2024-03-10" in result["start"]
        assert result["all_day"] is False

    def test_all_day_event(self):
        event = Event()
        event.add("uid", "allday-123")
        event.add("summary", "Holiday")
        event.add("dtstart", date(2024, 3, 10))
        event.add("dtend", date(2024, 3, 11))

        result = format_event(event, "Europe/Warsaw")

        assert result["all_day"] is True

    def test_event_with_location(self):
        event = Event()
        event.add("uid", "loc-123")
        event.add("summary", "Office Meeting")
        event.add("location", "Room 101")
        event.add("dtstart", datetime(2024, 3, 10, 14, 0))

        result = format_event(event, "Europe/Warsaw")

        assert result["location"] == "Room 101"


class TestFormatEventShort:
    def test_short_format(self):
        event = Event()
        event.add("uid", "short-123")
        event.add("summary", "Quick Sync")
        event.add("dtstart", datetime(2024, 3, 10, 14, 30))
        event.add("dtend", datetime(2024, 3, 10, 15, 0))

        result = format_event_short(event, "Europe/Warsaw")

        assert result["start"] == "14:30"
        assert result["end"] == "15:00"
        assert "description" not in result

    def test_all_day_short(self):
        event = Event()
        event.add("uid", "allday-short")
        event.add("summary", "Conference")
        event.add("dtstart", date(2024, 3, 10))

        result = format_event_short(event, "Europe/Warsaw")

        assert result["start"] == "All day"


class TestFormatRecurringEvent:
    def test_weekly_recurring(self):
        event = Event()
        event.add("uid", "recurring-123")
        event.add("summary", "Weekly Standup")
        event.add("dtstart", datetime(2024, 3, 10, 10, 0))
        event.add("rrule", {"FREQ": "WEEKLY", "BYDAY": ["MO", "WE", "FR"]})

        result = format_recurring_event(event, "Europe/Warsaw")

        assert "recurrence" in result
        assert result["recurrence"]["frequency"] == "WEEKLY"
        assert "Monday" in result["recurrence"]["description"]

    def test_monthly_with_until(self):
        event = Event()
        event.add("uid", "monthly-123")
        event.add("summary", "Monthly Review")
        event.add("dtstart", datetime(2024, 3, 10, 14, 0))
        event.add("rrule", {
            "FREQ": "MONTHLY",
            "UNTIL": datetime(2024, 12, 31),
        })

        result = format_recurring_event(event, "Europe/Warsaw")

        assert result["recurrence"]["frequency"] == "MONTHLY"
        assert "2024-12-31" in result["recurrence"]["until"]
