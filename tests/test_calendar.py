"""Tests for ICS Calendar client."""

from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from icalendar import Calendar, Event

from ics_calendar_mcp.calendar import (
    ICSCalendarClient,
    get_client,
    reset_client,
    set_client,
)


SAMPLE_ICS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:event-1
SUMMARY:Team Meeting
DTSTART:20240310T140000
DTEND:20240310T150000
END:VEVENT
BEGIN:VEVENT
UID:event-2
SUMMARY:Weekly Standup
DTSTART:20240311T100000
DTEND:20240311T103000
RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
END:VEVENT
END:VCALENDAR"""


@pytest.fixture
def sample_calendar():
    return Calendar.from_ical(SAMPLE_ICS)


@pytest.fixture(autouse=True)
def reset_singleton():
    reset_client()
    yield
    reset_client()


class TestICSCalendarClient:
    def test_init_with_url(self, monkeypatch):
        monkeypatch.delenv("ICS_CALENDAR_URL", raising=False)
        client = ICSCalendarClient(url="https://example.com/cal.ics")
        assert client.url == "https://example.com/cal.ics"

    def test_init_with_env(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://env.example.com/cal.ics")
        client = ICSCalendarClient()
        assert client.url == "https://env.example.com/cal.ics"

    def test_init_missing_url(self, monkeypatch):
        monkeypatch.delenv("ICS_CALENDAR_URL", raising=False)
        with pytest.raises(ValueError, match="ICS_CALENDAR_URL is required"):
            ICSCalendarClient()

    def test_default_settings(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
        client = ICSCalendarClient()
        assert client.cache_ttl == 300
        assert client.timezone == "Europe/Warsaw"

    def test_custom_settings(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
        monkeypatch.setenv("ICS_CACHE_TTL", "600")
        monkeypatch.setenv("ICS_TIMEZONE", "America/New_York")
        client = ICSCalendarClient()
        assert client.cache_ttl == 600
        assert client.timezone == "America/New_York"


class TestFetchCalendar:
    @pytest.mark.asyncio
    async def test_fetch_success(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
        client = ICSCalendarClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_response = AsyncMock()
            mock_response.text = SAMPLE_ICS
            mock_response.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_response

            calendar = await client.fetch_calendar()

            assert calendar is not None
            assert client._last_fetch is not None

    @pytest.mark.asyncio
    async def test_fetch_caching(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
        client = ICSCalendarClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_response = AsyncMock()
            mock_response.text = SAMPLE_ICS
            mock_response.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_response

            await client.fetch_calendar()
            await client.fetch_calendar()

            # Should only fetch once due to caching
            assert mock_instance.get.call_count == 1


class TestGetEventsBetween:
    @pytest.mark.asyncio
    async def test_get_events(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
        client = ICSCalendarClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_response = AsyncMock()
            mock_response.text = SAMPLE_ICS
            mock_response.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_response

            events = await client.get_events_between(
                date(2024, 3, 10),
                date(2024, 3, 11),
            )

            assert len(events) >= 1
            summaries = [e["summary"] for e in events]
            assert "Team Meeting" in summaries


class TestGetRecurringEvents:
    @pytest.mark.asyncio
    async def test_list_recurring(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
        client = ICSCalendarClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_response = AsyncMock()
            mock_response.text = SAMPLE_ICS
            mock_response.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_response

            events = await client.get_recurring_events()

            assert len(events) == 1
            assert events[0]["summary"] == "Weekly Standup"
            assert "recurrence" in events[0]


class TestSingleton:
    def test_get_client(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
        client1 = get_client()
        client2 = get_client()
        assert client1 is client2

    def test_set_client(self, monkeypatch):
        monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
        custom_client = ICSCalendarClient()
        set_client(custom_client)
        assert get_client() is custom_client
