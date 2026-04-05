#!/usr/bin/env zsh
set -euo pipefail

TARGET_DIR="${1:-wiki_vault}"

mkdir -p "${TARGET_DIR}"/{content/{projects,concepts,entities,syntheses,source-notes,logs,inbox,attachments},raw/{pdfs,videos,decks,audio,webclips,spreadsheets,misc},manifests,exports/transcripts}

touch "${TARGET_DIR}"/README.md
touch "${TARGET_DIR}"/vault.yaml
touch "${TARGET_DIR}"/content/index.md
touch "${TARGET_DIR}"/content/logs/log.md
touch "${TARGET_DIR}"/manifests/{sources.jsonl,pages.jsonl,links.jsonl,jobs.jsonl}

echo "Bootstrapped vault at ${TARGET_DIR}"
