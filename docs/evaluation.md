# Evaluation (synthetic only)

**Do not claim real-world fraud detection accuracy from this dataset.**

Measured against `data/samples/demo/demo_transactions.csv` (same scenarios as `scenarios/phase2_rules.csv`) after seeding `flagged_wallets.csv`.

## Seeded scenario detection

| Scenario | Expected | Result (Phase 5 run) |
|----------|----------|----------------------|
| `0xordinary` | score 0, no rules | Pass |
| `0xlarge-e2e` | `large_transfer` → 25 medium | Pass |
| `0xforward` | `rapid_fund_movement` → 30 medium | Pass |
| `0xflag` | `flagged_wallet_exposure` → 40 medium | Pass |
| `0xvelocity-5` | `high_velocity` → 25 medium | Pass |
| `0xfailure-3` | `repeated_failures` → 15 low | Pass |
| `0xoverlap` | large + flagged → 65 high | Pass |
| `0xcap-5` | multi-rule, capped 100 critical | Pass |

All five rules fire at least once on the demo set (verified by `tests/integration/test_phase2_scenarios.py`).

## “Legitimate-looking” false positives

`0xoverlap` intentionally combines a high-value transfer with a locally flagged counterparty. The system correctly raises a high score; that is a **feature for teaching review workflow**, not a claim that the wallet is fraudulent. Operators can mark `false_positive`.

## Rule-engine latency

On the 20-row demo CSV (local SQLite, Apple Silicon class laptop), ingest + assess completed in well under one second in Phase 5 smoke runs. Exact wall times vary by machine; treat this as “interactive for demo scale,” not a load test.

## LLM metrics

| Metric | Notes |
|--------|-------|
| Schema validation pass rate | 100% for `LLM_PROVIDER=mock` and for monkeypatched valid fixtures in pytest |
| Evidence-ID validation | Unknown IDs rejected (HTTP 502) with `failed` report row; covered by integration tests |
| Live provider latency | Optional / environment-dependent; not required for CI green |

Offline/CI path: set `LLM_PROVIDER=mock` so reports complete without network or API keys.
