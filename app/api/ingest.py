from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.raw_ingestor import ingest_single_source, scan_and_ingest_raw_files
from app.services.publisher import sync_and_build

router = APIRouter(tags=["ingest"])


class IngestRequest(BaseModel):
    source_path: str


@router.post("/ingest")
def ingest(payload: IngestRequest, settings: Settings = Depends(get_settings)) -> dict[str, object]:
    vault_root = Path(settings.resolved_vault_path)
    source_path = Path(payload.source_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Source file not found: {source_path}")
    try:
        changed, source_id = ingest_single_source(vault_root, source_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    sync_and_build(settings, vault_root)
    return {"status": "ingested", "source_id": source_id, "changed": changed}


@router.post("/ingest/scan")
def ingest_scan(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    vault_root = Path(settings.resolved_vault_path)
    summary = scan_and_ingest_raw_files(vault_root)
    if summary.processed_files > 0:
        sync_and_build(settings, vault_root)
        summary.rebuilt = True
    return {"status": "ok", "summary": summary.to_dict()}
