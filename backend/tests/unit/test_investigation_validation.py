import pytest
from fastapi import HTTPException

from app.services.investigation import validate_report


def _evidence(*ids: str) -> dict[str, object]:
    return {"items": [{"evidence_id": evidence_id, "kind": "transaction"} for evidence_id in ids]}


def test_validate_report_accepts_valid_schema() -> None:
    model, report = validate_report(
        {
            "model": "test",
            "report": {
                "summary": "Observed large transfer.",
                "evidence": [
                    {
                        "evidence_id": "transaction_1",
                        "observation": "Amount exceeded threshold.",
                        "interpretation": "Worth reviewing.",
                    }
                ],
                "recommended_checks": ["Review recipient."],
                "limitations": ["Not proof of fraud."],
            },
        },
        _evidence("transaction_1", "assessment"),
    )
    assert model == "test"
    assert report["summary"].startswith("Observed")


def test_validate_report_rejects_unknown_evidence_id() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_report(
            {
                "model": "test",
                "report": {
                    "summary": "Claim.",
                    "evidence": [{"evidence_id": "made_up", "observation": "x", "interpretation": "y"}],
                    "recommended_checks": [],
                    "limitations": [],
                },
            },
            _evidence("transaction_1"),
        )
    assert exc.value.status_code == 502
    assert "unknown evidence" in exc.value.detail.lower()


def test_validate_report_rejects_malformed_and_missing_fields() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_report({"model": "test", "report": {"summary": "only"}}, _evidence("transaction_1"))
    assert exc.value.status_code == 502

    with pytest.raises(HTTPException) as exc_missing_model:
        validate_report({"report": {"summary": "x", "evidence": [], "recommended_checks": [], "limitations": []}}, _evidence())
    assert exc_missing_model.value.status_code == 502

    with pytest.raises(HTTPException) as exc_extra:
        validate_report(
            {
                "model": "test",
                "report": {
                    "summary": "x",
                    "evidence": [],
                    "recommended_checks": [],
                    "limitations": [],
                    "invented": True,
                },
            },
            _evidence(),
        )
    assert exc_extra.value.status_code == 502
