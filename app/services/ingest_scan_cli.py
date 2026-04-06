from __future__ import annotations

import json
import sys

from app.config import get_settings
from app.services.publisher import sync_and_build
from app.services.raw_ingestor import scan_and_ingest_raw_files
from app.services.vault_loader import resolve_runtime_vault, validate_vault_contract


def main() -> int:
    settings = get_settings()
    vault_root = resolve_runtime_vault(settings)
    validate_vault_contract(vault_root).raise_for_error()

    summary = scan_and_ingest_raw_files(vault_root)
    if summary.processed_files > 0:
        sync_and_build(settings, vault_root)
        summary.rebuilt = True
    print(json.dumps(summary.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
