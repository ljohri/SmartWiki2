from __future__ import annotations

import re

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def extract_wikilinks(markdown_text: str) -> list[str]:
    return WIKILINK_RE.findall(markdown_text)
