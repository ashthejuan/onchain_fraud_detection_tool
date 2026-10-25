# Synthetic scenario expectations

`scenarios/phase2_rules.csv` is synthetic API test input. Seed `flagged_wallets.csv` before ingesting it; the scenarios use its first flagged address.

| Transaction(s) | Expected rules | Expected score / note |
|---|---|---|
| `0xordinary` | none | Baseline score 0, low severity |
| `0xlarge-e2e` | `large_transfer` | 25, medium |
| `0xreceive` | none | Incoming transfer alone does not trigger rapid movement |
| `0xforward` | `rapid_fund_movement` | 30, medium |
| `0xflag` | `flagged_wallet_exposure` | 40, medium |
| `0xvelocity-1` through `-4` | none | Fewer than five outgoing transfers in the window |
| `0xvelocity-5` | `high_velocity` | 25, medium |
| `0xfailure-1` and `-2` | none | Fewer than three failed transfers in the window |
| `0xfailure-3` | `repeated_failures` | 15, low |
| `0xoverlap` | `large_transfer`, `flagged_wallet_exposure` | 65, high; legitimate-looking high-value activity may still be flagged |
| `0xcap-5` | `large_transfer`, `high_velocity`, `rapid_fund_movement`, `flagged_wallet_exposure` | Raw weight 120, capped at 100, critical |

Weights are summed for overlapping rules and capped at 100. Thresholds are inclusive for large transfers and rule counts. Velocity and failure windows are 10 minutes; rapid movement uses 30 minutes. The source transaction must precede the forwarding transaction.
