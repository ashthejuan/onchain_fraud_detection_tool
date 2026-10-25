export type Severity = "low" | "medium" | "high" | "critical";
export type ReviewStatus = "open" | "investigating" | "resolved" | "false_positive";
export type TransactionStatus = "success" | "failed" | "pending";

export interface Transaction {
  id: number;
  chain_id: number;
  tx_hash: string;
  from_address: string;
  to_address: string | null;
  amount: string;
  asset_symbol: string;
  block_number: number | null;
  block_timestamp: string;
  status: TransactionStatus;
}

export interface TriggeredRule {
  rule_id: string;
  weight: number;
  observation: string;
  evidence_refs: string[];
}

export interface Assessment {
  id: number;
  transaction_id: number;
  risk_score: number;
  severity: Severity;
  triggered_rules: TriggeredRule[];
  ruleset_version: string;
  assessed_at: string;
  review_status: ReviewStatus;
  transaction: Transaction;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface IngestSummary {
  accepted: number;
  rejected: number;
  duplicates: number;
  errors: { row: number; error: string }[];
  errors_truncated: boolean;
}

export interface InvestigationReport {
  summary: string;
  evidence: { evidence_id: string; observation: string; interpretation: string }[];
  recommended_checks: string[];
  limitations: string[];
}

export interface GenerateResponse {
  report_id: number;
  assessment_id: number;
  status: "pending" | "completed" | "failed";
  report: InvestigationReport;
}

export interface WalletRecord {
  chain_id: number;
  address: string;
  is_flagged: boolean;
  flag_reason: string | null;
  created_at: string;
}
