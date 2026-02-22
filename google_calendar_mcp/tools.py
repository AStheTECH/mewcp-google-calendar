import logging
from datetime import datetime, timedelta
from typing import List

from fastmcp import FastMCP

from .schemas import ApiObjectResponse, OAuthTokenData
from .service import get_service

logger = logging.getLogger("calendar-mcp-server")

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


@mcp.tool(
    name="list_calendars", description="List all calendars accessible by the user"
)
def list_calendars(
    oauth_token: OAuthTokenData,
) -> ApiObjectResponse:
    """List all calendars"""
    logger.info("Executing list_calendars")
    try:
        service = get_service(oauth_token)

        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get("items", [])

        logger.info(f"Found {len(calendars)} calendars")
        return {"count": len(calendars), "calendars": calendars}
    except Exception as e:
        logger.error(f"Error in list_calendars: {e}")
        return {"error": str(e)}


@mcp.tool(name="get_calendar", description="Get details of a specific calendar")
def get_calendar(oauth_token: OAuthTokenData, calendar_id: str = "primary") -> ApiObjectResponse:
    """Get calendar details"""
    logger.info(f"Executing get_calendar for: {calendar_id}")
    try:
        service = get_service(oauth_token)

        calendar = service.calendars().get(calendarId=calendar_id).execute()

        logger.info("Retrieved calendar details")
        return calendar
    except Exception as e:
        logger.error(f"Error in get_calendar: {e}")
        return {"error": str(e)}


@mcp.tool(name="create_calendar", description="Create a new calendar")
def create_calendar(
    oauth_token: OAuthTokenData, summary: str, description: str = "", timezone: str = "UTC"
) -> ApiObjectResponse:
    """Create a new calendar"""
    logger.info(f"Executing create_calendar: {summary}")
    try:
        service = get_service(oauth_token)

        calendar = {
            "summary": summary,
            "description": description,
            "timeZone": timezone,
        }

        created_calendar = service.calendars().insert(body=calendar).execute()

        logger.info(f"Calendar created: {created_calendar.get('id')}")
        return {
            "message": "Calendar created successfully",
            "calendar": created_calendar,
        }
    except Exception as e:
        logger.error(f"Error in create_calendar: {e}")
        return {"error": str(e)}


@mcp.tool(name="delete_calendar", description="Delete a calendar")
def delete_calendar(oauth_token: OAuthTokenData, calendar_id: str) -> ApiObjectResponse:
    """Delete a calendar"""
    logger.info(f"Executing delete_calendar for: {calendar_id}")
    try:
        service = get_service(oauth_token)

        service.calendars().delete(calendarId=calendar_id).execute()

        logger.info("Calendar deleted successfully")
        return {"message": f"Calendar {calendar_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error in delete_calendar: {e}")
        return {"error": str(e)}


@mcp.tool(
    name="list_events",
    description="List events from a calendar within a time range. Use ISO 8601 format for time_min/time_max: 'YYYY-MM-DDTHH:MM:SSZ' (e.g., '2026-01-08T00:00:00Z'). Defaults to events starting from now if time_min not specified.",
)
def list_events(
    oauth_token: OAuthTokenData,
    calendar_id: str = "primary",
    max_results: int = 10,
    time_min: str = "",
    time_max: str = "",
    query: str = "",
) -> ApiObjectResponse:
    """List calendar events"""
    logger.info(f"Executing list_events for calendar: {calendar_id}")
    try:
        service = get_service(oauth_token)

        # Default to now if no time_min specified
        if not time_min:
            time_min = datetime.utcnow().isoformat() + "Z"

        kwargs = {
            "calendarId": calendar_id,
            "maxResults": min(max_results, 2500),
            "singleEvents": True,
            "orderBy": "startTime",
            "timeMin": time_min,
        }

        if time_max:
            kwargs["timeMax"] = time_max

        if query:
            kwargs["q"] = query

        events_result = service.events().list(**kwargs).execute()
        events = events_result.get("items", [])

        logger.info(f"Found {len(events)} events")
        return {"count": len(events), "events": events}
    except Exception as e:
        logger.error(f"Error in list_events: {e}")
        return {"error": str(e)}


@mcp.tool(name="get_event", description="Get details of a specific event")
def get_event(oauth_token: OAuthTokenData, event_id: str, calendar_id: str = "primary") -> ApiObjectResponse:
    """Get event details"""
    logger.info(f"Executing get_event for: {event_id}")
    try:
        service = get_service(oauth_token)

        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        logger.info("Retrieved event details")
        return event
    except Exception as e:
        logger.error(f"Error in get_event: {e}")
        return {"error": str(e)}


@mcp.tool(
    name="create_event",
    description="Create a new calendar event. Use ISO 8601 format for start_time and end_time: 'YYYY-MM-DDTHH:MM:SS' (e.g., '2026-01-08T14:30:00' for Jan 8, 2026 at 2:30 PM). You can also include timezone offset like '2026-01-08T14:30:00-05:00' for EST.",
)
def create_event(
    oauth_token: OAuthTokenData,
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    description: str = "",
    location: str = "",
    attendees: List[str] = [],
    timezone: str = "UTC",
) -> ApiObjectResponse:
    """Create a calendar event"""
    logger.info(f"Executing create_event: {summary}")
    try:
        service = get_service(oauth_token)

        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_time,
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_time,
                "timeZone": timezone,
            },
        }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        created_event = (
            service.events().insert(calendarId=calendar_id, body=event).execute()
        )

        logger.info(f"Event created: {created_event.get('id')}")
        return {"message": "Event created successfully", "event": created_event}
    except Exception as e:
        logger.error(f"Error in create_event: {e}")
        return {"error": str(e)}


@mcp.tool(
    name="create_quick_event",
    description="Create an event using natural language text (e.g., 'Lunch with John tomorrow at 12pm')",
)
def create_quick_event(
    oauth_token: OAuthTokenData, text: str, calendar_id: str = "primary"
) -> ApiObjectResponse:
    """Create event using quick add"""
    logger.info(f"Executing create_quick_event: {text}")
    try:
        service = get_service(oauth_token)

        event = service.events().quickAdd(calendarId=calendar_id, text=text).execute()

        logger.info(f"Quick event created: {event.get('id')}")
        return {"message": "Event created successfully", "event": event}
    except Exception as e:
        logger.error(f"Error in create_quick_event: {e}")
        return {"error": str(e)}


@mcp.tool(
    name="update_event",
    description="Update an existing calendar event. Use ISO 8601 format for start_time and end_time: 'YYYY-MM-DDTHH:MM:SS' (e.g., '2026-01-08T14:30:00'). Leave fields empty to keep existing values.",
)
def update_event(
    oauth_token: OAuthTokenData,
    event_id: str,
    calendar_id: str = "primary",
    summary: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = "",
    timezone: str = "UTC",
) -> ApiObjectResponse:
    """Update a calendar event"""
    logger.info(f"Executing update_event for: {event_id}")
    try:
        service = get_service(oauth_token)

        # Get existing event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Update fields if provided
        if summary:
            event["summary"] = summary
        if description:
            event["description"] = description
        if location:
            event["location"] = location
        if start_time:
            event["start"] = {
                "dateTime": start_time,
                "timeZone": timezone,
            }
        if end_time:
            event["end"] = {
                "dateTime": end_time,
                "timeZone": timezone,
            }

        updated_event = (
            service.events()
            .update(calendarId=calendar_id, eventId=event_id, body=event)
            .execute()
        )

        logger.info("Event updated successfully")
        return {"message": "Event updated successfully", "event": updated_event}
    except Exception as e:
        logger.error(f"Error in update_event: {e}")
        return {"error": str(e)}


@mcp.tool(name="delete_event", description="Delete a calendar event")
def delete_event(oauth_token: OAuthTokenData, event_id: str, calendar_id: str = "primary") -> ApiObjectResponse:
    """Delete a calendar event"""
    logger.info(f"Executing delete_event for: {event_id}")
    try:
        service = get_service(oauth_token)

        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

        logger.info("Event deleted successfully")
        return {"message": f"Event {event_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error in delete_event: {e}")
        return {"error": str(e)}


@mcp.tool(
    name="search_events", description="Search for events containing specific text"
)
def search_events(
    oauth_token: OAuthTokenData, query: str, calendar_id: str = "primary", max_results: int = 10
) -> ApiObjectResponse:
    """Search calendar events"""
    logger.info(f"Executing search_events with query: {query}")
    try:
        service = get_service(oauth_token)

        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                q=query,
                maxResults=min(max_results, 2500),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        logger.info(f"Search found {len(events)} events")
        return {"count": len(events), "events": events}
    except Exception as e:
        logger.error(f"Error in search_events: {e}")
        return {"error": str(e)}


@mcp.tool(
    name="get_upcoming_events", description="Get upcoming events for the next N days"
)
def get_upcoming_events(
    oauth_token: OAuthTokenData, days: int = 7, calendar_id: str = "primary", max_results: int = 10
) -> ApiObjectResponse:
    """Get upcoming events"""
    logger.info(f"Executing get_upcoming_events for next {days} days")
    try:
        service = get_service(oauth_token)

        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days)).isoformat() + "Z"

        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=min(max_results, 2500),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        logger.info(f"Found {len(events)} upcoming events")
        return {"count": len(events), "events": events}
    except Exception as e:
        logger.error(f"Error in get_upcoming_events: {e}")
        return {"error": str(e)}


@mcp.tool(name="get_todays_events", description="Get all events for today")
def get_todays_events(oauth_token: OAuthTokenData, calendar_id: str = "primary") -> ApiObjectResponse:
    """Get today's events"""
    logger.info("Executing get_todays_events")
    try:
        service = get_service(oauth_token)

        now = datetime.utcnow()
        time_min = (
            now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
        )
        time_max = (
            now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
            + "Z"
        )

        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        logger.info(f"Found {len(events)} events today")
        return {"count": len(events), "events": events}
    except Exception as e:
        logger.error(f"Error in get_todays_events: {e}")
        return {"error": str(e)}


@mcp.tool(name="add_attendees", description="Add attendees to an existing event")
def add_attendees(
    oauth_token: OAuthTokenData,
    event_id: str,
    attendee_emails: List[str],
    calendar_id: str = "primary",
) -> ApiObjectResponse:
    """Add attendees to an event"""
    logger.info(f"Executing add_attendees for event: {event_id}")
    try:
        service = get_service(oauth_token)

        # Get existing event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Get existing attendees or initialize empty list
        existing_attendees = event.get("attendees", [])
        existing_emails = {a["email"] for a in existing_attendees}

        # Add new attendees
        for email in attendee_emails:
            if email not in existing_emails:
                existing_attendees.append({"email": email})

        event["attendees"] = existing_attendees

        updated_event = (
            service.events()
            .update(
                calendarId=calendar_id, eventId=event_id, body=event, sendUpdates="all"
            )
            .execute()
        )

        logger.info("Attendees added successfully")
        return {"message": "Attendees added successfully", "event": updated_event}
    except Exception as e:
        logger.error(f"Error in add_attendees: {e}")
        return {"error": str(e)}


@mcp.tool(
    name="get_free_busy",
    description="Get free/busy information for calendars. Use ISO 8601 format with 'Z' suffix: 'YYYY-MM-DDTHH:MM:SSZ' (e.g., '2026-01-08T09:00:00Z' for 9 AM UTC).",
)
def get_free_busy(
    oauth_token: OAuthTokenData, time_min: str, time_max: str, calendar_ids: List[str] = []
) -> ApiObjectResponse:
    """Get free/busy information"""
    logger.info("Executing get_free_busy")
    try:
        service = get_service(oauth_token)

        if not calendar_ids:
            calendar_ids = ["primary"]

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": cal_id} for cal_id in calendar_ids],
        }

        freebusy_result = service.freebusy().query(body=body).execute()

        logger.info("Retrieved free/busy information")
        return freebusy_result
    except Exception as e:
        logger.error(f"Error in get_free_busy: {e}")
        return {"error": str(e)}


@mcp.tool(name="move_event", description="Move an event to a different calendar")
def move_event(
    oauth_token: OAuthTokenData,
    event_id: str,
    source_calendar_id: str,
    destination_calendar_id: str,
) -> ApiObjectResponse:
    """Move event to another calendar"""
    logger.info(f"Executing move_event: {event_id}")
    try:
        service = get_service(oauth_token)

        moved_event = (
            service.events()
            .move(
                calendarId=source_calendar_id,
                eventId=event_id,
                destination=destination_calendar_id,
            )
            .execute()
        )

        logger.info("Event moved successfully")
        return {"message": "Event moved successfully", "event": moved_event}
    except Exception as e:
        logger.error(f"Error in move_event: {e}")
        return {"error": str(e)}


@mcp.tool(
    name="create_recurring_event",
    description="Create a recurring calendar event. Use ISO 8601 format for times: 'YYYY-MM-DDTHH:MM:SS'. Recurrence examples: 'RRULE:FREQ=DAILY' (daily), 'RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR' (Mon/Wed/Fri), 'RRULE:FREQ=MONTHLY;BYMONTHDAY=15' (15th of each month).",
)
def create_recurring_event(
    oauth_token: OAuthTokenData,
    summary: str,
    start_time: str,
    end_time: str,
    recurrence_rule: str,
    calendar_id: str = "primary",
    description: str = "",
    location: str = "",
    timezone: str = "UTC",
) -> ApiObjectResponse:
    """Create a recurring event"""
    logger.info(f"Executing create_recurring_event: {summary}")
    try:
        service = get_service(oauth_token)

        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_time,
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_time,
                "timeZone": timezone,
            },
            "recurrence": [recurrence_rule],
        }

        created_event = (
            service.events().insert(calendarId=calendar_id, body=event).execute()
        )

        logger.info(f"Recurring event created: {created_event.get('id')}")
        return {
            "message": "Recurring event created successfully",
            "event": created_event,
        }
    except Exception as e:
        logger.error(f"Error in create_recurring_event: {e}")
        return {"error": str(e)}
