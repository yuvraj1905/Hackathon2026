from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from io import BytesIO
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv

from app.models.project_models import ProjectRequest, FinalPipelineResponse
from app.models.modification_models import ModificationRequest, ModificationResponse
from app.models.user_models import UserLogin, TokenResponse, UserResponse, UserInDB
from app.orchestrator.project_pipeline import ProjectPipeline
from app.agents.modification_agent import ModificationAgent
from app.agents.estimation_agent import EstimationAgent
from app.services.calibration_engine import CalibrationEngine
from app.services.database import db
from app.services.document_parser import extract_text_from_upload
from app.services.document_cleaner import clean_extracted_text_with_llm, should_use_llm_cleanup
from app.services.input_fusion_service import build_final_description
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from app.services.proposal_renderer import render_proposal
from app.services.proposal_pdf_service import ProposalPDFService
from googleapiclient.errors import HttpError as GoogleHttpError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ── In-memory estimation cache (LRU-style, capped at 100 entries) ──────────
_estimation_cache: dict[str, dict] = {}
_MAX_CACHE_SIZE = 100

pdf_service = ProposalPDFService()

# Lazily initialized on first /proposal/google-doc request (credentials optional)
_google_docs_service: Any = None


def _get_google_docs_service():
    """Return the module-level GoogleDocsService singleton, creating it on first call."""
    global _google_docs_service
    if _google_docs_service is None:
        from app.services.google_docs_service import GoogleDocsService
        _google_docs_service = GoogleDocsService()
    return _google_docs_service


pipeline: ProjectPipeline = None
modification_agent: ModificationAgent = None
calibration_engine: CalibrationEngine = None
estimation_agent: EstimationAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline, modification_agent, calibration_engine, estimation_agent
    logger.info("Initializing estimation pipeline...")
    await db.connect()
    logger.info("Connected to PostgreSQL")
    pipeline = ProjectPipeline()
    calibration_engine = CalibrationEngine()
    estimation_agent = EstimationAgent(calibration_engine=calibration_engine)
    modification_agent = ModificationAgent()
    logger.info("Pipeline ready")
    yield
    logger.info("Shutting down...")
    await db.disconnect()


app = FastAPI(
    title="Presales Estimation Engine",
    description="Production-grade AI estimation pipeline for GeekyAnts",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    db_connected = await db.healthcheck()
    return {
        "status": "healthy" if db_connected else "degraded",
        "pipeline_initialized": pipeline is not None,
        "database_connected": db_connected,
    }


@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin) -> TokenResponse:
    """
    Authenticate user and return JWT access token.
    
    Args:
        credentials: Email and password
        
    Returns:
        JWT access token and user details
    """
    user = await authenticate_user(credentials.email, credentials.password)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )
    
    access_token = create_access_token(user.id, user.email)
    
    logger.info("User logged in: email=%s", user.email)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
        ),
    )


@app.post("/estimate", response_model=FinalPipelineResponse)
async def estimate_project(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
) -> FinalPipelineResponse:
    """
    Execute full estimation pipeline for a project.
    
    Requires JWT authentication. Supports three input modes:
    1. file upload: Upload a PRD document via multipart/form-data (PDF/DOCX/XLSX/XLS)
    2. manual input: Provide additional_details text directly (JSON or form-data)
    3. re-estimation: Provide project_id to re-run estimation with stored data
    
    All modes can be combined (hybrid mode).
    
    **multipart/form-data fields:**
    - file: PRD document (optional, PDF/DOCX/XLSX/XLS)
    - additional_details: Manual project description (optional, min 10 chars if no file)
    - build_options: JSON array string e.g. '["mobile","web"]' (optional)
    - timeline_constraint: Timeline string e.g. "3 months" (optional)
    - additional_context: Extra context (optional)
    - preferred_tech_stack: Comma-separated techs e.g. "React, Node.js" (optional)
    - project_id: UUID of existing project for re-estimation (optional)
    
    **JSON body fields:**
    - additional_details: Manual project description (required, min 10 chars)
    - build_options: Array of strings (optional)
    - timeline_constraint: Timeline string (optional)
    - additional_context: Extra context (optional)
    - preferred_tech_stack: Array of strings (optional)
    - project_id: UUID of existing project for re-estimation (optional)
    
    Args:
        request: Project request with description and/or file
        current_user: Authenticated user (from JWT token)
        
    Returns:
        Complete estimation with domain, features, hours, tech stack, and proposal
    """
    try:
        content_type = (request.headers.get("content-type") or "").lower()

        additional_details = None
        extracted_text = None
        additional_context = None
        preferred_tech_stack = None
        timeline_constraint = None
        build_options = []
        uploaded_filename = None
        uploaded_file_extension = None
        project_id = None

        if "application/json" in content_type:
            body = await request.json()
            json_payload = ProjectRequest(**body)
            
            additional_details = json_payload.additional_details
            build_options = list(json_payload.build_options) if json_payload.build_options else []
            additional_context = json_payload.additional_context
            preferred_tech_stack = json_payload.preferred_tech_stack
            timeline_constraint = json_payload.timeline_constraint
            project_id = body.get("project_id")

        elif "multipart/form-data" in content_type:
            form = await request.form()

            additional_details_raw = form.get("additional_details")
            additional_details = (
                str(additional_details_raw).strip()
                if additional_details_raw is not None
                else None
            )

            file_item = form.get("file")
            if (
                file_item is not None
                and hasattr(file_item, "filename")
                and hasattr(file_item, "read")
                and file_item.filename
            ):
                uploaded_filename = file_item.filename
                uploaded_file_extension = Path(uploaded_filename).suffix.lower().lstrip(".")
                
                if uploaded_file_extension not in {"pdf", "docx", "xlsx", "xls"}:
                    raise HTTPException(
                        status_code=400,
                        detail="Unsupported file type. Allowed: pdf, docx, xlsx, xls",
                    )
                
                file_content = await file_item.read()
                file_size = len(file_content)
                await file_item.seek(0)
                
                extracted_text = await extract_text_from_upload(file_item)
                
                if should_use_llm_cleanup(extracted_text, file_size):
                    try:
                        extracted_text = await clean_extracted_text_with_llm(extracted_text)
                    except Exception as e:
                        logger.warning("LLM cleanup failed, using raw extraction: %s", str(e))

            additional_context_raw = form.get("additional_context")
            additional_context = (
                str(additional_context_raw).strip()
                if additional_context_raw is not None and str(additional_context_raw).strip()
                else None
            )

            preferred_stack_raw = form.get("preferred_tech_stack")
            if preferred_stack_raw is not None and str(preferred_stack_raw).strip():
                preferred_tech_stack = [
                    part.strip()
                    for part in str(preferred_stack_raw).split(",")
                    if part.strip()
                ]

            build_options_raw = form.get("build_options")
            if build_options_raw is not None and str(build_options_raw).strip():
                raw = str(build_options_raw).strip()
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        build_options = [str(x).strip().lower() for x in parsed if x]
                    else:
                        build_options = []
                except json.JSONDecodeError:
                    build_options = [
                        part.strip().lower()
                        for part in raw.split(",")
                        if part.strip()
                    ]
            
            allowed = {"mobile", "web", "design", "backend", "admin"}
            build_options = [x for x in build_options if x in allowed]

            timeline_raw = form.get("timeline_constraint")
            timeline_constraint = (
                str(timeline_raw).strip()
                if timeline_raw is not None and str(timeline_raw).strip()
                else None
            )

            project_id_raw = form.get("project_id")
            project_id = (
                str(project_id_raw).strip()
                if project_id_raw is not None and str(project_id_raw).strip()
                else None
            )

        else:
            raise HTTPException(
                status_code=415,
                detail="Unsupported Content-Type. Use application/json or multipart/form-data.",
            )

        # If project_id is provided, fetch stored project data as defaults
        if project_id:
            try:
                import uuid as uuid_module
                project_uuid = uuid_module.UUID(project_id)
                
                async with db.pool.acquire() as conn:
                    project = await conn.fetchrow(
                        """
                        SELECT additional_details, build_options, timeline_constraint 
                        FROM projects 
                        WHERE id = $1 AND user_id = $2
                        """,
                        project_uuid,
                        current_user.id,
                    )
                    
                    if not project:
                        raise HTTPException(
                            status_code=404,
                            detail="Project not found or access denied",
                        )
                    
                    # Use stored values as defaults (new inputs override stored)
                    if not additional_details and project["additional_details"]:
                        additional_details = project["additional_details"]
                        logger.info(f"Using stored additional_details for project {project_id}")
                    
                    if not build_options and project["build_options"]:
                        build_options = list(project["build_options"])
                        logger.info(f"Using stored build_options for project {project_id}")
                    
                    if not timeline_constraint and project["timeline_constraint"]:
                        timeline_constraint = project["timeline_constraint"]
                        logger.info(f"Using stored timeline_constraint for project {project_id}")
                    
                    # Fetch stored extracted_text from documents table
                    doc = await conn.fetchrow(
                        """
                        SELECT extracted_text 
                        FROM documents 
                        WHERE project_id = $1
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        project_uuid,
                    )
                    
                    if doc and doc["extracted_text"] and not extracted_text:
                        extracted_text = doc["extracted_text"]
                        logger.info(f"Using stored extracted_text for project {project_id}")
                        
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid project_id format. Must be a valid UUID.",
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Failed to fetch project data for re-estimation: {e}")

        has_manual = bool((additional_details or "").strip()) and len((additional_details or "").strip()) >= 10
        has_file = bool((extracted_text or "").strip())
        
        if not has_manual and not has_file:
            raise HTTPException(
                status_code=400,
                detail="Provide additional_details (at least 10 characters) or upload a document.",
            )

        final_description = build_final_description(additional_details, extracted_text)

        if has_manual and has_file:
            input_mode = "hybrid"
        elif has_file:
            input_mode = "file_only"
        else:
            input_mode = "manual_only"

        logger.info(
            "Processing estimation request mode=%s description_len=%d user=%s",
            input_mode,
            len(final_description),
            current_user.email,
        )

        result = await pipeline.run({
            "description": final_description,
            "additional_context": additional_context,
            "preferred_tech_stack": preferred_tech_stack,
            "build_options": build_options,
            "timeline_constraint": timeline_constraint,
            "additional_details": additional_details or "",
            "extracted_text": extracted_text or "",
        })

        try:
            # Ensure build_options is always a list for PostgreSQL TEXT[] (asyncpg accepts list)
            build_options_for_db = list(build_options) if build_options else []

            async with db.pool.acquire() as conn:
                proj_row = await conn.fetchrow(
                    """
                    INSERT INTO projects (user_id, additional_details, build_options, timeline_constraint)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    current_user.id,
                    additional_details,
                    build_options_for_db,
                    timeline_constraint,
                )
                project_id = proj_row["id"]
                
                if extracted_text and uploaded_filename:
                    await conn.execute(
                        """
                        INSERT INTO documents (user_id, project_id, filename, file_type, extracted_text)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        current_user.id,
                        project_id,
                        uploaded_filename,
                        uploaded_file_extension,
                        extracted_text,
                    )
                
                logger.info(
                    "Project stored: project_id=%s user=%s has_document=%s",
                    project_id,
                    current_user.email,
                    bool(extracted_text),
                )
        except Exception as e:
            logger.warning("Failed to store project data: %s", str(e))
        # Cache result for proposal PDF generation
        request_id = result["request_id"]
        if len(_estimation_cache) >= _MAX_CACHE_SIZE:
            oldest = next(iter(_estimation_cache))
            del _estimation_cache[oldest]
        _estimation_cache[request_id] = result
        logger.info("Cached estimation: request_id=%s (cache size=%d)", request_id, len(_estimation_cache))

        logger.info(
            "Estimation completed: %s mode=%s",
            request_id,
            input_mode
        )

        return FinalPipelineResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal estimation error")


@app.post("/modify", response_model=ModificationResponse)
async def modify_scope(request: ModificationRequest) -> ModificationResponse:
    """
    Modify project scope and re-estimate.
    
    Args:
        request: Current features and modification instruction
        
    Returns:
        Updated estimation with modified features
    """
    try:
        logger.info(f"Processing modification: {request.instruction[:100]}...")
        
        current_features_list = [
            {
                "name": f.name,
                "category": f.category,
                "complexity": f.complexity
            }
            for f in request.current_features
        ]
        
        modification_result = await modification_agent.execute({
            "current_features": current_features_list,
            "instruction": request.instruction
        })
        
        updated_features = modification_result.get("features", [])
        
        estimation_result = await estimation_agent.execute({
            "features": updated_features,
            "original_description": request.instruction
        })
        
        estimated_features = estimation_result.get("features", [])
        total_hours = estimation_result.get("total_hours", 0)
        min_hours = estimation_result.get("min_hours", 0)
        max_hours = estimation_result.get("max_hours", 0)
        
        formatted_features = []
        for feature in estimated_features:
            formatted_features.append({
                "name": feature.get("name", ""),
                "description": feature.get("category", "Core"),
                "complexity": feature.get("complexity", "Medium").lower(),
                "estimated_hours": feature.get("final_hours", 0.0),
                "dependencies": [],
                "confidence_score": 0.75
            })
        
        changes_summary = _generate_changes_summary(
            current_features_list,
            updated_features
        )
        
        logger.info(f"Modification completed: {len(updated_features)} features")
        
        return ModificationResponse(
            total_hours=total_hours,
            min_hours=min_hours,
            max_hours=max_hours,
            features=formatted_features,
            changes_summary=changes_summary
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Modification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal modification error")


def _flatten_tech_layer(value: Any) -> list[str]:
    """
    Convert a tech_stack layer (list or nested dict) to a list of display strings.
    Supports the estimate API response structure: backend/frontend as dicts,
    database with primary/cache/search/secondary, infrastructure with cloud_provider, etc.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    if not isinstance(value, dict):
        return [str(value)] if str(value).strip() else []
    skip_keys = {"justification", "type", "recommendations", "best_for", "services"}
    out: list[str] = []
    for k, v in value.items():
        if v is None or k in skip_keys:
            continue
        if isinstance(v, dict):
            name = v.get("name") if isinstance(v.get("name"), str) else None
            if name:
                out.append(name)
            elif k in ("primary", "secondary", "cache", "search") and isinstance(v, dict):
                if v.get("name"):
                    out.append(str(v["name"]))
            continue
        if isinstance(v, list):
            out.extend(str(x) for x in v if x is not None and str(x).strip())
            continue
        s = str(v).strip()
        if s:
            out.append(s)
    return out


def _build_proposal_context(data: dict[str, Any]) -> dict[str, Any]:
    """
    Build the Jinja2 template context from a cached estimation result dict.

    Expects the estimate API response structure: request_id, domain_detection,
    estimation (total_hours, min_hours, max_hours, features with name, complexity,
    total_hours, subfeatures, confidence_score), tech_stack (nested dicts),
    proposal, planning, metadata.

    Returns:
        Context dict ready for render_proposal().
    """
    proposal = data.get("proposal", {})
    estimation = data.get("estimation", {})
    tech_stack = data.get("tech_stack", {})
    domain_detection = data.get("domain_detection", {})
    planning = data.get("planning", {})

    detected_domain = (
        str(domain_detection.get("detected_domain", "Unknown"))
        .replace("_", " ")
        .title()
    )

    # Features: new structure has name, complexity, total_hours, subfeatures, confidence_score.
    # Template uses total_hours for hours; description can be derived from subfeature names.
    raw_features = estimation.get("features", [])
    features = []
    for f in raw_features:
        subfeatures = f.get("subfeatures", [])
        description = ", ".join(s.get("name", "") for s in subfeatures if s.get("name")) or f.get("name", "")
        features.append({
            "name": f.get("name", ""),
            "description": description,
            "complexity": (f.get("complexity", "medium") or "medium").lower().replace(" ", "_"),
            "total_hours": f.get("total_hours", 0.0),
            "estimated_hours": f.get("total_hours", 0.0),
            "subfeatures": subfeatures,
            "confidence_score": f.get("confidence_score", 0),
        })

    # Prefer proposal assumptions (LLM-generated) over estimation assumptions (hardcoded fallback)
    assumptions = proposal.get("assumptions", []) or estimation.get("assumptions", [])

    return {
        "request_id": data.get("request_id", "N/A"),
        "project_title": f"{detected_domain} Platform",
        "detected_domain": detected_domain,
        "abstract": proposal.get("abstract", ""),
        "executive_summary": proposal.get("executive_summary", ""),
        "proposed_solution": proposal.get("proposed_solution", ""),
        "scope_of_work": proposal.get("scope_of_work", ""),
        "deliverables": proposal.get("deliverables", []),
        "project_timeline": proposal.get("project_timeline", []),
        "risks": proposal.get("risks", []),
        "mitigation_strategies": proposal.get("mitigation_strategies", []),
        "assumptions": assumptions,
        "client_dependencies": proposal.get("client_dependencies", []),
        "features": features,
        "total_hours": estimation.get("total_hours", 0),
        "min_hours": estimation.get("min_hours", 0),
        "max_hours": estimation.get("max_hours", 0),
        "confidence_score": estimation.get("confidence_score", 0),
        "tech_frontend": _flatten_tech_layer(tech_stack.get("frontend")),
        "tech_backend": _flatten_tech_layer(tech_stack.get("backend")),
        "tech_database": _flatten_tech_layer(tech_stack.get("database")),
        "tech_infrastructure": _flatten_tech_layer(tech_stack.get("infrastructure")),
        "tech_third_party": _flatten_tech_layer(tech_stack.get("third_party_services")),
        "tech_justification": tech_stack.get("justification", ""),
        "team_composition": proposal.get(
            "team_composition", planning.get("team_recommendation", {})
        ),
        "timeline_weeks": proposal.get("timeline_weeks", "TBD"),
        "phase_split": planning.get("phase_split", {}),
        "category_breakdown": planning.get("complexity_breakdown", {}),
    }


@app.get("/proposal/pdf/{request_id}")
async def get_proposal_pdf(request_id: str) -> StreamingResponse:
    """
    Generate and stream a branded PDF proposal for a previously run estimation.

    Args:
        request_id: The UUID returned in the /estimate response.

    Returns:
        Streaming PDF response suitable for inline browser display.

    Raises:
        404 if the estimation is not found in the cache (re-run /estimate first).
    """
    cached = _estimation_cache.get(request_id)
    if cached is None:
        logger.warning("Proposal PDF requested for unknown request_id=%s", request_id)
        raise HTTPException(
            status_code=404,
            detail=f"Estimation '{request_id}' not found. Re-run the estimation to regenerate.",
        )

    try:
        logger.info("Generating proposal PDF for request_id=%s", request_id)
        context = _build_proposal_context(cached)
        html = render_proposal(context)
        pdf_bytes = pdf_service.generate_pdf(html)
    except RuntimeError as exc:
        # WeasyPrint system libraries (Pango/Cairo) not installed
        logger.error("PDF generation unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("Proposal PDF generation failed for request_id=%s", request_id)
        raise HTTPException(status_code=500, detail="Failed to generate proposal PDF")

    logger.info(
        "Serving proposal PDF: request_id=%s size=%d bytes",
        request_id,
        len(pdf_bytes),
    )

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'inline; filename="proposal.pdf"',
        },
    )


@app.get("/proposal/html/{request_id}")
async def get_proposal_html(request_id: str) -> dict:
    """
    Return rendered proposal HTML and title for client-side Google Docs export.

    Args:
        request_id: The UUID returned by /estimate.

    Returns:
        JSON: ``{"html": "<rendered html>", "title": "Project — Proposal"}``
    """
    cached = _estimation_cache.get(request_id)
    if cached is None:
        logger.warning("Proposal HTML requested for unknown request_id=%s", request_id)
        raise HTTPException(
            status_code=404,
            detail=f"Estimation '{request_id}' not found. Re-run the estimation to regenerate.",
        )

    try:
        context = _build_proposal_context(cached)
        html = render_proposal(context)
        title = f"{context['project_title']} — Proposal"
    except Exception:
        logger.exception("Proposal HTML generation failed for request_id=%s", request_id)
        raise HTTPException(status_code=500, detail="Failed to generate proposal HTML")

    logger.info("Serving proposal HTML: request_id=%s", request_id)
    return {"html": html, "title": title}


@app.get("/proposal/google-doc/{request_id}")
async def get_proposal_google_doc(
    request_id: str,
    email: Optional[str] = Query(default=None, description="Grant this email writer access to the doc"),
) -> dict:
    """
    Generate a branded proposal as a native Google Doc and return its edit URL.

    Args:
        request_id: The UUID returned by /estimate.
        email:       Optional query param — if provided, the doc is shared with this address.

    Returns:
        JSON: ``{"doc_url": "https://docs.google.com/document/d/.../edit"}``

    Raises:
        404: estimation not in cache (re-run /estimate first).
        503: service account credentials missing or invalid.
        502: Google API returned an unexpected error.
    """
    cached = _estimation_cache.get(request_id)
    if cached is None:
        logger.warning("Google Doc requested for unknown request_id=%s", request_id)
        raise HTTPException(
            status_code=404,
            detail=f"Estimation '{request_id}' not found. Re-run the estimation to regenerate.",
        )

    # Resolve share email: use provided value, fall back to configured default
    from app.config.settings import settings as _settings
    candidate = (email or "").strip()
    if candidate and "@" not in candidate:
        logger.warning("Invalid email param '%s' — falling back to default", candidate)
        candidate = ""
    share_email: str = candidate or _settings.DEFAULT_PROPOSAL_SHARE_EMAIL
    logger.info("Sharing generated proposal with: %s", share_email)

    context = _build_proposal_context(cached)
    html = render_proposal(context)
    title = f"{context['project_title']} — Proposal"

    try:
        svc = _get_google_docs_service()
        doc_url: str = await asyncio.to_thread(
            svc.create_doc_from_html, html, title, share_email
        )
    except Exception as exc:
        logger.warning(
            "Google Docs export failed for request_id=%s (%s: %s) — falling back to PDF",
            request_id,
            type(exc).__name__,
            exc,
        )
        return {
            "doc_url": f"/proposal/pdf/{request_id}",
            "fallback": True,
            "message": "Google Docs unavailable — opening as PDF instead.",
        }

    logger.info("Google Doc ready: request_id=%s url=%s", request_id, doc_url)
    return {"doc_url": doc_url}


def _generate_changes_summary(
    old_features: list,
    new_features: list
) -> str:
    """
    Generate a summary of changes made.
    
    Args:
        old_features: Original feature list
        new_features: Updated feature list
        
    Returns:
        Human-readable changes summary
    """
    old_names = {f.get("name", "") for f in old_features}
    new_names = {f.get("name", "") for f in new_features}
    
    added = new_names - old_names
    removed = old_names - new_names
    
    changes = []
    
    if added:
        changes.append(f"Added {len(added)} feature(s)")
    if removed:
        changes.append(f"Removed {len(removed)} feature(s)")
    if not added and not removed:
        changes.append("Modified existing features")
    
    return ", ".join(changes) if changes else "No changes detected"


