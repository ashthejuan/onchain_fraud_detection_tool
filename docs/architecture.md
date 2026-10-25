# Architecture

College MVP that turns CSV blockchain transactions into deterministic risk alerts and optional LLM investigation reports.

## Components

```
Next.js UI  ──REST /api/v1/*──►  FastAPI
                                  ├─ CSV ingest + normalize/dedupe
                                  ├─ ruleset-v1 scoring
                                  ├─ evidence builder
                                  └─ LLM client + schema/evidence validation
                                         │
                                         ▼
                                      SQLite
                           transactions · wallets ·
                     risk_assessments · investigation_reports
```

| Layer | Responsibility |
|-------|----------------|
| Ingestion | Validate CSV rows, normalize EVM addresses/hashes, unique on `(chain_id, tx_hash)`, assess each accepted row |
| Rule engine | Five deterministic rules; weights summed and capped at 100; severity bands Low/Medium/High/Critical |
| Assessments | Append-only rows with triggered rule evidence; review status for analyst workflow |
| Investigation | Evidence snapshot from DB only; LLM JSON validated; unknown evidence IDs rejected; completed reports reused unless `regenerate` |
| Dashboard | Overview, transactions, alerts, report view, wallet flag provenance |

## Data flow (happy path)

1. Operator seeds local flagged wallets and uploads a CSV.
2. Backend stores transactions and writes a risk assessment per accepted row.
3. Dashboard lists alerts sorted by score; detail shows triggered rules.
4. Operator requests an investigation report; backend builds an evidence package, calls the LLM (or `LLM_PROVIDER=mock`), validates output, and persists the report with the exact snapshot used.
5. Re-request returns the completed report; `regenerate: true` creates a new row.

## Safety conventions

- Alerts are **risk indicators**, not proof of fraud.
- API keys stay in server env; the frontend only talks to `/api/v1/*`.
- Transaction metadata in prompts is treated as untrusted data.
- Indexes exist on chain, wallet addresses, timestamps, and common alert filters.

## Related docs

- Limitations: `docs/limitations.md`
- Demo script: `docs/DEMO.md`
- Evaluation notes: `docs/evaluation.md`
- Product requirements: `context/prd.md`
