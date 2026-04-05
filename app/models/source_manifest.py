from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field


class SourceManifestEntry(BaseModel):
    source_id: str
    raw_path: str
    detected_type: str = "misc"
    ingested_at: str = Field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    @classmethod
    def from_path(cls, source_id: str, file_path: Path, detected_type: str = "misc") -> "SourceManifestEntry":
        return cls(source_id=source_id, raw_path=str(file_path), detected_type=detected_type)
