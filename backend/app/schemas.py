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


class ReplyDraftPayload(PathlightModel):
    resume_id: int = Field(gt=0)
    job_id: int = Field(gt=0)
    question: str = Field(min_length=2, max_length=2_000)


class ReplyDraftRead(PathlightModel):
    label: str
    content: str
    fact_codes: list[str]


class ReplyDraftResponse(PathlightModel):
    drafts: list[ReplyDraftRead]
    clarifying_questions: list[str] = Field(default_factory=list)


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


class JobStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    READY = "ready"
    CONTACTED = "contacted"
    WAITING = "waiting"
    READ_NO_REPLY = "read_no_reply"
    RESUME_SENT = "resume_sent"
    ASSESSMENT = "assessment"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class JobPayload(PathlightModel):
    company: str = Field(default="", max_length=255)
    title: str = Field(default="", max_length=255)
    city: str = Field(default="", max_length=128)
    salary: str = Field(default="", max_length=128)
    experience: str = Field(default="", max_length=128)
    education: str = Field(default="", max_length=128)
    source_link: str = Field(default="", max_length=1_024)
    status: JobStatus = JobStatus.PENDING_REVIEW
    next_action_at: datetime | None = None
    notes: str = Field(default="", max_length=2_000)
    jd_text: str = Field(default="", max_length=20_000)

    @field_validator("source_link")
    @classmethod
    def validate_source_link(cls, value: str) -> str:
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("Source link must start with http:// or https://")
        return value


class JobScreenshotRead(PathlightModel):
    id: int
    filename: str
    ocr_text: str

    model_config = ConfigDict(from_attributes=True)


class JobRead(JobPayload):
    id: int
    source: str
    ocr_text: str
    created_at: datetime
    updated_at: datetime
    screenshots: list[JobScreenshotRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BrowserJobPreviewPayload(PathlightModel):
    page_title: str = Field(min_length=1, max_length=255)
    source_link: str = Field(min_length=1, max_length=1_024)
    visible_text: str = Field(min_length=30, max_length=30_000)

    @field_validator("source_link")
    @classmethod
    def validate_browser_source_link(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("Source link must start with http:// or https://")
        return value


class BrowserJobPreviewRead(PathlightModel):
    title: str
    company: str
    city: str
    salary: str
    experience: str
    education: str
    source_link: str
    jd_excerpt: str


class BrowserJobImportPayload(BrowserJobPreviewPayload):
    company: str = Field(default="", max_length=255)
    title: str = Field(default="", max_length=255)
    city: str = Field(default="", max_length=128)
    salary: str = Field(default="", max_length=128)
    experience: str = Field(default="", max_length=128)
    education: str = Field(default="", max_length=128)


class BrowserImportStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


class BrowserSessionRead(PathlightModel):
    chrome_running: bool
    cdp_available: bool
    observing: bool = False
    message: str = ""


class BrowserScanRead(PathlightModel):
    status: str
    import_id: int | None = None
    message: str = ""


class BrowserImportRead(PathlightModel):
    id: int
    page_title: str
    source_link: str
    visible_text: str
    company: str
    title: str
    city: str
    salary: str
    experience: str
    education: str
    status: BrowserImportStatus
    captured_at: datetime

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
    action_items: list["ActionItemRead"] = Field(default_factory=list)
    recent_trace: list[TraceRead]


class ActionItemRead(PathlightModel):
    job_id: int
    title: str
    company: str
    status: JobStatus
    action: str
    next_action_at: datetime | None = None


class SavedResponse(PathlightModel):
    saved: bool = True
