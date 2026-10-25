import ssl

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import InvestigationReport, RiskAssessment
from app.services import investigation as investigation_service
from tests.helpers import csv_payload


def _ingest_large(client: TestClient) -> dict:
    client.post(
        "/api/v1/transactions/ingest",
        files={
            "file": (
                "large.csv",
                csv_payload("1,0xlarge,0xsender,0xreceiver,150,ETH,2026-01-01T00:00:00Z,success,100"),
                "text/csv",
            )
        },
    )
    return client.get("/api/v1/alerts").json()["items"][0]


def test_investigation_report_uses_validated_evidence_and_reuses_completed_report(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    alert = _ingest_large(client)
    calls: list[object] = []

    def fake_generate(evidence: dict[str, object]) -> dict[str, object]:
        calls.append(evidence)
        return {
            "model": "test",
            "report": {
                "summary": "Large transfer observed.",
                "evidence": [
                    {
                        "evidence_id": "transaction_1",
                        "observation": "A 150 ETH transfer occurred.",
                        "interpretation": "This is a large transfer.",
                    }
                ],
                "recommended_checks": ["Review recipient history."],
                "limitations": ["Fraud is not established."],
            },
        }

    monkeypatch.setattr(investigation_service, "generate_report", fake_generate)
    first = client.post(f"/api/v1/assessments/{alert['id']}/investigation-report", json={})
    second = client.post(f"/api/v1/assessments/{alert['id']}/investigation-report", json={})

    assert first.status_code == 200
    assert first.json()["status"] == "completed"
    assert first.json()["report"]["summary"] == "Large transfer observed."
    assert second.json()["report_id"] == first.json()["report_id"]
    assert len(calls) == 1

    snapshot = first.json()
    fetched = client.get(f"/api/v1/reports/{snapshot['report_id']}")
    assert fetched.status_code == 200
    with app.state.testing_sessionmaker() as session:
        row = session.get(InvestigationReport, snapshot["report_id"])
        assert row is not None
        assert "items" in row.evidence_snapshot
        assert any(item["evidence_id"] == "assessment" for item in row.evidence_snapshot["items"])
        assert any(item["evidence_id"] == "transaction_1" for item in row.evidence_snapshot["items"])


def test_investigation_report_regenerate_creates_new_completed_report(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    alert = _ingest_large(client)
    versions = iter(["first", "second"])

    def fake_generate(evidence: dict[str, object]) -> dict[str, object]:
        label = next(versions)
        return {
            "model": "test",
            "report": {
                "summary": label,
                "evidence": [
                    {
                        "evidence_id": "transaction_1",
                        "observation": "obs",
                        "interpretation": "interp",
                    }
                ],
                "recommended_checks": [],
                "limitations": [],
            },
        }

    monkeypatch.setattr(investigation_service, "generate_report", fake_generate)
    first = client.post(f"/api/v1/assessments/{alert['id']}/investigation-report", json={})
    regenerated = client.post(
        f"/api/v1/assessments/{alert['id']}/investigation-report",
        json={"regenerate": True},
    )

    assert first.json()["report"]["summary"] == "first"
    assert regenerated.json()["report"]["summary"] == "second"
    assert regenerated.json()["report_id"] != first.json()["report_id"]


def test_investigation_report_rejects_unknown_evidence_id_and_keeps_assessment(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    alert = _ingest_large(client)
    monkeypatch.setattr(
        investigation_service,
        "generate_report",
        lambda evidence: {
            "model": "test",
            "report": {
                "summary": "Claim.",
                "evidence": [{"evidence_id": "made_up", "observation": "x", "interpretation": "y"}],
                "recommended_checks": [],
                "limitations": [],
            },
        },
    )

    response = client.post(f"/api/v1/assessments/{alert['id']}/investigation-report", json={})

    assert response.status_code == 502
    with app.state.testing_sessionmaker() as session:
        assessment = session.get(RiskAssessment, alert["id"])
        assert assessment is not None
        assert assessment.risk_score == 25
        failed = session.scalars(
            select(InvestigationReport).where(
                InvestigationReport.assessment_id == alert["id"],
                InvestigationReport.status == "failed",
            )
        ).all()
        assert len(failed) == 1
        assert failed[0].error_message


def test_provider_error_marks_failed_report_without_changing_assessment(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    alert = _ingest_large(client)

    def boom(_evidence: dict[str, object]) -> dict[str, object]:
        from fastapi import HTTPException

        raise HTTPException(status_code=502, detail="LLM provider failed or returned an invalid response")

    monkeypatch.setattr(investigation_service, "generate_report", boom)
    response = client.post(f"/api/v1/assessments/{alert['id']}/investigation-report", json={})
    assert response.status_code == 502

    with app.state.testing_sessionmaker() as session:
        assessment = session.get(RiskAssessment, alert["id"])
        assert assessment is not None
        assert assessment.risk_score == 25
        assert assessment.severity == "medium"
        failed = session.scalar(
            select(InvestigationReport).where(InvestigationReport.assessment_id == alert["id"])
        )
        assert failed is not None
        assert failed.status == "failed"


def test_mock_provider_path_completes_without_network(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    alert = _ingest_large(client)
    monkeypatch.setattr(investigation_service.settings, "llm_provider", "mock")
    response = client.post(f"/api/v1/assessments/{alert['id']}/investigation-report", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["report"]["summary"]


def test_provider_ssl_context_verifies_nvidia_tls_certificate() -> None:
    context = investigation_service.provider_ssl_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
