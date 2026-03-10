"""ICS Calendar client for fetching and parsing calendar feeds."""

import os
from datetime import date, datetime, timedelta
from typing import Any

import httpx
from icalendar import Calendar
import recurring_ical_events

from .utils import format_event, format_event_short, format_recurring_event


class ICSCalendarClient:
    """Client for fetching and parsing ICS calendar feeds."""

    def __init__(
        self,
        url: str | None = None,
        cache_ttl: int | None = None,
        timezone: str | None = None,
    ):
        self.url = url or os.environ.get("ICS_CALENDAR_URL")
        if not self.url:
            raise ValueError("ICS_CALENDAR_URL is required")

        self.cache_ttl = cache_ttl or int(os.environ.get("ICS_CACHE_TTL", "300"))
        self.timezone = timezone or os.environ.get("ICS_TIMEZONE", "Europe/Warsaw")

        self._calendar: Calendar | None = None
        self._last_fetch: datetime | None = None

    async def fetch_calendar(self, force: bool = False) -> Calendar:
        """Fetch and parse ICS calendar, with caching."""
        now = datetime.now()

        if (
            not force
            and self._calendar is not None
            and self._last_fetch is not None
            and (now - self._last_fetch).total_seconds() < self.cache_ttl
        ):
            return self._calendar

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.url)
            response.raise_for_status()

            self._calendar = Calendar.from_ical(response.text)
            self._last_fetch = now

            return self._calendar

    async def get_events_between(
        self,
        start: date,
        end: date,
        short_format: bool = False,
    ) -> list[dict]:
        """Get events between dates with recurrence expansion."""
        calendar = await self.fetch_calendar()

        # recurring_ical_events expands recurring events
        events = recurring_ical_events.of(calendar).between(start, end)

        formatter = format_event_short if short_format else format_event
        result = []

        for event in events:
            formatted = formatter(event, self.timezone)
            result.append(formatted)

        # Sort by start time
        result.sort(key=lambda e: e.get("start") or "")

        return result

    async def get_events_today(self) -> list[dict]:
        """Get all events for today."""
        today = date.today()
        return await self.get_events_between(today, today + timedelta(days=1))

    async def get_event_by_uid(self, uid: str) -> dict | None:
        """Get a specific event by UID."""
        calendar = await self.fetch_calendar()

        for component in calendar.walk():
            if component.name == "VEVENT":
                event_uid = str(component.get("UID", ""))
                if event_uid == uid:
                    return format_event(component, self.timezone)

        return None

    async def get_recurring_events(self) -> list[dict]:
        """Get all recurring events (base events, not expanded)."""
        calendar = await self.fetch_calendar()

        result = []
        for component in calendar.walk():
            if component.name == "VEVENT" and component.get("RRULE"):
                formatted = format_recurring_event(component, self.timezone)
                result.append(formatted)

        # Sort by summary
        result.sort(key=lambda e: e.get("summary", "").lower())

        return result

    async def search_events(
        self,
        query: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[dict]:
        """Search events by title/description."""
        if start is None:
            start = date.today()
        if end is None:
            end = start + timedelta(days=365)

        events = await self.get_events_between(start, end)
        query_lower = query.lower()

        return [
            e for e in events
            if query_lower in e.get("summary", "").lower()
            or query_lower in e.get("description", "").lower()
            or query_lower in e.get("location", "").lower()
        ]


# Singleton pattern
_client: ICSCalendarClient | None = None


def get_client() -> ICSCalendarClient:
    """Get or create the singleton client."""
    global _client
    if _client is None:
        _client = ICSCalendarClient()
    return _client


def reset_client() -> None:
    """Reset the singleton client (for testing)."""
    global _client
    _client = None


def set_client(client: ICSCalendarClient) -> None:
    """Set a custom client (for testing)."""
    global _client
    _client = client
