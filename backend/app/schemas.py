from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyPayload(BaseModel):
    api_key: str = Field(min_length=1)


class FactRead(BaseModel):
    id: int
    fact_code: str
    category: str
    content: str
    source_excerpt: str
    status: str

    model_config = {"from_attributes": True}


class FactUpdate(BaseModel):
    category: str = ""
    content: str = Field(min_length=1)
    status: str = "candidate"


class ResumeRead(BaseModel):
    id: int
    filename: str
    created_at: datetime
    facts: list[FactRead] = []

    model_config = {"from_attributes": True}


class PreferencePayload(BaseModel):
    role_direction: str = ""
    cities: str = ""
    salary_floor: str = ""
    industries: str = ""
    work_mode: str = ""
    notes: str = ""


class JdPayload(BaseModel):
    jd_text: str = Field(min_length=10)


class MatchPayload(BaseModel):
    resume_id: int
    jd_text: str = Field(min_length=10)


class ApplicationPayload(BaseModel):
    company: str
    position: str
    jd_link: str = ""
    resume_version: str = ""
    greeting: str = ""
    status: str = "draft"
    notes: str = ""


class ApplicationRead(ApplicationPayload):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
