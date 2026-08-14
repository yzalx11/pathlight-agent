from app.llm.schemas import JobInsight, ReplyDraftSet


def validate_job_insight(
    insight: JobInsight, allowed_fact_codes: set[str]
) -> JobInsight:
    """Drop hallucinated fact references before any model output reaches the UI."""

    return insight.model_copy(
        update={"fact_codes": [code for code in insight.fact_codes if code in allowed_fact_codes]}
    )


def validate_reply_drafts(
    draft_set: ReplyDraftSet, allowed_fact_codes: set[str]
) -> ReplyDraftSet | None:
    """Keep only drafts that retain at least one confirmed, traceable fact."""

    validated_drafts = []
    for draft in draft_set.drafts:
        fact_codes = [code for code in draft.fact_codes if code in allowed_fact_codes]
        if fact_codes:
            validated_drafts.append(draft.model_copy(update={"fact_codes": fact_codes}))

    if not validated_drafts:
        return None
    return draft_set.model_copy(update={"drafts": validated_drafts})
