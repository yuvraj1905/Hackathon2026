function getApiBase(): string {
  if (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }
  return "http://127.0.0.1:8000";
}

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem("authToken");
  } catch {
    return null;
  }
}


export async function logoutApi(): Promise<void> {
  const token = getAuthToken();
  const API_BASE = getApiBase();
  if (!token) return;
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  } catch {
    throw new Error("Failed to logout. Please try again.");
  }
}

export async function fetchEstimate(payload: {
  project_description?: string;
  file?: File;
  platforms?: string[];
  timeline?: string;
}): Promise<any> {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required. Please log in again.");
  }

  const API_BASE = getApiBase();
  let response: Response;

  if (payload.file) {
    const formData = new FormData();
    formData.append("file", payload.file);

    if (payload.project_description?.trim()) {
      formData.append("additional_details", payload.project_description.trim());
    }

    if (payload.platforms?.length) {
      formData.append("build_options", JSON.stringify(payload.platforms));
    }

    if (payload.timeline?.trim()) {
      formData.append("timeline_constraint", payload.timeline.trim());
    }

    response = await fetch(`${API_BASE}/estimate`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });
  } else {
    const body: Record<string, unknown> = {
      additional_details: payload.project_description?.trim(),
      build_options: payload.platforms?.length ? payload.platforms : undefined,
      timeline_constraint: payload.timeline?.trim() || undefined,
    };

    response = await fetch(`${API_BASE}/estimate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
  }

  if (!response.ok) {
    const errText = await response.text().catch(() => "");
    if (response.status === 401) {
      throw new Error("Session expired. Please log in again.");
    }
    throw new Error(
      `Estimation failed (${response.status}): ${errText || response.statusText}`,
    );
  }

  return response.json();
}

export interface StoredProposalSummary {
  id: string;
  request_id: string;
  title: string;
  domain: string;
  totalHours: number;
  createdAt: string;
}

export const PROPOSALS_HISTORY_KEY = "proposalsHistory";

let lastEstimateRaw: any = null;

export function setLastEstimateRaw(raw: any): void {
  lastEstimateRaw = raw ?? null;
}

export function takeLastEstimateRaw(): any {
  const value = lastEstimateRaw;
  lastEstimateRaw = null;
  return value;
}

export function appendProposalToHistory(
  raw: any,
  options?: { title?: string },
): void {
  if (typeof window === "undefined" || !raw) return;

  try {
    const id: string =
      (raw.request_id && String(raw.request_id)) ||
      (typeof crypto !== "undefined" &&
        (crypto as any).randomUUID
        ? (crypto as any).randomUUID()
          (crypto as any).randomUUID()
        : String(Date.now()));

    const domainRaw =
      (raw.domain_detection &&
        (raw.domain_detection.detected_domain as string)) ||
      "unknown";
    const domain = String(domainRaw).replace(/_/g, " ").trim();

    const totalHours = Number(raw.estimation?.total_hours ?? 0) || 0;

    const derivedTitle =
      options?.title?.trim() ||
      (raw.metadata && (raw.metadata.project_title as string)) ||
      (domain ? `${domain[0]?.toUpperCase() || ""}${domain.slice(1)} project` : "New proposal");

    const createdAt = new Date().toISOString();

    const request_id = raw.request_id || "";

    const entry: StoredProposalSummary = {
      id,
      request_id,
      title: derivedTitle,
      domain,
      totalHours,
      createdAt,
    };

    const existingRaw = window.sessionStorage.getItem(PROPOSALS_HISTORY_KEY);
    const existing: StoredProposalSummary[] = existingRaw
      ? JSON.parse(existingRaw)
      : [];

    const withoutDup = existing.filter((p) => p.id !== id);
    const next = [entry, ...withoutDup];

    window.sessionStorage.setItem(PROPOSALS_HISTORY_KEY, JSON.stringify(next));
  } catch {
    // Swallow storage errors – history is a non-critical enhancement.
  }
}

export async function fetchProjects(): Promise<StoredProposalSummary[]> {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required. Please log in again.");
  }
  const API_BASE = getApiBase();
  const response = await fetch(`${API_BASE}/projects`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    const errText = await response.text().catch(() => "");
    if (response.status === 401) {
      throw new Error("Session expired. Please log in again.");
    }
    throw new Error(
      `Failed to load projects (${response.status}): ${errText || response.statusText}`,
    );
  }
  return response.json();
}

export function loadProposalsHistory(): StoredProposalSummary[] {
  if (typeof window === "undefined") return [];

  try {
    const existingRaw = window.sessionStorage.getItem(PROPOSALS_HISTORY_KEY);
    if (!existingRaw) return [];
    const parsed = JSON.parse(existingRaw) as StoredProposalSummary[];
    if (!Array.isArray(parsed)) return [];
    return parsed;
  } catch {
    return [];
  }
}
