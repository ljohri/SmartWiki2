from pathlib import Path

from app.config import get_settings
from app.services.publisher import sync_content


def test_sync_content_to_quartz(tmp_path: Path, monkeypatch) -> None:
    vault_root = tmp_path / "vault"
    quartz_root = tmp_path / "quartz"
    (vault_root / "content" / "projects").mkdir(parents=True)
    (vault_root / "content" / "projects" / "demo.md").write_text("# Demo", encoding="utf-8")

    monkeypatch.setenv("SMARTWIKI_QUARTZ_DIR", str(quartz_root))
    get_settings.cache_clear()
    settings = get_settings()

    target = sync_content(settings, vault_root)
    assert target == quartz_root / "content"
    assert (quartz_root / "content" / "projects" / "demo.md").exists()
