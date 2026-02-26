const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface EstimationRequest {
  project_description: string;
  additional_context?: string | null;
  preferred_tech_stack?: string[] | null;
  budget_range?: string | null;
  timeline_constraint?: string | null;
}

export interface Feature {
  name: string;
  description: string;
  complexity: "low" | "medium" | "high" | "very_high";
  estimated_hours: number;
  dependencies: string[];
  confidence_score: number;
}

export interface DomainDetection {
  detected_domain: string;
  confidence: number;
  secondary_domains: string[];
  reasoning: string;
}

export interface Estimation {
  total_hours: number;
  min_hours: number;
  max_hours: number;
  features: Feature[];
  overall_complexity: "low" | "medium" | "high" | "very_high";
  confidence_score: number;
  assumptions: string[];
}

export interface TechStack {
  frontend: string[];
  backend: string[];
  database: string[];
  infrastructure: string[];
  third_party_services: string[];
  justification: string;
}

export interface Proposal {
  executive_summary: string;
  scope_of_work: string;
  deliverables: string[];
  timeline_weeks: number;
  team_composition: Record<string, number>;
  risks: string[];
  mitigation_strategies: string[];
}

export interface EstimationResponse {
  request_id: string;
  domain_detection: DomainDetection;
  estimation: Estimation;
  tech_stack: TechStack;
  proposal: Proposal;
  metadata: Record<string, any>;
}

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = "APIError";
  }
}

export async function estimateProject(
  payload: EstimationRequest
): Promise<EstimationResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/estimate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        errorData.detail || "Estimation request failed",
        response.status,
        errorData
      );
    }

    const data = await response.json();
    return data as EstimationResponse;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof TypeError) {
      throw new APIError("Network error. Please check if the backend is running.");
    }

    throw new APIError("An unexpected error occurred");
  }
}

export async function healthCheck(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new APIError("Health check failed", response.status);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError("Backend is not reachable");
  }
}

export interface ModificationRequest {
  current_features: Array<{
    name: string;
    category: string;
    complexity: string;
  }>;
  instruction: string;
}

export interface ModificationResponse {
  total_hours: number;
  min_hours: number;
  max_hours: number;
  features: Feature[];
  changes_summary: string;
}

export async function modifyScope(
  payload: ModificationRequest
): Promise<ModificationResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/modify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        errorData.detail || "Scope modification failed",
        response.status,
        errorData
      );
    }

    const data = await response.json();
    return data as ModificationResponse;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof TypeError) {
      throw new APIError("Network error. Please check if the backend is running.");
    }

    throw new APIError("An unexpected error occurred");
  }
}
