# Google Calendar MCP Server

A Model Context Protocol (MCP) server that provides access to Google Calendar API endpoints.

## Features

This MCP server provides the following Google Calendar operations:

### Calendar Management
- **list_calendars**: List all accessible calendars
- **get_calendar**: Get details of a specific calendar
- **create_calendar**: Create a new calendar
- **delete_calendar**: Delete a calendar

### Event Operations
- **list_events**: List events within a time range
- **get_event**: Get details of a specific event
- **create_event**: Create a new calendar event
- **create_quick_event**: Create event using natural language
- **update_event**: Update an existing event
- **delete_event**: Delete an event
- **search_events**: Search for events by text
- **move_event**: Move event to another calendar
- **create_recurring_event**: Create a recurring event

### Convenience Tools
- **get_todays_events**: Get all events for today
- **get_upcoming_events**: Get events for the next N days
- **add_attendees**: Add attendees to an event
- **get_free_busy**: Get free/busy information

## Setup

### 1. Install Dependencies

```bash
cd calendar
pip install -r requirements.txt
```

### 2. Configure Google OAuth

You need to create OAuth credentials with the following scopes:
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/calendar.events`
- `https://www.googleapis.com/auth/calendar.readonly`

Save your OAuth credentials as `secret.json` in this directory.

### 3. Authenticate

Run the authentication script:

```bash
python authenticate.py
```

This will:
1. Open a browser window for authentication
2. Create a `token.json` file to store your credentials
3. Reuse the token on subsequent runs

### 4. Configure Your MCP Client

#### For Claude Desktop (stdio mode - default)

Add this to your Claude Desktop MCP settings file:

**Location**: `~/.config/Claude/claude_desktop_config.json` (Linux)

```json
{
  "mcpServers": {
    "calendar": {
      "command": "python3",
      "args": ["/home/shadyskies/Desktop/mcp-tools/calendar/calendar_mcp_server.py"],
      "cwd": "/home/shadyskies/Desktop/mcp-tools/calendar"
    }
  }
}
```

#### For HTTP/SSE Transport

**SSE (Server-Sent Events)**:
```bash
python calendar_mcp_server.py --transport sse --host 0.0.0.0 --port 8003
```

**Streamable HTTP**:
```bash
python calendar_mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8003
```

## Usage Examples

### List Calendars
```json
{
  "tool": "list_calendars"
}
```

### Get Today's Events
```json
{
  "tool": "get_todays_events"
}
```

### Get Upcoming Events
```json
{
  "tool": "get_upcoming_events",
  "arguments": {
    "days": 7,
    "max_results": 20
  }
}
```

### Create Event
```json
{
  "tool": "create_event",
  "arguments": {
    "summary": "Team Meeting",
    "start_time": "2026-01-08T10:00:00",
    "end_time": "2026-01-08T11:00:00",
    "description": "Weekly team sync",
    "location": "Conference Room A",
    "attendees": ["colleague@example.com"],
    "timezone": "America/New_York"
  }
}
```

### Create Quick Event
```json
{
  "tool": "create_quick_event",
  "arguments": {
    "text": "Lunch with John tomorrow at 12pm"
  }
}
```

### Search Events
```json
{
  "tool": "search_events",
  "arguments": {
    "query": "meeting",
    "max_results": 10
  }
}
```

### Create Recurring Event
```json
{
  "tool": "create_recurring_event",
  "arguments": {
    "summary": "Weekly Standup",
    "start_time": "2026-01-08T09:00:00",
    "end_time": "2026-01-08T09:30:00",
    "recurrence_rule": "RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR",
    "timezone": "America/New_York"
  }
}
```

### Get Free/Busy Information
```json
{
  "tool": "get_free_busy",
  "arguments": {
    "time_min": "2026-01-08T00:00:00Z",
    "time_max": "2026-01-08T23:59:59Z",
    "calendar_ids": ["primary"]
  }
}
```

## Date/Time Format

All date/time values should be in ISO 8601 format:
- **With timezone**: `2026-01-08T10:00:00-05:00`
- **UTC**: `2026-01-08T10:00:00Z`
- **Without timezone** (uses specified timezone parameter): `2026-01-08T10:00:00`

Examples:
- `2026-01-08T14:30:00` - Jan 8, 2026 at 2:30 PM
- `2026-12-25T09:00:00-08:00` - Dec 25, 2026 at 9 AM PST
- `2026-06-15T18:00:00Z` - Jun 15, 2026 at 6 PM UTC

## Recurrence Rules

Recurrence rules follow RFC 5545 (iCalendar) format:

**Daily**:
- Every day: `RRULE:FREQ=DAILY`
- Every 2 days: `RRULE:FREQ=DAILY;INTERVAL=2`
- For 10 occurrences: `RRULE:FREQ=DAILY;COUNT=10`

**Weekly**:
- Every week: `RRULE:FREQ=WEEKLY`
- Every Monday and Wednesday: `RRULE:FREQ=WEEKLY;BYDAY=MO,WE`
- Every other week: `RRULE:FREQ=WEEKLY;INTERVAL=2`

**Monthly**:
- Every month: `RRULE:FREQ=MONTHLY`
- Every 15th of the month: `RRULE:FREQ=MONTHLY;BYMONTHDAY=15`
- First Monday of every month: `RRULE:FREQ=MONTHLY;BYDAY=1MO`

**Yearly**:
- Every year: `RRULE:FREQ=YEARLY`
- Every December 25th: `RRULE:FREQ=YEARLY;BYMONTH=12;BYMONTHDAY=25`

**Until a date**:
- Until Jan 31, 2026: `RRULE:FREQ=DAILY;UNTIL=20260131T235959Z`

## Common Timezones

- `UTC` - Coordinated Universal Time
- `America/New_York` - Eastern Time
- `America/Chicago` - Central Time
- `America/Denver` - Mountain Time
- `America/Los_Angeles` - Pacific Time
- `Europe/London` - GMT/BST
- `Europe/Paris` - CET/CEST
- `Asia/Tokyo` - Japan Standard Time
- `Australia/Sydney` - Australian Eastern Time

## Calendar IDs

- `primary` - User's primary calendar
- Specific calendar ID can be obtained from `list_calendars`

## Troubleshooting

### "token.json not found" Error
Run the authentication script:
```bash
python authenticate.py
```

### Authentication Issues
If you get authentication errors:
1. Delete `token.json`
2. Run `python authenticate.py` again
3. Complete the OAuth flow in your browser

### Permission Denied
Make sure your OAuth credentials have the correct scopes enabled in the Google Cloud Console:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services → Credentials
3. Edit your OAuth 2.0 Client ID
4. Ensure all required scopes are enabled
5. Add `http://localhost:8080` to authorized redirect URIs

### Invalid DateTime
Ensure your datetime strings are in ISO 8601 format. Common mistakes:
- Missing timezone indicator (add `Z` for UTC or timezone offset)
- Wrong format (use `YYYY-MM-DDTHH:MM:SS`)
- End time before start time

### Quota Limits
Google Calendar API has usage quotas. Check your quota usage in the Google Cloud Console if you encounter quota errors.

## Security Notes

- Keep `secret.json` and `token.json` secure and never commit them to version control
- The server uses OAuth 2.0 for secure authentication
- Access tokens are refreshed automatically when they expire
- All operations are performed with the authenticated user's permissions

## Logging

The server logs all operations to:
- Console/stderr (for real-time monitoring)
- `calendar_mcp_server.log` (for persistent records)

Log levels:
- `INFO`: Normal operations and key events
- `DEBUG`: Detailed information
- `WARNING`: Warnings
- `ERROR`: Authentication failures, API errors
