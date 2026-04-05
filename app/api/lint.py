from pathlib import Path

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.services.linter import lint_vault

router = APIRouter(tags=["lint"])


@router.get("/lint")
def lint(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    errors = lint_vault(Path(settings.resolved_vault_path))
    return {"ok": not errors, "errors": errors}
