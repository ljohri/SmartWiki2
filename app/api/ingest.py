from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.ingester import append_log, register_source
from app.services.publisher import sync_and_build

router = APIRouter(tags=["ingest"])


class IngestRequest(BaseModel):
    source_path: str


@router.post("/ingest")
def ingest(payload: IngestRequest, settings: Settings = Depends(get_settings)) -> dict[str, str]:
    vault_root = Path(settings.resolved_vault_path)
    source_path = Path(payload.source_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Source file not found: {source_path}")
    entry = register_source(vault_root, source_path)
    append_log(vault_root, f"Ingested source {entry.source_id}")
    sync_and_build(settings, vault_root)
    return {"status": "ingested", "source_id": entry.source_id}
