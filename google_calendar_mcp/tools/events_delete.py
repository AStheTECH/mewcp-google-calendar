from __future__ import annotations

import logging

from googleapiclient.errors import HttpError
from mcp.types import ToolAnnotations
from pydantic import Field

from . import mcp, _upstream_error
from ..logging_utils import ToolLogger
from ..schemas import (
    EventData,
    EventResult,
    MessageData,
    MessageResult,
    ToolError,
)
from ..service import get_service

logger = logging.getLogger("calendar-mcp-server")


@mcp.tool(
    name="delete_event",
    description=(
        "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
        "Permanently deletes a calendar event. "
        "This action is irreversible: the event, its attendees list, reminders, and all associated data are removed immediately and cannot be recovered. "
        "Attendees will receive cancellation emails (controlled by send_updates). "
        "For recurring events: deleting the master event ID removes the entire series and all its instances. "
        "Deleting a specific instance ID removes only that one occurrence. "
        "NEVER call this tool autonomously or as part of an automated flow. "
        "You MUST stop, tell the user the event title, date, and time that will be permanently deleted, "
        "and for recurring events clarify whether you are deleting one occurrence or the entire series, "
        "and wait for their explicit written confirmation before proceeding."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
)
def delete_event(
    event_id: str = Field(..., description="ID of the event to delete"),
    calendar_id: str = Field(default="primary", description="Calendar ID containing the event"),
    send_updates: str = Field(default="all", description="Who receives cancellation emails: 'all' (recommended), 'externalOnly', or 'none'"),
) -> MessageResult:
    tlog = ToolLogger(logger, "delete_event")
    try:
        service = get_service()
        service.events().delete(
            calendarId=calendar_id, eventId=event_id, sendUpdates=send_updates,
        ).execute()
        tlog.success()
        return MessageResult(
            success=True, statusCode=200,
            data=MessageData(message=f"Event {event_id} deleted successfully"),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return MessageResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return MessageResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return MessageResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="move_event",
    description=(
        "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
        "Moves a default event from one calendar to another. "
        "Only events of type 'default' can be moved — birthday, focusTime, fromGmail, outOfOffice, and workingLocation events cannot be moved and will return an error. "
        "The event is removed from the source calendar and placed in the destination calendar — "
        "any calendar-specific settings, sharing permissions, or notification rules from the source will no longer apply. "
        "While technically reversible by moving back, this can disrupt other attendees and shared calendar visibility in ways that are hard to track down. "
        "NEVER call this tool autonomously. "
        "You MUST tell the user which event is being moved, from which calendar to which, and wait for their explicit confirmation."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
)
def move_event(
    event_id: str = Field(..., description="ID of the event to move"),
    source_calendar_id: str = Field(..., description="ID of the calendar currently containing the event"),
    destination_calendar_id: str = Field(..., description="ID of the destination calendar"),
) -> EventResult:
    tlog = ToolLogger(logger, "move_event")
    try:
        service = get_service()
        moved = service.events().move(
            calendarId=source_calendar_id,
            eventId=event_id,
            destination=destination_calendar_id,
        ).execute()
        tlog.success()
        return EventResult(
            success=True, statusCode=200,
            data=EventData.model_validate(moved),
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
