"""
GPU Instance API Server

This server runs ON the GPU instance (e.g., Brev) after training completes.
It loads the trained models and exposes REST API endpoints for inference.

Usage:
    uvicorn gpu_server:app --host 0.0.0.0 --port 8000

Endpoints:
    POST /api/generate - Code generation
    POST /api/classify - Text classification
    POST /api/security - Security analysis
    GET  /health - Health check
    GET  /models - List loaded models
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import torch
import logging
import os
from pathlib import Path

# Import inference engines
from module.tasks.inference_engine import InferenceEngine
from module.tasks.text_classifier import TextClassifier
from module.tasks.security_classifier import SecurityClassifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="GPU Inference Server",
    description="Machine Learning inference server for trained models",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model paths
MODEL_PATHS = {
    "code_generation": "models/code_generation",
    "text_classification": "models/text_classification",
    "security_classification": "models/security_classification"
}

# Global model instances (loaded on startup)
models: Dict[str, Any] = {}

# Request/Response models
class CodeGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Code description or task")
    max_tokens: Optional[int] = Field(128, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.8, description="Sampling temperature")
    top_p: Optional[float] = Field(0.95, description="Nucleus sampling threshold")

class ClassificationRequest(BaseModel):
    text: str = Field(..., description="Text to classify")

class SecurityAnalysisRequest(BaseModel):
    code: str = Field(..., description="Code to analyze for security issues")

class GenerationResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None

class ClassificationResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    gpu_available: bool
    cuda_version: Optional[str]
    models_loaded: Dict[str, bool]

class ModelsResponse(BaseModel):
    models: Dict[str, Dict[str, Any]]


@app.on_event("startup")
async def load_models():
    """Load all trained models on server startup"""
    logger.info("Starting GPU Inference Server...")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        logger.info(f"CUDA version: {torch.version.cuda}")
        logger.info(f"GPU device: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU count: {torch.cuda.device_count()}")

    # Load code generation model
    code_gen_path = MODEL_PATHS["code_generation"]
    if os.path.exists(code_gen_path):
        try:
            logger.info(f"Loading code generation model from {code_gen_path}...")
            models["code_generation"] = InferenceEngine(code_gen_path)
            logger.info("Code generation model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load code generation model: {e}")
            models["code_generation"] = None
    else:
        logger.warning(f"Code generation model not found at {code_gen_path}")
        models["code_generation"] = None

    # Load text classification model
    text_class_path = MODEL_PATHS["text_classification"]
    if os.path.exists(text_class_path):
        try:
            logger.info(f"Loading text classification model from {text_class_path}...")
            models["text_classification"] = TextClassifier(text_class_path)
            logger.info("Text classification model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load text classification model: {e}")
            models["text_classification"] = None
    else:
        logger.warning(f"Text classification model not found at {text_class_path}")
        models["text_classification"] = None

    # Load security classification model
    security_class_path = MODEL_PATHS["security_classification"]
    if os.path.exists(security_class_path):
        try:
            logger.info(f"Loading security classification model from {security_class_path}...")
            models["security_classification"] = SecurityClassifier(security_class_path)
            logger.info("Security classification model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load security classification model: {e}")
            models["security_classification"] = None
    else:
        logger.warning(f"Security classification model not found at {security_class_path}")
        models["security_classification"] = None

    loaded_count = sum(1 for m in models.values() if m is not None)
    logger.info(f"Models loaded: {loaded_count}/{len(MODEL_PATHS)}")

    if loaded_count == 0:
        logger.warning("⚠️  No models loaded! Make sure to train models before starting the server.")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gpu_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "models_loaded": {
            name: model is not None
            for name, model in models.items()
        }
    }


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """List loaded models and their information"""
    models_info = {}

    for name, model in models.items():
        if model is not None:
            device = getattr(model, 'device', None)
            models_info[name] = {
                "loaded": True,
                "device": str(device) if device else "unknown",
                "path": MODEL_PATHS[name]
            }
        else:
            models_info[name] = {
                "loaded": False,
                "device": None,
                "path": MODEL_PATHS[name]
            }

    return {"models": models_info}


@app.post("/api/generate", response_model=GenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code from description"""
    try:
        if models.get("code_generation") is None:
            raise HTTPException(
                status_code=503,
                detail="Code generation model not loaded. Please train the model first."
            )

        logger.info(f"Generating code for prompt: {request.prompt[:100]}...")

        # Generate code
        generated_code = models["code_generation"].generate(request.prompt)

        return {
            "success": True,
            "data": {
                "code": generated_code,
                "prompt": request.prompt
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    """Classify text (binary classification)"""
    try:
        if models.get("text_classification") is None:
            raise HTTPException(
                status_code=503,
                detail="Text classification model not loaded. Please train the model first."
            )

        logger.info(f"Classifying text: {request.text[:100]}...")

        # Classify
        prediction = models["text_classification"].classify(request.text)

        # Map prediction to label
        label = "positive" if prediction == 1 else "negative"

        return {
            "success": True,
            "data": {
                "prediction": int(prediction),
                "label": label,
                "text": request.text
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/security", response_model=ClassificationResponse)
async def analyze_security(request: SecurityAnalysisRequest):
    """Analyze code for security vulnerabilities"""
    try:
        if models.get("security_classification") is None:
            raise HTTPException(
                status_code=503,
                detail="Security classification model not loaded. Please train the model first."
            )

        logger.info(f"Analyzing code for security issues...")

        # Analyze
        prediction = models["security_classification"].classify(request.code)

        # Map prediction to security level
        # Assuming 0 = safe, 1 = warning, 2 = critical (adjust based on your model)
        security_levels = ["safe", "warning", "critical"]
        level = security_levels[prediction] if prediction < len(security_levels) else "unknown"

        return {
            "success": True,
            "data": {
                "prediction": int(prediction),
                "level": level,
                "code": request.code
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GPU Inference Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "models": "/models",
            "generate": "/api/generate",
            "classify": "/api/classify",
            "security": "/api/security"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
