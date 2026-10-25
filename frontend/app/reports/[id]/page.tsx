"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { GenerateResponse } from "@/lib/types";
import { Identifier, PageHeading, StateMessage } from "@/components/UI";

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const reportId = Number(params.id);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [assessmentId, setAssessmentId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const response = await api.report(reportId);
      setResult(response);
      setAssessmentId(response.assessment_id);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load this report."); }
    finally { setLoading(false); }
  }, [reportId]);

  // This loader updates React state only after its asynchronous API call settles.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  async function regenerate() {
    if (!assessmentId) return;
    setBusy(true); setError("");
    try {
      const updated = await api.createReport(assessmentId, true);
      setResult(updated);
      if (updated.report_id !== reportId) router.replace(`/reports/${updated.report_id}?assessment_id=${assessmentId}`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not regenerate this report."); }
    finally { setBusy(false); }
  }

  function retry() { setLoading(true); setError(""); void load(); }

  return <>
    <PageHeading eyebrow="Workspace / Investigation report" title="Investigation report" description="A structured AI-generated investigative aid based on the stored evidence snapshot." action={<Link className="button button-secondary" href={assessmentId ? `/alerts/${assessmentId}` : "/alerts"}>Back to alert</Link>} />
    <div className="ai-disclaimer"><span className="ai-mark">AI</span><div><strong>AI-generated investigative aid</strong><p>Interpretations are not proof of fraud. Verify each point against the underlying records.</p></div>{assessmentId && <button className="button button-secondary button-small" disabled={busy} onClick={() => void regenerate()}>{busy ? "Regenerating…" : "Regenerate"}</button>}</div>
    <StateMessage loading={loading} error={error} onRetry={retry} />
    {!loading && result?.status === "pending" && <div className="inline-notice" role="status">The report is still being prepared. Retry in a moment to check for the completed report.<button className="text-button" onClick={() => void load()}>Check again</button></div>}
    {!loading && result?.status === "failed" && <div className="state-message state-error" role="alert"><strong>Report generation failed.</strong><span>Retry the report from its alert detail page.</span>{assessmentId && <Link className="button button-secondary" href={`/alerts/${assessmentId}`}>Return to alert</Link>}</div>}
    {!loading && result && result.status === "completed" && <>
      <section className="report-summary"><div className="report-meta">Report {result.report_id} · Assessment {result.assessment_id}</div><h2>Summary</h2><p>{result.report.summary}</p></section>
      <section className="content-section"><div className="section-heading"><div><h2>Observed evidence and interpretation</h2><p>Observations are shown separately from the model’s interpretation.</p></div></div>
        {result.report.evidence.length ? <div className="evidence-list">{result.report.evidence.map((item, index) => <article className="report-evidence" key={`${item.evidence_id}-${index}`}><div className="report-evidence-id"><Identifier value={item.evidence_id} /></div><div><h3>Observed evidence</h3><p>{item.observation}</p></div><div><h3>Interpretation</h3><p>{item.interpretation}</p></div></article>)}</div> : <div className="empty-panel">The report contains no cited evidence items.</div>}
      </section>
      <div className="report-columns"><section className="content-section"><h2>Recommended checks</h2>{result.report.recommended_checks.length ? <ul className="report-list">{result.report.recommended_checks.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p className="muted">No additional checks were recommended.</p>}</section><section className="content-section"><h2>Limitations</h2>{result.report.limitations.length ? <ul className="report-list">{result.report.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p className="muted">No limitations were listed.</p>}</section></div>
      <p className="report-timestamp">Report status: {result.status}</p>
    </>}
  </>;
}
