"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Assessment, Severity } from "@/lib/types";
import { AlertRows, PageHeading, StateMessage } from "@/components/UI";

type Summary = { transactions: number; alerts: number; open: number; severity: Record<Severity, number>; recent: Assessment[] };
const severityOrder: Severity[] = ["critical", "high", "medium", "low"];

export default function OverviewPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [importMessage, setImportMessage] = useState("");

  const load = useCallback(async () => {
    try {
      const [transactions, all, open, ...severityPages] = await Promise.all([
        api.transactions({ limit: 1 }),
        api.alerts({ limit: 1 }),
        api.alerts({ review_status: "open", limit: 1 }),
        ...severityOrder.map((severity) => api.alerts({ severity, limit: severity === "critical" || severity === "high" ? 5 : 1 })),
      ]);
      const counts = {} as Record<Severity, number>;
      severityOrder.forEach((severity, index) => { counts[severity] = severityPages[index].total; });
      const recent = severityPages.slice(0, 2).flatMap((page) => page.items).sort((a, b) => b.risk_score - a.risk_score || b.assessed_at.localeCompare(a.assessed_at)).slice(0, 5);
      setSummary({ transactions: transactions.total, alerts: all.total, open: open.total, severity: counts, recent });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load the overview.");
    } finally {
      setLoading(false);
    }
  }, []);

  // This loader updates React state only after its asynchronous API calls settle.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  async function importCsv(file?: File) {
    if (!file) return;
    setUploading(true);
    setImportMessage("");
    try {
      const result = await api.ingest(file);
      setImportMessage(`${result.accepted} accepted · ${result.duplicates} duplicates · ${result.rejected} rejected`);
      setLoading(true); setError("");
      await load();
    } catch (cause) {
      setImportMessage(cause instanceof Error ? cause.message : "Could not import this CSV.");
    } finally {
      setUploading(false);
    }
  }

  function retry() { setLoading(true); setError(""); void load(); }

  const totalBySeverity = summary ? severityOrder.reduce((sum, severity) => sum + summary.severity[severity], 0) : 0;

  return <>
    <PageHeading eyebrow="Workspace / Overview" title="Risk overview" description="A current view of transaction activity and the alerts that need review." action={<label className="button button-primary upload-button">{uploading ? "Importing…" : "Import CSV"}<input type="file" accept=".csv,text/csv" disabled={uploading} onChange={(event) => { void importCsv(event.target.files?.[0]); event.currentTarget.value = ""; }} /></label>} />
    {importMessage && <div className="inline-notice" role="status">{importMessage}</div>}
    <StateMessage loading={loading} error={error} onRetry={retry} />
    {!loading && !error && summary && <>
      <section className="overview-lead" aria-label="Open risk queue">
        <div className="lead-copy"><span className="lead-label">Needs attention</span><div className="lead-number">{summary.open.toLocaleString()}</div><p>open alerts are waiting for an analyst review</p><Link className="button button-primary" href="/alerts">Review open alerts <span aria-hidden="true">↗</span></Link></div>
        <div className="severity-panel"><div className="section-topline"><div><h2>Risk distribution</h2><p>Current assessed transactions</p></div><span>{summary.alerts.toLocaleString()} total</span></div>
          <div className="severity-bar" aria-label={`${summary.severity.critical} critical, ${summary.severity.high} high, ${summary.severity.medium} medium, ${summary.severity.low} low`}>{severityOrder.map((severity) => <span key={severity} className={`bar-${severity}`} style={{ width: `${totalBySeverity ? (summary.severity[severity] / totalBySeverity) * 100 : 0}%` }} />)}</div>
          <div className="severity-legend">{severityOrder.map((severity) => <div key={severity}><span className={`legend-dot dot-${severity}`} />{severity}<strong>{summary.severity[severity].toLocaleString()}</strong></div>)}</div>
        </div>
      </section>

      <section className="metric-strip" aria-label="Workspace totals">
        <div><span>Transactions</span><strong>{summary.transactions.toLocaleString()}</strong></div>
        <div><span>Assessed alerts</span><strong>{summary.alerts.toLocaleString()}</strong></div>
        <div><span>Open for review</span><strong>{summary.open.toLocaleString()}</strong></div>
      </section>

      <section className="content-section">
        <div className="section-heading"><div><h2>Recent high-priority alerts</h2><p>Highest severity first, with the latest assessments shown.</p></div><Link className="text-link" href="/alerts">All alerts <span aria-hidden="true">→</span></Link></div>
        {summary.recent.length ? <AlertRows items={summary.recent} /> : <div className="empty-panel">No alerts have been assessed yet. Import a transaction CSV to begin.</div>}
      </section>
    </>}
  </>;
}
