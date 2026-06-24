from __future__ import annotations

import logging

from fastmcp import FastMCP
from googleapiclient.errors import HttpError

logger = logging.getLogger("calendar-mcp-server")


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


# Import sub-modules to register all tools via @mcp.tool decorators
from . import calendars, events_read, events_write, events_delete, freebusy  # noqa: E402, F401
