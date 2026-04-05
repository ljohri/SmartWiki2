from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REQUIRED_DIRS = [
    "content/projects",
    "content/concepts",
    "content/entities",
    "content/syntheses",
    "content/source-notes",
    "content/logs",
    "content/inbox",
    "content/attachments",
    "raw/pdfs",
    "raw/videos",
    "raw/decks",
    "raw/audio",
    "raw/webclips",
    "raw/spreadsheets",
    "raw/misc",
    "manifests",
    "exports/transcripts",
]

REQUIRED_FILES = [
    "README.md",
    "vault.yaml",
    "content/index.md",
    "manifests/sources.jsonl",
    "manifests/pages.jsonl",
    "manifests/links.jsonl",
    "manifests/jobs.jsonl",
]

FRONTMATTER_REQUIRED_FIELDS = {
    "id",
    "title",
    "type",
    "status",
    "created",
    "updated",
    "aliases",
    "tags",
    "projects",
    "sources",
    "related",
    "publish",
}


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    errors: list[str]

    def raise_for_error(self) -> None:
        if not self.ok:
            details = "\n".join(f"- {err}" for err in self.errors)
            raise ValueError(f"wiki_vault contract validation failed:\n{details}")


def expected_paths(vault_root: Path) -> tuple[list[Path], list[Path]]:
    required_dirs = [vault_root / rel for rel in REQUIRED_DIRS]
    required_files = [vault_root / rel for rel in REQUIRED_FILES]
    return required_dirs, required_files
