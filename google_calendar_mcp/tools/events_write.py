from __future__ import annotations

import logging
import uuid
from typing import List

from googleapiclient.errors import HttpError
from mcp.types import ToolAnnotations
from pydantic import Field

from . import mcp, _upstream_error
from ..logging_utils import ToolLogger
from ..schemas import (
    EventData,
    EventResult,
    EventUpdateData,
    EventUpdateResult,
    ToolError,
)
from ..service import get_service

logger = logging.getLogger("calendar-mcp-server")


@mcp.tool(
    name="create_event",
    description=(
        "Creates a new calendar event and optionally invites attendees. "
        "For timed events use ISO 8601 datetime: '2026-01-08T14:30:00' with a timezone. "
        "For all-day events set is_all_day=True and use date-only format: '2026-01-08' — "
        "for all-day events end_time is exclusive, so a single-day event on Jan 8 needs end_time='2026-01-09'. "
        "Returns the created event with its ID."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
)
def create_event(
    summary: str = Field(..., description="Event title"),
    start_time: str = Field(..., description="Start time: ISO 8601 datetime e.g. '2026-01-08T14:30:00', or date e.g. '2026-01-08' for all-day events"),
    end_time: str = Field(..., description="End time: ISO 8601 datetime or date. For all-day, end is exclusive: event on Jan 8 alone needs end_time='2026-01-09'"),
    calendar_id: str = Field(default="primary", description="Calendar ID to create the event in. Use 'primary' for the user's main calendar"),
    description: str = Field(default="", description="Event description or agenda"),
    location: str = Field(default="", description="Event location. Enables map directions and 'time to leave' alerts in Google Calendar"),
    attendees: List[str] = Field(default=[], description="Attendee email addresses. Invitation emails are sent per send_updates"),
    timezone: str = Field(default="UTC", description="IANA timezone for the event, e.g. 'America/New_York'. Ignored for all-day events"),
    is_all_day: bool = Field(default=False, description="Set True for all-day events. Use date-only format (YYYY-MM-DD) for start_time and end_time"),
    color_id: str = Field(default="", description="Color ID 1–11 for the event. Empty uses the calendar's default color"),
    visibility: str = Field(default="", description="Event visibility: 'default', 'public', 'private', or 'confidential'. Empty uses calendar default"),
    transparency: str = Field(default="", description="Free/busy status: 'opaque' (user shows as busy, default) or 'transparent' (user shows as free/available during this event)"),
    reminder_minutes: int = Field(default=-1, description="Minutes before event for a popup reminder (0–40320). Set -1 to use the calendar's default reminders"),
    send_updates: str = Field(default="all", description="Who receives invitation emails: 'all' (everyone), 'externalOnly' (non-Google users only), 'none' (no emails)"),
    add_meet: bool = Field(default=False, description="Set True to automatically create a Google Meet video conference link for this event"),
    optional_attendees: List[str] = Field(default=[], description="Email addresses of optional attendees. These people are invited but their attendance is not required"),
    guests_can_invite_others: bool = Field(default=True, description="Whether attendees can invite additional guests. Defaults to True per Google Calendar"),
    guests_can_modify: bool = Field(default=False, description="Whether attendees can modify the event. Defaults to False"),
) -> EventResult:
    tlog = ToolLogger(logger, "create_event")
    try:
        service = get_service()
        body: dict = {
            "summary": summary,
        }
        if description:
            body["description"] = description
        if location:
            body["location"] = location
        if color_id:
            body["colorId"] = color_id
        if visibility:
            body["visibility"] = visibility
        if transparency:
            body["transparency"] = transparency
        if reminder_minutes >= 0:
            body["reminders"] = {"useDefault": False, "overrides": [{"method": "popup", "minutes": reminder_minutes}]}
        if is_all_day:
            body["start"] = {"date": start_time}
            body["end"] = {"date": end_time}
        else:
            body["start"] = {"dateTime": start_time, "timeZone": timezone}
            body["end"] = {"dateTime": end_time, "timeZone": timezone}
        all_attendees = [{"email": email} for email in attendees]
        all_attendees += [{"email": email, "optional": True} for email in optional_attendees]
        if all_attendees:
            body["attendees"] = all_attendees
        body["guestsCanInviteOthers"] = guests_can_invite_others
        body["guestsCanModify"] = guests_can_modify
        if add_meet:
            body["conferenceData"] = {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        created = service.events().insert(
            calendarId=calendar_id, body=body, sendUpdates=send_updates,
            conferenceDataVersion=1,
        ).execute()
        tlog.success()
        return EventResult(
            success=True, statusCode=200,
            data=EventData.model_validate(created),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="create_quick_event",
    description=(
        "Creates an event from a natural language text description. "
        "Google Calendar parses the text to extract title, date, time, and recurrence. "
        "Examples: 'Lunch with Sarah tomorrow at noon', 'Team standup every Monday at 9am'. "
        "Returns the created event. For complex events with attendees or custom fields, use create_event instead."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
)
def create_quick_event(
    text: str = Field(..., description="Natural language event description, e.g. 'Dentist appointment next Friday at 3pm'"),
    calendar_id: str = Field(default="primary", description="Calendar ID to create the event in. Use 'primary' for the user's main calendar"),
    send_updates: str = Field(default="all", description="Who receives invitation emails: 'all', 'externalOnly', or 'none'"),
) -> EventResult:
    tlog = ToolLogger(logger, "create_quick_event")
    try:
        service = get_service()
        event = service.events().quickAdd(
            calendarId=calendar_id, text=text, sendUpdates=send_updates,
        ).execute()
        tlog.success()
        return EventResult(
            success=True, statusCode=200,
            data=EventData.model_validate(event),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="create_recurring_event",
    description=(
        "Creates a recurring calendar event using an RRULE recurrence pattern. "
        "recurrence_rule must start with 'RRULE:' followed by RFC 5545 parameters. "
        "Examples: 'RRULE:FREQ=DAILY;COUNT=5', 'RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR', 'RRULE:FREQ=MONTHLY;BYMONTHDAY=15', 'RRULE:FREQ=YEARLY'. "
        "Returns the master recurring event — individual instances are expanded by Google Calendar."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
)
def create_recurring_event(
    summary: str = Field(..., description="Event title"),
    start_time: str = Field(..., description="Start time of the first occurrence in ISO 8601 format, e.g. '2026-01-08T14:30:00'"),
    end_time: str = Field(..., description="End time of the first occurrence in ISO 8601 format, e.g. '2026-01-08T15:30:00'"),
    recurrence_rule: str = Field(..., description="RRULE string starting with 'RRULE:', e.g. 'RRULE:FREQ=WEEKLY;BYDAY=MO'"),
    calendar_id: str = Field(default="primary", description="Calendar ID to create the event in. Use 'primary' for the user's main calendar"),
    description: str = Field(default="", description="Event description or agenda"),
    location: str = Field(default="", description="Event location"),
    attendees: List[str] = Field(default=[], description="Attendee email addresses. Invitation emails are sent per send_updates"),
    timezone: str = Field(default="UTC", description="IANA timezone for the event, e.g. 'America/New_York'"),
    transparency: str = Field(default="", description="Free/busy status: 'opaque' (shows as busy, default) or 'transparent' (shows as free)"),
    reminder_minutes: int = Field(default=-1, description="Minutes before each occurrence for a popup reminder (0–40320). Set -1 to use calendar default"),
    send_updates: str = Field(default="all", description="Who receives invitation emails: 'all', 'externalOnly', or 'none'"),
    add_meet: bool = Field(default=False, description="Set True to automatically create a Google Meet video conference link for this event"),
    optional_attendees: List[str] = Field(default=[], description="Email addresses of optional attendees. These people are invited but their attendance is not required"),
    guests_can_invite_others: bool = Field(default=True, description="Whether attendees can invite additional guests. Defaults to True per Google Calendar"),
    guests_can_modify: bool = Field(default=False, description="Whether attendees can modify the event. Defaults to False"),
) -> EventResult:
    tlog = ToolLogger(logger, "create_recurring_event")
    if not recurrence_rule.startswith("RRULE:"):
        msg = "recurrence_rule must start with 'RRULE:', e.g. 'RRULE:FREQ=WEEKLY;BYDAY=MO'"
        tlog.failure("VALIDATION_ERROR", msg)
        return EventResult(
            success=False, statusCode=400, retriable=False,
            error=ToolError(code="VALIDATION_ERROR", message=msg),
        )
    try:
        service = get_service()
        body: dict = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": timezone},
            "end": {"dateTime": end_time, "timeZone": timezone},
            "recurrence": [recurrence_rule],
        }
        if description:
            body["description"] = description
        if location:
            body["location"] = location
        if transparency:
            body["transparency"] = transparency
        if reminder_minutes >= 0:
            body["reminders"] = {"useDefault": False, "overrides": [{"method": "popup", "minutes": reminder_minutes}]}
        all_attendees = [{"email": email} for email in attendees]
        all_attendees += [{"email": email, "optional": True} for email in optional_attendees]
        if all_attendees:
            body["attendees"] = all_attendees
        body["guestsCanInviteOthers"] = guests_can_invite_others
        body["guestsCanModify"] = guests_can_modify
        if add_meet:
            body["conferenceData"] = {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        created = service.events().insert(
            calendarId=calendar_id, body=body, sendUpdates=send_updates,
            conferenceDataVersion=1,
        ).execute()
        tlog.success()
        return EventResult(
            success=True, statusCode=200,
            data=EventData.model_validate(created),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="update_event",
    description=(
        "Updates an existing calendar event. Only the fields you provide are changed — leave a field empty to keep its current value. "
        "Fetches the current event first, applies changes, then saves. "
        "Use ISO 8601 for times: 'YYYY-MM-DDTHH:MM:SS'. "
        "For recurring events: pass the master recurring event ID to change all instances, or a specific instance ID to change only that occurrence. "
        "WARNING: do not update individual instances one-by-one to change the whole series — update the master event instead. "
        "Modifying instances individually creates exceptions that clutter the calendar and trigger excessive notifications. "
        "To cancel a single instance without affecting the rest of the series, set status='cancelled'."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
)
def update_event(
    event_id: str = Field(..., description="ID of the event to update. For recurring events, use the master event ID to change all instances, or an instance ID to change only one occurrence"),
    calendar_id: str = Field(default="primary", description="Calendar ID containing the event"),
    summary: str = Field(default="", description="New event title. Leave empty to keep existing"),
    start_time: str = Field(default="", description="New start time in ISO 8601 format. Leave empty to keep existing"),
    end_time: str = Field(default="", description="New end time in ISO 8601 format. Leave empty to keep existing"),
    description: str = Field(default="", description="New event description. Leave empty to keep existing"),
    location: str = Field(default="", description="New event location. Leave empty to keep existing"),
    timezone: str = Field(default="", description="Timezone for the updated start/end times, e.g. 'America/New_York'. Leave empty to keep the event's existing timezone"),
    status: str = Field(default="", description="Event status: 'confirmed', 'tentative', or 'cancelled'. Set 'cancelled' on a recurring event instance ID to cancel only that occurrence without affecting the rest of the series"),
    transparency: str = Field(default="", description="Free/busy status: 'opaque' (shows as busy) or 'transparent' (shows as free). Leave empty to keep existing"),
    reminder_minutes: int = Field(default=-1, description="Minutes before event for a popup reminder (0–40320). Set -1 to keep existing reminders"),
    send_updates: str = Field(default="all", description="Who receives update notifications: 'all', 'externalOnly', or 'none'"),
    add_meet: bool = Field(default=False, description="Set True to add a Google Meet video conference link to this event. Has no effect if a Meet link already exists"),
    guests_can_invite_others: bool | None = Field(default=None, description="Whether attendees can invite additional guests. Leave unset to keep existing value"),
    guests_can_modify: bool | None = Field(default=None, description="Whether attendees can modify the event. Leave unset to keep existing value"),
) -> EventUpdateResult:
    tlog = ToolLogger(logger, "update_event")
    try:
        service = get_service()
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        before = EventData.model_validate(event)
        if summary:
            event["summary"] = summary
        if description:
            event["description"] = description
        if location:
            event["location"] = location
        if status:
            event["status"] = status
        if transparency:
            event["transparency"] = transparency
        if reminder_minutes >= 0:
            event["reminders"] = {"useDefault": False, "overrides": [{"method": "popup", "minutes": reminder_minutes}]}
        if start_time or end_time:
            existing_tz = event.get("start", {}).get("timeZone", "UTC")
            tz_to_use = timezone if timezone else existing_tz
            if start_time:
                event["start"] = {"dateTime": start_time, "timeZone": tz_to_use}
            if end_time:
                event["end"] = {"dateTime": end_time, "timeZone": tz_to_use}
        if guests_can_invite_others is not None:
            event["guestsCanInviteOthers"] = guests_can_invite_others
        if guests_can_modify is not None:
            event["guestsCanModify"] = guests_can_modify
        if add_meet and not event.get("conferenceData"):
            event["conferenceData"] = {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        updated = service.events().update(
            calendarId=calendar_id, eventId=event_id, body=event, sendUpdates=send_updates,
            conferenceDataVersion=1,
        ).execute()
        tlog.success()
        return EventUpdateResult(
            success=True, statusCode=200,
            data=EventUpdateData(before=before, after=EventData.model_validate(updated)),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventUpdateResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventUpdateResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventUpdateResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="add_attendees",
    description="Adds new attendees to an existing event and sends them invitation emails. Skips emails that are already on the attendee list.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
)
def add_attendees(
    event_id: str = Field(..., description="ID of the event to add attendees to"),
    attendee_emails: List[str] = Field(..., description="Email addresses to add as required attendees"),
    calendar_id: str = Field(default="primary", description="Calendar ID containing the event"),
    send_updates: str = Field(default="all", description="Who receives invitation emails: 'all', 'externalOnly', or 'none'"),
    optional_attendees: List[str] = Field(default=[], description="Email addresses to add as optional attendees. These are invited but their attendance is not required"),
) -> EventUpdateResult:
    tlog = ToolLogger(logger, "add_attendees")
    try:
        service = get_service()
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        before = EventData.model_validate(event)
        existing = event.get("attendees", [])
        existing_emails = {a["email"] for a in existing}
        for email in attendee_emails:
            if email not in existing_emails:
                existing.append({"email": email})
        for email in optional_attendees:
            if email not in existing_emails:
                existing.append({"email": email, "optional": True})
        event["attendees"] = existing
        updated = service.events().update(
            calendarId=calendar_id, eventId=event_id, body=event, sendUpdates=send_updates,
            conferenceDataVersion=1,
        ).execute()
        tlog.success()
        return EventUpdateResult(
            success=True, statusCode=200,
            data=EventUpdateData(before=before, after=EventData.model_validate(updated)),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventUpdateResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventUpdateResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventUpdateResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )
