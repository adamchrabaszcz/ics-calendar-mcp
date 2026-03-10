# ICS Calendar MCP Server

A lightweight MCP (Model Context Protocol) server for reading ICS calendar feeds with proper recurring event expansion.

## Features

- Fetch and parse ICS calendar feeds (Outlook, Google Calendar, etc.)
- Properly expands recurring events using `recurring-ical-events`
- Caches calendar data to reduce API calls
- Timezone-aware event handling
- Simple configuration via environment variables

## Installation

### Using uvx (recommended)

```bash
uvx --from git+https://github.com/adamchrabaszcz/ics-calendar-mcp ics-calendar-mcp
```

### Using pip

```bash
pip install git+https://github.com/adamchrabaszcz/ics-calendar-mcp
```

### From source

```bash
git clone https://github.com/adamchrabaszcz/ics-calendar-mcp
cd ics-calendar-mcp
pip install -e .
```

## Configuration

Set the following environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ICS_CALENDAR_URL` | Yes | - | URL to the ICS calendar feed |
| `ICS_CACHE_TTL` | No | 300 | Cache duration in seconds |
| `ICS_TIMEZONE` | No | Europe/Warsaw | Default timezone for events |

### Example: Outlook Calendar

```bash
export ICS_CALENDAR_URL="https://outlook.office365.com/owa/calendar/xxx@domain.com/yyy/calendar.ics"
```

## MCP Tools

### `get_events_today`

Get all calendar events for today.

```json
{
  "date": "2024-03-10",
  "events": [...],
  "count": 3
}
```

### `get_events_range`

Get events within a date range.

**Parameters:**
- `start_date` (string): Start date in ISO format (YYYY-MM-DD)
- `end_date` (string): End date in ISO format (YYYY-MM-DD)

```json
{
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "events": [...],
  "count": 15
}
```

### `get_event_details`

Get detailed information about a specific event.

**Parameters:**
- `event_uid` (string): The unique identifier of the event

### `list_recurring_events`

List all recurring events with their recurrence rules.

```json
{
  "events": [
    {
      "uid": "event-123",
      "summary": "Weekly Standup",
      "recurrence": {
        "frequency": "WEEKLY",
        "days": ["MO", "TU", "WE", "TH", "FR"],
        "description": "weekly on Monday, Tuesday, Wednesday, Thursday, Friday"
      }
    }
  ],
  "count": 5
}
```

### `search_events`

Search for events matching a query.

**Parameters:**
- `query` (string): Search term
- `start_date` (string, optional): Start date for search range
- `end_date` (string, optional): End date for search range

## Claude Code Configuration

Add to your `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "ics-calendar": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/adamchrabaszcz/ics-calendar-mcp", "ics-calendar-mcp"],
      "env": {
        "ICS_CALENDAR_URL": "https://your-calendar-url.ics"
      }
    }
  }
}
```

## Development

### Setup

```bash
git clone https://github.com/adamchrabaszcz/ics-calendar-mcp
cd ics-calendar-mcp
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/
```

### Run locally

```bash
ICS_CALENDAR_URL="https://your-calendar.ics" python -m ics_calendar_mcp
```

## License

MIT
