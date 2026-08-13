from app.llm.deepseek import _parse_insight


def test_normalizes_scalar_list_fields():
    insight = _parse_insight(
        """{
            "role_focus": "维护 Python API",
            "day_to_day": "编写接口并处理数据",
            "risks": [],
            "questions_to_clarify": [],
            "fact_codes": "F001"
        }"""
    )

    assert insight.day_to_day == ["编写接口并处理数据"]
    assert insight.fact_codes == ["F001"]
