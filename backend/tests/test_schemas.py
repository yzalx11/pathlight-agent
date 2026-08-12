import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas import ApplicationPayload, ApplicationStatus, FactStatus, FactUpdate
from app.main import app


def test_application_payload_requires_http_link() -> None:
    with pytest.raises(ValidationError):
        ApplicationPayload(company="Pathlight", position="Engineer", jd_link="www.example.com")


def test_domain_statuses_are_constrained() -> None:
    payload = FactUpdate(category="project", content="Built a local workbench", status="confirmed")

    assert payload.status is FactStatus.CONFIRMED
    application = ApplicationPayload(company="Pathlight", position="Engineer", status="follow_up")
    assert application.status is ApplicationStatus.FOLLOW_UP


def test_validation_errors_are_json_serializable() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/applications",
        json={"company": "Pathlight", "position": "Engineer", "jd_link": "not-a-url"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Validation failed."
