from __future__ import annotations

import json
from pathlib import Path

from app.models.source_manifest import SourceManifestEntry
from app.util.slugs import slugify
from app.util.timestamps import now_iso8601


def register_source(vault_root: Path, source_path: Path) -> SourceManifestEntry:
    source_id = f"src-{slugify(source_path.stem)}"
    entry = SourceManifestEntry.from_path(source_id=source_id, file_path=source_path)
    manifest_file = vault_root / "manifests" / "sources.jsonl"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    with manifest_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump()) + "\n")
    return entry


def append_log(vault_root: Path, message: str) -> None:
    log_file = vault_root / "content" / "logs" / "log.md"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"- {now_iso8601()} {message}\n")
