#!/usr/bin/env zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python3"
[[ -x "$PY" ]] || PY="${PYTHON:-python3}"
cd "$ROOT" || exit 1
exec "$PY" -m app.services.lint_cli
