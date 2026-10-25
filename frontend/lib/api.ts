import type {
  Assessment,
  GenerateResponse,
  IngestSummary,
  Page,
  ReviewStatus,
  Transaction,
  WalletRecord,
} from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new Error("The API could not be reached. Check that the backend is running.");
  }
  if (!response.ok) {
    if (response.status >= 500) {
      throw new Error("The API could not complete this request. Try again shortly.");
    }
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail || `Request failed (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

function queryString(values: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  const result = params.toString();
  return result ? `?${result}` : "";
}

export const api = {
  transactions: (values: Record<string, string | number | undefined> = {}) =>
    request<Page<Transaction>>(`/api/v1/transactions${queryString(values)}`),
  transaction: (hash: string, chainId?: number) =>
    request<Transaction>(`/api/v1/transactions/${encodeURIComponent(hash)}${queryString({ chain_id: chainId })}`),
  alerts: (values: Record<string, string | number | undefined> = {}) =>
    request<Page<Assessment>>(`/api/v1/alerts${queryString(values)}`),
  assessment: (id: number) => request<Assessment>(`/api/v1/assessments/${id}`),
  updateReviewStatus: (id: number, review_status: ReviewStatus) =>
    request<Assessment>(`/api/v1/alerts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_status }),
    }),
  createReport: (id: number, regenerate = false) =>
    request<GenerateResponse>(`/api/v1/assessments/${id}/investigation-report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ regenerate }),
    }),
  report: (id: number) => request<GenerateResponse>(`/api/v1/reports/${id}`),
  wallet: (address: string, chainId: number) =>
    request<WalletRecord | null>(`/api/v1/wallets/${encodeURIComponent(address)}${queryString({ chain_id: chainId })}`),
  ingest: (file: File) => {
    const body = new FormData();
    body.set("file", file);
    return request<IngestSummary>("/api/v1/transactions/ingest", { method: "POST", body });
  },
};
