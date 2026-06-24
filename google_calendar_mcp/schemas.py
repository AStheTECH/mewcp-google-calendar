from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Base envelope — shared across all tools
# ---------------------------------------------------------------------------

class ToolError(BaseModel):
    code: str
    message: str
    details: Any = None


class ToolResult(BaseModel):
    success: bool
    statusCode: int
    retriable: bool = False
    retry_after_seconds: int | None = None
    error: ToolError | None = None


# ---------------------------------------------------------------------------
# Google Calendar API response models
# extra="allow" lets unmapped API fields pass through without errors
# ---------------------------------------------------------------------------

class EventDateTime(BaseModel):
    """Represents event start/end time — either date (all-day) or dateTime (timed)."""
    model_config = ConfigDict(extra="allow")

    date: str | None = None        # all-day event: "YYYY-MM-DD"
    dateTime: str | None = None    # timed event: RFC3339 e.g. "2026-01-08T14:30:00+00:00"
    timeZone: str | None = None


class AttendeeData(BaseModel):
    model_config = ConfigDict(extra="allow")

    email: str
    id: str | None = None
    displayName: str | None = None
    organizer: bool | None = None
    self: bool | None = None
    resource: bool | None = None
    optional: bool | None = None
    responseStatus: str | None = None   # needsAction | declined | tentative | accepted
    comment: str | None = None
    additionalGuests: int | None = None


class PersonData(BaseModel):
    """Creator or organizer of an event."""
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    email: str | None = None
    displayName: str | None = None
    self: bool | None = None


class CalendarData(BaseModel):
    """Calendar resource from calendars.get or calendarList entries."""
    model_config = ConfigDict(extra="allow")

    id: str
    summary: str
    description: str | None = None
    location: str | None = None
    timeZone: str | None = None
    accessRole: str | None = None       # freeBusyReader | reader | writer | owner
    backgroundColor: str | None = None
    foregroundColor: str | None = None
    selected: bool | None = None
    primary: bool | None = None
    hidden: bool | None = None


class ReminderOverride(BaseModel):
    method: str        # email | popup
    minutes: int


class Reminders(BaseModel):
    model_config = ConfigDict(extra="allow")

    useDefault: bool
    overrides: list[ReminderOverride] | None = None


class EventData(BaseModel):
    """Full event resource from the Google Calendar API."""
    model_config = ConfigDict(extra="allow")

    id: str
    summary: str | None = None
    start: EventDateTime
    end: EventDateTime
    status: str | None = None           # confirmed | tentative | cancelled
    htmlLink: str | None = None
    created: str | None = None          # RFC3339 timestamp
    updated: str | None = None          # RFC3339 timestamp
    description: str | None = None
    location: str | None = None
    colorId: str | None = None
    creator: PersonData | None = None
    organizer: PersonData | None = None
    recurrence: list[str] | None = None
    recurringEventId: str | None = None
    originalStartTime: EventDateTime | None = None  # instance only: scheduled start per RRULE, differs from start if instance was rescheduled
    transparency: str | None = None     # opaque | transparent
    visibility: str | None = None       # default | public | private | confidential
    iCalUID: str | None = None
    sequence: int | None = None
    attendees: list[AttendeeData] | None = None
    attendeesOmitted: bool | None = None
    guestsCanInviteOthers: bool | None = None
    guestsCanModify: bool | None = None
    guestsCanSeeOtherGuests: bool | None = None
    hangoutLink: str | None = None
    conferenceData: dict | None = None
    reminders: Reminders | None = None
    eventType: str | None = None        # default | outOfOffice | focusTime | workingLocation


class TimePeriod(BaseModel):
    start: str
    end: str


class FreeBusyCalendar(BaseModel):
    model_config = ConfigDict(extra="allow")

    busy: list[TimePeriod] = []
    errors: list[dict] | None = None


class FreeBusyData(BaseModel):
    """Response from freebusy.query."""
    model_config = ConfigDict(extra="allow")

    timeMin: str
    timeMax: str
    calendars: dict[str, FreeBusyCalendar]


# ---------------------------------------------------------------------------
# List wrappers
# ---------------------------------------------------------------------------

class CalendarListData(BaseModel):
    count: int
    calendars: list[CalendarData]
    next_page_token: str | None = None


class EventListData(BaseModel):
    count: int
    events: list[EventData]
    next_page_token: str | None = None


class MessageData(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Typed result classes — data field typed per tool group
# FastMCP uses the return annotation to generate outputSchema
# ---------------------------------------------------------------------------

class CalendarListResult(ToolResult):
    data: CalendarListData | None = None


class CalendarResult(ToolResult):
    data: CalendarData | None = None


class EventListResult(ToolResult):
    data: EventListData | None = None


class EventResult(ToolResult):
    data: EventData | None = None


class EventUpdateData(BaseModel):
    before: EventData
    after: EventData


class EventUpdateResult(ToolResult):
    data: EventUpdateData | None = None


class MessageResult(ToolResult):
    data: MessageData | None = None


class FreeBusyResult(ToolResult):
    data: FreeBusyData | None = None
