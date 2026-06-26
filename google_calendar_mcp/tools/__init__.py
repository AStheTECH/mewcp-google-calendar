from fastmcp import FastMCP

from .calendars_tools import register_calendars_tools
from .events_delete_tools import register_events_delete_tools
from .events_read_tools import register_events_read_tools
from .events_write_tools import register_events_write_tools
from .freebusy_tools import register_freebusy_tools


def register_tools(mcp: FastMCP) -> None:
    register_events_read_tools(mcp)
    register_events_write_tools(mcp)
    register_events_delete_tools(mcp)
    register_calendars_tools(mcp)
    register_freebusy_tools(mcp)
