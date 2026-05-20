from typing import Any, TypedDict


class ToolError(TypedDict):
    error: str


CalendarToolResponse = dict[str, Any] | ToolError

ApiObjectResponse = dict[str, Any] | ToolError
