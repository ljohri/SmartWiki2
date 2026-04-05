from pathlib import Path

from app.services.vault_loader import validate_vault_contract


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
        "manifests/sources.jsonl",
        "manifests/pages.jsonl",
        "manifests/links.jsonl",
        "manifests/jobs.jsonl",
    ]:
        (root / rel).touch()


def test_validate_vault_contract_success(tmp_path: Path) -> None:
    vault = tmp_path / "wiki_vault"
    _bootstrap_minimal_vault(vault)
    result = validate_vault_contract(vault)
    assert result.ok
    assert result.errors == []


def test_validate_vault_contract_reports_missing(tmp_path: Path) -> None:
    vault = tmp_path / "wiki_vault"
    vault.mkdir()
    result = validate_vault_contract(vault)
    assert not result.ok
    assert any("Missing required directory" in err for err in result.errors)
    assert any("Missing required file" in err for err in result.errors)
