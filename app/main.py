from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import logging
import json
from dotenv import load_dotenv

from app.models.project_models import ProjectRequest, FinalPipelineResponse
from app.models.modification_models import ModificationRequest, ModificationResponse
from app.orchestrator.project_pipeline import ProjectPipeline
from app.agents.modification_agent import ModificationAgent
from app.agents.estimation_agent import EstimationAgent
from app.services.calibration_engine import CalibrationEngine
from app.services.database import db

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


@app.post("/estimate", response_model=FinalPipelineResponse)
async def estimate_project(request: ProjectRequest) -> FinalPipelineResponse:
    """
    Execute full estimation pipeline for a project.
    
    Args:
        request: Project request with description and optional context
        
    Returns:
        Complete estimation with domain, features, hours, tech stack, and proposal
    """
    try:
        logger.info(f"Processing estimation request: {request.project_description[:100]}...")
        
        result = await pipeline.run({
            "description": request.project_description,
            "additional_context": request.additional_context,
            "preferred_tech_stack": request.preferred_tech_stack
        })
        
        logger.info(f"Estimation completed: {result['request_id']}")
        
        return FinalPipelineResponse(**result)
        
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


@app.post("/estimate/stream")
async def estimate_project_stream(request: ProjectRequest):
    """
    Execute estimation pipeline with streaming progress updates.
    
    Args:
        request: Project request with description and optional context
        
    Returns:
        Server-Sent Events stream with stage-by-stage progress
    """
    async def event_generator():
        try:
            async for event in pipeline.run_streaming({
                "description": request.project_description,
                "additional_context": request.additional_context,
                "preferred_tech_stack": request.preferred_tech_stack
            }):
                yield f"data: {json.dumps(event)}\n\n"
                
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield f"data: {json.dumps({'stage': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
