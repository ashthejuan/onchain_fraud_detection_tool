# On-Chain Fraud Detection & AI Investigation Platform

College MVP: import CSV transactions, score them with deterministic rules, review alerts in a Next.js dashboard, and optionally generate evidence-grounded LLM investigation reports.

**Alerts are risk indicators for human review — not proof of fraud.**

## Requirements

- Python 3.11+
- Node.js 20+ (frontend)
- Optional: NVIDIA NIM API key for live LLM reports (`LLM_PROVIDER=mock` works offline)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.example .env
# Offline demo/CI: set LLM_PROVIDER=mock in .env
python -m alembic -c backend/alembic.ini upgrade head
PYTHONPATH=backend python backend/scripts/seed_wallets.py
uvicorn --app-dir backend app.main:app --reload
```

SQLite DB: `data/app.db`. API docs: `http://127.0.0.1:8000/docs`. Health: `http://127.0.0.1:8000/health`.

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. Ensure `CORS_ORIGINS` includes the frontend origin (default `http://localhost:3000`).

## Demo in one shot

See **`docs/DEMO.md`**. Seed wallets, then import `data/samples/demo/demo_transactions.csv`. Expected hits: `data/samples/EXPECTED.md`.

```bash
curl -F 'file=@data/samples/demo/demo_transactions.csv' \
  http://127.0.0.1:8000/api/v1/transactions/ingest
```

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/transactions/ingest` | CSV upload |
| `GET` | `/api/v1/transactions` | List / filter |
| `GET` | `/api/v1/transactions/{tx_hash}` | Detail |
| `GET` | `/api/v1/alerts` | Risk queue |
| `GET` | `/api/v1/assessments/{id}` | Assessment detail |
| `PATCH` | `/api/v1/alerts/{id}` | Review status |
| `POST` | `/api/v1/assessments/{id}/investigation-report` | Generate / reuse report |
| `GET` | `/api/v1/reports/{id}` | Fetch report |
| `GET` | `/api/v1/wallets/{address}` | Local flag record |

CSV columns: `chain_id`, `tx_hash`, `from_address`, `to_address`, `amount`, `asset_symbol`, `timestamp`, `status` (`success`\|`failed`\|`pending`); `block_number` optional. Unique key: `(chain_id, tx_hash)`.

## Detection (`ruleset-v1`)

| Rule | Weight |
|------|-------:|
| Large transfer (≥100 units) | 25 |
| High velocity (5 successful outs / 10 min) | 25 |
| Rapid fund movement (send after receive / 30 min) | 30 |
| Flagged wallet exposure | 40 |
| Repeated failures (3 failed outs / 10 min) | 15 |

Weights sum and cap at 100. Severity: low &lt;25, medium &lt;50, high &lt;75, else critical.

## LLM reports

Evidence is built only from DB records. Model JSON is schema-validated; unknown evidence IDs are rejected. Completed reports are reused unless `{"regenerate": true}`. Provider failures leave assessments unchanged and store a `failed` report.

```bash
# .env
LLM_PROVIDER=nvidia   # or mock
LLM_API_KEY=...
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=meta/llama-3.3-70b-instruct
```

## Tests

```bash
PYTHONPATH=backend python3 -m pytest backend/tests
```

Layout: `backend/tests/unit/` (rules, validation) and `backend/tests/integration/` (ingest, alerts, investigation, scenario CSV). CI-friendly path uses `LLM_PROVIDER=mock` or monkeypatched providers — no live key required.

## Documentation

| Doc | Contents |
|-----|----------|
| `docs/architecture.md` | Components and data flow |
| `docs/limitations.md` | Non-goals, uncertainty, mitigations |
| `docs/DEMO.md` | Step-by-step presentation script |
| `docs/evaluation.md` | Synthetic metrics (no real-world accuracy claims) |
| `context/prd.md` | Full product requirements |

## Environment examples

- Backend: `backend/.env.example` → copy to repo-root `.env`
- Frontend: `frontend/.env.example` → `frontend/.env.local` (`NEXT_PUBLIC_API_BASE_URL`)

Never commit real secrets. API keys are server-side only.
