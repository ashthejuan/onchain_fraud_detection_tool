import Link from "next/link";
import type { ReactNode } from "react";
import type { Assessment, ReviewStatus, Severity, Transaction } from "@/lib/types";

export function PageHeading({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="page-heading"><div>{eyebrow && <div className="page-context">{eyebrow}</div>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <div className="heading-action">{action}</div>}</div>;
}

export function StateMessage({ loading, error, empty, children, onRetry }: { loading?: boolean; error?: string; empty?: boolean; children?: ReactNode; onRetry?: () => void }) {
  if (loading) return <div className="state-message" role="status"><span className="loader-line" />Loading records…</div>;
  if (error) return <div className="state-message state-error" role="alert"><strong>Couldn’t load this view.</strong><span>{error}</span>{onRetry && <button className="text-button" onClick={onRetry}>Retry</button>}</div>;
  if (empty) return <div className="state-message">{children || "No records match this view."}</div>;
  return null;
}

export function SeverityLabel({ severity }: { severity: Severity }) {
  return <span className={`severity severity-${severity}`}>{capitalize(severity)}</span>;
}

export function ReviewLabel({ status }: { status: ReviewStatus }) {
  const labels: Record<ReviewStatus, string> = { open: "Open", investigating: "Investigating", resolved: "Resolved", false_positive: "False positive" };
  return <span className={`review review-${status}`}>{labels[status]}</span>;
}

export function Identifier({ value, href }: { value: string; href?: string }) {
  const display = shorten(value);
  return href ? <Link className="identifier" href={href} title={value}>{display}</Link> : <span className="identifier" title={value}>{display}</span>;
}

export function AlertRows({ items }: { items: Assessment[] }) {
  return <div className="table-scroll"><table><thead><tr><th>Transaction</th><th>Amount</th><th>Risk</th><th>Triggered rules</th><th>Review</th><th>Time</th></tr></thead><tbody>{items.map((alert) => <tr key={alert.id}>
    <td><Identifier value={alert.transaction.tx_hash} href={`/alerts/${alert.id}`} /><small className="cell-sub">Chain {alert.transaction.chain_id}</small></td>
    <td className="numeric">{formatAmount(alert.transaction)}</td>
    <td><div className="risk-cell"><strong>{alert.risk_score}</strong><SeverityLabel severity={alert.severity} /></div></td>
    <td>{alert.triggered_rules.length ? <span>{alert.triggered_rules.length} {alert.triggered_rules.length === 1 ? "rule" : "rules"}</span> : <span className="muted">No rules</span>}</td>
    <td><ReviewLabel status={alert.review_status} /></td>
    <td>{formatDate(alert.transaction.block_timestamp)}</td>
  </tr>)}</tbody></table></div>;
}

export function TransactionRows({ items }: { items: Transaction[] }) {
  return <div className="table-scroll"><table><thead><tr><th>Transaction</th><th>From</th><th>To</th><th>Amount</th><th>Status</th><th>Time</th></tr></thead><tbody>{items.map((tx) => <tr key={tx.id}>
    <td><Identifier value={tx.tx_hash} href={`/transactions/${encodeURIComponent(tx.tx_hash)}?chain_id=${tx.chain_id}`} /><small className="cell-sub">Chain {tx.chain_id}</small></td>
    <td><Identifier value={tx.from_address} href={`/wallets/${encodeURIComponent(tx.from_address)}?chain_id=${tx.chain_id}`} /></td>
    <td>{tx.to_address ? <Identifier value={tx.to_address} href={`/wallets/${encodeURIComponent(tx.to_address)}?chain_id=${tx.chain_id}`} /> : <span className="muted">—</span>}</td>
    <td className="numeric">{formatAmount(tx)}</td>
    <td><span className={`tx-status tx-${tx.status}`}>{capitalize(tx.status)}</span></td>
    <td>{formatDate(tx.block_timestamp)}</td>
  </tr>)}</tbody></table></div>;
}

export function Pagination({ total, limit, offset, onChange }: { total: number; limit: number; offset: number; onChange: (offset: number) => void }) {
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + limit, total);
  return <div className="pagination"><span>{start}–{end} of {total}</span><div><button className="button button-secondary button-small" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>Previous</button><button className="button button-secondary button-small" disabled={offset + limit >= total} onClick={() => onChange(offset + limit)}>Next</button></div></div>;
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function formatAmount(tx: Transaction): string {
  const [coefficient, exponentText = "0"] = tx.amount.toLowerCase().split("e");
  const [integerPart, fractionPart = ""] = coefficient.split(".");
  const digits = `${integerPart}${fractionPart}`;
  const decimalPosition = integerPart.length + Number(exponentText);
  const expandedInteger = decimalPosition <= 0 ? "0" : decimalPosition >= digits.length ? digits + "0".repeat(decimalPosition - digits.length) : digits.slice(0, decimalPosition);
  const expandedFraction = decimalPosition <= 0 ? "0".repeat(-decimalPosition) + digits : digits.slice(decimalPosition);
  const whole = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(BigInt(expandedInteger || "0"));
  const fraction = expandedFraction.slice(0, 6).replace(/0+$/, "");
  return `${tx.amount.startsWith("-") ? "−" : ""}${whole}${fraction ? `.${fraction}` : ""} ${tx.asset_symbol}`;
}

export function shorten(value: string): string {
  if (value.length < 20) return value;
  return `${value.slice(0, 8)}…${value.slice(-6)}`;
}

export function capitalize(value: string): string {
  return value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}
