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

## Karpathy Knowledge Store Alignment

![Karpathy-style knowledge store model for SmartWiki2](docs/karpathy-knowledge-store.svg)

The diagram captures the target system shape and complements what is already implemented:

- **Data ingest layer**: multiple source types land in `wiki_vault/raw/**` as immutable originals.
- **LLM engine layer**: compile, Q&A, lint/repair, and indexing/linking capabilities operate over vault data.
- **Knowledge store layer**: `wiki_vault/content/**` is the durable markdown knowledge base and publish source.
- **Output layer**: markdown pages today; slides/charts/report artifacts can be added and optionally filed back into wiki.
- **Frontend layer**: Obsidian/editor + API-based tooling around the same underlying vault.

Current vs roadmap in this repo:

- **Implemented now**
  - deterministic publish pipeline from `wiki_vault/content` to static site
  - ingest registration (`sources.jsonl` + `logs/log.md`) with rebuild
  - LLM-enabled `POST /api/query` over vault context
- **Planned next (from AGENTS contract + this model)**
  - ingest-time authoring (`source-note`, concept/entity/project updates)
  - richer linker/linter repair loops and index maintenance
  - derived outputs (slides/charts/summaries) with optional write-back to wiki

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

## Adding knowledge: from files to the published wiki

Understanding what “shows up” is important:

- **Published pages** come from **`wiki_vault/content`** (Markdown with the required frontmatter). The publisher syncs that tree into Quartz and builds the static site.
- **`wiki_vault/raw`** holds original artifacts (PDFs, notes exports, etc.). Those paths are **not** automatically turned into full wiki pages. You typically keep originals there, optionally **register** them via ingest, and **write or update** durable pages under `content/` (for example a `source-note` or `synthesis`) that summarize or link to the material.
- **`wiki_vault/content/attachments`** is for images and other assets you embed from Markdown; those files are published together with your pages.

### One new Markdown page (most common)

1. Create or edit a file under `wiki_vault/content/...` (for example `content/concepts/my-topic.md`) using the **required frontmatter** above.
2. Save the file.
3. **Rebuild** so the site picks it up:
   - In **dev** (`SMARTWIKI_ENV=dev`), saving under `content/` usually triggers a rebuild via the watcher.
   - Otherwise run `make rebuild-site`, or `curl -X POST http://localhost:8000/api/rebuild`.
4. Open **`http://localhost:8000/`** and navigate to the new page (the exact URL shape depends on how the Quartz build maps paths).

### One or more original files (sources, not yet pages)

1. Copy files into the appropriate folder under `wiki_vault/raw/...` (for example `raw/pdfs/`, `raw/misc/`).
2. **Optional but useful:** register each file with the ingest API so it is recorded in `manifests/sources.jsonl` and a line is appended to `content/logs/log.md`:

   ```bash
   curl -X POST http://localhost:8000/api/ingest \
     -H "content-type: application/json" \
     -d '{"source_path":"./wiki_vault/raw/misc/notes.txt"}'
   ```

   Ingest also triggers a **publish rebuild**; it does **not** by itself create a new Markdown page from arbitrary file types.

3. **Add durable wiki content** under `wiki_vault/content/...` (for example a `source-note` or `synthesis`) that describes the material and links to the file path or filename as needed.
4. Rebuild if you only edited `content/` without hitting ingest (see “One new Markdown page” above).

### A batch of files

1. Copy the whole set into `wiki_vault/raw/...` (and/or into `content/attachments/` if they are assets for pages).
2. For each source you want tracked, call **`POST /api/ingest`** with each path (or automate that with a small shell loop on your machine).
3. Add or update the Markdown pages under `content/` that reference them (one page per topic, or a single index page with links).
4. Run **`make rebuild-site`** or **`POST /api/rebuild`** once at the end if you did not rely on the dev watcher.

### Quick checklist

| Goal | Where to put files | What triggers the site update |
|------|--------------------|--------------------------------|
| New readable wiki page | `wiki_vault/content/**/*.md` | Save + rebuild (or dev watcher) |
| Original PDF / binary | `wiki_vault/raw/**` | Ingest optional; add `content/` page to surface it |
| Images for pages | `wiki_vault/content/attachments/**` | Link from Markdown; rebuild |

## Ingesting and authoring workflows (detailed)

This section expands the flows above. The **existing publish pipeline is unchanged**: sync `wiki_vault/content` → Quartz build → serve `/app/site`. Authoring and ingesting are how you **change the vault** before that pipeline runs.

![LLM authoring lifecycle: compile/classify/author/link/lint, write back to vault, then publish](docs/llm-authoring-lifecycle.svg)

### Concepts: authoring vs ingesting

| | **Authoring** | **Ingesting** (API) |
|---|----------------|---------------------|
| **What it is** | You create or edit durable wiki pages (Markdown + frontmatter) and assets under `wiki_vault/content/`. | You tell SmartWiki2 about a **file on disk** (usually under `wiki_vault/raw/`) via `POST /api/ingest`. |
| **Primary output** | New or updated `.md` pages (and attachments) that the site can render. | A JSON line in `manifests/sources.jsonl`, a line in `content/logs/log.md`, then a **full publish rebuild**. |
| **LLM today** | Not required. You write pages by hand (or use external tools). | **Not used.** Ingest does not call OpenRouter. |
| **LLM elsewhere** | `POST /api/query` uses the LLM to answer questions **from** existing `content/` text (optional key). | Same vault; query is separate from ingest. |

**Agents.md** describes a richer future ingest pipeline (extract text, auto `source-note`s, linker passes, index updates). The **current** program implements registration + log + rebuild; **authoring** is how you add the actual narrative pages and `[[wikilinks]]`.

### End-to-end data flow (unchanged)

![Publish pipeline: wiki_vault content → sync → Quartz build → /app/site → served at /](docs/publish-flow.svg)

Raw files under `wiki_vault/raw/` are **not** in that path unless you also reference them from Markdown or copy summaries into `content/`.

### Authoring workflow (wiki pages and links)

1. **Edit in the vault repo** (on disk at `wiki_vault/`, or your mounted path in Docker). Use your editor or Obsidian-compatible tooling; SmartWiki2 does not host an in-browser wiki editor.

2. **Place pages** under the contract folders, for example:
   - `content/concepts/…`, `content/projects/…`, `content/source-notes/…`, `content/syntheses/…`, etc.
   - Every publishable page should include the **required frontmatter** (see above).

3. **Wikilinks** use Obsidian-style `[[Page Title]]` or `[[path]]` patterns as you prefer; the linter checks resolution against other pages’ **stem names** (see `app/services/linker.py`). Prefer stable titles and add **`aliases`** in frontmatter when the same topic has multiple names.

4. **Attachments**: put files under `content/attachments/` and link them from Markdown so they sync and remain resolvable after publish.

5. **Trigger a publish** so the static site updates:
   - **`SMARTWIKI_ENV=dev`**: a filesystem watcher on `wiki_vault/content` debounces and runs sync+build when you save files (see app startup).
   - **Otherwise**: run `make rebuild-site`, or `POST /api/rebuild`, or use ingest (which also rebuilds—see below).

6. **Verify**: open `http://localhost:8000/` (or your deployment URL) and spot-check the new routes. Run `GET /api/lint` or `make lint-wiki` for structural issues.

### Ingest workflow (`POST /api/ingest`)

Use this when a **source file already exists** on the filesystem path you pass (absolute path, or path relative to the process working directory—typically the SmartWiki2 repo root when using `./wiki_vault/...`).

**Steps performed by the server** (in order):

1. **Resolve** `wiki_vault` via the same rules as the rest of the app (`WIKI_VAULT_PATH`, `./wiki_vault`, or container `/app/wiki_vault`).
2. **Validate** the `source_path` exists; if not, HTTP 404.
3. **Register** the source: append one JSON object per line to `manifests/sources.jsonl` with a generated `source_id` (derived from the filename stem), path, and timestamp metadata.
4. **Log**: append a bullet line to `content/logs/log.md` noting the ingest.
5. **Publish**: run the same **sync + Quartz build** as a manual rebuild—copy `wiki_vault/content` into `publisher/quartz/content`, build, copy output to `/app/site` (or `SMARTWIKI_SITE_DIR`).

**What ingest does *not* do today**

- It does **not** read PDF/video/binary content, extract text, or auto-generate Markdown pages.
- It does **not** run the LLM or auto-insert `[[wikilinks]]`.
- It does **not** modify `content/index.md` except indirectly if you edit it yourself.

After ingest, **authoring** is still how new knowledge appears as readable wiki pages: create or update Markdown under `content/` that references the material.

### Typical combined workflows

**A — New topic, written directly in the wiki**

1. Add `content/concepts/my-topic.md` (frontmatter + body + optional `[[links]]`).
2. Save; in dev, watcher rebuilds; else `POST /api/rebuild`.
3. Optional: `GET /api/lint` to catch missing links or frontmatter gaps.

**B — New external file + audit trail**

1. Copy `report.pdf` to `wiki_vault/raw/pdfs/`.
2. `POST /api/ingest` with `"source_path":"./wiki_vault/raw/pdfs/report.pdf"` (adjust path to match how you run the server).
3. Author a page such as `content/source-notes/report.md` summarizing the PDF and linking to it or naming it in the body.
4. Rebuild if you did not use dev mode for step 3 (ingest already rebuilt once after step 2).

**C — Batch of drops**

1. Copy many files into `raw/...`.
2. Loop `curl` ingest per file **or** ingest only the ones you care to register; others remain on disk unregistered.
3. Author or update one or more `content/` pages that tie the batch together (index, per-source notes, synthesis).
4. One final `POST /api/rebuild` if needed.

### LLM-assisted steps (current vs roadmap)

- **Today**: **`POST /api/query`** is the only endpoint that calls OpenRouter (when `OPENROUTER_API_KEY` is set). It answers using excerpts from existing `content/` pages—it does not write the vault.
- **Roadmap (Agents.md)**: ingest could later add extraction, classification, auto `source-note` creation, linker passes, and index/log maintenance. When that exists, it will still be clearest to treat those as **writes to `wiki_vault/`** followed by the **same** publish pipeline.

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

Option C (manual): you already ran `make bootstrap-vault`, so `wiki_vault` exists but has **no** `.git` yet. To point that folder at the upstream vault and match the remote tree, run these commands yourself (from a shell, not via a helper script in this repo):

```bash
cd wiki_vault
git init
git remote add origin git@github.com:ljohri/wiki_vault.git
git fetch origin
git checkout -B main origin/main
```

If `git checkout` fails because bootstrap created **untracked** files that would be overwritten, remove or rename those paths, or discard untracked files only if you do not need them:

```bash
git clean -fd
git checkout -B main origin/main
```

If the default branch on GitHub is `master` instead of `main`, use `origin/master` in the checkout lines above. Afterward, from the SmartWiki2 repo root, `make pull-vault` fast-forwards from `origin`.

**Alternative (often simpler):** delete the bootstrapped folder and clone fresh:

```bash
rm -rf wiki_vault
git clone git@github.com:ljohri/wiki_vault.git wiki_vault
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