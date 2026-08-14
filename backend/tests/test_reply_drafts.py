from app.llm.schemas import ReplyDraft, ReplyDraftSet
from app.llm.validators import validate_reply_drafts


def test_reply_drafts_drop_unconfirmed_fact_references() -> None:
    draft_set = ReplyDraftSet(
        drafts=[
            ReplyDraft(label="Grounded", content="I built the API project.", fact_codes=["F001", "F999"]),
            ReplyDraft(label="Ungrounded", content="I have five years of experience.", fact_codes=["F999"]),
        ]
    )

    validated = validate_reply_drafts(draft_set, {"F001"})

    assert validated is not None
    assert len(validated.drafts) == 1
    assert validated.drafts[0].fact_codes == ["F001"]


def test_reply_drafts_are_rejected_without_confirmed_evidence() -> None:
    draft_set = ReplyDraftSet(
        drafts=[ReplyDraft(label="No evidence", content="I can join tomorrow.", fact_codes=["F999"])]
    )

    assert validate_reply_drafts(draft_set, {"F001"}) is None
