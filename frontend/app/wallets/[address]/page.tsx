"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Assessment, Page, Transaction, WalletRecord } from "@/lib/types";
import { AlertRows, Identifier, PageHeading, StateMessage, TransactionRows } from "@/components/UI";

export default function WalletPage() {
  const params = useParams<{ address: string }>();
  const [chainId, setChainId] = useState<number | null>(null);
  const [wallet, setWallet] = useState<WalletRecord | null>(null);
  const [transactions, setTransactions] = useState<Page<Transaction> | null>(null);
  const [alerts, setAlerts] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const chain = Number(new URLSearchParams(window.location.search).get("chain_id")) || 1;
      const [record, txPage, alertPage] = await Promise.all([
        api.wallet(params.address, chain), api.transactions({ address: params.address, chain_id: chain, limit: 25 }), api.alerts({ search: params.address, limit: 25 }),
      ]);
      setChainId(chain); setWallet(record); setTransactions(txPage);
      setAlerts(alertPage.items.filter((alert) => alert.transaction.chain_id === chain && (alert.transaction.from_address.toLowerCase() === params.address.toLowerCase() || alert.transaction.to_address?.toLowerCase() === params.address.toLowerCase())));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load this wallet."); }
    finally { setLoading(false); }
  }, [params.address]);

  // This loader updates React state only after its asynchronous API calls settle.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  function retry() { setLoading(true); setError(""); void load(); }

  return <>
    <PageHeading eyebrow="Workspace / Wallets / Detail" title="Wallet activity" description="Transaction history and locally recorded risk flags for this address." action={<Link className="button button-secondary" href="/transactions">Transactions</Link>} />
    <StateMessage loading={loading} error={error} onRetry={retry} />
    {!loading && chainId !== null && <>
      <section className="detail-summary wallet-summary"><div className="wallet-address"><span>Wallet address · Chain {chainId}</span><Identifier value={params.address} /><button className="text-button" onClick={() => void navigator.clipboard.writeText(params.address)}>Copy address</button></div><div className="wallet-flag">{wallet?.is_flagged ? <><span className="severity severity-high">Locally flagged</span><p>{wallet.flag_reason || "Recorded in the local wallet registry; no reason was provided."}</p></> : <><span className="review review-resolved">No local flag recorded</span><p>This only reflects the project’s local wallet registry.</p></>}</div></section>
      <section className="content-section"><div className="section-heading"><div><h2>Related alerts</h2><p>Assessments involving this address on chain {chainId}.</p></div></div>{alerts.length ? <AlertRows items={alerts} /> : <div className="empty-panel">No related assessments were found.</div>}</section>
      <section className="content-section"><div className="section-heading"><div><h2>Transaction history</h2><p>{transactions?.total ?? 0} matching transactions · newest first</p></div></div>{transactions?.items.length ? <TransactionRows items={transactions.items} /> : <div className="empty-panel">No transactions were found for this wallet on chain {chainId}.</div>}</section>
    </>}
  </>;
}
