from pathlib import Path

from app.services.raw_ingestor import db_stats, ingest_single_source, scan_and_ingest_raw_files


def _bootstrap_minimal_vault(root: Path) -> None:
    required_dirs = [
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
    for rel in required_dirs:
        (root / rel).mkdir(parents=True, exist_ok=True)
    for rel in [
        "README.md",
        "vault.yaml",
        "content/index.md",
        "content/logs/log.md",
        "manifests/sources.jsonl",
        "manifests/pages.jsonl",
        "manifests/links.jsonl",
        "manifests/jobs.jsonl",
    ]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()


def test_ingest_single_source_creates_vault_local_artifacts(tmp_path: Path) -> None:
    vault = tmp_path / "wiki_vault"
    _bootstrap_minimal_vault(vault)
    raw_file = vault / "raw" / "misc" / "note.txt"
    raw_file.write_text("hello raw world", encoding="utf-8")

    changed, source_id = ingest_single_source(vault, raw_file)
    assert changed is True
    assert source_id.startswith("src-note-")

    db_file = vault / "manifests" / "ingest.sqlite"
    assert db_file.exists()

    transcript = vault / "exports" / "transcripts" / f"{source_id}.md"
    assert transcript.exists()
    assert "hello raw world" in transcript.read_text(encoding="utf-8")

    source_note_dir = vault / "content" / "source-notes"
    source_notes = list(source_note_dir.glob("*.md"))
    assert source_notes
    assert source_id in source_notes[0].read_text(encoding="utf-8")

    stats = db_stats(vault)
    assert stats["total"] == 1
    assert stats["ingested"] >= 1


def test_scan_ingests_only_new_or_changed_files(tmp_path: Path) -> None:
    vault = tmp_path / "wiki_vault"
    _bootstrap_minimal_vault(vault)
    file_a = vault / "raw" / "misc" / "a.txt"
    file_b = vault / "raw" / "misc" / "b.txt"
    file_a.write_text("alpha", encoding="utf-8")
    file_b.write_text("beta", encoding="utf-8")

    first = scan_and_ingest_raw_files(vault)
    assert first.scanned_files == 2
    assert first.processed_files == 2

    second = scan_and_ingest_raw_files(vault)
    assert second.scanned_files == 2
    assert second.processed_files == 0
    assert second.skipped_files == 2

    file_a.write_text("alpha-v2", encoding="utf-8")
    third = scan_and_ingest_raw_files(vault)
    assert third.scanned_files == 2
    assert third.processed_files == 1
