from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from googleapiclient.errors import HttpError
from mcp.types import ToolAnnotations
from pydantic import Field

from . import mcp, _upstream_error
from ..logging_utils import ToolLogger
from ..schemas import (
    EventData,
    EventListData,
    EventListResult,
    EventResult,
    ToolError,
)
from ..service import get_service

logger = logging.getLogger("calendar-mcp-server")


@mcp.tool(
    name="list_events",
    description=(
        "Lists events from a calendar within an optional time range. "
        "Returns events in start-time order. Recurring events are expanded into individual instances. "
        "Use ISO 8601 for time_min/time_max: 'YYYY-MM-DDTHH:MM:SSZ' (e.g. '2026-01-08T00:00:00Z'). "
        "Defaults to events from now onwards if time_min is not specified."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
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
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
def get_event(
    event_id: str = Field(..., description="ID of the event to retrieve"),
    calendar_id: str = Field(default="primary", description="Calendar ID containing the event. Use 'primary' for the user's main calendar"),
) -> EventResult:
    tlog = ToolLogger(logger, "get_event")
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
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
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
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
def get_upcoming_events(
    days: int = Field(default=7, description="Number of days to look ahead from now"),
    calendar_id: str = Field(default="primary", description="Calendar ID to query. Use 'primary' for the user's main calendar"),
    max_results: int = Field(default=10, description="Maximum number of events to return (1–2500)"),
) -> EventListResult:
    tlog = ToolLogger(logger, "get_upcoming_events")
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
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
def get_todays_events(
    calendar_id: str = Field(default="primary", description="Calendar ID to query. Use 'primary' for the user's main calendar"),
    timezone: str = Field(default="UTC", description="IANA timezone name to determine 'today', e.g. 'America/New_York'. Defaults to UTC"),
) -> EventListResult:
    tlog = ToolLogger(logger, "get_todays_events")
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
    name="list_event_instances",
    description=(
        "Lists all individual instances of a recurring event by its master event ID. "
        "Use this to see every occurrence of a recurring series — use get_event or list_events to find the master event ID first. "
        "Instances include recurringEventId (the master ID) and originalStartTime (the scheduled time per RRULE, "
        "which differs from start if the instance was rescheduled). "
        "Optionally filter by time range to see only upcoming or past occurrences."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
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
