from app.llm.schemas import JobInsight
from app.llm.validators import validate_job_insight


def test_job_insight_drops_unknown_fact_references() -> None:
    insight = JobInsight(
        role_focus="Build agent workflows.",
        day_to_day=["Implement integrations."],
        risks=[],
        questions_to_clarify=[],
        fact_codes=["F001", "F999"],
    )

    validated = validate_job_insight(insight, {"F001"})

    assert validated.fact_codes == ["F001"]
