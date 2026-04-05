from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.models.vault_contract import ValidationResult, expected_paths
from app.services.git_loader import clone_repo
from app.util.fs import is_non_empty_dir


class VaultInstantiationError(RuntimeError):
    pass


def resolve_runtime_vault(settings: Settings) -> Path:
    container_vault = Path("/app/wiki_vault")
    local_vault = Path("./wiki_vault").resolve()

    if settings.running_in_container:
        return _resolve_contract_order(container_vault, settings.wiki_vault_git_url)

    configured = settings.resolved_vault_path
    if configured.exists() and configured.is_dir():
        return configured
    if local_vault.exists() and local_vault.is_dir():
        return local_vault

    if settings.wiki_vault_git_url:
        clone_repo(settings.wiki_vault_git_url, local_vault)
        return local_vault

    raise VaultInstantiationError(
        "No local wiki_vault found. Create ./wiki_vault, set WIKI_VAULT_PATH, or set WIKI_VAULT_GIT_URL."
    )


def _resolve_contract_order(target_vault: Path, vault_git_url: str) -> Path:
    # Contract-mandated precedence for container runtime instantiation.
    dot_git = target_vault / ".git"
    if dot_git.exists():
        return target_vault

    if is_non_empty_dir(target_vault):
        return target_vault

    if vault_git_url:
        clone_repo(vault_git_url, target_vault)
        return target_vault

    raise VaultInstantiationError(
        "Unable to instantiate /app/wiki_vault: no .git, no non-empty directory, and WIKI_VAULT_GIT_URL is not set."
    )


def validate_vault_contract(vault_root: Path) -> ValidationResult:
    errors: list[str] = []
    required_dirs, required_files = expected_paths(vault_root)

    for req_dir in required_dirs:
        if not req_dir.exists() or not req_dir.is_dir():
            errors.append(f"Missing required directory: {req_dir}")

    for req_file in required_files:
        if not req_file.exists() or not req_file.is_file():
            errors.append(f"Missing required file: {req_file}")

    return ValidationResult(ok=not errors, errors=errors)
