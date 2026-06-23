import logging
import os

from pythonjsonlogger import jsonlogger

SERVER_VERSION = "v1.1.0"

# List breaking changes introduced in this version. Empty for non-breaking releases.
# Each entry: {"tool": str, "change": str, "migration": str}
# The gateway reads this on new server registration to auto-notify affected workflow owners.
BREAKING_CHANGES: list[dict] = []

# Timeouts are not configured here — google-api-python-client manages its own
# HTTP transport (httplib2). Timeout enforcement is handled at the gateway level.

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    handler.setFormatter(
        jsonlogger.JsonFormatter(fmt="%(asctime)s %(name)s %(levelname)s %(message)s")
    )
    logging.basicConfig(level=level, handlers=[handler], force=True)
