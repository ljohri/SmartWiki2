from pathlib import Path

from app.services.linker import find_missing_links


def test_find_missing_links(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "A.md").write_text("See [[B]] and [[MissingPage]].", encoding="utf-8")
    (content / "B.md").write_text("Existing page.", encoding="utf-8")

    missing = find_missing_links(content)
    assert content / "A.md" in missing
    assert "MissingPage" in missing[content / "A.md"]
    assert "B" not in missing[content / "A.md"]
