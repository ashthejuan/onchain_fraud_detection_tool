"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Assessment, ReviewStatus } from "@/lib/types";
import { formatAmount, formatDate, Identifier, PageHeading, ReviewLabel, SeverityLabel, StateMessage } from "@/components/UI";

const reviewOptions: { value: ReviewStatus; label: string }[] = [
  { value: "open", label: "Open" }, { value: "investigating", label: "Investigating" }, { value: "resolved", label: "Resolved" }, { value: "false_positive", label: "False positive" },
];

export default function AlertDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = Number(params.id);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const load = useCallback(async () => {
    try { setAssessment(await api.assessment(id)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load this alert."); }
    finally { setLoading(false); }
  }, [id]);

  // This loader updates React state only after its asynchronous API call settles.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  function retry() { setLoading(true); setError(""); void load(); }

  async function setStatus(status: ReviewStatus) {
    setBusy(true); setActionError("");
    try { setAssessment(await api.updateReviewStatus(id, status)); }
    catch (cause) { setActionError(cause instanceof Error ? cause.message : "Could not save the review status."); }
    finally { setBusy(false); }
  }

  async function openReport() {
    setBusy(true); setActionError("");
    try {
      const result = await api.createReport(id);
      router.push(`/reports/${result.report_id}?assessment_id=${id}`);
    } catch (cause) { setActionError(cause instanceof Error ? cause.message : "Could not generate the investigation report."); setBusy(false); }
  }

  return <>
    <PageHeading eyebrow="Workspace / Alerts / Detail" title={assessment ? `Alert ${assessment.id}` : "Alert detail"} description="Review the deterministic observations behind this risk assessment." action={<Link className="button button-secondary" href="/alerts">Back to alerts</Link>} />
    <StateMessage loading={loading} error={error} onRetry={retry} />
    {!loading && assessment && <>
      <section className="detail-summary">
        <div className="score-block"><span>Risk score</span><strong>{assessment.risk_score}<small> / 100</small></strong><SeverityLabel severity={assessment.severity} /></div>
        <div className="detail-fields"><div><span>Transaction</span><Identifier value={assessment.transaction.tx_hash} href={`/transactions/${encodeURIComponent(assessment.transaction.tx_hash)}?chain_id=${assessment.transaction.chain_id}`} /></div><div><span>Amount</span><strong>{formatAmount(assessment.transaction)}</strong></div><div><span>Assessed</span><strong>{formatDate(assessment.assessed_at)}</strong></div><div><span>Ruleset</span><strong>{assessment.ruleset_version}</strong></div></div>
      </section>

      <section className="content-section"><div className="section-heading"><div><h2>Triggered rules</h2><p>Rule-based observations recorded for this transaction.</p></div><span className="count-label">{assessment.triggered_rules.length} triggered</span></div>
        {assessment.triggered_rules.length ? <div className="evidence-list">{assessment.triggered_rules.map((rule) => <article className="evidence-row" key={rule.rule_id}><div className="evidence-weight">+{rule.weight}</div><div><h3>{rule.rule_id.replaceAll("_", " ")}</h3><p>{rule.observation}</p><small>Evidence references: {rule.evidence_refs.join(", ")}</small></div></article>)}</div> : <div className="empty-panel">No detection rules triggered for this assessment.</div>}
      </section>

      <section className="content-section action-section"><div><h2>Review outcome</h2><p>Recording a status does not change the risk score or its evidence.</p></div><div className="action-controls"><ReviewLabel status={assessment.review_status} /><label className="sr-only" htmlFor="review-status">Review status</label><select id="review-status" value={assessment.review_status} disabled={busy} onChange={(event) => void setStatus(event.target.value as ReviewStatus)}>{reviewOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select><button className="button button-primary" disabled={busy} onClick={() => void openReport()}>{busy ? "Working…" : "Generate investigation report"}</button></div>{actionError && <p className="action-error" role="alert">{actionError}</p>}</section>
    </>}
  </>;
}
