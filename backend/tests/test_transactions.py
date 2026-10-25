from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Wallet


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(engine)

    def override_get_db() -> Iterator[Session]:
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.state.testing_sessionmaker = TestingSession
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    del app.state.testing_sessionmaker
    Base.metadata.drop_all(engine)
    engine.dispose()


def _csv(*rows: str) -> str:
    return "chain_id,tx_hash,from_address,to_address,amount,asset_symbol,timestamp,status,block_number\n" + "\n".join(rows)


def test_ingest_valid_invalid_and_duplicate_rows_with_normalized_addresses(client: TestClient) -> None:
    payload = _csv(
        "1,0xAbC,0xSENDER,0xRECIPIENT,1.25,ETH,2026-01-01T00:00:00Z,success,100",
        "1,0xabc,0xSENDER,0xRECIPIENT,1.25,ETH,2026-01-01T00:00:00Z,success,100",
        "1,0xBad,0xSENDER,0xRECIPIENT,not-a-number,ETH,2026-01-01T00:00:00Z,success,101",
    )
    response = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", payload, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["accepted"] == 1
    assert response.json()["duplicates"] == 1
    assert response.json()["rejected"] == 1
    assert "row" in response.json()["errors"][0]

    listed = client.get("/api/v1/transactions?chain_id=1&address=0xsender")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["from_address"] == "0xsender"
    assert listed.json()["items"][0]["to_address"] == "0xrecipient"
    assert listed.json()["items"][0]["tx_hash"] == "0xabc"

    detail = client.get("/api/v1/transactions/0xABC?chain_id=1")
    assert detail.status_code == 200
    assert detail.json()["amount"] == "1.250000000000000000"


def test_ingest_rejects_missing_required_csv_header(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("bad.csv", "tx_hash,amount\n0xabc,1", "text/csv")},
    )

    assert response.status_code == 422
    assert "missing required columns" in response.json()["detail"].lower()


def test_transaction_list_filters_status_and_timestamp(client: TestClient) -> None:
    payload = _csv(
        "1,0xone,0xaaa,0xbbb,1,ETH,2026-01-01T00:00:00Z,success,100",
        "1,0xtwo,0xccc,0xddd,2,ETH,2026-01-03T00:00:00Z,failed,101",
    )
    client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", payload, "text/csv")},
    )

    response = client.get(
        "/api/v1/transactions?status=success&from_timestamp=2026-01-01T00:00:00Z&to_timestamp=2026-01-02T00:00:00Z"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["tx_hash"] == "0xone"


def test_transaction_detail_requires_chain_when_hash_is_ambiguous(client: TestClient) -> None:
    payload = _csv(
        "1,0xshared,0xaaa,0xbbb,1,ETH,2026-01-01T00:00:00Z,success,100",
        "10,0xshared,0xccc,0xddd,2,ETH,2026-01-03T00:00:00Z,success,101",
    )
    client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", payload, "text/csv")},
    )

    response = client.get("/api/v1/transactions/0xshared")

    assert response.status_code == 409


def test_ingest_assesses_transaction_and_exposes_alert_detail(client: TestClient) -> None:
    client.post(
        "/api/v1/transactions/ingest",
        files={
            "file": (
                "large.csv",
                _csv("1,0xlarge,0xsender,0xreceiver,150,ETH,2026-01-01T00:00:00Z,success,100"),
                "text/csv",
            )
        },
    )

    alerts = client.get("/api/v1/alerts?severity=medium")

    assert alerts.status_code == 200
    assert alerts.json()["total"] == 1
    alert = alerts.json()["items"][0]
    assert alert["transaction"]["tx_hash"] == "0xlarge"
    assert alert["risk_score"] == 25
    assert alert["severity"] == "medium"
    assert [rule["rule_id"] for rule in alert["triggered_rules"]] == ["large_transfer"]

    detail = client.get(f"/api/v1/assessments/{alert['id']}")
    assert detail.status_code == 200
    assert detail.json()["transaction"]["tx_hash"] == "0xlarge"
    assert detail.json()["ruleset_version"] == "ruleset-v1"


def test_phase_two_rules_work_through_ingest_and_alerts(client: TestClient) -> None:
    with app.state.testing_sessionmaker() as session:
        session.add(Wallet(chain_id=1, address="0x9999999999999999999999999999999999999999", is_flagged=True))
        session.commit()

    scenario_path = Path(__file__).resolve().parents[2] / "data/samples/scenarios/phase2_rules.csv"
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
