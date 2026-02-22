from typing import Any, TypedDict


class ToolError(TypedDict):
    error: str


class OAuthTokenData(TypedDict, total=False):
    token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: list[str]


CalendarToolResponse = dict[str, Any] | ToolError

ApiObjectResponse = dict[str, Any] | ToolError
