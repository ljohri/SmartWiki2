from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.frontmatter import validate_frontmatter_file
from app.services.linker import collect_markdown_pages, find_missing_links


def lint_vault(vault_root: Path, stale_days: int = 180) -> list[str]:
    errors: list[str] = []
    content_root = vault_root / "content"
    page_files = collect_markdown_pages(content_root)
    if not page_files:
        return ["No markdown pages found in content/"]

    for page in page_files:
        errors.extend(validate_frontmatter_file(page))

    missing_links = find_missing_links(content_root)
    for page, links in missing_links.items():
        errors.append(f"{page}: unresolved wikilinks {links}")

    stale_cutoff = datetime.now(tz=timezone.utc) - timedelta(days=stale_days)
    for page in page_files:
        mtime = datetime.fromtimestamp(page.stat().st_mtime, tz=timezone.utc)
        if mtime < stale_cutoff:
            errors.append(f"{page}: stale page (mtime older than {stale_days} days)")
    return errors
