"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Assessment, Transaction } from "@/lib/types";
import { formatAmount, formatDate, Identifier, PageHeading, SeverityLabel, StateMessage } from "@/components/UI";

export default function TransactionDetailPage() {
  const params = useParams<{ txHash: string }>();
  const [transaction, setTransaction] = useState<Transaction | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const chain = Number(new URLSearchParams(window.location.search).get("chain_id")) || undefined;
      const tx = await api.transaction(params.txHash, chain);
      setTransaction(tx);
      const matches = await api.alerts({ search: tx.tx_hash, limit: 200 });
      setAssessment(matches.items.find((item) => item.transaction.tx_hash === tx.tx_hash && item.transaction.chain_id === tx.chain_id) || null);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load this transaction."); }
    finally { setLoading(false); }
  }, [params.txHash]);

  // This loader updates React state only after its asynchronous API calls settle.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  function retry() { setLoading(true); setError(""); void load(); }

  return <>
    <PageHeading eyebrow="Workspace / Transactions / Detail" title="Transaction detail" description="Inspect the transaction record and its related risk assessment." action={<Link className="button button-secondary" href="/transactions">Back to transactions</Link>} />
    <StateMessage loading={loading} error={error} onRetry={retry} />
    {!loading && transaction && <>
      <section className="detail-summary transaction-summary"><div className="transaction-hash"><span>Transaction hash</span><Identifier value={transaction.tx_hash} /><button className="text-button" onClick={() => void navigator.clipboard.writeText(transaction.tx_hash)}>Copy hash</button></div><div className="detail-fields"><div><span>Amount</span><strong>{formatAmount(transaction)}</strong></div><div><span>Status</span><strong className={`tx-status tx-${transaction.status}`}>{transaction.status}</strong></div><div><span>Chain</span><strong>{transaction.chain_id}</strong></div><div><span>Block</span><strong>{transaction.block_number ?? "—"}</strong></div><div><span>Timestamp</span><strong>{formatDate(transaction.block_timestamp)}</strong></div></div></section>
      <section className="content-section"><div className="section-heading"><div><h2>Wallets</h2><p>Addresses are identifiers; the dataset does not establish real-world ownership.</p></div></div><div className="wallet-pair"><div><span>From</span><Identifier value={transaction.from_address} href={`/wallets/${encodeURIComponent(transaction.from_address)}?chain_id=${transaction.chain_id}`} /></div><div><span>To</span>{transaction.to_address ? <Identifier value={transaction.to_address} href={`/wallets/${encodeURIComponent(transaction.to_address)}?chain_id=${transaction.chain_id}`} /> : <span className="muted">No recipient recorded</span>}</div></div></section>
      <section className="content-section"><div className="section-heading"><div><h2>Risk assessment</h2><p>Deterministic assessment associated with this transaction.</p></div></div>{assessment ? <div className="assessment-link-row"><span className="risk-cell"><strong>{assessment.risk_score} / 100</strong><SeverityLabel severity={assessment.severity} /></span><Link className="button button-secondary" href={`/alerts/${assessment.id}`}>View alert evidence</Link></div> : <div className="empty-panel">No risk assessment is available for this transaction.</div>}</section>
    </>}
  </>;
}
