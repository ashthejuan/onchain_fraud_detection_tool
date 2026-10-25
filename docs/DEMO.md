# Demo script (≈10 minutes)

End-to-end path: ingest → alert → report → reuse/regenerate → review status → state limitations.

## 0. Prerequisites

```bash
# Backend (repo root)
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.example .env
# For offline demo without NVIDIA key:
#   set LLM_PROVIDER=mock in .env
python -m alembic -c backend/alembic.ini upgrade head
PYTHONPATH=backend python backend/scripts/seed_wallets.py
uvicorn --app-dir backend app.main:app --reload
```

```bash
# Frontend (second terminal)
cd frontend && npm install && cp .env.example .env.local && npm run dev
```

Open `http://localhost:3000`. API docs: `http://127.0.0.1:8000/docs`.

## 1. Import the demo CSV

Upload `data/samples/demo/demo_transactions.csv` from the overview, or:

```bash
curl -F 'file=@data/samples/demo/demo_transactions.csv' \
  http://127.0.0.1:8000/api/v1/transactions/ingest
```

Expect ~20 accepted rows on a clean DB (0 accepted / 20 duplicates on re-import).

## 2. Ordinary activity

Open Transactions and find `0xordinary` — score **0**, severity **low**. Point out that not every transfer becomes an alert of interest.

## 3. Walk a high / critical alert

Open Alerts, sort/filter to high score. Prefer:

| Hash | Why it matters |
|------|----------------|
| `0xlarge-e2e` | Single `large_transfer` (25, medium) |
| `0xforward` | `rapid_fund_movement` after `0xreceive` |
| `0xoverlap` | Legitimate-looking business + flagged counterparty (65, high) — false-positive teaching moment |
| `0xcap-5` | Multiple rules; score capped at **100**, critical |

On alert detail, show triggered rules and observations.

## 4. Generate an investigation report

From a medium/high alert, generate the AI report. Call out:

- Evidence IDs in the report match the stored snapshot
- Disclaimer: investigative aid, not proof of fraud
- Footer / UI messaging reinforces risk-indicator language

## 5. Reuse vs regenerate

Request the report again without regenerate — same `report_id`. Then regenerate — new row, prior history retained.

## 6. Review status

Mark one alert `false_positive` or `resolved`. Filter the alert list by that status.

## 7. Closing line for evaluators

> Alerts are deterministic risk indicators on synthetic data. LLM text is bounded by backend evidence and still requires human judgment. This does not claim real-world fraud detection accuracy.

Cheat sheet: `data/samples/EXPECTED.md`.
