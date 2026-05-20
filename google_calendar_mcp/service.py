import logging

from fastmcp_credentials import get_credentials
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger("calendar-mcp-server")


def get_service():
    cred = get_credentials()
    if not cred.access_token:
        raise ValueError("No OAuth access token available in credentials")
    logger.info("Creating Google Calendar API service with provided access token")
    creds = Credentials(token=cred.access_token, scopes=cred.scopes)
    service = build("calendar", "v3", credentials=creds)
    logger.info("Google Calendar API service created successfully")
    return service
