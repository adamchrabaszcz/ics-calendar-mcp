"""Tests for MCP tools."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from ics_calendar_mcp.calendar import reset_client, set_client, ICSCalendarClient
from ics_calendar_mcp.server import (
    get_events_today,
    get_events_range,
    get_event_details,
    list_recurring_events,
    search_events,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    reset_client()
    yield
    reset_client()


@pytest.fixture
def mock_client(monkeypatch):
    monkeypatch.setenv("ICS_CALENDAR_URL", "https://example.com/cal.ics")
    client = ICSCalendarClient()
    set_client(client)
    return client


class TestGetEventsToday:
    @pytest.mark.asyncio
    async def test_success(self, mock_client):
        mock_client.get_events_today = AsyncMock(return_value=[
            {"uid": "1", "summary": "Meeting", "start": "2024-03-10T14:00:00"},
        ])

        result = await get_events_today()

        assert result["count"] == 1
        assert result["events"][0]["summary"] == "Meeting"
        assert "date" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_client):
        mock_client.get_events_today = AsyncMock(return_value=[])

        result = await get_events_today()

        assert result["count"] == 0
        assert result["events"] == []

    @pytest.mark.asyncio
    async def test_error(self, mock_client):
        mock_client.get_events_today = AsyncMock(
            side_effect=Exception("Network error")
        )

        result = await get_events_today()

        assert "error" in result
        assert "Network error" in result["error"]


class TestGetEventsRange:
    @pytest.mark.asyncio
    async def test_success(self, mock_client):
        mock_client.get_events_between = AsyncMock(return_value=[
            {"uid": "1", "summary": "Event 1"},
            {"uid": "2", "summary": "Event 2"},
        ])

        result = await get_events_range("2024-03-10", "2024-03-15")

        assert result["count"] == 2
        assert result["start_date"] == "2024-03-10"
        assert result["end_date"] == "2024-03-15"

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, mock_client):
        result = await get_events_range("10-03-2024", "2024-03-15")

        assert "error" in result
        assert "Invalid date format" in result["error"]

    @pytest.mark.asyncio
    async def test_end_before_start(self, mock_client):
        mock_client.get_events_between = AsyncMock(return_value=[])

        result = await get_events_range("2024-03-15", "2024-03-10")

        assert "error" in result
        assert "end_date must be after start_date" in result["error"]


class TestGetEventDetails:
    @pytest.mark.asyncio
    async def test_found(self, mock_client):
        mock_client.get_event_by_uid = AsyncMock(return_value={
            "uid": "test-123",
            "summary": "Test Event",
            "description": "Full description",
        })

        result = await get_event_details("test-123")

        assert result["uid"] == "test-123"
        assert result["summary"] == "Test Event"

    @pytest.mark.asyncio
    async def test_not_found(self, mock_client):
        mock_client.get_event_by_uid = AsyncMock(return_value=None)

        result = await get_event_details("nonexistent")

        assert "error" in result
        assert "not found" in result["error"]


class TestListRecurringEvents:
    @pytest.mark.asyncio
    async def test_success(self, mock_client):
        mock_client.get_recurring_events = AsyncMock(return_value=[
            {
                "uid": "recurring-1",
                "summary": "Weekly Meeting",
                "recurrence": {"frequency": "WEEKLY"},
            },
        ])

        result = await list_recurring_events()

        assert result["count"] == 1
        assert result["events"][0]["summary"] == "Weekly Meeting"


class TestSearchEvents:
    @pytest.mark.asyncio
    async def test_success(self, mock_client):
        mock_client.search_events = AsyncMock(return_value=[
            {"uid": "1", "summary": "Team Standup"},
        ])

        result = await search_events("standup")

        assert result["count"] == 1
        assert result["query"] == "standup"

    @pytest.mark.asyncio
    async def test_with_date_range(self, mock_client):
        mock_client.search_events = AsyncMock(return_value=[])

        result = await search_events("meeting", "2024-03-01", "2024-03-31")

        assert result["count"] == 0
        mock_client.search_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_results(self, mock_client):
        mock_client.search_events = AsyncMock(return_value=[])

        result = await search_events("nonexistent")

        assert result["count"] == 0
        assert result["events"] == []
