# On-Chain Fraud Detection & AI Investigation Platform

Phases 1 and 2 provide a FastAPI service backed by SQLite for importing transactions, scoring them with deterministic rules, and reviewing risk alerts.

## Requirements

- Python 3.11 or newer
- `pip`

## Run locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.example .env
python -m alembic -c backend/alembic.ini upgrade head
PYTHONPATH=backend python backend/scripts/seed_wallets.py
uvicorn --app-dir backend app.main:app --reload
```

The SQLite database is created at `data/app.db`. The migration command must run before importing transactions. Interactive API documentation is available at `http://127.0.0.1:8000/docs`; health check is `http://127.0.0.1:8000/health`.

## Import the sample data

```bash
curl -F 'file=@data/samples/baseline_transactions.csv' \
  http://127.0.0.1:8000/api/v1/transactions/ingest
curl 'http://127.0.0.1:8000/api/v1/transactions?limit=50'
```

The import response reports accepted, rejected, and duplicate rows. Invalid rows include a CSV line number and a validation reason. Re-importing the sample is safe: its existing `(chain_id, tx_hash)` records are counted as duplicates.

## Transaction API

- `POST /api/v1/transactions/ingest` — multipart upload with a `file` CSV field.
- `GET /api/v1/transactions` — paginated list; supports `chain_id`, `address`, `status`, `from_timestamp`, and `to_timestamp` filters, plus `limit` and `offset`.
- `GET /api/v1/transactions/{tx_hash}?chain_id=1` — transaction detail. `chain_id` is optional unless the same hash exists on multiple chains.

CSV columns required: `chain_id`, `tx_hash`, `from_address`, `to_address`, `amount`, `asset_symbol`, `timestamp`, and `status`. `block_number` is optional. Status values are `success`, `failed`, or `pending`. Timestamps should be ISO 8601; timezone-free values are interpreted as UTC. EVM-style `0x` hashes and addresses are lowercased for consistent deduplication and lookup. Uploads are limited to 10 MiB.

Flagged wallets for later detection rules are in `data/samples/flagged_wallets.csv`. The seed script is idempotent and requires the migration to have run.

## Risk detection API

Newly accepted transactions are assessed during CSV ingestion. Assessments are append-only and use `ruleset-v1`: large transfers (≥100 units), five successful outgoing transfers in 10 minutes, forwarding after a receipt within 30 minutes, exposure to a locally flagged wallet, and three failed outgoing transfers in 10 minutes. Weights are summed and capped at 100; overlapping triggers can contribute together. Assessment rules and their evidence references are persisted with the transaction.

- `GET /api/v1/alerts` — filter by `severity`, `min_score`, `max_score`, `review_status`, or hash/address `search`; sorted highest score first. Supports `limit` and `offset`.
- `GET /api/v1/assessments/{id}` — assessment, triggered rules, and transaction summary.

Seed the flagged wallet list before importing the synthetic detection scenarios. Expected hits are documented in `data/samples/EXPECTED.md`.

## LLM investigation reports

Phase 3 adds `POST /api/v1/assessments/{id}/investigation-report` and `GET /api/v1/reports/{id}`. The POST request accepts `{"regenerate": false}`; completed reports are reused unless regeneration is requested. Evidence is assembled from the stored assessment, transaction, related wallet activity, and local wallet flags. Model output is schema-validated and citations to evidence IDs are checked before it is saved.

Copy `backend/.env.example` to the repository-root `.env`, then set `LLM_API_KEY` to your NVIDIA API key. The default `LLM_BASE_URL` is NVIDIA NIM's OpenAI-compatible endpoint and `LLM_MODEL` is an NVIDIA-hosted model identifier; change the model if needed for your NIM account. Apply the new migration before calling the endpoint:

```bash
python -m alembic -c backend/alembic.ini upgrade head
curl -X POST http://127.0.0.1:8000/api/v1/assessments/1/investigation-report \
  -H 'Content-Type: application/json' -d '{"regenerate": false}'
```

Reports are investigative aids. Their findings do not establish fraud.

## Tests

From the repository root:

```bash
PYTHONPATH=backend python3 -m pytest backend/tests
```
