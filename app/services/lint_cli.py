from __future__ import annotations

import sys

from app.config import get_settings
from app.services.linter import lint_vault
from app.services.vault_loader import resolve_runtime_vault


def main() -> int:
    settings = get_settings()
    vault_root = resolve_runtime_vault(settings)
    errors = lint_vault(vault_root)
    if not errors:
        print("No lint issues found.")
        return 0
    for err in errors:
        print(err)
    return 1


if __name__ == "__main__":
    sys.exit(main())
