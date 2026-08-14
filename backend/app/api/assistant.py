from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ReplyDraftPayload, ReplyDraftResponse
from app.services.assistant import create_reply_drafts


router = APIRouter()


@router.post("/assistant/reply-drafts", response_model=ReplyDraftResponse)
def draft_recruiter_reply(
    payload: ReplyDraftPayload, db: Session = Depends(get_db)
) -> ReplyDraftResponse:
    return ReplyDraftResponse(**create_reply_drafts(db, payload))
