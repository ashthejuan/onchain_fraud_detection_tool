# Demo dataset

One-shot synthetic CSV for live demos and evaluator walkthroughs.

1. Seed flagged wallets: `PYTHONPATH=backend python backend/scripts/seed_wallets.py`
2. Import this file via the dashboard or `POST /api/v1/transactions/ingest`
3. Expected outcomes: `EXPECTED.md` (parent folder) and `docs/DEMO.md`

Seed wallets **before** ingest so `flagged_wallet_exposure` can fire on the demo addresses.
