from app.llm.schemas import JobInsight


def validate_job_insight(
    insight: JobInsight, allowed_fact_codes: set[str]
) -> JobInsight:
    """Drop hallucinated fact references before any model output reaches the UI."""

    return insight.model_copy(
        update={"fact_codes": [code for code in insight.fact_codes if code in allowed_fact_codes]}
    )
