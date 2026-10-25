from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models import Wallet


def test_phase_two_rules_work_through_ingest_and_alerts(client: TestClient) -> None:
    with app.state.testing_sessionmaker() as session:
        session.add(Wallet(chain_id=1, address="0x9999999999999999999999999999999999999999", is_flagged=True))
        session.commit()

    scenario_path = Path(__file__).resolve().parents[3] / "data/samples/scenarios/phase2_rules.csv"
    scenario_lines = scenario_path.read_text(encoding="utf-8").splitlines()
    scenario_csv = "\n".join([scenario_lines[0], *reversed(scenario_lines[1:])])
    response = client.post(
        "/api/v1/transactions/ingest",
        files={"file": (scenario_path.name, scenario_csv, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["accepted"] == 20
    alerts = client.get("/api/v1/alerts?min_score=0&max_score=100&limit=200")
    assert alerts.status_code == 200
    rule_ids = {
        rule["rule_id"]
        for alert in alerts.json()["items"]
        for rule in alert["triggered_rules"]
    }
    assert rule_ids == {
        "large_transfer",
        "high_velocity",
        "rapid_fund_movement",
        "flagged_wallet_exposure",
        "repeated_failures",
    }
    ordinary = next(item for item in alerts.json()["items"] if item["transaction"]["tx_hash"] == "0xordinary")
    assert ordinary["risk_score"] == 0
    assert ordinary["severity"] == "low"
    overlap = next(item for item in alerts.json()["items"] if item["transaction"]["tx_hash"] == "0xoverlap")
    assert overlap["risk_score"] == 65
    assert overlap["severity"] == "high"
    capped = next(item for item in alerts.json()["items"] if item["transaction"]["tx_hash"] == "0xcap-5")
    assert capped["risk_score"] == 100
    assert capped["severity"] == "critical"

    duplicate = client.post(
        "/api/v1/transactions/ingest",
        files={"file": (scenario_path.name, scenario_csv, "text/csv")},
    )
    assert duplicate.json()["accepted"] == 0
    assert duplicate.json()["duplicates"] == 20
    assert client.get("/api/v1/alerts?limit=200").json()["total"] == 20
