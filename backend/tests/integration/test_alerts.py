from fastapi.testclient import TestClient

from tests.helpers import csv_payload


def test_ingest_assesses_transaction_and_exposes_alert_detail(client: TestClient) -> None:
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


def test_alert_filters_and_review_status_update(client: TestClient) -> None:
    client.post(
        "/api/v1/transactions/ingest",
        files={
            "file": (
                "mix.csv",
                csv_payload(
                    "1,0xsmall,0xa,0xb,1,ETH,2026-01-01T00:00:00Z,success,1",
                    "1,0xbig,0xa,0xb,200,ETH,2026-01-01T00:01:00Z,success,2",
                ),
                "text/csv",
            )
        },
    )

    medium = client.get("/api/v1/alerts?min_score=25&max_score=50&search=0xbig")
    assert medium.status_code == 200
    assert medium.json()["total"] == 1
    alert_id = medium.json()["items"][0]["id"]

    patched = client.patch(f"/api/v1/alerts/{alert_id}", json={"review_status": "false_positive"})
    assert patched.status_code == 200
    assert patched.json()["review_status"] == "false_positive"

    filtered = client.get("/api/v1/alerts?review_status=false_positive")
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == alert_id
