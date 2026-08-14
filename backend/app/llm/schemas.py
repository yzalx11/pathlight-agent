from pydantic import BaseModel, ConfigDict, Field


class JobInsight(BaseModel):
    """Supplementary interpretation of a job description, never a source of facts."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role_focus: str = Field(min_length=1, max_length=500)
    day_to_day: list[str] = Field(default_factory=list, max_length=5)
    risks: list[str] = Field(default_factory=list, max_length=5)
    questions_to_clarify: list[str] = Field(default_factory=list, max_length=5)
    fact_codes: list[str] = Field(default_factory=list, max_length=8)


class ReplyDraft(BaseModel):
    """A recruiter reply that can be traced back to confirmed resume facts."""

    model_config = ConfigDict(str_strip_whitespace=True)

    label: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1, max_length=1_200)
    fact_codes: list[str] = Field(default_factory=list, min_length=1, max_length=6)


class ReplyDraftSet(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    drafts: list[ReplyDraft] = Field(min_length=1, max_length=3)
    clarifying_questions: list[str] = Field(default_factory=list, max_length=3)
