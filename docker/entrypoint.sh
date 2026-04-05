#!/usr/bin/env bash
set -euo pipefail

cd /app

mkdir -p /app/wiki_vault
mkdir -p /app/site

python3 - <<'PY'
from app.config import get_settings
from app.services.publisher import sync_and_build
from app.services.vault_loader import resolve_runtime_vault, validate_vault_contract

settings = get_settings()
vault = resolve_runtime_vault(settings)
validate_vault_contract(vault).raise_for_error()
sync_and_build(settings, vault)
print(f"Vault ready: {vault}")
PY

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
