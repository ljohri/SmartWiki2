from __future__ import annotations

import shutil
from pathlib import Path


def sync_vault_content_to_quartz(vault_root: Path, quartz_root: Path) -> Path:
    source = vault_root / "content"
    target = quartz_root / "content"
    if not source.exists():
        raise FileNotFoundError(f"Vault content directory not found: {source}")

    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, dirs_exist_ok=True)
    return target
