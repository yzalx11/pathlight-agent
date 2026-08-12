import re


def parse_jd(jd_text: str) -> dict:
    lines = [line.strip(" -•\t") for line in jd_text.splitlines() if line.strip()]
    keywords = _keywords(jd_text)
    return {
        "title_hint": lines[0][:80] if lines else "",
        "responsibilities": lines[:6],
        "requirements": [
            line for line in lines if any(token in line for token in ["要求", "熟悉", "经验", "能力", "优先"])
        ][:8],
        "keywords": keywords,
        "confidence": "high" if len(lines) >= 6 else "medium" if len(lines) >= 3 else "low",
    }


def match_resume_to_jd(facts: list, jd_text: str, preference: object | None = None) -> dict:
    parsed = parse_jd(jd_text)
    jd_lower = jd_text.lower()
    matched = []
    missing = []

    for keyword in parsed["keywords"]:
        linked = [
            {"fact_code": fact.fact_code, "content": fact.content}
            for fact in facts
            if keyword.lower() in fact.content.lower()
        ]
        if linked:
            matched.append({"requirement": keyword, "evidence": linked[:3]})
        else:
            missing.append(keyword)

    score = 0 if not parsed["keywords"] else round(len(matched) / len(parsed["keywords"]) * 100)
    recommendation = _recommendation(score)
    preference_conflicts = _preference_conflicts(jd_lower, preference)
    if preference_conflicts and recommendation == "建议投递":
        recommendation = "谨慎投递"

    return {
        "jd": parsed,
        "score": score,
        "recommendation": recommendation,
        "matched": matched,
        "missing": missing,
        "preference_conflicts": preference_conflicts,
        "reason": _reason(score, missing, jd_lower, preference_conflicts),
    }


def draft_greeting(match_result: dict) -> str:
    evidence = []
    for item in match_result.get("matched", [])[:3]:
        fact_code = item["evidence"][0]["fact_code"]
        evidence.append(f"{item['requirement']}（{fact_code}）")
    evidence_text = "、".join(evidence) or "已确认的相关经历"
    return (
        "您好，我对这个岗位很感兴趣。结合 JD，我可重点说明的相关经历是"
        f"{evidence_text}。期待进一步了解团队的业务场景，并按岗位要求提供更贴合的简历版本。"
    )


def fact_check_draft(draft: str, fact_codes: set[str]) -> dict:
    referenced = set(re.findall(r"F\d{3}", draft))
    unknown = sorted(referenced - fact_codes)
    risks = []
    if not referenced:
        risks.append("草稿没有引用事实 ID，经历性表述需要补充证据。")
    if unknown:
        risks.append(f"草稿引用了不存在的事实 ID：{', '.join(unknown)}。")
    if any(word in draft for word in ["主导", "企业级", "提升", "第一", "精通"]):
        risks.append("草稿包含强表述，请确认是否有事实证据支撑。")
    return {"passed": not risks, "risks": risks}


def _recommendation(score: int) -> str:
    if score >= 65:
        return "建议投递"
    if score >= 35:
        return "谨慎投递"
    return "不建议投递"


def _preference_conflicts(jd_lower: str, preference: object | None) -> list[str]:
    if preference is None:
        return []
    conflicts = []
    cities = [city.strip().lower() for city in getattr(preference, "cities", "").split("/") if city.strip()]
    if cities and not any(city in jd_lower for city in cities) and "远程" not in jd_lower:
        conflicts.append("JD 未体现已保存的目标城市或远程安排。")
    work_mode = getattr(preference, "work_mode", "").lower()
    if "远程" in work_mode and "远程" not in jd_lower:
        conflicts.append("偏好远程工作，但 JD 未明确支持远程。")
    return conflicts


def _keywords(text: str) -> list[str]:
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9+#.]{1,20}|[\u4e00-\u9fff]{2,8}", text)
    stop_words = {"岗位", "职责", "要求", "负责", "熟悉", "优先", "经验", "能力", "我们", "相关"}
    seen: set[str] = set()
    result: list[str] = []
    for item in candidates:
        normalized = item.strip()
        if normalized in stop_words or normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        result.append(normalized)
    return result[:12]


def _reason(score: int, missing: list[str], jd_lower: str, conflicts: list[str]) -> str:
    if conflicts:
        return f"技能匹配度为 {score}%，但存在偏好冲突：{conflicts[0]}"
    if score >= 65:
        return "已确认的简历事实与 JD 关键词有较多交集，可以围绕证据点准备定制话术。"
    if score >= 35:
        return "存在部分匹配，但仍有明显缺口，建议投递前补强简历表达或准备解释。"
    if "实习" in jd_lower or "校招" in jd_lower:
        return "当前事实档案可匹配信息偏少，若岗位门槛合适可谨慎尝试。"
    return f"关键要求缺口较多：{', '.join(missing[:5])}。"
