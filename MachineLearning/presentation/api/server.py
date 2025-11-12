"""
FastAPI Server for Remote ML Operations
========================================

Server che espone API REST per:
- Training modelli
- Inferenza (code generation, classification)
- Monitoring e status

Deploy su istanza Brev/Nvidia con GPU.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import logging
from pathlib import Path
import sys
from datetime import datetime
import torch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from application.services.inference_service import InferenceService
from application.use_cases.train_model import TrainModelUseCase, TrainModelRequest
from domain.models.training_config import TrainingConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="ML Code Intelligence API",
    description="API for remote ML training and inference",
    version="1.0.0"
)

# CORS middleware (permetti richieste dal tuo PC)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione: specifica IP del tuo PC
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
training_jobs: Dict[str, Dict[str, Any]] = {}
inference_service: Optional[InferenceService] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    gpu_available: bool
    gpu_name: Optional[str] = None
    cuda_version: Optional[str] = None
    memory_allocated_gb: Optional[float] = None
    timestamp: str


class InferenceRequest(BaseModel):
    prompt: str = Field(..., description="Code prompt for generation")
    task: str = Field(default="code_generation", description="Task type")
    max_length: int = Field(default=100, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0.1, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    num_return_sequences: int = Field(default=1, ge=1, le=10)


class InferenceResponse(BaseModel):
    generated_code: List[str]
    prompt: str
    inference_time_ms: float
    model_name: str
    device: str


class TrainingJobRequest(BaseModel):
    dataset_path: str = Field(..., description="Path to dataset JSON")
    model_name: str = Field(default="Salesforce/codet5-small")
    task_type: str = Field(default="code_generation")
    num_epochs: int = Field(default=10, ge=1, le=100)
    batch_size: int = Field(default=8, ge=1, le=128)
    learning_rate: float = Field(default=5e-5, ge=1e-6, le=1e-3)
    output_dir: str = Field(default="models/trained_model")
    device: Optional[str] = None


class TrainingJobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    started_at: str


class TrainingStatusResponse(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Optional[float] = None
    current_epoch: Optional[int] = None
    total_epochs: Optional[int] = None
    loss: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ClassificationRequest(BaseModel):
    code: str = Field(..., description="Code to classify")
    task: str = Field(default="security", description="Classification task")


class ClassificationResponse(BaseModel):
    label: str
    confidence: float
    all_scores: Dict[str, float]
    code: str
    inference_time_ms: float


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "service": "ML Code Intelligence API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check server health and GPU availability"""
    gpu_available = torch.cuda.is_available()
    gpu_name = None
    cuda_version = None
    memory_allocated = None

    if gpu_available:
        gpu_name = torch.cuda.get_device_name(0)
        cuda_version = torch.version.cuda
        memory_allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)  # GB

    return HealthResponse(
        status="healthy",
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        cuda_version=cuda_version,
        memory_allocated_gb=round(memory_allocated, 2) if memory_allocated else None,
        timestamp=datetime.now().isoformat()
    )


# ============================================================================
# Inference Endpoints
# ============================================================================

@app.post("/api/v1/inference/generate", response_model=InferenceResponse, tags=["Inference"])
async def generate_code(request: InferenceRequest):
    """
    Generate code from prompt

    Example:
    ```
    POST /api/v1/inference/generate
    {
        "prompt": "def calculate_fibonacci(n):",
        "max_length": 150,
        "temperature": 0.7
    }
    ```
    """
    global inference_service

    try:
        # Lazy load inference service
        if inference_service is None:
            logger.info("Initializing InferenceService...")
            inference_service = InferenceService(
                models_dir="models",
                default_device="cuda" if torch.cuda.is_available() else "cpu"
            )

        # Generate
        import time
        start_time = time.time()

        generated = inference_service.generate_code(
            prompt=request.prompt,
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p,
            num_return_sequences=request.num_return_sequences
        )

        inference_time = (time.time() - start_time) * 1000  # ms

        return InferenceResponse(
            generated_code=generated if isinstance(generated, list) else [generated],
            prompt=request.prompt,
            inference_time_ms=round(inference_time, 2),
            model_name="code_generator",
            device=str(inference_service.device)
        )

    except Exception as e:
        logger.error(f"Inference failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.post("/api/v1/inference/classify", response_model=ClassificationResponse, tags=["Inference"])
async def classify_code(request: ClassificationRequest):
    """
    Classify code (e.g., security analysis)

    Example:
    ```
    POST /api/v1/inference/classify
    {
        "code": "import os; os.system('rm -rf /')",
        "task": "security"
    }
    ```
    """
    global inference_service

    try:
        if inference_service is None:
            inference_service = InferenceService(
                models_dir="models",
                default_device="cuda" if torch.cuda.is_available() else "cpu"
            )

        import time
        start_time = time.time()

        if request.task == "security":
            result = inference_service.detect_security_issues(request.code)
        else:
            result = inference_service.classify_text(request.code, task=request.task)

        inference_time = (time.time() - start_time) * 1000

        return ClassificationResponse(
            label=result.get("label", "unknown"),
            confidence=result.get("confidence", 0.0),
            all_scores=result.get("all_scores", {}),
            code=request.code,
            inference_time_ms=round(inference_time, 2)
        )

    except Exception as e:
        logger.error(f"Classification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


# ============================================================================
# Training Endpoints
# ============================================================================

@app.post("/api/v1/training/start", response_model=TrainingJobResponse, tags=["Training"])
async def start_training(request: TrainingJobRequest, background_tasks: BackgroundTasks):
    """
    Start training job (async)

    Example:
    ```
    POST /api/v1/training/start
    {
        "dataset_path": "data/dataset.json",
        "model_name": "Salesforce/codet5-small",
        "num_epochs": 20,
        "batch_size": 16
    }
    ```
    """
    # Generate job ID
    job_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Validate dataset exists
    dataset_path = Path(request.dataset_path)
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset not found: {request.dataset_path}")

    # Create job record
    training_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0.0,
        "current_epoch": 0,
        "total_epochs": request.num_epochs,
        "started_at": datetime.now().isoformat(),
        "request": request.dict()
    }

    # Start training in background
    background_tasks.add_task(run_training_job, job_id, request)

    return TrainingJobResponse(
        job_id=job_id,
        status="pending",
        message="Training job started",
        started_at=training_jobs[job_id]["started_at"]
    )


@app.get("/api/v1/training/status/{job_id}", response_model=TrainingStatusResponse, tags=["Training"])
async def get_training_status(job_id: str):
    """
    Get training job status

    Example:
    ```
    GET /api/v1/training/status/train_20250106_103000
    ```
    """
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    job = training_jobs[job_id]

    return TrainingStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress"),
        current_epoch=job.get("current_epoch"),
        total_epochs=job.get("total_epochs"),
        loss=job.get("loss"),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        error=job.get("error")
    )


@app.get("/api/v1/training/jobs", tags=["Training"])
async def list_training_jobs():
    """List all training jobs"""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "started_at": job.get("started_at")
            }
            for job_id, job in training_jobs.items()
        ],
        "total": len(training_jobs)
    }


# ============================================================================
# Background Tasks
# ============================================================================

async def run_training_job(job_id: str, request: TrainingJobRequest):
    """Run training job in background"""
    try:
        logger.info(f"Starting training job {job_id}")
        training_jobs[job_id]["status"] = "running"

        # Create training config
        config = TrainingConfig(
            model_name=request.model_name,
            task_type=request.task_type,
            num_epochs=request.num_epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            output_dir=request.output_dir,
            device=request.device or ("cuda" if torch.cuda.is_available() else "cpu")
        )

        # Create use case request
        use_case_request = TrainModelRequest(
            dataset_path=request.dataset_path,
            config=config
        )

        # Execute training
        use_case = TrainModelUseCase()
        result = use_case.execute(use_case_request)

        # Update job status
        training_jobs[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "current_epoch": request.num_epochs,
            "completed_at": datetime.now().isoformat(),
            "result": {
                "model_path": str(result.model_path),
                "final_loss": result.metrics.get("final_loss") if result.metrics else None
            }
        })

        logger.info(f"Training job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Training job {job_id} failed: {e}", exc_info=True)
        training_jobs[job_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


# ============================================================================
# Main
# ============================================================================

def main():
    """Start server"""
    import argparse

    parser = argparse.ArgumentParser(description="ML Code Intelligence API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")

    args = parser.parse_args()

    logger.info(f"Starting ML Code Intelligence API Server on {args.host}:{args.port}")
    logger.info(f"GPU Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"Docs available at: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "presentation.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )


if __name__ == "__main__":
    main()
