from pathlib import Path

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.services.publisher import sync_and_build

router = APIRouter(tags=["rebuild"])


@router.post("/rebuild")
def rebuild(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    site = sync_and_build(settings, Path(settings.resolved_vault_path))
    return {"status": "rebuilt", "site_dir": str(site)}
