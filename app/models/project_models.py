from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

# Allowed values for what the client wants to build (mobile, web, design, backend, admin)
BuildOption = Literal["mobile", "web", "design", "backend", "admin"]


class Domain(str, Enum):
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    SAAS = "saas"
    ENTERPRISE = "enterprise"
    MOBILE_APP = "mobile_app"
    WEB_APP = "web_app"
    AI_ML = "ai_ml"
    MARKETPLACE = "marketplace"
    SOCIAL_MEDIA = "social_media"
    IOT = "iot"
    BLOCKCHAIN = "blockchain"
    UNKNOWN = "unknown"


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Feature(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Feature description")
    complexity: ComplexityLevel = Field(..., description="Estimated complexity")
    estimated_hours: float = Field(..., ge=0, description="Estimated hours")
    dependencies: List[str] = Field(default_factory=list, description="Dependent features")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in estimate")


class DomainDetectionResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    detected_domain: Domain = Field(..., description="Primary detected domain")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    secondary_domains: List[Domain] = Field(default_factory=list, description="Secondary domains")
    reasoning: str = Field(..., description="Why this domain was selected")


class EstimationResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    total_hours: float = Field(..., ge=0, description="Total estimated hours")
    min_hours: float = Field(..., ge=0, description="Minimum hours estimate")
    max_hours: float = Field(..., ge=0, description="Maximum hours estimate")
    features: List[Feature] = Field(..., description="Breakdown by features")
    overall_complexity: ComplexityLevel = Field(..., description="Overall project complexity")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions made")


class TechStackRecommendation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    frontend: List[str] = Field(..., description="Frontend technologies")
    backend: List[str] = Field(..., description="Backend technologies")
    database: List[str] = Field(..., description="Database technologies")
    infrastructure: List[str] = Field(..., description="Infrastructure & DevOps")
    third_party_services: List[str] = Field(default_factory=list, description="Third-party integrations")
    justification: str = Field(..., description="Why this stack was recommended")


class ProposalResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    executive_summary: str = Field(..., description="High-level project summary")
    scope_of_work: str = Field(..., description="Detailed scope description")
    deliverables: List[str] = Field(..., description="Key deliverables")
    timeline_weeks: float = Field(..., ge=0, description="Estimated timeline in weeks")
    team_composition: Dict[str, int] = Field(..., description="Recommended team structure")
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Risk mitigation")


class ProjectRequest(BaseModel):
    """Request model for /estimate endpoint (JSON body)."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    additional_details: Optional[str] = Field(None, description="Project description from the client (min 10 chars)")
    build_options: List[BuildOption] = Field(
        default_factory=list,
        description="What the client wants to build: mobile, web, design, backend, admin",
    )
    additional_context: Optional[str] = Field(None, description="Any additional context or requirements")
    preferred_tech_stack: Optional[List[str]] = Field(None, description="Client's preferred technologies")
    timeline_constraint: Optional[str] = Field(None, description="Timeline constraints if any")


class PlanningResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    phase_split: Dict[str, float] = Field(..., description="Hours split by phase")
    team_recommendation: Dict[str, int] = Field(..., description="Recommended team composition")
    category_breakdown: Dict[str, float] = Field(..., description="Hours by category")


class FinalPipelineResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    request_id: str = Field(..., description="Unique request identifier")
    domain_detection: DomainDetectionResult = Field(..., description="Domain detection results")
    estimation: EstimationResult = Field(..., description="Estimation breakdown")
    tech_stack: TechStackRecommendation = Field(..., description="Recommended tech stack")
    proposal: ProposalResponse = Field(..., description="Final proposal document")
    planning: PlanningResult = Field(..., description="Planning and resource allocation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Pipeline metadata")
