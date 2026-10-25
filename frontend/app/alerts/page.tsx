"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { Assessment, Page, ReviewStatus, Severity } from "@/lib/types";
import { AlertRows, PageHeading, Pagination, StateMessage } from "@/components/UI";

const LIMIT = 25;
const statuses: { value: string; label: string }[] = [
  { value: "", label: "All" }, { value: "open", label: "Open" }, { value: "investigating", label: "Investigating" }, { value: "resolved", label: "Resolved" }, { value: "false_positive", label: "False positive" },
];

export default function AlertsPage() {
  const [page, setPage] = useState<Page<Assessment> | null>(null);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState<Severity | "">("");
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus | "">("");
  const [minScore, setMinScore] = useState("");
  const [maxScore, setMaxScore] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setPage(await api.alerts({ limit: LIMIT, offset, search: query || undefined, severity: severity || undefined, review_status: reviewStatus || undefined, min_score: minScore || undefined, max_score: maxScore || undefined }));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load alerts."); }
    finally { setLoading(false); }
  }, [offset, query, severity, reviewStatus, minScore, maxScore]);

  // This loader updates React state only after its asynchronous API call settles.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  function beginLoad() { setLoading(true); setError(""); }
  function changeOffset(value: number) { beginLoad(); setOffset(value); }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); beginLoad(); setOffset(0); setQuery(search.trim());
  }

  return <>
    <PageHeading eyebrow="Workspace / Alerts" title="Risk alerts" description="Prioritize flagged transactions, inspect their evidence, and record review outcomes." />
    <section className="content-section list-section">
      <div className="status-tabs" role="group" aria-label="Review status filter">{statuses.map((item) => <button key={item.value} className={reviewStatus === item.value ? "status-tab selected" : "status-tab"} aria-pressed={reviewStatus === item.value} onClick={() => { beginLoad(); setOffset(0); setReviewStatus(item.value as ReviewStatus | ""); }}>{item.label}</button>)}</div>
      <div className="filter-toolbar alert-filters">
        <form className="search-form" onSubmit={submitSearch}><label className="sr-only" htmlFor="alert-search">Search hash or wallet</label><input id="alert-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search hash or wallet" /><button className="button button-secondary button-small">Search</button></form>
        <label className="filter-select">Severity<select value={severity} onChange={(event) => { beginLoad(); setOffset(0); setSeverity(event.target.value as Severity | ""); }}><option value="">All severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label>
        <label className="filter-number">Score from<input inputMode="numeric" type="number" min="0" max="100" value={minScore} onChange={(event) => { beginLoad(); setOffset(0); setMinScore(event.target.value); }} /></label>
        <label className="filter-number">to<input inputMode="numeric" type="number" min="0" max="100" value={maxScore} onChange={(event) => { beginLoad(); setOffset(0); setMaxScore(event.target.value); }} /></label>
      </div>
      <StateMessage loading={loading} error={error} empty={!loading && !error && !!page && page.items.length === 0} onRetry={() => { beginLoad(); void load(); }}>No alerts match these search and filter settings.</StateMessage>
      {!loading && !error && page && page.items.length > 0 && <><AlertRows items={page.items} /><Pagination total={page.total} limit={page.limit} offset={page.offset} onChange={changeOffset} /></>}
    </section>
  </>;
}
