"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { Page, Transaction } from "@/lib/types";
import { PageHeading, Pagination, StateMessage, TransactionRows } from "@/components/UI";

const LIMIT = 25;

export default function TransactionsPage() {
  const [page, setPage] = useState<Page<Transaction> | null>(null);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try { setPage(await api.transactions({ limit: LIMIT, offset, search: query || undefined, status: status || undefined })); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load transactions."); }
    finally { setLoading(false); }
  }, [offset, query, status]);

  // This loader updates React state only after its asynchronous API call settles.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  function beginLoad() { setLoading(true); setError(""); }
  function changeOffset(value: number) { beginLoad(); setOffset(value); }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); beginLoad(); setOffset(0); setQuery(search.trim());
  }

  return <>
    <PageHeading eyebrow="Workspace / Transactions" title="Transactions" description="Search transaction hashes and wallet addresses across the imported dataset." />
    <section className="content-section list-section">
      <div className="filter-toolbar">
        <form className="search-form" onSubmit={submitSearch}><label className="sr-only" htmlFor="transaction-search">Search hash or wallet</label><input id="transaction-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search hash or wallet" /><button className="button button-secondary button-small">Search</button></form>
        <label className="filter-select">Status<select value={status} onChange={(event) => { beginLoad(); setOffset(0); setStatus(event.target.value); }}><option value="">All statuses</option><option value="success">Success</option><option value="failed">Failed</option><option value="pending">Pending</option></select></label>
      </div>
      <StateMessage loading={loading} error={error} empty={!loading && !error && !!page && page.items.length === 0} onRetry={() => { beginLoad(); void load(); }}>No transactions match these search and filter settings.</StateMessage>
      {!loading && !error && page && page.items.length > 0 && <><TransactionRows items={page.items} /><Pagination total={page.total} limit={page.limit} offset={page.offset} onChange={changeOffset} /></>}
    </section>
  </>;
}
