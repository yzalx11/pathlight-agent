from fastapi import APIRouter

from app.config import settings
from app.schemas import ApiKeyPayload, SavedResponse
from app.services.credentials import has_deepseek_key, save_deepseek_key

router = APIRouter()


@router.get("/settings")
def get_settings() -> dict:
    return {
        "llm_provider": settings.llm_provider,
        "model": settings.deepseek_model,
        "has_api_key": has_deepseek_key() or bool(settings.deepseek_api_key),
    }


@router.put("/settings/deepseek-key", response_model=SavedResponse)
def set_deepseek_key(payload: ApiKeyPayload) -> SavedResponse:
    save_deepseek_key(payload.api_key)
    return SavedResponse()
