"""Utility functions for date parsing and event formatting."""

from datetime import date, datetime, time
from typing import Any

import pytz
from icalendar import Event


def parse_date(date_str: str) -> date:
    """Parse ISO format date string (YYYY-MM-DD) to date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def parse_datetime(dt_value: Any, timezone: str = "Europe/Warsaw") -> datetime:
    """Convert icalendar datetime to timezone-aware datetime."""
    tz = pytz.timezone(timezone)

    if isinstance(dt_value, datetime):
        if dt_value.tzinfo is None:
            return tz.localize(dt_value)
        return dt_value.astimezone(tz)
    elif isinstance(dt_value, date):
        return tz.localize(datetime.combine(dt_value, time.min))
    else:
        return tz.localize(datetime.now())


def format_event(event: Event, timezone: str = "Europe/Warsaw") -> dict:
    """Convert icalendar Event to a dictionary."""
    dtstart = event.get("DTSTART")
    dtend = event.get("DTEND")

    start_dt = parse_datetime(dtstart.dt, timezone) if dtstart else None
    end_dt = parse_datetime(dtend.dt, timezone) if dtend else None

    is_all_day = False
    if dtstart and isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime):
        is_all_day = True

    result = {
        "uid": str(event.get("UID", "")),
        "summary": str(event.get("SUMMARY", "No title")),
        "start": start_dt.isoformat() if start_dt else None,
        "end": end_dt.isoformat() if end_dt else None,
        "all_day": is_all_day,
    }

    if event.get("LOCATION"):
        result["location"] = str(event.get("LOCATION"))

    if event.get("DESCRIPTION"):
        result["description"] = str(event.get("DESCRIPTION"))

    if event.get("STATUS"):
        result["status"] = str(event.get("STATUS"))

    if event.get("ORGANIZER"):
        organizer = event.get("ORGANIZER")
        result["organizer"] = str(organizer).replace("mailto:", "")

    return result


def format_event_short(event: Event, timezone: str = "Europe/Warsaw") -> dict:
    """Format event with minimal fields for list views."""
    dtstart = event.get("DTSTART")
    dtend = event.get("DTEND")

    start_dt = parse_datetime(dtstart.dt, timezone) if dtstart else None
    end_dt = parse_datetime(dtend.dt, timezone) if dtend else None

    is_all_day = False
    if dtstart and isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime):
        is_all_day = True

    result = {
        "uid": str(event.get("UID", "")),
        "summary": str(event.get("SUMMARY", "No title")),
        "start": start_dt.strftime("%H:%M") if start_dt and not is_all_day else "All day",
        "end": end_dt.strftime("%H:%M") if end_dt and not is_all_day else None,
    }

    if event.get("LOCATION"):
        result["location"] = str(event.get("LOCATION"))

    return result


def format_recurring_event(event: Event, timezone: str = "Europe/Warsaw") -> dict:
    """Format a recurring event with its recurrence rule."""
    result = format_event(event, timezone)

    rrule = event.get("RRULE")
    if rrule:
        rule_dict = dict(rrule)
        freq = rule_dict.get("FREQ", [None])[0]
        interval = rule_dict.get("INTERVAL", [1])[0]
        until = rule_dict.get("UNTIL", [None])[0]
        byday = rule_dict.get("BYDAY", [])

        result["recurrence"] = {
            "frequency": freq,
            "interval": interval,
            "until": until.isoformat() if until else None,
            "days": list(byday) if byday else None,
        }

        # Human-readable description
        freq_map = {
            "DAILY": "daily",
            "WEEKLY": "weekly",
            "MONTHLY": "monthly",
            "YEARLY": "yearly",
        }
        day_map = {
            "MO": "Monday",
            "TU": "Tuesday",
            "WE": "Wednesday",
            "TH": "Thursday",
            "FR": "Friday",
            "SA": "Saturday",
            "SU": "Sunday",
        }

        desc = freq_map.get(freq, freq)
        if interval and interval > 1:
            desc = f"every {interval} {desc.rstrip('ly')}s"
        if byday:
            days = [day_map.get(d, d) for d in byday]
            desc += f" on {', '.join(days)}"
        if until:
            desc += f" until {until.strftime('%Y-%m-%d')}"

        result["recurrence"]["description"] = desc

    return result
