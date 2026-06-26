from __future__ import annotations

from googleapiclient.errors import HttpError


def _upstream_error(e: HttpError) -> tuple[int, bool, int | None]:
    status = int(e.resp.status)
    retriable = status in (429, 500, 502, 503)
    retry_after: int | None = None
    if status == 429:
        raw = e.resp.get("retry-after") or e.resp.get("Retry-After")
        retry_after = int(raw) if raw else None
        if retry_after is None:
            retriable = False
    return status, retriable, retry_after
