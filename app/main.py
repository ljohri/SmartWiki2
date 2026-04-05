from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.lint import router as lint_router
from app.api.query import router as query_router
from app.api.rebuild import router as rebuild_router
from app.config import get_settings
from app.services.publisher import start_dev_rebuild_watcher, sync_and_build
from app.services.vault_loader import resolve_runtime_vault, validate_vault_contract

logger = logging.getLogger("smartwiki2")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.smartwiki_log_level.upper())
    # Resolve and validate vault before serving any API/site traffic.
    vault_root = resolve_runtime_vault(settings)
    validation = validate_vault_contract(vault_root)
    validation.raise_for_error()
    watcher = None
    try:
        # Initial publish build keeps "/" usable immediately after startup.
        sync_and_build(settings, vault_root)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Initial Quartz build failed: %s", exc)
    if settings.smartwiki_env == "dev":
        try:
            # In dev mode, rebuild automatically when content files change.
            watcher = start_dev_rebuild_watcher(settings, vault_root)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not start dev content watcher: %s", exc)
    yield
    if watcher is not None:
        watcher.stop()
        watcher.join(timeout=2)


app = FastAPI(title="SmartWiki2", lifespan=lifespan)
app.include_router(health_router, prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(lint_router, prefix="/api")
app.include_router(rebuild_router, prefix="/api")

settings = get_settings()
site_dir = settings.resolved_site_dir
site_dir.mkdir(parents=True, exist_ok=True)
placeholder = site_dir / "index.html"
if not placeholder.exists():
    placeholder.write_text(
        "<html><body><h1>SmartWiki2</h1><p>Published site will appear here after first Quartz build.</p></body></html>",
        encoding="utf-8",
    )
app.mount("/", StaticFiles(directory=str(site_dir), html=True), name="site")
