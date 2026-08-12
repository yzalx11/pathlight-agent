from fastapi import APIRouter

from app.schemas import ApiKeyPayload, SavedResponse
from app.services.credentials import has_deepseek_key, save_deepseek_key

router = APIRouter()


@router.get("/settings")
def get_settings() -> dict:
    return {"has_deepseek_key": has_deepseek_key()}


@router.put("/settings/deepseek-key", response_model=SavedResponse)
def set_deepseek_key(payload: ApiKeyPayload) -> SavedResponse:
    save_deepseek_key(payload.api_key)
    return SavedResponse()
