from __future__ import annotations

import sys

from app.config import get_settings
from app.services.publisher import sync_and_build
from app.services.vault_loader import resolve_runtime_vault, validate_vault_contract


def main() -> int:
    settings = get_settings()
    vault_root = resolve_runtime_vault(settings)
    validate_vault_contract(vault_root).raise_for_error()
    sync_and_build(settings, vault_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
