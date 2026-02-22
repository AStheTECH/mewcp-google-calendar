import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .schemas import OAuthTokenData

logger = logging.getLogger("calendar-mcp-server")


def get_token_data(oauth_token: OAuthTokenData) -> dict[str, Any]:
    return {
        "token": oauth_token.get("token"),
        "refresh_token": oauth_token.get("refresh_token"),
        "token_uri": oauth_token.get("token_uri") or "https://oauth2.googleapis.com/token",
        "client_id": oauth_token.get("client_id"),
        "client_secret": oauth_token.get("client_secret"),
        "scopes": oauth_token.get("scopes"),
    }


def get_service(oauth_token: OAuthTokenData):
    auth_data = get_token_data(oauth_token)
    logger.info("Creating Google Calendar API service with provided access token")
    creds = Credentials(**auth_data)
    service = build("calendar", "v3", credentials=creds)
    logger.info("Google Calendar API service created successfully")
    return service
