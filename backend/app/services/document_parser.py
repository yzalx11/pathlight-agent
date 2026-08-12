from pathlib import Path

import fitz
from docx import Document


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    raise ValueError("Only PDF and DOCX resumes are supported in M0.")


def build_candidate_facts(text: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    facts: list[dict[str, str]] = []
    for index, line in enumerate(lines[:20], start=1):
        category = _guess_category(line)
        facts.append(
            {
                "fact_code": f"F{index:03d}",
                "category": category,
                "content": line,
                "source_excerpt": line[:500],
                "status": "candidate",
            }
        )
    return facts


def _extract_pdf(path: Path) -> str:
    with fitz.open(path) as doc:
        return "\n".join(page.get_text() for page in doc)


def _extract_docx(path: Path) -> str:
    doc = Document(path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


def _guess_category(line: str) -> str:
    lowered = line.lower()
    if any(word in lowered for word in ["大学", "学院", "bachelor", "master"]):
        return "education"
    if any(word in lowered for word in ["项目", "project", "系统", "平台"]):
        return "project"
    if any(word in lowered for word in ["实习", "工作", "公司", "intern"]):
        return "experience"
    if any(word in lowered for word in ["python", "java", "sql", "vue", "fastapi"]):
        return "skill"
    return "general"
