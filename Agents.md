# SmartWiki2 Agent Instructions

You are building SmartWiki2 as a **control program** for a Karpathy-style wiki.

## Core architecture

This repository is the **program repo**.
The wiki data lives in a **separate Git repository** that is instantiated at runtime inside this repo under:

- `/app/wiki_vault` in the container
- `./wiki_vault` in local development

The data repo is currently:

- `git@github.com:ljohri/wiki_vault.git`

### Non-negotiable rule
Do **not** convert this into a monorepo.
Do **not** use git submodules, git subtree, or vendor-copy the vault into the control repo.
The relationship between code and data is **runtime instantiation only**.

The same program, when pointed at a different vault repo with the same contract, must yield a different wiki.

## Product goal

Build a local/containerized wiki system with these properties:

1. The vault is Markdown-first and Obsidian-compatible.
2. The control program uses an OpenRouter-backed LLM agent to:
   - ingest raw materials
   - classify notes
   - create and update wiki pages
   - maintain wikilinks
   - maintain index and log pages
   - lint the wiki for duplicates, weak links, stale pages, and missing structure
3. The published wiki is generated and served **inside the container**.
4. The data repo stays independent from the control repo.
5. The control repo README must document the **exact data repo contract** so any compliant vault can be plugged in.

## Required implementation shape

### Tech stack
Use:
- Python 3.12 for the control program
- FastAPI for API endpoints and static serving
- OpenAI Python SDK pointed at OpenRouter base URL
- Quartz for site publishing/rendering
- Docker for runtime
- Makefile for common commands

### Directory layout in control repo

Create this structure:

.
├── AGENTS.md
├── README.md
├── .gitignore
├── .env.example
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh
├── publisher/
│   ├── quartz/                 # Quartz app skeleton
│   └── sync_to_quartz.py       # Copies/symlinks publishable content from wiki_vault/content
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── ingest.py
│   │   ├── query.py
│   │   ├── lint.py
│   │   ├── rebuild.py
│   │   └── health.py
│   ├── llm/
│   │   ├── openrouter_client.py
│   │   ├── prompts.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── vault_loader.py
│   │   ├── git_loader.py
│   │   ├── ingester.py
│   │   ├── classifier.py
│   │   ├── linker.py
│   │   ├── synthesizer.py
│   │   ├── linter.py
│   │   ├── publisher.py
│   │   └── frontmatter.py
│   ├── models/
│   │   ├── page_types.py
│   │   ├── source_manifest.py
│   │   └── vault_contract.py
│   └── util/
│       ├── fs.py
│       ├── markdown.py
│       ├── slugs.py
│       └── timestamps.py
├── scripts/
│   ├── bootstrap_vault.sh
│   ├── clone_vault.sh
│   ├── rebuild_site.sh
│   ├── lint_wiki.sh
│   └── dev_shell.sh
└── tests/
    ├── test_vault_contract.py
    ├── test_linking.py
    ├── test_publish.py
    └── test_instantiation_modes.py

### Runtime instantiation contract

The program must support three mutually exclusive ways to instantiate `wiki_vault`:

1. **bind mount**
   - host path mounted to `/app/wiki_vault`
2. **runtime clone**
   - container clones `WIKI_VAULT_GIT_URL` into `/app/wiki_vault`
3. **pre-existing folder**
   - local dev folder `./wiki_vault`

Implement this resolution order:
1. if `/app/wiki_vault/.git` exists, use it
2. else if `/app/wiki_vault` exists and is non-empty, use it
3. else if `WIKI_VAULT_GIT_URL` is set, clone it
4. else fail with a clear error

### Hard separation rules

- `wiki_vault/` must be in `.gitignore` in the control repo
- do not import program code into the vault repo
- do not store application runtime state in the control repo if it belongs to vault content
- do not require the vault repo to know internal Python package names from SmartWiki2
- interact with the vault through filesystem contract only

## Vault contract

The external data repo must be expected to look like this:

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

### Meaning of folders

- `content/` = durable Markdown pages that form the wiki
- `raw/` = original source artifacts
- `manifests/` = machine-readable registry files
- `exports/` = extracted transcripts, OCR-like text, normalized text exports
- `attachments/` = images/files embedded by content pages

### Required page classes

The LLM should maintain these page types:

- `project`
- `concept`
- `entity`
- `source-note`
- `synthesis`
- `decision`
- `index`
- `log`

### Required frontmatter for all content pages

Every page in `content/` must support this frontmatter contract:

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

Additional optional fields:
- `confidence`
- `entity_type`
- `concept_family`
- `canonical_source`
- `review_due`
- `owner`

## LLM behavior

### Ingest behavior
When a new raw artifact is added:

1. register it in `manifests/sources.jsonl`
2. extract or normalize text into `exports/` if needed
3. create or update a `source-note`
4. identify candidate entities, concepts, and projects
5. update or create durable pages in:
   - `content/entities`
   - `content/concepts`
   - `content/projects`
   - `content/syntheses`
6. add or repair wikilinks
7. update `content/index.md`
8. append a brief entry to `content/logs/log.md`
9. rebuild the published site

### Linking behavior
The linker must:
- prefer updating existing pages over creating near-duplicates
- use aliases to detect page collisions
- insert `[[wikilinks]]` only when semantically meaningful
- avoid over-linking every mention
- maintain reciprocal discoverability through backlinks or related fields where appropriate

### Lint behavior
Create a lint pass that flags:
- orphan pages
- duplicate concepts/entities
- empty source notes
- pages with missing frontmatter
- links to missing pages
- pages with too many trivial links
- stale pages with old `updated` timestamps
- source notes not connected to any synthesis/project/concept/entity page

## Query behavior

The query API should answer from the vault, not from arbitrary hidden memory.
Response generation should:
- retrieve relevant wiki pages and source notes
- cite page paths used
- prefer syntheses over raw notes when available
- expose uncertainty when the vault is thin or contradictory

## Publishing behavior

Use Quartz as the publisher.

Implementation rule:
- treat `wiki_vault/content` as the publishable source of truth
- sync `wiki_vault/content` into `publisher/quartz/content`
- build Quartz output into `/app/site`
- serve `/app/site` from FastAPI as static files

Attachments from `wiki_vault/content/attachments` must remain resolvable after publish.

Implement both:
- dev mode: rebuild on content change
- prod mode: build once on startup and rebuild on explicit API call or ingest

## Container behavior

The container must:
1. prepare `/app/wiki_vault`
2. instantiate the vault
3. validate vault structure
4. sync content into Quartz
5. build the site
6. start FastAPI
7. serve published site and API from the same container

### Suggested URLs
- `/` => published Quartz site
- `/api/health`
- `/api/ingest`
- `/api/query`
- `/api/lint`
- `/api/rebuild`

## OpenRouter behavior

Use environment variables:
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL` default `https://openrouter.ai/api/v1`
- `OPENROUTER_HTTP_REFERER`
- `OPENROUTER_TITLE`

Use deterministic settings by default for structural tasks:
- low temperature
- JSON schema / structured outputs where possible
- retry with backoff
- capture prompt/response metadata into manifests if enabled

## Git behavior

The control program must be able to:
- clone the vault repo
- fetch latest changes
- optionally commit vault content changes when explicitly requested
- never auto-push without explicit command

Add separate commands for:
- pull vault
- rebuild wiki
- lint wiki
- commit vault changes
- push vault changes

Do not mix control repo commits with vault repo commits.

## Security behavior

Support both:
- local dev via SSH agent forwarding
- automation via deploy key or GitHub App token

Do not bake private keys into the image.
Do not commit secrets.
Document `known_hosts` handling for GitHub SSH.

## README requirement

The root README of SmartWiki2 must include:
1. architectural overview
2. explicit explanation that this is NOT a monorepo
3. exact `wiki_vault` contract
4. container instantiation modes
5. OpenRouter setup
6. Quartz publish flow
7. examples using a different compliant vault
8. commands for bootstrap, ingest, query, lint, publish

## Output quality

Generate production-grade code, not pseudocode.
Prefer small focused modules.
Write tests for vault contract, linking, and publish flow.
Use clear error messages for missing vault structure.