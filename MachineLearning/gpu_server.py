"""
GPU Instance API Server
========================

FastAPI server for machine learning inference on GPU instances.

This server runs ON the GPU instance (e.g., Brev) after training completes.
It loads trained models and exposes REST API endpoints for inference.

Architecture:
    - Uses Clean Architecture v2.0
    - InferenceService orchestrates all model operations
    - Dependency injection via Container

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

# Import application services (Clean Architecture v2.0)
from application.services.inference_service import InferenceService
from infrastructure.inference import GenerationConfig
from domain.exceptions import InferenceError
from config.container import Container

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

# Global inference service (loaded on startup)
inference_service: Optional[InferenceService] = None
container: Optional[Container] = None

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
    """Load all trained models on server startup using Clean Architecture"""
    global inference_service, container

    logger.info("Starting GPU Inference Server (Clean Architecture v2.0)...")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        logger.info(f"CUDA version: {torch.version.cuda}")
        logger.info(f"GPU device: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU count: {torch.cuda.device_count()}")

    # Initialize DI container
    container = Container()

    # Get inference service with auto device detection
    inference_service = container.inference_service(device=None)

    loaded_count = 0

    # Load code generation model
    code_gen_path = MODEL_PATHS["code_generation"]
    if os.path.exists(code_gen_path):
        try:
            logger.info(f"Loading code generation model from {code_gen_path}...")
            # Configure generation with optimal parameters
            config = GenerationConfig(
                max_new_tokens=128,
                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                num_beams=5,
                early_stopping=True
            )
            inference_service.load_code_generator(
                model_path=code_gen_path,
                model_type='seq2seq',
                config=config,
                local_files_only=True
            )
            logger.info("Code generation model loaded successfully!")
            loaded_count += 1
        except InferenceError as e:
            logger.error(f"Failed to load code generation model: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading code generation model: {e}")
    else:
        logger.warning(f"Code generation model not found at {code_gen_path}")

    # Load text classification model
    text_class_path = MODEL_PATHS["text_classification"]
    if os.path.exists(text_class_path):
        try:
            logger.info(f"Loading text classification model from {text_class_path}...")
            # Define label names if available (adjust based on your model)
            label_names = ["negative", "positive"]  # Binary classification
            inference_service.load_text_classifier(
                model_path=text_class_path,
                label_names=label_names,
                local_files_only=True
            )
            logger.info("Text classification model loaded successfully!")
            loaded_count += 1
        except InferenceError as e:
            logger.error(f"Failed to load text classification model: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading text classification model: {e}")
    else:
        logger.warning(f"Text classification model not found at {text_class_path}")

    # Load security classification model
    security_class_path = MODEL_PATHS["security_classification"]
    if os.path.exists(security_class_path):
        try:
            logger.info(f"Loading security classification model from {security_class_path}...")
            # Define security labels
            label_names = ["safe", "warning", "critical"]
            inference_service.load_security_classifier(
                model_path=security_class_path,
                label_names=label_names,
                vulnerability_threshold=0.5,
                local_files_only=True
            )
            logger.info("Security classification model loaded successfully!")
            loaded_count += 1
        except InferenceError as e:
            logger.error(f"Failed to load security classification model: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading security classification model: {e}")
    else:
        logger.warning(f"Security classification model not found at {security_class_path}")

    logger.info(f"Models loaded: {loaded_count}/{len(MODEL_PATHS)}")

    if loaded_count == 0:
        logger.warning("[WARNING] No models loaded! Make sure to train models before starting the server.")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if inference_service is None:
        models_loaded = {
            "code_generation": False,
            "text_classification": False,
            "security_classification": False
        }
    else:
        loaded = inference_service.get_loaded_models()
        models_loaded = {
            "code_generation": loaded.get('code_generator', False),
            "text_classification": loaded.get('text_classifier', False),
            "security_classification": loaded.get('security_classifier', False)
        }

    return {
        "status": "healthy",
        "gpu_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "models_loaded": models_loaded
    }


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """List loaded models and their information"""
    models_info = {}

    if inference_service is None:
        for name in MODEL_PATHS:
            models_info[name] = {
                "loaded": False,
                "device": None,
                "path": MODEL_PATHS[name]
            }
    else:
        loaded = inference_service.get_loaded_models()
        device_str = str(inference_service.device) if hasattr(inference_service, 'device') else "auto"

        models_info["code_generation"] = {
            "loaded": loaded.get('code_generator', False),
            "device": device_str if loaded.get('code_generator', False) else None,
            "path": MODEL_PATHS["code_generation"]
        }
        models_info["text_classification"] = {
            "loaded": loaded.get('text_classifier', False),
            "device": device_str if loaded.get('text_classifier', False) else None,
            "path": MODEL_PATHS["text_classification"]
        }
        models_info["security_classification"] = {
            "loaded": loaded.get('security_classifier', False),
            "device": device_str if loaded.get('security_classifier', False) else None,
            "path": MODEL_PATHS["security_classification"]
        }

    return {"models": models_info}


@app.post("/api/generate", response_model=GenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code from description"""
    try:
        if inference_service is None or not inference_service.is_code_generator_loaded():
            raise HTTPException(
                status_code=503,
                detail="Code generation model not loaded. Please train the model first."
            )

        logger.info(f"Generating code for prompt: {request.prompt[:100]}...")

        # Configure generation with request parameters
        config = GenerationConfig(
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            do_sample=True,
            num_beams=5,
            early_stopping=True
        )

        # Generate code using InferenceService
        generated_code = inference_service.generate_code(
            prompt=request.prompt,
            config=config
        )

        return {
            "success": True,
            "data": {
                "code": generated_code,
                "prompt": request.prompt
            }
        }

    except HTTPException:
        raise
    except InferenceError as e:
        logger.error(f"Code generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during code generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    """Classify text (binary classification)"""
    try:
        if inference_service is None or not inference_service.is_text_classifier_loaded():
            raise HTTPException(
                status_code=503,
                detail="Text classification model not loaded. Please train the model first."
            )

        logger.info(f"Classifying text: {request.text[:100]}...")

        # Classify using InferenceService
        result = inference_service.classify_text(
            text=request.text,
            return_confidence=True,
            return_all_scores=False
        )

        return {
            "success": True,
            "data": {
                "prediction": result['label'],
                "label": result.get('label_name', 'unknown'),
                "confidence": result.get('confidence', 0.0),
                "text": request.text
            }
        }

    except HTTPException:
        raise
    except InferenceError as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during classification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/security", response_model=ClassificationResponse)
async def analyze_security(request: SecurityAnalysisRequest):
    """Analyze code for security vulnerabilities"""
    try:
        if inference_service is None or not inference_service.is_security_classifier_loaded():
            raise HTTPException(
                status_code=503,
                detail="Security classification model not loaded. Please train the model first."
            )

        logger.info(f"Analyzing code for security issues...")

        # Analyze using InferenceService
        result = inference_service.classify_security(
            text=request.code,
            return_confidence=True,
            return_all_scores=False
        )

        return {
            "success": True,
            "data": {
                "prediction": result['label'],
                "level": result.get('label_name', 'unknown'),
                "is_vulnerable": result.get('is_vulnerable', False),
                "confidence": result.get('confidence', 0.0),
                "code": request.code
            }
        }

    except HTTPException:
        raise
    except InferenceError as e:
        logger.error(f"Security analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during security analysis: {e}")
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
