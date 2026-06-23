from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastmcp import FastMCP
from googleapiclient.errors import HttpError
from pydantic import Field

from .logging_utils import FULL_SCOPE, READONLY_SCOPE, ToolLogger, check_scope
from .schemas import (
    CalendarData,
    CalendarListData,
    CalendarListResult,
    CalendarResult,
    EventData,
    EventListData,
    EventListResult,
    EventResult,
    FreeBusyData,
    FreeBusyCalendar,
    FreeBusyResult,
    MessageData,
    MessageResult,
    ToolError,
)
from .service import get_service

logger = logging.getLogger("calendar-mcp-server")

TOOL_REGISTRY: dict[str, dict] = {
    "list_calendars":         {"scope": READONLY_SCOPE, "destructive": False},
    "get_calendar":           {"scope": READONLY_SCOPE, "destructive": False},
    "create_calendar":        {"scope": FULL_SCOPE,     "destructive": False},
    "delete_calendar":        {"scope": FULL_SCOPE,     "destructive": True},
    "list_events":            {"scope": READONLY_SCOPE, "destructive": False},
    "get_event":              {"scope": READONLY_SCOPE, "destructive": False},
    "create_event":           {"scope": FULL_SCOPE,     "destructive": False},
    "create_quick_event":     {"scope": FULL_SCOPE,     "destructive": False},
    "update_event":           {"scope": FULL_SCOPE,     "destructive": False},
    "delete_event":           {"scope": FULL_SCOPE,     "destructive": True},
    "search_events":          {"scope": READONLY_SCOPE, "destructive": False},
    "get_upcoming_events":    {"scope": READONLY_SCOPE, "destructive": False},
    "get_todays_events":      {"scope": READONLY_SCOPE, "destructive": False},
    "add_attendees":          {"scope": FULL_SCOPE,     "destructive": False},
    "get_free_busy":          {"scope": READONLY_SCOPE, "destructive": False},
    "move_event":             {"scope": FULL_SCOPE,     "destructive": True},
    "create_recurring_event": {"scope": FULL_SCOPE,     "destructive": False},
    "list_event_instances":   {"scope": READONLY_SCOPE, "destructive": False},
    "clear_calendar":         {"scope": FULL_SCOPE,     "destructive": True},
}


def _upstream_error(e: HttpError) -> tuple[int, bool, int | None]:
    """Extract statusCode, retriable, retry_after_seconds from an HttpError."""
    status = int(e.resp.status)
    retriable = status in (429, 500, 502, 503)
    retry_after: int | None = None
    if status == 429:
        raw = e.resp.get("retry-after") or e.resp.get("Retry-After")
        retry_after = int(raw) if raw else None
        if retry_after is None:
            retriable = False
    return status, retriable, retry_after


class _ToolCollector:
    def __init__(self):
        self.items = []

    def tool(self, *args, **kwargs):
        def decorator(func):
            self.items.append((args, kwargs, func))
            return func
        return decorator


mcp = _ToolCollector()


def register_tools(real_mcp: FastMCP) -> None:
    for args, kwargs, func in mcp.items:
        real_mcp.tool(*args, **kwargs)(func)


# ---------------------------------------------------------------------------
# Calendar management
# ---------------------------------------------------------------------------

@mcp.tool(
    name="list_calendars",
    description="Lists all calendars the user has access to. Returns calendar IDs, names, timezones, colors, and access roles. Use min_access_role to filter to calendars the user can write to.",
)
def list_calendars(
    min_access_role: str = Field(default="", description="Minimum access role to filter by: 'freeBusyReader', 'reader', 'writer', or 'owner'. Empty returns all calendars"),
    show_hidden: bool = Field(default=False, description="Include calendars hidden from the list view"),
    max_results: int = Field(default=100, description="Maximum number of calendars to return (1–250)"),
    page_token: str = Field(default="", description="Pagination token from a previous response's next_page_token to fetch the next page"),
) -> CalendarListResult:
    tlog = ToolLogger(logger, "list_calendars")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return CalendarListResult(**err.model_dump())
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
)
def get_calendar(
    calendar_id: str = Field(default="primary", description="Calendar ID. Use 'primary' for the user's main calendar"),
) -> CalendarResult:
    tlog = ToolLogger(logger, "get_calendar")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return CalendarResult(**err.model_dump())
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
)
def create_calendar(
    summary: str = Field(..., description="Name of the new calendar"),
    description: str = Field(default="", description="Optional description for the calendar"),
    timezone: str = Field(default="UTC", description="IANA timezone name for the calendar, e.g. 'America/New_York'"),
) -> CalendarResult:
    tlog = ToolLogger(logger, "create_calendar")
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return CalendarResult(**err.model_dump())
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
)
def delete_calendar(
    calendar_id: str = Field(..., description="ID of the calendar to delete"),
) -> MessageResult:
    tlog = ToolLogger(logger, "delete_calendar")
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return MessageResult(**err.model_dump())
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


# ---------------------------------------------------------------------------
# Event queries
# ---------------------------------------------------------------------------

@mcp.tool(
    name="list_events",
    description=(
        "Lists events from a calendar within an optional time range. "
        "Returns events in start-time order. Recurring events are expanded into individual instances. "
        "Use ISO 8601 for time_min/time_max: 'YYYY-MM-DDTHH:MM:SSZ' (e.g. '2026-01-08T00:00:00Z'). "
        "Defaults to events from now onwards if time_min is not specified."
    ),
)
def list_events(
    calendar_id: str = Field(default="primary", description="Calendar ID. Use 'primary' for the user's main calendar"),
    max_results: int = Field(default=10, description="Maximum number of events to return (1–2500)"),
    time_min: str = Field(default="", description="Start of time range in ISO 8601 format, e.g. '2026-01-08T00:00:00Z'. Defaults to now"),
    time_max: str = Field(default="", description="End of time range in ISO 8601 format, e.g. '2026-01-15T23:59:59Z'. Omit for open-ended"),
    query: str = Field(default="", description="Free-text search query to filter events by title, description, or location"),
    show_deleted: bool = Field(default=False, description="Include cancelled events in results"),
    page_token: str = Field(default="", description="Pagination token from a previous response's next_page_token to fetch the next page"),
) -> EventListResult:
    tlog = ToolLogger(logger, "list_events")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventListResult(**err.model_dump())
    if time_min and time_max and time_min >= time_max:
        msg = "time_min must be before time_max"
        tlog.failure("VALIDATION_ERROR", msg)
        return EventListResult(
            success=False, statusCode=400, retriable=False,
            error=ToolError(code="VALIDATION_ERROR", message=msg),
        )
    try:
        service = get_service()
        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()
        kwargs: dict = {
            "calendarId": calendar_id,
            "maxResults": min(max_results, 2500),
            "singleEvents": True,
            "orderBy": "startTime",
            "timeMin": time_min,
            "showDeleted": show_deleted,
        }
        if time_max:
            kwargs["timeMax"] = time_max
        if query:
            kwargs["q"] = query
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.events().list(**kwargs).execute()
        events = [EventData.model_validate(e) for e in result.get("items", [])]
        tlog.success()
        return EventListResult(
            success=True, statusCode=200,
            data=EventListData(count=len(events), events=events, next_page_token=result.get("nextPageToken")),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventListResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="get_event",
    description="Gets full details of a specific event including attendees, RSVP statuses, recurrence rules, reminders, and conferencing info.",
)
def get_event(
    event_id: str = Field(..., description="ID of the event to retrieve"),
    calendar_id: str = Field(default="primary", description="Calendar ID containing the event. Use 'primary' for the user's main calendar"),
) -> EventResult:
    tlog = ToolLogger(logger, "get_event")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventResult(**err.model_dump())
    try:
        service = get_service()
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
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
    name="search_events",
    description=(
        "Searches for events by text across titles, descriptions, and locations. "
        "Optionally bound the search to a time range with time_min/time_max (ISO 8601, e.g. '2026-01-08T00:00:00Z'). "
        "Without a time range the search spans all history — always use a time range for large calendars."
    ),
)
def search_events(
    query: str = Field(..., description="Text to search for in event titles, descriptions, and locations"),
    calendar_id: str = Field(default="primary", description="Calendar ID to search in. Use 'primary' for the user's main calendar"),
    max_results: int = Field(default=10, description="Maximum number of events to return (1–2500)"),
    time_min: str = Field(default="", description="Optional start of time range in ISO 8601 format, e.g. '2026-01-01T00:00:00Z'"),
    time_max: str = Field(default="", description="Optional end of time range in ISO 8601 format, e.g. '2026-12-31T23:59:59Z'"),
    page_token: str = Field(default="", description="Pagination token from a previous response's next_page_token to fetch the next page"),
) -> EventListResult:
    tlog = ToolLogger(logger, "search_events")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventListResult(**err.model_dump())
    if time_min and time_max and time_min >= time_max:
        msg = "time_min must be before time_max"
        tlog.failure("VALIDATION_ERROR", msg)
        return EventListResult(
            success=False, statusCode=400, retriable=False,
            error=ToolError(code="VALIDATION_ERROR", message=msg),
        )
    try:
        service = get_service()
        kwargs: dict = {
            "calendarId": calendar_id,
            "q": query,
            "maxResults": min(max_results, 2500),
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_min:
            kwargs["timeMin"] = time_min
        if time_max:
            kwargs["timeMax"] = time_max
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.events().list(**kwargs).execute()
        events = [EventData.model_validate(e) for e in result.get("items", [])]
        tlog.success()
        return EventListResult(
            success=True, statusCode=200,
            data=EventListData(count=len(events), events=events, next_page_token=result.get("nextPageToken")),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventListResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="get_upcoming_events",
    description="Gets events starting from now through the next N days. Returns events in start-time order. Recurring events are expanded into individual instances.",
)
def get_upcoming_events(
    days: int = Field(default=7, description="Number of days to look ahead from now"),
    calendar_id: str = Field(default="primary", description="Calendar ID to query. Use 'primary' for the user's main calendar"),
    max_results: int = Field(default=10, description="Maximum number of events to return (1–2500)"),
) -> EventListResult:
    tlog = ToolLogger(logger, "get_upcoming_events")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventListResult(**err.model_dump())
    if days < 1:
        msg = "days must be at least 1"
        tlog.failure("VALIDATION_ERROR", msg)
        return EventListResult(
            success=False, statusCode=400, retriable=False,
            error=ToolError(code="VALIDATION_ERROR", message=msg),
        )
    try:
        service = get_service()
        now = datetime.now(timezone.utc)
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=now.isoformat(),
            timeMax=(now + timedelta(days=days)).isoformat() + "Z",
            maxResults=min(max_results, 2500),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = [EventData.model_validate(e) for e in result.get("items", [])]
        tlog.success()
        return EventListResult(
            success=True, statusCode=200,
            data=EventListData(count=len(events), events=events),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventListResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="get_todays_events",
    description="Gets all events scheduled for today in the given timezone. Pass the user's local timezone to get the correct day (e.g. 'America/New_York'). Defaults to UTC.",
)
def get_todays_events(
    calendar_id: str = Field(default="primary", description="Calendar ID to query. Use 'primary' for the user's main calendar"),
    timezone: str = Field(default="UTC", description="IANA timezone name to determine 'today', e.g. 'America/New_York'. Defaults to UTC"),
) -> EventListResult:
    tlog = ToolLogger(logger, "get_todays_events")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventListResult(**err.model_dump())
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        msg = f"Unknown timezone '{timezone}'. Use an IANA timezone name, e.g. 'America/New_York'"
        tlog.failure("VALIDATION_ERROR", msg)
        return EventListResult(
            success=False, statusCode=400, retriable=False,
            error=ToolError(code="VALIDATION_ERROR", message=msg),
        )
    try:
        service = get_service()
        now_local = datetime.now(tz)
        start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now_local.replace(hour=23, minute=59, second=59, microsecond=999999)
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = [EventData.model_validate(e) for e in result.get("items", [])]
        tlog.success()
        return EventListResult(
            success=True, statusCode=200,
            data=EventListData(count=len(events), events=events),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventListResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


@mcp.tool(
    name="get_free_busy",
    description="Returns busy time blocks for one or more calendars within a time range. Useful for finding open slots before scheduling. Use ISO 8601 with Z suffix: 'YYYY-MM-DDTHH:MM:SSZ'.",
)
def get_free_busy(
    time_min: str = Field(..., description="Start of the time range in ISO 8601 format with Z suffix, e.g. '2026-01-08T09:00:00Z'"),
    time_max: str = Field(..., description="End of the time range in ISO 8601 format with Z suffix, e.g. '2026-01-08T17:00:00Z'"),
    calendar_ids: List[str] = Field(default=[], description="Calendar IDs to query. Defaults to ['primary'] if empty"),
) -> FreeBusyResult:
    tlog = ToolLogger(logger, "get_free_busy")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return FreeBusyResult(**err.model_dump())
    if time_min >= time_max:
        msg = "time_min must be before time_max"
        tlog.failure("VALIDATION_ERROR", msg)
        return FreeBusyResult(
            success=False, statusCode=400, retriable=False,
            error=ToolError(code="VALIDATION_ERROR", message=msg),
        )
    try:
        service = get_service()
        ids = calendar_ids if calendar_ids else ["primary"]
        result = service.freebusy().query(body={
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": cid} for cid in ids],
        }).execute()
        calendars = {
            cid: FreeBusyCalendar.model_validate(data)
            for cid, data in result.get("calendars", {}).items()
        }
        tlog.success()
        return FreeBusyResult(
            success=True, statusCode=200,
            data=FreeBusyData(
                timeMin=result.get("timeMin", time_min),
                timeMax=result.get("timeMax", time_max),
                calendars=calendars,
            ),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return FreeBusyResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return FreeBusyResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return FreeBusyResult(
            success=False, statusCode=500, retriable=False,
            error=ToolError(code="SERVER_ERROR", message=str(e)),
        )


# ---------------------------------------------------------------------------
# Event mutations
# ---------------------------------------------------------------------------

@mcp.tool(
    name="create_event",
    description=(
        "Creates a new calendar event and optionally invites attendees. "
        "For timed events use ISO 8601 datetime: '2026-01-08T14:30:00' with a timezone. "
        "For all-day events set is_all_day=True and use date-only format: '2026-01-08' — "
        "for all-day events end_time is exclusive, so a single-day event on Jan 8 needs end_time='2026-01-09'. "
        "Returns the created event with its ID."
    ),
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
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventResult(**err.model_dump())
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
)
def create_quick_event(
    text: str = Field(..., description="Natural language event description, e.g. 'Dentist appointment next Friday at 3pm'"),
    calendar_id: str = Field(default="primary", description="Calendar ID to create the event in. Use 'primary' for the user's main calendar"),
    send_updates: str = Field(default="all", description="Who receives invitation emails: 'all', 'externalOnly', or 'none'"),
) -> EventResult:
    tlog = ToolLogger(logger, "create_quick_event")
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventResult(**err.model_dump())
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
) -> EventResult:
    tlog = ToolLogger(logger, "update_event")
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventResult(**err.model_dump())
    try:
        service = get_service()
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
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
            # Use the event's existing timezone if caller didn't specify one
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
        return EventResult(
            success=True, statusCode=200,
            data=EventData.model_validate(updated),
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
)
def delete_event(
    event_id: str = Field(..., description="ID of the event to delete"),
    calendar_id: str = Field(default="primary", description="Calendar ID containing the event"),
    send_updates: str = Field(default="all", description="Who receives cancellation emails: 'all' (recommended), 'externalOnly', or 'none'"),
) -> MessageResult:
    tlog = ToolLogger(logger, "delete_event")
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return MessageResult(**err.model_dump())
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
    name="add_attendees",
    description="Adds new attendees to an existing event and sends them invitation emails. Skips emails that are already on the attendee list.",
)
def add_attendees(
    event_id: str = Field(..., description="ID of the event to add attendees to"),
    attendee_emails: List[str] = Field(..., description="Email addresses to add as required attendees"),
    calendar_id: str = Field(default="primary", description="Calendar ID containing the event"),
    send_updates: str = Field(default="all", description="Who receives invitation emails: 'all', 'externalOnly', or 'none'"),
    optional_attendees: List[str] = Field(default=[], description="Email addresses to add as optional attendees. These are invited but their attendance is not required"),
) -> EventResult:
    tlog = ToolLogger(logger, "add_attendees")
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventResult(**err.model_dump())
    try:
        service = get_service()
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
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
        return EventResult(
            success=True, statusCode=200,
            data=EventData.model_validate(updated),
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
)
def move_event(
    event_id: str = Field(..., description="ID of the event to move"),
    source_calendar_id: str = Field(..., description="ID of the calendar currently containing the event"),
    destination_calendar_id: str = Field(..., description="ID of the destination calendar"),
) -> EventResult:
    tlog = ToolLogger(logger, "move_event")
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventResult(**err.model_dump())
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


@mcp.tool(
    name="list_event_instances",
    description=(
        "Lists all individual instances of a recurring event by its master event ID. "
        "Use this to see every occurrence of a recurring series — use get_event or list_events to find the master event ID first. "
        "Instances include recurringEventId (the master ID) and originalStartTime (the scheduled time per RRULE, "
        "which differs from start if the instance was rescheduled). "
        "Optionally filter by time range to see only upcoming or past occurrences."
    ),
)
def list_event_instances(
    recurring_event_id: str = Field(..., description="ID of the master recurring event whose instances to list"),
    calendar_id: str = Field(default="primary", description="Calendar ID containing the recurring event. Use 'primary' for the user's main calendar"),
    max_results: int = Field(default=10, description="Maximum number of instances to return (1–2500)"),
    time_min: str = Field(default="", description="Optional start of time range in ISO 8601 format, e.g. '2026-01-01T00:00:00Z'. Filters to instances starting at or after this time"),
    time_max: str = Field(default="", description="Optional end of time range in ISO 8601 format. Filters to instances starting before this time"),
    show_deleted: bool = Field(default=False, description="Include cancelled instances in results"),
    page_token: str = Field(default="", description="Pagination token from a previous response's next_page_token to fetch the next page"),
) -> EventListResult:
    tlog = ToolLogger(logger, "list_event_instances")
    if err := check_scope(READONLY_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventListResult(**err.model_dump())
    if time_min and time_max and time_min >= time_max:
        msg = "time_min must be before time_max"
        tlog.failure("VALIDATION_ERROR", msg)
        return EventListResult(
            success=False, statusCode=400, retriable=False,
            error=ToolError(code="VALIDATION_ERROR", message=msg),
        )
    try:
        service = get_service()
        kwargs: dict = {
            "calendarId": calendar_id,
            "eventId": recurring_event_id,
            "maxResults": min(max_results, 2500),
            "showDeleted": show_deleted,
        }
        if time_min:
            kwargs["timeMin"] = time_min
        if time_max:
            kwargs["timeMax"] = time_max
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.events().instances(**kwargs).execute()
        events = [EventData.model_validate(e) for e in result.get("items", [])]
        tlog.success()
        return EventListResult(
            success=True, statusCode=200,
            data=EventListData(count=len(events), events=events, next_page_token=result.get("nextPageToken")),
        )
    except HttpError as e:
        status, retriable, retry_after = _upstream_error(e)
        tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
        return EventListResult(
            success=False, statusCode=status, retriable=retriable,
            retry_after_seconds=retry_after,
            error=ToolError(code="UPSTREAM_ERROR", message=str(e)),
        )
    except ValueError as e:
        tlog.failure("AUTH_ERROR", str(e))
        return EventListResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(e)),
        )
    except Exception as e:
        tlog.failure("SERVER_ERROR", str(e))
        return EventListResult(
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
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return EventResult(**err.model_dump())
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
)
def clear_calendar(
    calendar_id: str = Field(..., description="ID of the calendar to clear. Use 'primary' for the user's main calendar. WARNING: all events in this calendar will be permanently deleted"),
) -> MessageResult:
    tlog = ToolLogger(logger, "clear_calendar")
    if err := check_scope(FULL_SCOPE):
        tlog.failure("AUTH_ERROR", err.error.message)
        return MessageResult(**err.model_dump())
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
