# Limitations

This project is a **synthetic, offline-first college MVP**. It is not a production fraud system.

## Non-goals

- Live Ethereum / mempool ingestion
- Machine-learning classifiers or trained models
- Sanctions / chain-intelligence APIs
- Automatic freeze, block, or fund recovery
- Wallet deanonymization or identity resolution
- Multi-tenant auth or production hardening beyond basics

## What alerts mean

Rule hits and risk scores are **indicators for human review**. They do not establish fraud, intent, or legal liability. Overlapping rules can raise scores on legitimate-looking high-value activity (see `0xoverlap` in the demo set).

## LLM reports

- Built only from a bounded backend evidence snapshot.
- Schema and evidence-ID checks reduce hallucination of citations, but narrative text can still be wrong or incomplete.
- Provider outages leave assessments intact and persist a `failed` report row.
- Cost and latency depend on the configured host; use `LLM_PROVIDER=mock` for offline demos and CI.

## Dataset caveats

Evaluation uses seeded synthetic CSVs. Do **not** claim real-world detection accuracy from these scenarios. Metrics in `docs/evaluation.md` measure rule/scenario fit on that data only.

## Risk mitigations (summary)

| Risk | Mitigation in this MVP |
|------|------------------------|
| Hallucinated citations | Validate every `evidence_id` against the snapshot |
| Prompt injection via metadata | Prompt frames contents as untrusted data |
| Key leakage | Keys only in server env; never returned by API |
| Duplicate imports | Unique `(chain_id, tx_hash)` with duplicate counts |
| Provider failure | Persist `failed` report; assessment unchanged |
| Overclaiming accuracy | Document synthetic evaluation only |
