from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID
from dotenv import load_dotenv

from app.models.project_models import ProjectRequest, FinalPipelineResponse
from app.models.modification_models import ModificationRequest, ModificationResponse
from app.models.user_models import UserLogin, TokenResponse, UserResponse, UserInDB
from app.models.document_models import DocumentUploadResponse, DocumentResponse
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

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Upload a document for parsing and storage.
    
    Extracts text from PDF/DOCX, optionally cleans with LLM, and stores in database.
    Returns document_id for use in subsequent /estimate calls.
    
    Args:
        request: Multipart form data with file and optional fields
        current_user: Authenticated user (from JWT token)
        
    Returns:
        Document ID and extraction preview
    """
    try:
        content_type = (request.headers.get("content-type") or "").lower()
        
        if "multipart/form-data" not in content_type:
            raise HTTPException(
                status_code=415,
                detail="Content-Type must be multipart/form-data",
            )
        
        form = await request.form()
        
        file_item = form.get("file")
        if file_item is None or not hasattr(file_item, "filename") or not file_item.filename:
            raise HTTPException(
                status_code=400,
                detail="File is required",
            )
        
        filename = file_item.filename
        extension = Path(filename).suffix.lower().lstrip(".")
        
        if extension not in {"pdf", "docx", "xlsx", "xls"}:
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
        
        manual_input_raw = form.get("additional_details")
        manual_input = (
            str(manual_input_raw).strip()
            if manual_input_raw is not None and str(manual_input_raw).strip()
            else None
        )
        
        build_options_raw = form.get("build_options")
        build_options: list[str] = []
        if build_options_raw is not None and str(build_options_raw).strip():
            raw = str(build_options_raw).strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    build_options = [str(x).strip().lower() for x in parsed if x]
            except json.JSONDecodeError:
                build_options = [p.strip().lower() for p in raw.split(",") if p.strip()]
        
        allowed = {"mobile", "web", "design", "backend", "admin"}
        build_options = [x for x in build_options if x in allowed]
        
        fused_description = build_final_description(manual_input, extracted_text)
        
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO documents (
                    user_id, filename, file_type, extracted_text, 
                    manual_input, build_options, fused_description, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'uploaded')
                RETURNING id, created_at
                """,
                current_user.id,
                filename,
                extension,
                extracted_text,
                manual_input,
                build_options,
                fused_description,
            )
        
        document_id = row["id"]
        
        logger.info(
            "Document uploaded: id=%s user=%s filename=%s chars=%d",
            document_id,
            current_user.email,
            filename,
            len(extracted_text),
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=filename,
            file_type=extension,
            extracted_preview=extracted_text[:500] + ("..." if len(extracted_text) > 500 else ""),
            status="uploaded",
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error("Document upload validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Document upload failed")
        raise HTTPException(status_code=500, detail="Failed to process document")


@app.post("/estimate", response_model=FinalPipelineResponse)
async def estimate_project(request: Request) -> FinalPipelineResponse:
    """
    Execute full estimation pipeline for a project.
    
    Supports three input modes:
    1. document_id: Use a previously uploaded document from /upload
    2. file upload: Upload a new document via multipart/form-data
    3. manual input: Provide additional_details text directly
    
    Args:
        request: Project request with description and optional context
        
    Returns:
        Complete estimation with domain, features, hours, tech stack, and proposal
    """
    try:
        content_type = (request.headers.get("content-type") or "").lower()

        additional_details = None
        extracted_text = None
        additional_context = None
        preferred_tech_stack = None
        build_options = []
        final_description = None
        document_id = None

        if "application/json" in content_type:
            body = await request.json()
            json_payload = ProjectRequest(**body)
            
            if json_payload.document_id:
                try:
                    doc_uuid = UUID(json_payload.document_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid document_id format")
                
                async with db.pool.acquire() as conn:
                    doc_row = await conn.fetchrow(
                        """
                        SELECT fused_description, build_options, status 
                        FROM documents WHERE id = $1
                        """,
                        doc_uuid,
                    )
                
                if doc_row is None:
                    raise HTTPException(status_code=404, detail="Document not found")
                
                final_description = doc_row["fused_description"]
                build_options = list(doc_row["build_options"] or [])
                document_id = json_payload.document_id
                
                await db.pool.execute(
                    "UPDATE documents SET status = 'processing' WHERE id = $1",
                    doc_uuid,
                )
            else:
                additional_details = json_payload.additional_details
                build_options = list(json_payload.build_options) if json_payload.build_options else []
            
            additional_context = json_payload.additional_context
            preferred_tech_stack = json_payload.preferred_tech_stack

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
                extracted_text = await extract_text_from_upload(file_item)

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
            # Restrict to allowed build options only
            allowed = {"mobile", "web", "design", "backend", "admin"}
            build_options = [x for x in build_options if x in allowed]

            _ = form.get("timeline_constraint")

        else:
            raise HTTPException(
                status_code=415,
                detail="Unsupported Content-Type. Use application/json or multipart/form-data.",
            )

        if final_description is None:
            has_manual = bool((additional_details or "").strip()) and len((additional_details or "").strip()) >= 10
            has_file = bool((extracted_text or "").strip())
            if not has_manual and not has_file:
                raise HTTPException(
                    status_code=400,
                    detail="Provide additional details (at least 10 characters), upload a document, or use document_id.",
                )

            final_description = build_final_description(additional_details, extracted_text)

            if has_manual and has_file:
                input_mode = "hybrid"
            elif has_file:
                input_mode = "file_only"
            else:
                input_mode = "manual_only"
        else:
            input_mode = "document_id"

        logger.info(
            "Processing estimation request mode=%s description_len=%d",
            input_mode,
            len(final_description),
        )

        # Single pipeline execution path (no duplication).
        result = await pipeline.run({
            "description": final_description,
            "additional_context": additional_context,
            "preferred_tech_stack": preferred_tech_stack,
            "build_options": build_options,
        })

        if document_id:
            try:
                doc_uuid = UUID(document_id)
                await db.pool.execute(
                    "UPDATE documents SET status = 'completed', updated_at = NOW() WHERE id = $1",
                    doc_uuid,
                )
            except Exception as e:
                logger.warning("Failed to update document status: %s", str(e))

        logger.info(
            "Estimation completed: %s mode=%s",
            result["request_id"],
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


