from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

PANDOC = "/opt/anaconda3/bin/pandoc"
_IGNORE_FILE = ".pdf-lint-ignore"

# Directories under vault_root to skip when collecting pages for PDF generation
_SKIP_DIRS: frozenset[str] = frozenset({"PDFs", ".obsidian", ".git", "Attachments"})

# Matches an existing PDF-version link line (with optional leading newline)
_PDF_LINK_RE = re.compile(r"\[PDF Version\]\([^)]*\.pdf\)\n?")

# Matches YAML frontmatter at the start of a file
_FRONTMATTER_RE = re.compile(r"^---[ \t]*\n.*?\n---[ \t]*(?:\n|$)", re.DOTALL)


def _ignore_path(vault_root: Path) -> Path:
    return vault_root / _IGNORE_FILE


def load_ignore_list(vault_root: Path) -> set[str]:
    """Return the set of vault-relative paths that should never get a PDF."""
    p = _ignore_path(vault_root)
    if not p.exists():
        return set()
    return {line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()}


def _add_to_ignore_list(vault_root: Path, md_path: Path) -> None:
    rel = str(md_path.relative_to(vault_root))
    ignore = load_ignore_list(vault_root)
    if rel in ignore:
        return
    with _ignore_path(vault_root).open("a", encoding="utf-8") as f:
        f.write(rel + "\n")


def collect_vault_pages(vault_root: Path) -> list[Path]:
    """Walk vault_root for markdown files, skipping output and binary directories."""
    pages = []
    for p in vault_root.rglob("*.md"):
        rel_parts = p.relative_to(vault_root).parts
        if not any(part in _SKIP_DIRS or part.startswith(".") for part in rel_parts[:-1]):
            pages.append(p)
    return sorted(pages)


def pdf_path_for(md_path: Path, vault_root: Path) -> Path:
    """Return the canonical PDF output path for a markdown file."""
    rel = md_path.relative_to(vault_root)
    return vault_root / "PDFs" / rel.with_suffix(".pdf")


def generate_pdf(md_path: Path, vault_root: Path) -> tuple[bool, str]:
    """Run pandoc to produce a PDF; return (success, error_message).

    Files that previously failed are recorded in vault_root/.pdf-lint-ignore
    and silently skipped on future runs.
    """
    rel = str(md_path.relative_to(vault_root))
    if rel in load_ignore_list(vault_root):
        return True, ""  # silently skip — already on the ignore list

    out_pdf = pdf_path_for(md_path, vault_root)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            PANDOC, str(md_path),
            "-o", str(out_pdf),
            "--pdf-engine=xelatex",
            "-V", "geometry:margin=1in",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _add_to_ignore_list(vault_root, md_path)
        return False, result.stderr.strip()
    return True, ""


def insert_pdf_link(md_path: Path, pdf_path: Path) -> None:
    """Insert or update a [PDF Version](...) link in the markdown file."""
    rel = os.path.relpath(str(pdf_path), str(md_path.parent))
    link_line = f"[PDF Version]({rel})\n"

    text = md_path.read_text(encoding="utf-8")

    # Remove any pre-existing PDF link so we don't duplicate it
    text = _PDF_LINK_RE.sub("", text)

    fm_match = _FRONTMATTER_RE.match(text)
    if fm_match:
        end = fm_match.end()
        tail = text[end:].lstrip("\n")
        text = text[:end] + "\n" + link_line + "\n" + tail
    else:
        text = link_line + "\n" + text.lstrip("\n")

    md_path.write_text(text, encoding="utf-8")
