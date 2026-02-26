from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

from app.models.project_models import ProjectRequest, FinalPipelineResponse
from app.orchestrator.project_pipeline import ProjectPipeline

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

pipeline: ProjectPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    logger.info("Initializing estimation pipeline...")
    pipeline = ProjectPipeline()
    logger.info("Pipeline ready")
    yield
    logger.info("Shutting down...")


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
    return {"status": "healthy", "pipeline_initialized": pipeline is not None}


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
