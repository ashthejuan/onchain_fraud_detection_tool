from fastapi.testclient import TestClient

from tests.helpers import csv_payload


def test_ingest_valid_invalid_and_duplicate_rows_with_normalized_addresses(client: TestClient) -> None:
    payload = csv_payload(
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
    payload = csv_payload(
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
    payload = csv_payload(
        "1,0xshared,0xaaa,0xbbb,1,ETH,2026-01-01T00:00:00Z,success,100",
        "10,0xshared,0xccc,0xddd,2,ETH,2026-01-03T00:00:00Z,success,101",
    )
    client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", payload, "text/csv")},
    )

    response = client.get("/api/v1/transactions/0xshared")

    assert response.status_code == 409
