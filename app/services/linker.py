from __future__ import annotations

from pathlib import Path

from app.util.markdown import extract_wikilinks


def collect_markdown_pages(content_root: Path) -> list[Path]:
    return sorted(content_root.rglob("*.md"))


def build_page_title_index(content_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for page in collect_markdown_pages(content_root):
        index[page.stem.lower()] = page
    return index


def find_missing_links(content_root: Path) -> dict[Path, list[str]]:
    index = build_page_title_index(content_root)
    missing: dict[Path, list[str]] = {}
    for page in collect_markdown_pages(content_root):
        links = extract_wikilinks(page.read_text(encoding="utf-8"))
        unresolved = [lk for lk in links if lk.strip().lower() not in index]
        if unresolved:
            missing[page] = unresolved
    return missing
