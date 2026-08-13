from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.llm.schemas import JobInsight

class FactCategory(StrEnum):
    GENERAL = "general"
    EDUCATION = "education"
    PROJECT = "project"
    EXPERIENCE = "experience"
    SKILL = "skill"


class FactStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    FOLLOW_UP = "follow_up"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class TraceStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class PathlightModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ApiKeyPayload(PathlightModel):
    api_key: str = Field(min_length=12, max_length=512)


class FactRead(PathlightModel):
    id: int
    fact_code: str
    category: FactCategory
    content: str
    source_excerpt: str
    status: FactStatus

    model_config = ConfigDict(from_attributes=True)


class FactUpdate(PathlightModel):
    category: FactCategory
    content: str = Field(min_length=1, max_length=4_000)
    status: FactStatus = FactStatus.CANDIDATE


class ResumeRead(PathlightModel):
    id: int
    filename: str
    created_at: datetime
    facts: list[FactRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PreferencePayload(PathlightModel):
    role_direction: str = Field(default="", max_length=255)
    cities: str = Field(default="", max_length=255)
    salary_floor: str = Field(default="", max_length=255)
    industries: str = Field(default="", max_length=255)
    work_mode: str = Field(default="", max_length=255)
    notes: str = Field(default="", max_length=2_000)


class JdPayload(PathlightModel):
    jd_text: str = Field(min_length=10, max_length=20_000)


class ParsedJdRead(PathlightModel):
    title_hint: str
    responsibilities: list[str]
    requirements: list[str]
    keywords: list[str]
    confidence: str


class OcrRead(PathlightModel):
    text: str
    lines_detected: int = Field(ge=0)


class MatchPayload(JdPayload):
    resume_id: int = Field(gt=0)


class EvidenceRead(PathlightModel):
    fact_code: str
    content: str


class MatchedRequirementRead(PathlightModel):
    requirement: str
    evidence: list[EvidenceRead]


class FactCheckRead(PathlightModel):
    passed: bool
    risks: list[str]


class MatchRead(PathlightModel):
    jd: ParsedJdRead
    score: int = Field(ge=0, le=100)
    recommendation: str
    matched: list[MatchedRequirementRead]
    missing: list[str]
    preference_conflicts: list[str]
    reason: str
    greeting: str
    fact_check: FactCheckRead
    llm_insight: JobInsight | None = None


class ApplicationPayload(PathlightModel):
    company: str = Field(min_length=1, max_length=255)
    position: str = Field(min_length=1, max_length=255)
    jd_link: str = Field(default="", max_length=1_024)
    resume_version: str = Field(default="", max_length=255)
    greeting: str = Field(default="", max_length=4_000)
    status: ApplicationStatus = ApplicationStatus.DRAFT
    notes: str = Field(default="", max_length=2_000)

    @field_validator("jd_link")
    @classmethod
    def validate_jd_link(cls, value: str) -> str:
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("JD link must start with http:// or https://")
        return value


class ApplicationRead(ApplicationPayload):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TraceRead(PathlightModel):
    run_id: str
    task_type: str
    status: TraceStatus
    summary: str
    created_at: datetime


class DashboardRead(PathlightModel):
    resumes_total: int
    facts_confirmed: int
    applications_total: int
    follow_up_total: int
    recent_trace: list[TraceRead]


class SavedResponse(PathlightModel):
    saved: bool = True
