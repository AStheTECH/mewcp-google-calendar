from __future__ import annotations

import logging

from googleapiclient.errors import HttpError
from mcp.types import ToolAnnotations
from pydantic import Field

from . import mcp, _upstream_error
from ..logging_utils import ToolLogger
from ..schemas import (
    CalendarData,
    CalendarListData,
    CalendarListResult,
    CalendarResult,
    MessageData,
    MessageResult,
    ToolError,
)
from ..service import get_service

logger = logging.getLogger("calendar-mcp-server")


@mcp.tool(
    name="list_calendars",
    description="Lists all calendars the user has access to. Returns calendar IDs, names, timezones, colors, and access roles. Use min_access_role to filter to calendars the user can write to.",
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
def list_calendars(
    min_access_role: str = Field(default="", description="Minimum access role to filter by: 'freeBusyReader', 'reader', 'writer', or 'owner'. Empty returns all calendars"),
    show_hidden: bool = Field(default=False, description="Include calendars hidden from the list view"),
    max_results: int = Field(default=100, description="Maximum number of calendars to return (1–250)"),
    page_token: str = Field(default="", description="Pagination token from a previous response's next_page_token to fetch the next page"),
) -> CalendarListResult:
    tlog = ToolLogger(logger, "list_calendars")
    try:
        service = get_service()
        kwargs: dict = {"maxResults": min(max_results, 250), "showHidden": show_hidden}
        if min_access_role:
            kwargs["minAccessRole"] = min_access_role
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.calendarList().list(**kwargs).execute()
        calendars = [CalendarData.model_validate(c) for c in result.get("items", [])]
        tlog.success()
        return CalendarListResult(
            success=True, statusCode=200,
            data=CalendarListData(
                count=len(calendars),
                calendars=calendars,
                next_page_token=result.get("nextPageToken"),
            ),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return CalendarListResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return CalendarListResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return CalendarListResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="get_calendar",
    description="Gets full details of a specific calendar including its name, description, timezone, and color settings.",
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
def get_calendar(
    calendar_id: str = Field(default="primary", description="Calendar ID. Use 'primary' for the user's main calendar"),
) -> CalendarResult:
    tlog = ToolLogger(logger, "get_calendar")
    try:
        service = get_service()
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        tlog.success()
        return CalendarResult(
            success=True, statusCode=200,
            data=CalendarData.model_validate(calendar),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return CalendarResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return CalendarResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return CalendarResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="create_calendar",
    description="Creates a new calendar owned by the user. Returns the created calendar with its ID, which is needed for all subsequent operations on that calendar.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
)
def create_calendar(
    summary: str = Field(..., description="Name of the new calendar"),
    description: str = Field(default="", description="Optional description for the calendar"),
    timezone: str = Field(default="UTC", description="IANA timezone name for the calendar, e.g. 'America/New_York'"),
) -> CalendarResult:
    tlog = ToolLogger(logger, "create_calendar")
    try:
        service = get_service()
        body = {"summary": summary, "description": description, "timeZone": timezone}
        created = service.calendars().insert(body=body).execute()
        tlog.success()
        return CalendarResult(
            success=True, statusCode=200,
            data=CalendarData.model_validate(created),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return CalendarResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return CalendarResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return CalendarResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="delete_calendar",
    description=(
        "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
        "Permanently deletes an entire calendar and every event it contains. "
        "This action is irreversible: all events, recurring series, and history in the calendar are gone immediately with no way to recover them. "
        "NEVER call this tool autonomously or as part of an automated flow. "
        "You MUST stop, tell the user exactly which calendar will be deleted and that all its events will be permanently lost, "
        "and wait for their explicit written confirmation before proceeding."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
)
def delete_calendar(
    calendar_id: str = Field(..., description="ID of the calendar to delete"),
) -> MessageResult:
    tlog = ToolLogger(logger, "delete_calendar")
    try:
        service = get_service()
        service.calendars().delete(calendarId=calendar_id).execute()
        tlog.success()
        return MessageResult(
            success=True, statusCode=200,
            data=MessageData(message=f"Calendar {calendar_id} deleted successfully"),
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
    name="clear_calendar",
    description=(
        "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
        "Permanently deletes ALL events from a calendar without deleting the calendar itself. "
        "This action is irreversible: every event in the calendar — past, present, and future — is removed immediately with no way to recover them. "
        "The calendar itself remains and can be used for new events. "
        "This is the only way to clear the primary calendar, which cannot be deleted. "
        "NEVER call this tool autonomously or as part of an automated flow. "
        "You MUST stop, tell the user exactly which calendar will be cleared and that every event in it will be permanently deleted, "
        "and wait for their explicit written confirmation before proceeding."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
)
def clear_calendar(
    calendar_id: str = Field(..., description="ID of the calendar to clear. Use 'primary' for the user's main calendar. WARNING: all events in this calendar will be permanently deleted"),
) -> MessageResult:
    tlog = ToolLogger(logger, "clear_calendar")
    try:
        service = get_service()
        service.calendars().clear(calendarId=calendar_id).execute()
        tlog.success()
        return MessageResult(
            success=True, statusCode=200,
            data=MessageData(message=f"All events cleared from calendar {calendar_id}"),
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
