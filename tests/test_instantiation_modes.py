from pathlib import Path

import pytest

from app.services.vault_loader import VaultInstantiationError, _resolve_contract_order


def test_instantiation_uses_git_directory_first(tmp_path: Path) -> None:
    vault = tmp_path / "wiki_vault"
    (vault / ".git").mkdir(parents=True)
    assert _resolve_contract_order(vault, "") == vault


def test_instantiation_uses_non_empty_directory_second(tmp_path: Path) -> None:
    vault = tmp_path / "wiki_vault"
    vault.mkdir(parents=True)
    (vault / "README.md").write_text("hello", encoding="utf-8")
    assert _resolve_contract_order(vault, "") == vault


def test_instantiation_fails_without_clone_source(tmp_path: Path) -> None:
    vault = tmp_path / "wiki_vault"
    vault.mkdir(parents=True)
    with pytest.raises(VaultInstantiationError):
        _resolve_contract_order(vault, "")
