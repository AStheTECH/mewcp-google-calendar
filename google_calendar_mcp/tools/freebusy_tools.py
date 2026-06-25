from __future__ import annotations

import logging
from typing import List

from googleapiclient.errors import HttpError
from mcp.types import ToolAnnotations
from pydantic import Field

from . import mcp, _upstream_error
from ..logging_utils import ToolLogger
from ..schemas import (
    FreeBusyCalendar,
    FreeBusyData,
    FreeBusyResult,
    ToolError,
)
from ..service import get_service

logger = logging.getLogger("calendar-mcp-server")


@mcp.tool(
    name="get_free_busy",
    description=(
        "Returns busy time blocks for one or more calendars within a time range. "
        "Use this to find when someone is available or to schedule without conflicts. "
        "Provide time_min and time_max in ISO 8601 format with timezone, e.g. '2026-01-08T09:00:00Z'. "
        "Returns a map of calendar ID → list of busy time blocks. "
        "Free time = gaps between the busy blocks within the requested range."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
def get_free_busy(
    time_min: str = Field(..., description="Start of the query window in ISO 8601 format, e.g. '2026-01-08T09:00:00Z'"),
    time_max: str = Field(..., description="End of the query window in ISO 8601 format, e.g. '2026-01-08T17:00:00Z'"),
    calendar_ids: List[str] = Field(default=[], description="Calendar IDs to query. Defaults to ['primary'] if empty"),
) -> FreeBusyResult:
    tlog = ToolLogger(logger, "get_free_busy")
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
