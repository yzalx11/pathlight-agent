from types import SimpleNamespace

from app.services.jd import draft_greeting, fact_check_draft, match_resume_to_jd, parse_jd


def test_parse_jd_extracts_keywords_and_confidence() -> None:
    result = parse_jd("后端开发实习生\n负责 FastAPI 服务开发\n要求熟悉 Python 和 SQL\n有 Vue 经验优先")

    assert result["confidence"] == "medium"
    assert "FastAPI" in result["keywords"]
    assert result["requirements"]


def test_matching_uses_fact_evidence_and_preferences() -> None:
    facts = [
        SimpleNamespace(fact_code="F001", content="使用 Python 和 FastAPI 构建本地服务"),
        SimpleNamespace(fact_code="F002", content="熟悉 Vue 和 SQLite"),
    ]
    preference = SimpleNamespace(cities="上海 / 杭州", work_mode="远程")

    result = match_resume_to_jd(facts, "后端开发\n要求 Python、FastAPI、Vue\n工作地点：北京", preference)

    assert result["matched"]
    assert result["preference_conflicts"]
    greeting = draft_greeting(result)
    assert "F001" in greeting
    assert fact_check_draft(greeting, {"F001", "F002"})["passed"]
