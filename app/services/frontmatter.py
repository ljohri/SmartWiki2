from __future__ import annotations

from pathlib import Path

import frontmatter

from app.models.vault_contract import FRONTMATTER_REQUIRED_FIELDS


def validate_frontmatter_file(file_path: Path) -> list[str]:
    errors: list[str] = []
    post = frontmatter.load(file_path)
    missing = [field for field in FRONTMATTER_REQUIRED_FIELDS if field not in post.metadata]
    if missing:
        errors.append(f"{file_path}: missing frontmatter fields {sorted(missing)}")
    return errors
