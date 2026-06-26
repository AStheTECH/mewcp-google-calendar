**Schedule smarter — create, search, and manage Google Calendar events through AI.**

A Model Context Protocol (MCP) server that exposes Google Calendar's API for creating, reading, updating, and deleting events and calendars.


## Overview

The Google Calendar MCP Server provides full calendar management directly from AI workflows:

- List, search, and retrieve events with rich filtering by time range, text, and recurrence
- Create single, all-day, quick, and recurring events with attendees, reminders, and Meet links
- Update events and manage attendees, then get before/after state in a single response
- Query free/busy blocks across multiple calendars to find open slots without conflicts

Perfect for:

- AI assistants that schedule, reschedule, and manage meetings on behalf of users
- Workflow automation that reads calendar state to trigger time-based actions
- Agents that coordinate availability and send invitations across teams


## Tools

### Events — Read

<details>
<summary><code>list_events</code> — List events from a calendar</summary>

Lists events from a calendar within an optional time range. Returns events in start-time order. Recurring events are expanded into individual instances. Use ISO 8601 for time_min/time_max: 'YYYY-MM-DDTHH:MM:SSZ' (e.g. '2026-01-08T00:00:00Z'). Defaults to events from now onwards if time_min is not specified.

**Inputs:**
```
- `calendar_id` (string, optional, default: "primary") — Calendar ID. Use 'primary' for the user's main calendar
- `max_results` (int, optional, default: 10) — Maximum number of events to return (1–2500)
- `time_min` (string, optional, default: "") — Start of time range in ISO 8601 format, e.g. '2026-01-08T00:00:00Z'. Defaults to now
- `time_max` (string, optional, default: "") — End of time range in ISO 8601 format, e.g. '2026-01-15T23:59:59Z'. Omit for open-ended
- `query` (string, optional, default: "") — Free-text search query to filter events by title, description, or location
- `show_deleted` (bool, optional, default: false) — Include cancelled events in results
- `page_token` (string, optional, default: "") — Pagination token from a previous response's next_page_token to fetch the next page
```

**Output `data` schema:**

```typescript
{
  count: number;
  events: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  }[];
  next_page_token: string | null;
}
```

</details>


<details>
<summary><code>get_event</code> — Get a single event by ID</summary>

Gets full details of a specific event including attendees, RSVP statuses, recurrence rules, reminders, and conferencing info.

**Inputs:**
```
- `event_id` (string, required) — ID of the event to retrieve
- `calendar_id` (string, optional, default: "primary") — Calendar ID containing the event. Use 'primary' for the user's main calendar
```

**Output `data` schema:**

```typescript
{
  id: string;
  summary: string | null;
  start: { date: string | null; dateTime: string | null; timeZone: string | null; };
  end: { date: string | null; dateTime: string | null; timeZone: string | null; };
  status: string | null;
  htmlLink: string | null;
  created: string | null;
  updated: string | null;
  description: string | null;
  location: string | null;
  colorId: string | null;
  creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  recurrence: string[] | null;
  recurringEventId: string | null;
  originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
  transparency: string | null;
  visibility: string | null;
  iCalUID: string | null;
  sequence: number | null;
  attendees: {
    email: string;
    id: string | null;
    displayName: string | null;
    organizer: boolean | null;
    self: boolean | null;
    resource: boolean | null;
    optional: boolean | null;
    responseStatus: string | null;
    comment: string | null;
    additionalGuests: number | null;
  }[] | null;
  attendeesOmitted: boolean | null;
  guestsCanInviteOthers: boolean | null;
  guestsCanModify: boolean | null;
  guestsCanSeeOtherGuests: boolean | null;
  hangoutLink: string | null;
  conferenceData: object | null;
  reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
  eventType: string | null;
}
```

</details>


<details>
<summary><code>search_events</code> — Search events by text</summary>

Searches for events by text across titles, descriptions, and locations. Optionally bound the search to a time range with time_min/time_max (ISO 8601, e.g. '2026-01-08T00:00:00Z'). Without a time range the search spans all history — always use a time range for large calendars.

**Inputs:**
```
- `query` (string, required) — Text to search for in event titles, descriptions, and locations
- `calendar_id` (string, optional, default: "primary") — Calendar ID to search in. Use 'primary' for the user's main calendar
- `max_results` (int, optional, default: 10) — Maximum number of events to return (1–2500)
- `time_min` (string, optional, default: "") — Optional start of time range in ISO 8601 format, e.g. '2026-01-01T00:00:00Z'
- `time_max` (string, optional, default: "") — Optional end of time range in ISO 8601 format, e.g. '2026-12-31T23:59:59Z'
- `page_token` (string, optional, default: "") — Pagination token from a previous response's next_page_token to fetch the next page
```

**Output `data` schema:**

```typescript
{
  count: number;
  events: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  }[];
  next_page_token: string | null;
}
```

</details>


<details>
<summary><code>get_upcoming_events</code> — Get events in the next N days</summary>

Gets events starting from now through the next N days. Returns events in start-time order. Recurring events are expanded into individual instances.

**Inputs:**
```
- `days` (int, optional, default: 7) — Number of days to look ahead from now
- `calendar_id` (string, optional, default: "primary") — Calendar ID to query. Use 'primary' for the user's main calendar
- `max_results` (int, optional, default: 10) — Maximum number of events to return (1–2500)
```

**Output `data` schema:**

```typescript
{
  count: number;
  events: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  }[];
  next_page_token: string | null;
}
```

</details>


<details>
<summary><code>get_todays_events</code> — Get all events for today</summary>

Gets all events scheduled for today in the given timezone. Pass the user's local timezone to get the correct day (e.g. 'America/New_York'). Defaults to UTC.

**Inputs:**
```
- `calendar_id` (string, optional, default: "primary") — Calendar ID to query. Use 'primary' for the user's main calendar
- `timezone` (string, optional, default: "UTC") — IANA timezone name to determine 'today', e.g. 'America/New_York'. Defaults to UTC
```

**Output `data` schema:**

```typescript
{
  count: number;
  events: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  }[];
  next_page_token: string | null;
}
```

</details>


<details>
<summary><code>list_event_instances</code> — List instances of a recurring event</summary>

Lists all individual instances of a recurring event by its master event ID. Use this to see every occurrence of a recurring series — use get_event or list_events to find the master event ID first. Instances include recurringEventId (the master ID) and originalStartTime (the scheduled time per RRULE, which differs from start if the instance was rescheduled). Optionally filter by time range to see only upcoming or past occurrences.

**Inputs:**
```
- `recurring_event_id` (string, required) — ID of the master recurring event whose instances to list
- `calendar_id` (string, optional, default: "primary") — Calendar ID containing the recurring event. Use 'primary' for the user's main calendar
- `max_results` (int, optional, default: 10) — Maximum number of instances to return (1–2500)
- `time_min` (string, optional, default: "") — Optional start of time range in ISO 8601 format, e.g. '2026-01-01T00:00:00Z'. Filters to instances starting at or after this time
- `time_max` (string, optional, default: "") — Optional end of time range in ISO 8601 format. Filters to instances starting before this time
- `show_deleted` (bool, optional, default: false) — Include cancelled instances in results
- `page_token` (string, optional, default: "") — Pagination token from a previous response's next_page_token to fetch the next page
```

**Output `data` schema:**

```typescript
{
  count: number;
  events: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  }[];
  next_page_token: string | null;
}
```

</details>


### Events — Write

<details>
<summary><code>create_event</code> — Create a new calendar event</summary>

Creates a new calendar event and optionally invites attendees. For timed events use ISO 8601 datetime: '2026-01-08T14:30:00' with a timezone. For all-day events set is_all_day=True and use date-only format: '2026-01-08' — for all-day events end_time is exclusive, so a single-day event on Jan 8 needs end_time='2026-01-09'. Returns the created event with its ID.

**Inputs:**
```
- `summary` (string, required) — Event title
- `start_time` (string, required) — Start time: ISO 8601 datetime e.g. '2026-01-08T14:30:00', or date e.g. '2026-01-08' for all-day events
- `end_time` (string, required) — End time: ISO 8601 datetime or date. For all-day, end is exclusive: event on Jan 8 alone needs end_time='2026-01-09'
- `calendar_id` (string, optional, default: "primary") — Calendar ID to create the event in. Use 'primary' for the user's main calendar
- `description` (string, optional, default: "") — Event description or agenda
- `location` (string, optional, default: "") — Event location. Enables map directions and 'time to leave' alerts in Google Calendar
- `attendees` (list[string], optional, default: []) — Attendee email addresses. Invitation emails are sent per send_updates
- `timezone` (string, optional, default: "UTC") — IANA timezone for the event, e.g. 'America/New_York'. Ignored for all-day events
- `is_all_day` (bool, optional, default: false) — Set True for all-day events. Use date-only format (YYYY-MM-DD) for start_time and end_time
- `color_id` (string, optional, default: "") — Color ID 1–11 for the event. Empty uses the calendar's default color
- `visibility` (string, optional, default: "") — Event visibility: 'default', 'public', 'private', or 'confidential'. Empty uses calendar default
- `transparency` (string, optional, default: "") — Free/busy status: 'opaque' (user shows as busy, default) or 'transparent' (user shows as free/available during this event)
- `reminder_minutes` (int, optional, default: -1) — Minutes before event for a popup reminder (0–40320). Set -1 to use the calendar's default reminders
- `send_updates` (string, optional, default: "all") — Who receives invitation emails: 'all' (everyone), 'externalOnly' (non-Google users only), 'none' (no emails)
- `add_meet` (bool, optional, default: false) — Set True to automatically create a Google Meet video conference link for this event
- `optional_attendees` (list[string], optional, default: []) — Email addresses of optional attendees. These people are invited but their attendance is not required
- `guests_can_invite_others` (bool, optional, default: true) — Whether attendees can invite additional guests. Defaults to True per Google Calendar
- `guests_can_modify` (bool, optional, default: false) — Whether attendees can modify the event. Defaults to False
```

**Output `data` schema:**

```typescript
{
  id: string;
  summary: string | null;
  start: { date: string | null; dateTime: string | null; timeZone: string | null; };
  end: { date: string | null; dateTime: string | null; timeZone: string | null; };
  status: string | null;
  htmlLink: string | null;
  created: string | null;
  updated: string | null;
  description: string | null;
  location: string | null;
  colorId: string | null;
  creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  recurrence: string[] | null;
  recurringEventId: string | null;
  originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
  transparency: string | null;
  visibility: string | null;
  iCalUID: string | null;
  sequence: number | null;
  attendees: {
    email: string;
    id: string | null;
    displayName: string | null;
    organizer: boolean | null;
    self: boolean | null;
    resource: boolean | null;
    optional: boolean | null;
    responseStatus: string | null;
    comment: string | null;
    additionalGuests: number | null;
  }[] | null;
  attendeesOmitted: boolean | null;
  guestsCanInviteOthers: boolean | null;
  guestsCanModify: boolean | null;
  guestsCanSeeOtherGuests: boolean | null;
  hangoutLink: string | null;
  conferenceData: object | null;
  reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
  eventType: string | null;
}
```

</details>


<details>
<summary><code>create_quick_event</code> — Create an event from natural language</summary>

Creates an event from a natural language text description. Google Calendar parses the text to extract title, date, time, and recurrence. Examples: 'Lunch with Sarah tomorrow at noon', 'Team standup every Monday at 9am'. Returns the created event. For complex events with attendees or custom fields, use create_event instead.

**Inputs:**
```
- `text` (string, required) — Natural language event description, e.g. 'Dentist appointment next Friday at 3pm'
- `calendar_id` (string, optional, default: "primary") — Calendar ID to create the event in. Use 'primary' for the user's main calendar
- `send_updates` (string, optional, default: "all") — Who receives invitation emails: 'all', 'externalOnly', or 'none'
```

**Output `data` schema:**

```typescript
{
  id: string;
  summary: string | null;
  start: { date: string | null; dateTime: string | null; timeZone: string | null; };
  end: { date: string | null; dateTime: string | null; timeZone: string | null; };
  status: string | null;
  htmlLink: string | null;
  created: string | null;
  updated: string | null;
  description: string | null;
  location: string | null;
  colorId: string | null;
  creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  recurrence: string[] | null;
  recurringEventId: string | null;
  originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
  transparency: string | null;
  visibility: string | null;
  iCalUID: string | null;
  sequence: number | null;
  attendees: {
    email: string;
    id: string | null;
    displayName: string | null;
    organizer: boolean | null;
    self: boolean | null;
    resource: boolean | null;
    optional: boolean | null;
    responseStatus: string | null;
    comment: string | null;
    additionalGuests: number | null;
  }[] | null;
  attendeesOmitted: boolean | null;
  guestsCanInviteOthers: boolean | null;
  guestsCanModify: boolean | null;
  guestsCanSeeOtherGuests: boolean | null;
  hangoutLink: string | null;
  conferenceData: object | null;
  reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
  eventType: string | null;
}
```

</details>


<details>
<summary><code>create_recurring_event</code> — Create a recurring event with an RRULE</summary>

Creates a recurring calendar event using an RRULE recurrence pattern. recurrence_rule must start with 'RRULE:' followed by RFC 5545 parameters. Examples: 'RRULE:FREQ=DAILY;COUNT=5', 'RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR', 'RRULE:FREQ=MONTHLY;BYMONTHDAY=15', 'RRULE:FREQ=YEARLY'. Returns the master recurring event — individual instances are expanded by Google Calendar.

**Inputs:**
```
- `summary` (string, required) — Event title
- `start_time` (string, required) — Start time of the first occurrence in ISO 8601 format, e.g. '2026-01-08T14:30:00'
- `end_time` (string, required) — End time of the first occurrence in ISO 8601 format, e.g. '2026-01-08T15:30:00'
- `recurrence_rule` (string, required) — RRULE string starting with 'RRULE:', e.g. 'RRULE:FREQ=WEEKLY;BYDAY=MO'
- `calendar_id` (string, optional, default: "primary") — Calendar ID to create the event in. Use 'primary' for the user's main calendar
- `description` (string, optional, default: "") — Event description or agenda
- `location` (string, optional, default: "") — Event location
- `attendees` (list[string], optional, default: []) — Attendee email addresses. Invitation emails are sent per send_updates
- `timezone` (string, optional, default: "UTC") — IANA timezone for the event, e.g. 'America/New_York'
- `transparency` (string, optional, default: "") — Free/busy status: 'opaque' (shows as busy, default) or 'transparent' (shows as free)
- `reminder_minutes` (int, optional, default: -1) — Minutes before each occurrence for a popup reminder (0–40320). Set -1 to use calendar default
- `send_updates` (string, optional, default: "all") — Who receives invitation emails: 'all', 'externalOnly', or 'none'
- `add_meet` (bool, optional, default: false) — Set True to automatically create a Google Meet video conference link for this event
- `optional_attendees` (list[string], optional, default: []) — Email addresses of optional attendees. These people are invited but their attendance is not required
- `guests_can_invite_others` (bool, optional, default: true) — Whether attendees can invite additional guests. Defaults to True per Google Calendar
- `guests_can_modify` (bool, optional, default: false) — Whether attendees can modify the event. Defaults to False
```

**Output `data` schema:**

```typescript
{
  id: string;
  summary: string | null;
  start: { date: string | null; dateTime: string | null; timeZone: string | null; };
  end: { date: string | null; dateTime: string | null; timeZone: string | null; };
  status: string | null;
  htmlLink: string | null;
  created: string | null;
  updated: string | null;
  description: string | null;
  location: string | null;
  colorId: string | null;
  creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  recurrence: string[] | null;
  recurringEventId: string | null;
  originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
  transparency: string | null;
  visibility: string | null;
  iCalUID: string | null;
  sequence: number | null;
  attendees: {
    email: string;
    id: string | null;
    displayName: string | null;
    organizer: boolean | null;
    self: boolean | null;
    resource: boolean | null;
    optional: boolean | null;
    responseStatus: string | null;
    comment: string | null;
    additionalGuests: number | null;
  }[] | null;
  attendeesOmitted: boolean | null;
  guestsCanInviteOthers: boolean | null;
  guestsCanModify: boolean | null;
  guestsCanSeeOtherGuests: boolean | null;
  hangoutLink: string | null;
  conferenceData: object | null;
  reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
  eventType: string | null;
}
```

</details>


<details>
<summary><code>update_event</code> — Update an existing event</summary>

Updates an existing calendar event. Only the fields you provide are changed — leave a field empty to keep its current value. Fetches the current event first, applies changes, then saves. Use ISO 8601 for times: 'YYYY-MM-DDTHH:MM:SS'. For recurring events: pass the master recurring event ID to change all instances, or a specific instance ID to change only that occurrence. WARNING: do not update individual instances one-by-one to change the whole series — update the master event instead. Modifying instances individually creates exceptions that clutter the calendar and trigger excessive notifications. To cancel a single instance without affecting the rest of the series, set status='cancelled'.

**Inputs:**
```
- `event_id` (string, required) — ID of the event to update. For recurring events, use the master event ID to change all instances, or an instance ID to change only one occurrence
- `calendar_id` (string, optional, default: "primary") — Calendar ID containing the event
- `summary` (string, optional, default: "") — New event title. Leave empty to keep existing
- `start_time` (string, optional, default: "") — New start time in ISO 8601 format. Leave empty to keep existing
- `end_time` (string, optional, default: "") — New end time in ISO 8601 format. Leave empty to keep existing
- `description` (string, optional, default: "") — New event description. Leave empty to keep existing
- `location` (string, optional, default: "") — New event location. Leave empty to keep existing
- `timezone` (string, optional, default: "") — Timezone for the updated start/end times, e.g. 'America/New_York'. Leave empty to keep the event's existing timezone
- `status` (string, optional, default: "") — Event status: 'confirmed', 'tentative', or 'cancelled'. Set 'cancelled' on a recurring event instance ID to cancel only that occurrence without affecting the rest of the series
- `transparency` (string, optional, default: "") — Free/busy status: 'opaque' (shows as busy) or 'transparent' (shows as free). Leave empty to keep existing
- `reminder_minutes` (int, optional, default: -1) — Minutes before event for a popup reminder (0–40320). Set -1 to keep existing reminders
- `send_updates` (string, optional, default: "all") — Who receives update notifications: 'all', 'externalOnly', or 'none'
- `add_meet` (bool, optional, default: false) — Set True to add a Google Meet video conference link to this event. Has no effect if a Meet link already exists
- `guests_can_invite_others` (bool, optional) — Whether attendees can invite additional guests. Leave unset to keep existing value
- `guests_can_modify` (bool, optional) — Whether attendees can modify the event. Leave unset to keep existing value
```

**Output `data` schema:**

```typescript
{
  before: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  };
  after: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  };
}
```

</details>


<details>
<summary><code>add_attendees</code> — Add attendees to an event</summary>

Adds new attendees to an existing event and sends them invitation emails. Skips emails that are already on the attendee list.

**Inputs:**
```
- `event_id` (string, required) — ID of the event to add attendees to
- `attendee_emails` (list[string], required) — Email addresses to add as required attendees
- `calendar_id` (string, optional, default: "primary") — Calendar ID containing the event
- `send_updates` (string, optional, default: "all") — Who receives invitation emails: 'all', 'externalOnly', or 'none'
- `optional_attendees` (list[string], optional, default: []) — Email addresses to add as optional attendees. These are invited but their attendance is not required
```

**Output `data` schema:**

```typescript
{
  before: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  };
  after: {
    id: string;
    summary: string | null;
    start: { date: string | null; dateTime: string | null; timeZone: string | null; };
    end: { date: string | null; dateTime: string | null; timeZone: string | null; };
    status: string | null;
    htmlLink: string | null;
    created: string | null;
    updated: string | null;
    description: string | null;
    location: string | null;
    colorId: string | null;
    creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
    recurrence: string[] | null;
    recurringEventId: string | null;
    originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
    transparency: string | null;
    visibility: string | null;
    iCalUID: string | null;
    sequence: number | null;
    attendees: {
      email: string;
      id: string | null;
      displayName: string | null;
      organizer: boolean | null;
      self: boolean | null;
      resource: boolean | null;
      optional: boolean | null;
      responseStatus: string | null;
      comment: string | null;
      additionalGuests: number | null;
    }[] | null;
    attendeesOmitted: boolean | null;
    guestsCanInviteOthers: boolean | null;
    guestsCanModify: boolean | null;
    guestsCanSeeOtherGuests: boolean | null;
    hangoutLink: string | null;
    conferenceData: object | null;
    reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
    eventType: string | null;
  };
}
```

</details>


### Events — Delete

<details>
<summary><code>delete_event</code> — Permanently delete an event</summary>

DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. Permanently deletes a calendar event. This action is irreversible: the event, its attendees list, reminders, and all associated data are removed immediately and cannot be recovered. Attendees will receive cancellation emails (controlled by send_updates). For recurring events: deleting the master event ID removes the entire series and all its instances. Deleting a specific instance ID removes only that one occurrence. NEVER call this tool autonomously or as part of an automated flow. You MUST stop, tell the user the event title, date, and time that will be permanently deleted, and for recurring events clarify whether you are deleting one occurrence or the entire series, and wait for their explicit written confirmation before proceeding.

**Inputs:**
```
- `event_id` (string, required) — ID of the event to delete
- `calendar_id` (string, optional, default: "primary") — Calendar ID containing the event
- `send_updates` (string, optional, default: "all") — Who receives cancellation emails: 'all' (recommended), 'externalOnly', or 'none'
```

**Output `data` schema:**

```typescript
{
  message: string;
}
```

</details>


<details>
<summary><code>move_event</code> — Move an event to another calendar</summary>

DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. Moves a default event from one calendar to another. Only events of type 'default' can be moved — birthday, focusTime, fromGmail, outOfOffice, and workingLocation events cannot be moved and will return an error. The event is removed from the source calendar and placed in the destination calendar — any calendar-specific settings, sharing permissions, or notification rules from the source will no longer apply. While technically reversible by moving back, this can disrupt other attendees and shared calendar visibility in ways that are hard to track down. NEVER call this tool autonomously. You MUST tell the user which event is being moved, from which calendar to which, and wait for their explicit confirmation.

**Inputs:**
```
- `event_id` (string, required) — ID of the event to move
- `source_calendar_id` (string, required) — ID of the calendar currently containing the event
- `destination_calendar_id` (string, required) — ID of the destination calendar
```

**Output `data` schema:**

```typescript
{
  id: string;
  summary: string | null;
  start: { date: string | null; dateTime: string | null; timeZone: string | null; };
  end: { date: string | null; dateTime: string | null; timeZone: string | null; };
  status: string | null;
  htmlLink: string | null;
  created: string | null;
  updated: string | null;
  description: string | null;
  location: string | null;
  colorId: string | null;
  creator: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  organizer: { id: string | null; email: string | null; displayName: string | null; self: boolean | null; } | null;
  recurrence: string[] | null;
  recurringEventId: string | null;
  originalStartTime: { date: string | null; dateTime: string | null; timeZone: string | null; } | null;
  transparency: string | null;
  visibility: string | null;
  iCalUID: string | null;
  sequence: number | null;
  attendees: {
    email: string;
    id: string | null;
    displayName: string | null;
    organizer: boolean | null;
    self: boolean | null;
    resource: boolean | null;
    optional: boolean | null;
    responseStatus: string | null;
    comment: string | null;
    additionalGuests: number | null;
  }[] | null;
  attendeesOmitted: boolean | null;
  guestsCanInviteOthers: boolean | null;
  guestsCanModify: boolean | null;
  guestsCanSeeOtherGuests: boolean | null;
  hangoutLink: string | null;
  conferenceData: object | null;
  reminders: { useDefault: boolean; overrides: { method: string; minutes: number; }[] | null; } | null;
  eventType: string | null;
}
```

</details>


### Calendars

<details>
<summary><code>list_calendars</code> — List all calendars</summary>

Lists all calendars the user has access to. Returns calendar IDs, names, timezones, colors, and access roles. Use min_access_role to filter to calendars the user can write to.

**Inputs:**
```
- `min_access_role` (string, optional, default: "") — Minimum access role to filter by: 'freeBusyReader', 'reader', 'writer', or 'owner'. Empty returns all calendars
- `show_hidden` (bool, optional, default: false) — Include calendars hidden from the list view
- `max_results` (int, optional, default: 100) — Maximum number of calendars to return (1–250)
- `page_token` (string, optional, default: "") — Pagination token from a previous response's next_page_token to fetch the next page
```

**Output `data` schema:**

```typescript
{
  count: number;
  calendars: {
    id: string;
    summary: string;
    description: string | null;
    location: string | null;
    timeZone: string | null;
    accessRole: string | null;
    backgroundColor: string | null;
    foregroundColor: string | null;
    selected: boolean | null;
    primary: boolean | null;
    hidden: boolean | null;
  }[];
  next_page_token: string | null;
}
```

</details>


<details>
<summary><code>get_calendar</code> — Get a single calendar</summary>

Gets full details of a specific calendar including its name, description, timezone, and color settings.

**Inputs:**
```
- `calendar_id` (string, optional, default: "primary") — Calendar ID. Use 'primary' for the user's main calendar
```

**Output `data` schema:**

```typescript
{
  id: string;
  summary: string;
  description: string | null;
  location: string | null;
  timeZone: string | null;
  accessRole: string | null;
  backgroundColor: string | null;
  foregroundColor: string | null;
  selected: boolean | null;
  primary: boolean | null;
  hidden: boolean | null;
}
```

</details>


<details>
<summary><code>create_calendar</code> — Create a new calendar</summary>

Creates a new calendar owned by the user. Returns the created calendar with its ID, which is needed for all subsequent operations on that calendar.

**Inputs:**
```
- `summary` (string, required) — Name of the new calendar
- `description` (string, optional, default: "") — Optional description for the calendar
- `timezone` (string, optional, default: "UTC") — IANA timezone name for the calendar, e.g. 'America/New_York'
```

**Output `data` schema:**

```typescript
{
  id: string;
  summary: string;
  description: string | null;
  location: string | null;
  timeZone: string | null;
  accessRole: string | null;
  backgroundColor: string | null;
  foregroundColor: string | null;
  selected: boolean | null;
  primary: boolean | null;
  hidden: boolean | null;
}
```

</details>


<details>
<summary><code>delete_calendar</code> — Permanently delete a calendar</summary>

DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. Permanently deletes an entire calendar and every event it contains. This action is irreversible: all events, recurring series, and history in the calendar are gone immediately with no way to recover them. NEVER call this tool autonomously or as part of an automated flow. You MUST stop, tell the user exactly which calendar will be deleted and that all its events will be permanently lost, and wait for their explicit written confirmation before proceeding.

**Inputs:**
```
- `calendar_id` (string, required) — ID of the calendar to delete
```

**Output `data` schema:**

```typescript
{
  message: string;
}
```

</details>


<details>
<summary><code>clear_calendar</code> — Delete all events from a calendar</summary>

DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. Permanently deletes ALL events from a calendar without deleting the calendar itself. This action is irreversible: every event in the calendar — past, present, and future — is removed immediately with no way to recover them. The calendar itself remains and can be used for new events. This is the only way to clear the primary calendar, which cannot be deleted. NEVER call this tool autonomously or as part of an automated flow. You MUST stop, tell the user exactly which calendar will be cleared and that every event in it will be permanently deleted, and wait for their explicit written confirmation before proceeding.

**Inputs:**
```
- `calendar_id` (string, required) — ID of the calendar to clear. Use 'primary' for the user's main calendar. WARNING: all events in this calendar will be permanently deleted
```

**Output `data` schema:**

```typescript
{
  message: string;
}
```

</details>


### Free/Busy

<details>
<summary><code>get_free_busy</code> — Query busy blocks across calendars</summary>

Returns busy time blocks for one or more calendars within a time range. Use this to find when someone is available or to schedule without conflicts. Provide time_min and time_max in ISO 8601 format with timezone, e.g. '2026-01-08T09:00:00Z'. Returns a map of calendar ID → list of busy time blocks. Free time = gaps between the busy blocks within the requested range.

**Inputs:**
```
- `time_min` (string, required) — Start of the query window in ISO 8601 format, e.g. '2026-01-08T09:00:00Z'
- `time_max` (string, required) — End of the query window in ISO 8601 format, e.g. '2026-01-08T17:00:00Z'
- `calendar_ids` (list[string], optional, default: []) — Calendar IDs to query. Defaults to ['primary'] if empty
```

**Output `data` schema:**

```typescript
{
  timeMin: string;
  timeMax: string;
  calendars: {
    [calendarId: string]: {
      busy: {
        start: string;
        end: string;
      }[];
      errors: object[] | null;
    };
  };
}
```

</details>


## API Parameters Reference

<details>
<summary><strong>Response Envelope</strong></summary>

Every tool returns the same top-level envelope. Only `data` varies per tool.

```typescript
// Success
{
  success: true;
  statusCode: number;
  retriable: false;
  retry_after_seconds: null;
  error: null;
  data: { ... };   // schema shown per tool above
}

// Error
{
  success: false;
  statusCode: number;
  retriable: boolean;
  retry_after_seconds: number | null;
  error: {
    code: string;    // VALIDATION_ERROR | AUTH_ERROR | UPSTREAM_ERROR | SERVER_ERROR
    message: string;
    details: any;
  };
  data: null;
}
```

- `retriable` — `true` when it is safe to retry (rate limit, network error, 503). `false` for validation and auth errors.
- `retry_after_seconds` — seconds to wait before retrying; present only when `retriable` is `true` and the upstream specifies a delay.

</details>

<details>
<summary><strong>Date and Time Formats</strong></summary>

All tools use ISO 8601 format for date and time values.

**Timed events:**
```
YYYY-MM-DDTHH:MM:SS         local time (requires timezone param)
YYYY-MM-DDTHH:MM:SSZ        UTC
YYYY-MM-DDTHH:MM:SS±HH:MM   explicit offset
```

**All-day events** (use with `is_all_day=true`):
```
YYYY-MM-DD    e.g. 2026-01-08
```

For all-day events, `end_time` is exclusive — a single-day event on Jan 8 needs `end_time='2026-01-09'`.

</details>

<details>
<summary><strong>Recurrence Rules (RRULE)</strong></summary>

`create_recurring_event` requires an RFC 5545 RRULE string starting with `RRULE:`.

```
RRULE:FREQ=DAILY;COUNT=5                     — 5 daily occurrences
RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR            — every Mon/Wed/Fri
RRULE:FREQ=MONTHLY;BYMONTHDAY=15            — 15th of each month
RRULE:FREQ=YEARLY                            — same date each year
RRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20261231T000000Z  — until a date
```

</details>

<details>
<summary><strong>Calendar ID</strong></summary>

- `primary` — the user's main Google Calendar (always valid)
- All other calendars use a full ID from `list_calendars`, e.g. `work@group.calendar.google.com`

`list_calendars` returns `id` for every calendar the user has access to.

</details>

<details>
<summary><strong>Pagination</strong></summary>

`list_events`, `search_events`, `list_event_instances`, and `list_calendars` support pagination via `next_page_token`.

When `data.next_page_token` is non-null in a response, pass it as `page_token` in the next call with the same parameters to retrieve the next page.

</details>


## Troubleshooting

<details>
<summary><strong>Missing or Invalid Headers</strong></summary>

- **Cause:** OAuth token not provided in request headers or incorrect format
- **Solution:**
  1. Verify `Authorization: Bearer YOUR_TOKEN` and `X-Mewcp-Credential-Id: CREDENTIAL-ID` headers are present
  2. Check the OAuth token has not expired — reconnect in your MewCP account if needed

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

- **Cause:** No Google Calendar credential linked to your account
- **Solution:**
  1. Go to **Credentials** in your MewCP dashboard
  2. Connect your Google account (OAuth)
  3. Retry the request with the correct `X-Mewcp-Credential-Id` header

</details>

<details>
<summary><strong>Malformed Request Payload</strong></summary>

- **Cause:** JSON payload is invalid or missing required fields
- **Solution:**
  1. Validate JSON syntax before sending
  2. Ensure all required tool parameters are included
  3. Check parameter types match expected values (e.g. `time_min` must be ISO 8601)

</details>

<details>
<summary><strong>Server Not Found</strong></summary>

- **Cause:** Incorrect server name in the API endpoint
- **Solution:**
  1. Verify endpoint format: `{server-name}/mcp/{tool-name}`
  2. Use the correct server name from documentation
  3. Check available servers in your Curious Layer account

</details>

<details>
<summary><strong>Google Calendar API Error</strong></summary>

- **Cause:** Upstream Google Calendar API returned an error
- **Solution:**
  1. Check [Google Workspace Status](https://www.google.com/appsstatus) for service issues
  2. Verify your Google account has the required calendar permissions
  3. Review the error message in the response for specific details

</details>

---

<details>
<summary><strong>Resources</strong></summary>

- **[Google Calendar API Documentation](https://developers.google.com/calendar/api/v3/reference)** — Official API reference
- **[Google Calendar API Events Reference](https://developers.google.com/calendar/api/v3/reference/events)** — Complete events endpoint reference
- **[FastMCP Docs](https://gofastmcp.com/v2/getting-started/welcome)** — FastMCP specification
- **[FastMCP Credentials](https://pypi.org/project/fastmcp-credentials/)** — FastMCP Credentials package for credential handling

</details>
