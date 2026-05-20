**Schedule smarter - create, search, and manage Google Calendar events through AI.**

A Model Context Protocol (MCP) server that exposes Google Calendar's API for creating, reading, updating, and deleting events and calendars.


## Overview

The Google Calendar MCP Server provides full calendar management capabilities:

- Create, update, delete, and search events across any calendar
- Manage multiple calendars — list, create, or delete them
- Query free/busy availability, recurring events, and upcoming schedules

Perfect for:

- Scheduling and rescheduling meetings via AI assistants
- Automating event creation and calendar organization workflows
- Querying availability and surfacing upcoming events in chat interfaces


## Tools

<details>
<summary><code>list_calendars</code> — List all calendars accessible by the user</summary>

Returns all calendars in the authenticated user's Google Calendar account.

**Inputs:**
```
(none)
```

**Output:**

```json
{
  "count": 3,
  "calendars": [{ "id": "primary", "summary": "My Calendar", ... }]
}
```

</details>


<details>
<summary><code>get_calendar</code> — Get details of a specific calendar</summary>

Fetches metadata for a single calendar by its ID.

**Inputs:**
```
- `calendar_id` (string, optional) — Calendar ID to retrieve. Defaults to "primary"
```

**Output:**

```json
{
  "id": "primary",
  "summary": "My Calendar",
  "timeZone": "America/New_York"
}
```

</details>


<details>
<summary><code>create_calendar</code> — Create a new calendar</summary>

Creates a new Google Calendar in the user's account.

**Inputs:**
```
- `summary`     (string, required) — Name of the new calendar
- `description` (string, optional) — Description of the calendar
- `timezone`    (string, optional) — Timezone string (e.g. "America/New_York"). Defaults to "UTC"
```

**Output:**

```json
{
  "message": "Calendar created successfully",
  "calendar": { "id": "...", "summary": "Work", ... }
}
```

</details>


<details>
<summary><code>delete_calendar</code> — Delete a calendar</summary>

Permanently deletes a calendar by its ID.

**Inputs:**
```
- `calendar_id` (string, required) — ID of the calendar to delete
```

**Output:**

```json
{
  "message": "Calendar cal123 deleted successfully"
}
```

</details>


<details>
<summary><code>list_events</code> — List events from a calendar within a time range</summary>

Returns events from a calendar, optionally filtered by time range and search query. Defaults to events from now onwards if no time range is specified.

**Inputs:**
```
- `calendar_id`  (string,  optional) — Calendar to query. Defaults to "primary"
- `max_results`  (integer, optional) — Maximum number of events to return. Defaults to 10
- `time_min`     (string,  optional) — Start of time range in ISO 8601 format (e.g. "2026-01-08T00:00:00Z")
- `time_max`     (string,  optional) — End of time range in ISO 8601 format
- `query`        (string,  optional) — Free-text search query to filter events
```

**Output:**

```json
{
  "count": 2,
  "events": [{ "id": "...", "summary": "Team Standup", ... }]
}
```

</details>


<details>
<summary><code>get_event</code> — Get details of a specific event</summary>

Fetches full details for a single event by its ID.

**Inputs:**
```
- `event_id`    (string, required) — ID of the event to retrieve
- `calendar_id` (string, optional) — Calendar containing the event. Defaults to "primary"
```

**Output:**

```json
{
  "id": "abc123",
  "summary": "Team Standup",
  "start": { "dateTime": "2026-01-08T09:00:00Z" },
  ...
}
```

</details>


<details>
<summary><code>create_event</code> — Create a new calendar event</summary>

Creates a new event on the specified calendar with full details including attendees.

**Inputs:**
```
- `summary`     (string,       required) — Event title
- `start_time`  (string,       required) — Start time in ISO 8601 format (e.g. "2026-01-08T14:30:00")
- `end_time`    (string,       required) — End time in ISO 8601 format
- `calendar_id` (string,       optional) — Target calendar. Defaults to "primary"
- `description` (string,       optional) — Event description
- `location`    (string,       optional) — Event location
- `attendees`   (list[string], optional) — List of attendee email addresses
- `timezone`    (string,       optional) — Timezone for start/end times (e.g. "America/New_York"). Defaults to "UTC"
```

**Output:**

```json
{
  "message": "Event created successfully",
  "event": { "id": "...", "summary": "Lunch", ... }
}
```

</details>


<details>
<summary><code>create_quick_event</code> — Create an event using natural language text</summary>

Creates a calendar event from a plain-text description (e.g. "Lunch with John tomorrow at 12pm").

**Inputs:**
```
- `text`        (string, required) — Natural language event description
- `calendar_id` (string, optional) — Target calendar. Defaults to "primary"
```

**Output:**

```json
{
  "message": "Event created successfully",
  "event": { "id": "...", "summary": "Lunch with John", ... }
}
```

</details>


<details>
<summary><code>update_event</code> — Update an existing calendar event</summary>

Updates one or more fields of an existing event. Only provided fields are changed; others are preserved.

**Inputs:**
```
- `event_id`    (string, required) — ID of the event to update
- `calendar_id` (string, optional) — Calendar containing the event. Defaults to "primary"
- `summary`     (string, optional) — New event title
- `start_time`  (string, optional) — New start time in ISO 8601 format
- `end_time`    (string, optional) — New end time in ISO 8601 format
- `description` (string, optional) — New event description
- `location`    (string, optional) — New event location
- `timezone`    (string, optional) — Timezone for updated times. Defaults to "UTC"
```

**Output:**

```json
{
  "message": "Event updated successfully",
  "event": { "id": "...", ... }
}
```

</details>


<details>
<summary><code>delete_event</code> — Delete a calendar event</summary>

Permanently deletes an event from the specified calendar.

**Inputs:**
```
- `event_id`    (string, required) — ID of the event to delete
- `calendar_id` (string, optional) — Calendar containing the event. Defaults to "primary"
```

**Output:**

```json
{
  "message": "Event evt123 deleted successfully"
}
```

</details>


<details>
<summary><code>search_events</code> — Search for events containing specific text</summary>

Searches across event titles, descriptions, and locations on a calendar.

**Inputs:**
```
- `query`       (string,  required) — Search text
- `calendar_id` (string,  optional) — Calendar to search. Defaults to "primary"
- `max_results` (integer, optional) — Maximum results to return. Defaults to 10
```

**Output:**

```json
{
  "count": 1,
  "events": [{ "id": "...", "summary": "Project Kickoff", ... }]
}
```

</details>


<details>
<summary><code>get_upcoming_events</code> — Get upcoming events for the next N days</summary>

Returns events starting from now through a specified number of days ahead.

**Inputs:**
```
- `days`        (integer, optional) — Number of days to look ahead. Defaults to 7
- `calendar_id` (string,  optional) — Calendar to query. Defaults to "primary"
- `max_results` (integer, optional) — Maximum results to return. Defaults to 10
```

**Output:**

```json
{
  "count": 5,
  "events": [{ "id": "...", "summary": "Weekly Sync", ... }]
}
```

</details>


<details>
<summary><code>get_todays_events</code> — Get all events for today</summary>

Returns all events scheduled for the current calendar day.

**Inputs:**
```
- `calendar_id` (string, optional) — Calendar to query. Defaults to "primary"
```

**Output:**

```json
{
  "count": 3,
  "events": [{ "id": "...", "summary": "Morning Standup", ... }]
}
```

</details>


<details>
<summary><code>add_attendees</code> — Add attendees to an existing event</summary>

Adds one or more attendees to an event and sends them invitations.

**Inputs:**
```
- `event_id`        (string,       required) — ID of the event to update
- `attendee_emails` (list[string], required) — Email addresses to add
- `calendar_id`     (string,       optional) — Calendar containing the event. Defaults to "primary"
```

**Output:**

```json
{
  "message": "Attendees added successfully",
  "event": { "id": "...", "attendees": [...], ... }
}
```

</details>


<details>
<summary><code>get_free_busy</code> — Get free/busy information for calendars</summary>

Queries the free/busy schedule of one or more calendars within a time window.

**Inputs:**
```
- `time_min`     (string,       required) — Start of query window in ISO 8601 format with Z suffix (e.g. "2026-01-08T09:00:00Z")
- `time_max`     (string,       required) — End of query window in ISO 8601 format with Z suffix
- `calendar_ids` (list[string], optional) — List of calendar IDs to query. Defaults to ["primary"]
```

**Output:**

```json
{
  "calendars": {
    "primary": { "busy": [{ "start": "...", "end": "..." }] }
  }
}
```

</details>


<details>
<summary><code>move_event</code> — Move an event to a different calendar</summary>

Moves an existing event from one calendar to another.

**Inputs:**
```
- `event_id`               (string, required) — ID of the event to move
- `source_calendar_id`     (string, required) — Calendar currently holding the event
- `destination_calendar_id`(string, required) — Calendar to move the event into
```

**Output:**

```json
{
  "message": "Event moved successfully",
  "event": { "id": "...", ... }
}
```

</details>


<details>
<summary><code>create_recurring_event</code> — Create a recurring calendar event</summary>

Creates an event that repeats on a schedule defined by an RRULE string.

**Inputs:**
```
- `summary`         (string, required) — Event title
- `start_time`      (string, required) — First occurrence start time in ISO 8601 format
- `end_time`        (string, required) — First occurrence end time in ISO 8601 format
- `recurrence_rule` (string, required) — RRULE string (e.g. "RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR")
- `calendar_id`     (string, optional) — Target calendar. Defaults to "primary"
- `description`     (string, optional) — Event description
- `location`        (string, optional) — Event location
- `timezone`        (string, optional) — Timezone for event times. Defaults to "UTC"
```

**Output:**

```json
{
  "message": "Recurring event created successfully",
  "event": { "id": "...", "recurrence": ["RRULE:FREQ=WEEKLY;..."], ... }
}
```

</details>


## API Parameters Reference

<details>
<summary><strong>Common Parameters</strong></summary>

- `calendar_id` — Google Calendar ID. Use `"primary"` for the user's default calendar, or a full calendar ID like `"user@example.com"` for others. Retrieve IDs via `list_calendars`.
- `max_results` — Caps the number of items returned. Maximum accepted by the Google API is 2500.
- `timezone` — IANA timezone string (e.g. `"America/New_York"`, `"Europe/London"`). Applied to `start_time` and `end_time` when creating or updating events.

</details>

<details>
<summary><strong>Time Formats</strong></summary>

**Event times (create/update):**

```
Format:  YYYY-MM-DDTHH:MM:SS
Example: 2026-01-08T14:30:00

With timezone offset:
Example: 2026-01-08T14:30:00-05:00
```

**Query range times (list/free-busy):**

```
Format:  YYYY-MM-DDTHH:MM:SSZ  (UTC, Z suffix required)
Example: 2026-01-08T00:00:00Z
```

**Recurrence rules (RRULE):**

```
Daily:            RRULE:FREQ=DAILY
Weekly Mon/Wed/Fri: RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR
Monthly on 15th:  RRULE:FREQ=MONTHLY;BYMONTHDAY=15
```

</details>


## Troubleshooting

<details>
<summary><strong>Missing or Invalid Headers</strong></summary>

- **Cause:** OAuth token not provided in request headers or incorrect format
- **Solution:**
  1. Verify `Authorization: Bearer YOUR_API_KEY` and `X-Mewcp-Credential-Id: CREDENTIAL-ID` headers are present
  2. Check your credential is active in your MewCP account

</details>

<details>
<summary><strong>Insufficient Credits</strong></summary>

- **Cause:** API calls have exceeded your request limits
- **Solution:**
  1. Check credit usage in your Curious Layer dashboard
  2. Upgrade to a paid plan or add credits for higher limits
  3. Contact support for credit adjustments

</details>

<details>
<summary><strong>Credential Not Connected</strong></summary>

- **Cause:** No Google account linked to your MewCP credential
- **Solution:**
  1. Go to **Credentials** in your MewCP dashboard
  2. Connect your Google account via OAuth
  3. Retry the request with the correct `X-Mewcp-Credential-Id` header

</details>

<details>
<summary><strong>Malformed Request Payload</strong></summary>

- **Cause:** JSON payload is invalid or missing required fields
- **Solution:**
  1. Validate JSON syntax before sending
  2. Ensure all required tool parameters are included
  3. Check parameter types match expected values

</details>

<details>
<summary><strong>Server Not Found</strong></summary>

- **Cause:** Incorrect server name in the API endpoint
- **Solution:**
  1. Verify endpoint format: `{server-name}/mcp/{tool-name}`
  2. Use correct server name from documentation
  3. Check available servers in your Curious Layer account

</details>

<details>
<summary><strong>Google Calendar API Error</strong></summary>

- **Cause:** Upstream Google Calendar API returned an error
- **Solution:**
  1. Check Google Workspace service status at [Google Status Dashboard](https://www.google.com/appsstatus)
  2. Verify your Google account has the required Calendar permissions
  3. Review the error message for specific details

</details>

---

<details>
<summary><strong>Resources</strong></summary>

- **[Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)** — Official API reference
- **[Google Calendar API Reference](https://developers.google.com/calendar/api/v3/reference)** — Complete endpoint reference
- **[FastMCP Docs](https://gofastmcp.com/v2/getting-started/welcome)** — FastMCP specification
- **[FastMCP Credentials](https://pypi.org/project/fastmcp-credentials/)** — FastMCP Credentials package for credential handling

</details>
