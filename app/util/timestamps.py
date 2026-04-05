from __future__ import annotations

from datetime import datetime, timezone


def now_iso8601() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
