# Google Calendar MCP Server

A Model Context Protocol (MCP) server that provides access to the Google Calendar API. This server allows you to manage calendars and events directly through MCP.

## Authentication

Authentication is handled by passing a valid `oauth_token` with each tool call. You must obtain a token with the necessary Google Calendar scopes (e.g., `https://www.googleapis.com/auth/calendar`). The server does not handle the OAuth flow to generate this token.

## Features

The server provides a comprehensive set of tools for interacting with Google Calendar, including:

- **Calendar Management**: `list_calendars`, `get_calendar`, `create_calendar`, `delete_calendar`.
- **Event Management**: `list_events`, `get_event`, `create_event`, `update_event`, `delete_event`, `move_event`.
- **Quick Actions**: `create_quick_event` (using natural language), `get_todays_events`, `get_upcoming_events`.
- **Advanced Features**: `search_events`, `add_attendees`, `get_free_busy`, `create_recurring_event`.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Server:**
    The server can be run in different transport modes.

    -   **For `stdio` transport:**
        ```bash
        python google-calendar_mcp_server.py
        ```
    -   **For `sse` (Server-Sent Events) transport:**
        ```bash
        python google-calendar_mcp_server.py --transport sse --host 127.0.0.1 --port 8001
        ```

## Usage Examples

All tool calls require a valid `oauth_token` argument.

### List Calendars
```json
{
  "tool": "list_calendars",
  "arguments": {
    "oauth_token": "your_oauth_token_string"
  }
}
```

### Get Today's Events
```json
{
  "tool": "get_todays_events",
  "arguments": {
    "oauth_token": "your_oauth_token_string",
    "calendar_id": "primary"
  }
}
```

### Create a Quick Event
```json
{
  "tool": "create_quick_event",
  "arguments": {
    "oauth_token": "your_oauth_token_string",
    "text": "Dinner with Jane tomorrow at 7pm"
  }
}
```

### Create a Detailed Event
```json
{
  "tool": "create_event",
  "arguments": {
    "oauth_token": "your_oauth_token_string",
    "summary": "Project Sync",
    "start_time": "2026-01-09T10:00:00",
    "end_time": "2026-01-09T11:00:00",
    "attendees": ["coworker@example.com"],
    "timezone": "America/New_York"
  }
}
```

## Date/Time Formats

Use the ISO 8601 format for all date and time strings.
- **Example:** `2026-01-09T10:00:00-05:00` (for EST) or `2026-01-09T15:00:00Z` (for UTC).
- The tool descriptions provide more detail on required formats.

