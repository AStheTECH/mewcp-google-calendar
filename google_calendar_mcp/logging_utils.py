from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from fastmcp_credentials import get_credentials

if TYPE_CHECKING:
    from .schemas import ToolResult

FULL_SCOPE = "https://www.googleapis.com/auth/calendar"
READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"

# Full calendar scope covers all readonly operations
_READONLY_SATISFIED_BY = {READONLY_SCOPE, FULL_SCOPE, EVENTS_SCOPE}
_WRITE_SATISFIED_BY = {FULL_SCOPE, EVENTS_SCOPE}


class ToolLogger:
    def __init__(self, logger: logging.Logger, tool: str) -> None:
        self._log = logger
        self._tool = tool
        self._start = time.monotonic()
        try:
            cred = get_credentials()
            self._rid = (cred.extra or {}).get("request_id")
        except Exception:
            self._rid = None
        self._log.info("tool=%s status=started request_id=%s", self._tool, self._rid)

    def _ms(self) -> int:
        return round((time.monotonic() - self._start) * 1000)

    def success(self) -> None:
        self._log.info(
            "tool=%s status=ok duration_ms=%d request_id=%s",
            self._tool, self._ms(), self._rid,
        )

    def failure(self, code: str, message: str) -> None:
        self._log.error(
            "tool=%s status=error code=%s duration_ms=%d request_id=%s msg=%s",
            self._tool, code, self._ms(), self._rid, message,
        )


def check_scope(required: str) -> ToolResult | None:
    """Returns an error ToolResult if the required scope is not granted, else None."""
    from .schemas import ToolError, ToolResult

    try:
        cred = get_credentials()
        scopes: set[str] = set(cred.scopes or [])
    except Exception as e:
        return ToolResult(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=f"Could not read credentials: {e}"),
        )

    if required == READONLY_SCOPE:
        granted = bool(scopes & _READONLY_SATISFIED_BY)
    else:
        granted = bool(scopes & _WRITE_SATISFIED_BY)

    if not granted:
        return ToolResult(
            success=False, statusCode=403, retriable=False,
            error=ToolError(
                code="AUTH_ERROR",
                message=f"Required scope not granted: {required}",
            ),
        )
    return None
