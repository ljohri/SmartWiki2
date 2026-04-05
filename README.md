# SmartWiki2

SmartWiki2 is the control program for a Karpathy-style wiki. It manages ingestion, linking, linting, query-time retrieval, and site publishing while keeping wiki data in an independent repository (`wiki_vault`).

## Architecture Overview

SmartWiki2 uses:
- Python 3.12
- FastAPI for APIs and static site serving
- OpenAI Python SDK configured for OpenRouter
- Quartz publishing workspace under `publisher/quartz`
- Docker for local/container runtime
- Makefile + scripts for operational commands

Runtime flow:
1. Instantiate `wiki_vault` via bind mount, pre-existing folder, or runtime clone.
2. Validate vault contract.
3. Sync `wiki_vault/content` to `publisher/quartz/content`.
4. Build published output into `/app/site`.
5. Serve `/app/site` and `/api/*` from the same FastAPI process.

## Not a Monorepo

This repository is the **program repo only**.

The wiki content is an independent git repository instantiated at runtime:
- local dev: `./wiki_vault`
- container: `/app/wiki_vault`

Hard constraints:
- no submodules
- no subtree
- no vendoring of vault content into this repo

Invariant: same SmartWiki2 code + different compliant vault => different published wiki.

## External Vault Contract

A compliant `wiki_vault` repository must contain:

```text
wiki_vault/
├── README.md
├── vault.yaml
├── content/
│   ├── index.md
│   ├── projects/
│   ├── concepts/
│   ├── entities/
│   ├── syntheses/
│   ├── source-notes/
│   ├── logs/
│   ├── inbox/
│   └── attachments/
├── raw/
│   ├── pdfs/
│   ├── videos/
│   ├── decks/
│   ├── audio/
│   ├── webclips/
│   ├── spreadsheets/
│   └── misc/
├── manifests/
│   ├── sources.jsonl
│   ├── pages.jsonl
│   ├── links.jsonl
│   └── jobs.jsonl
└── exports/
    └── transcripts/
```

Folder meaning:
- `content/`: durable markdown wiki pages
- `raw/`: original source artifacts
- `manifests/`: machine-readable operational registry
- `exports/`: normalized extraction/transcription output
- `content/attachments/`: publishable embedded assets

Required page types:
- `project`
- `concept`
- `entity`
- `source-note`
- `synthesis`
- `decision`
- `index`
- `log`

Required frontmatter for content pages:

```yaml
---
id: "uuid-or-stable-slug"
title: "Page Title"
type: "project|concept|entity|source-note|synthesis|decision|index|log"
status: "draft|active|archived"
created: "ISO-8601"
updated: "ISO-8601"
aliases: []
tags: []
projects: []
sources: []
related: []
publish: true
---
```

Optional frontmatter fields:
- `confidence`
- `entity_type`
- `concept_family`
- `canonical_source`
- `review_due`
- `owner`

## Vault Instantiation Modes

Supported mutually-exclusive modes:
1. bind mount: host vault mounted to `/app/wiki_vault`
2. runtime clone: clone `WIKI_VAULT_GIT_URL` into `/app/wiki_vault`
3. pre-existing local folder: `./wiki_vault`

Container resolution order (exact):
1. use `/app/wiki_vault` if `/app/wiki_vault/.git` exists
2. else use `/app/wiki_vault` if directory exists and non-empty
3. else clone `WIKI_VAULT_GIT_URL` to `/app/wiki_vault`
4. else fail with clear error

## OpenRouter Setup

Set these environment variables:
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`)
- `OPENROUTER_HTTP_REFERER`
- `OPENROUTER_TITLE`

SmartWiki2 uses OpenAI SDK with `base_url` pointed at OpenRouter and deterministic defaults (`temperature=0.1` for structural operations, retries with exponential backoff).

## Quartz Publish Flow

Publishing contract:
1. source of truth is `wiki_vault/content`
2. sync to `publisher/quartz/content`
3. run Quartz build in `publisher/quartz`
4. copy build output to `/app/site`
5. serve `/app/site` via FastAPI at `/`

Attachments under `wiki_vault/content/attachments` are synced as part of content and remain resolvable in published output.

Modes:
- dev mode (`SMARTWIKI_ENV=dev`): startup build + file watcher rebuilds on content changes
- prod mode: startup build once + explicit rebuild via API (`/api/rebuild`) or ingest pipeline

## API Endpoints

- `GET /api/health`
- `POST /api/ingest`
- `POST /api/query`
- `GET /api/lint`
- `POST /api/rebuild`

Site URL:
- `GET /` serves published wiki

## End-to-End Setup (Local)

### 1) Prerequisites

- Python 3.12+
- Node.js 20+ (for Quartz build workspace)
- git

### 2) Configure environment and OpenRouter

Create local env file:

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
OPENROUTER_API_KEY=or-xxxxxxxx
OPENROUTER_MODEL=openai/gpt-4.1-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_HTTP_REFERER=http://localhost:8000
OPENROUTER_TITLE=SmartWiki2
SMARTWIKI_ENV=dev
```

### 3) Prepare `wiki_vault`

Option A: bootstrap an empty compliant vault structure:

```bash
make bootstrap-vault
```

Option B: clone existing external vault:

```bash
export WIKI_VAULT_GIT_URL=git@github.com:ljohri/wiki_vault.git
make clone-vault
```

### 4) Add source files to ingest

Put raw files into vault `raw/` folders, for example:

```bash
mkdir -p wiki_vault/raw/misc
echo "Project Alpha is focused on retrieval quality." > wiki_vault/raw/misc/project-alpha.txt
```

### 5) Add or edit wiki pages directly (optional/manual)

Create or edit markdown pages under `wiki_vault/content/*`, for example:

```bash
mkdir -p wiki_vault/content/projects
cat > wiki_vault/content/projects/project-alpha.md <<'EOF'
---
id: "project-alpha"
title: "Project Alpha"
type: "project"
status: "active"
created: "2026-04-05T00:00:00Z"
updated: "2026-04-05T00:00:00Z"
aliases: []
tags: []
projects: []
sources: []
related: []
publish: true
---

Project Alpha is a test project.
EOF
```

### 6) Install deps and run SmartWiki2

```bash
make install
make run
```

App and site will be available at:
- `http://localhost:8000/` (published site)
- `http://localhost:8000/api/health` (API health)

### 7) Ingest a raw file

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "content-type: application/json" \
  -d '{"source_path":"./wiki_vault/raw/misc/project-alpha.txt"}'
```

This appends to `wiki_vault/manifests/sources.jsonl`, updates logs, and triggers a publish rebuild.

### 8) Query with OpenRouter-backed retrieval

```bash
curl -X POST http://localhost:8000/api/query \
  -H "content-type: application/json" \
  -d '{"question":"What is Project Alpha about?"}'
```

### 9) Validate and rebuild manually

```bash
make lint-wiki
make rebuild-site
```

## End-to-End Setup (Docker)

### Runtime clone mode

```bash
docker build -f docker/Dockerfile -t smartwiki2 .
docker run --rm -p 8000:8000 \
  -e OPENROUTER_API_KEY=or-xxxxxxxx \
  -e WIKI_VAULT_GIT_URL=git@github.com:ljohri/wiki_vault.git \
  smartwiki2
```

### Bind mount mode

```bash
docker run --rm -p 8000:8000 \
  -e OPENROUTER_API_KEY=or-xxxxxxxx \
  -v "$(pwd)/wiki_vault:/app/wiki_vault" \
  smartwiki2
```

In both modes, SmartWiki2 serves API and published site from the same container process.

## Commands

Install and run:

```bash
make install
make run
```

Vault lifecycle:

```bash
make bootstrap-vault
make clone-vault
make pull-vault
```

Wiki operations:

```bash
make lint-wiki
make rebuild-site
```

Ingest and query via API:

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "content-type: application/json" \
  -d '{"source_path":"./wiki_vault/raw/misc/example.txt"}'

curl -X POST http://localhost:8000/api/query \
  -H "content-type: application/json" \
  -d '{"question":"What does the vault currently say about Project Alpha?"}'
```

Tests:

```bash
make test
```

Explicit vault git operations (data repo only):

```bash
make commit-vault m="Update wiki pages"
make push-vault
```

## Docker

Build and run:

```bash
docker build -f docker/Dockerfile -t smartwiki2 .
docker run --rm -p 8000:8000 -e OPENROUTER_API_KEY=... -e WIKI_VAULT_GIT_URL=git@github.com:ljohri/wiki_vault.git smartwiki2
```

SSH support notes:
- forward SSH agent for git@github.com clone/pull workflows
- pre-populate `known_hosts` for GitHub in runtime environment
- never bake private keys into images

## Alternate Vault Example

Use any compliant vault without code changes:

```bash
export WIKI_VAULT_GIT_URL=git@github.com:example/my-compliant-vault.git
make run
```

If `example/my-compliant-vault` satisfies the same contract, SmartWiki2 will publish that vault’s wiki, demonstrating strict code/data separation.