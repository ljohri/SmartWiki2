from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.models.source_manifest import SourceManifestEntry
from app.util.slugs import slugify
from app.util.timestamps import now_iso8601


def stable_source_id_for_rel_path(rel_to_vault: Path) -> str:
    """
    Stable source id derived from vault-relative path.
    This avoids collisions for duplicate file stems in different folders.
    """
    key = rel_to_vault.as_posix().encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()[:10]
    stem = slugify(rel_to_vault.stem) or "source"
    return f"src-{stem}-{digest}"


def register_source(
    vault_root: Path,
    source_path: Path,
    *,
    detected_type: str = "misc",
    source_id: str | None = None,
) -> SourceManifestEntry:
    rel = source_path.resolve().relative_to(vault_root.resolve())
    sid = source_id or stable_source_id_for_rel_path(rel)
    entry = SourceManifestEntry.from_path(source_id=sid, file_path=source_path, detected_type=detected_type)
    manifest_file = vault_root / "manifests" / "sources.jsonl"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    # Keep sources.jsonl append-only for new source IDs, but avoid duplicate rows for the same source_id.
    if manifest_file.exists():
        existing = manifest_file.read_text(encoding="utf-8").splitlines()
        for line in existing:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if payload.get("source_id") == sid:
                return entry
    with manifest_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump()) + "\n")
    return entry


def append_log(vault_root: Path, message: str) -> None:
    log_file = vault_root / "content" / "logs" / "log.md"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"- {now_iso8601()} {message}\n")
