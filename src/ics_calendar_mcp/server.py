"""MCP Server with calendar tools."""

from datetime import date, timedelta

from mcp.server.fastmcp import FastMCP

from .calendar import get_client
from .utils import parse_date

mcp = FastMCP(
    "ics-calendar",
    dependencies=["httpx", "icalendar", "recurring-ical-events", "python-dateutil"],
)


@mcp.tool()
async def get_events_today() -> dict:
    """
    Get all calendar events for today.

    Returns events with their times, titles, locations, and other details.
    Recurring events are automatically expanded.

    Returns:
        dict with 'events' list and 'count'
    """
    try:
        client = get_client()
        events = await client.get_events_today()
        return {
            "date": date.today().isoformat(),
            "events": events,
            "count": len(events),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_events_range(start_date: str, end_date: str) -> dict:
    """
    Get calendar events within a date range.

    Args:
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)

    Returns:
        dict with 'events' list, 'count', and date range info
    """
    try:
        client = get_client()
        start = parse_date(start_date)
        end = parse_date(end_date)

        if end < start:
            return {"error": "end_date must be after start_date"}

        events = await client.get_events_between(start, end + timedelta(days=1))
        return {
            "start_date": start_date,
            "end_date": end_date,
            "events": events,
            "count": len(events),
        }
    except ValueError as e:
        return {"error": f"Invalid date format: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_event_details(event_uid: str) -> dict:
    """
    Get detailed information about a specific event by its UID.

    Args:
        event_uid: The unique identifier of the event

    Returns:
        dict with full event details or error if not found
    """
    try:
        client = get_client()
        event = await client.get_event_by_uid(event_uid)

        if event is None:
            return {"error": f"Event not found: {event_uid}"}

        return event
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def list_recurring_events() -> dict:
    """
    List all recurring events with their recurrence rules.

    Returns base recurring events (not expanded instances) with their
    frequency, days, and end dates.

    Returns:
        dict with 'events' list and 'count'
    """
    try:
        client = get_client()
        events = await client.get_recurring_events()
        return {
            "events": events,
            "count": len(events),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def search_events(
    query: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Search for events matching a query in title, description, or location.

    Args:
        query: Search term to match
        start_date: Optional start date (YYYY-MM-DD), defaults to today
        end_date: Optional end date (YYYY-MM-DD), defaults to 1 year from start

    Returns:
        dict with matching 'events' list and 'count'
    """
    try:
        client = get_client()

        start = parse_date(start_date) if start_date else None
        end = parse_date(end_date) if end_date else None

        events = await client.search_events(query, start, end)
        return {
            "query": query,
            "events": events,
            "count": len(events),
        }
    except ValueError as e:
        return {"error": f"Invalid date format: {e}"}
    except Exception as e:
        return {"error": str(e)}
