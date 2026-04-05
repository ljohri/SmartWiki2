#!/usr/bin/env zsh
set -euo pipefail

REPO_URL="${WIKI_VAULT_GIT_URL:-git@github.com:ljohri/wiki_vault.git}"
TARGET_DIR="${1:-wiki_vault}"

if [[ -d "${TARGET_DIR}/.git" ]]; then
  echo "Vault already exists at ${TARGET_DIR}"
  exit 0
fi

git clone "${REPO_URL}" "${TARGET_DIR}"
echo "Cloned ${REPO_URL} into ${TARGET_DIR}"
