"""
FastAPI Server Backend

Server backend che espone API REST per comunicare con istanze Brev NVIDIA.
Gestisce richieste dal frontend e inoltra alle istanze Brev.

Run:
    uvicorn client.backend.server:app --reload --port 5000
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import usando import assoluti invece che relativi
try:
    from client.backend.brev_client import BrevClient, BrevClientPool, BrevResponse
except ImportError:
    # Fallback per import relativi (quando eseguito come modulo)
    from brev_client import BrevClient, BrevClientPool, BrevResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Brev Client API",
    description="API per comunicare con istanze Brev NVIDIA",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica i domini consentiti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
BREV_API_URL = os.getenv('BREV_API_URL', 'http://localhost:8000')
BREV_API_KEY = os.getenv('BREV_API_KEY')
SERVER_API_KEY = os.getenv('SERVER_API_KEY', 'dev-key-12345')  # Per autenticare client

# Initialize Brev client
# Se hai multiple istanze, usa BrevClientPool
BREV_INSTANCES = os.getenv('BREV_INSTANCES', BREV_API_URL).split(',')

if len(BREV_INSTANCES) > 1:
    brev_client = BrevClientPool(BREV_INSTANCES, BREV_API_KEY)
    logger.info(f"Initialized client pool with {len(BREV_INSTANCES)} instances")
else:
    brev_client = BrevClient(BREV_API_URL, BREV_API_KEY)
    logger.info(f"Initialized single client for {BREV_API_URL}")


# ============================================
# Request/Response Models
# ============================================

class CodeGenerationRequest(BaseModel):
    """Request for code generation"""
    prompt: str = Field(..., description="Descrizione del codice da generare")
    language: str = Field("python", description="Linguaggio di programmazione")
    max_length: int = Field(512, ge=50, le=2048, description="Lunghezza massima output")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Creatività")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a sum function in Python",
                "language": "python",
                "max_length": 256,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }


class TextClassificationRequest(BaseModel):
    """Request for text classification"""
    text: str = Field(..., description="Testo da classificare")
    classes: Optional[List[str]] = Field(None, description="Classi possibili")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is a positive review",
                "classes": ["positive", "negative", "neutral"]
            }
        }


class SecurityAnalysisRequest(BaseModel):
    """Request for security analysis"""
    code: str = Field(..., description="Codice da analizzare")
    language: str = Field("python", description="Linguaggio")
    scan_type: str = Field("quick", description="Tipo di scan (quick/deep)")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def execute(cmd):\n    import os\n    os.system(cmd)",
                "language": "python",
                "scan_type": "quick"
            }
        }


class BatchGenerationRequest(BaseModel):
    """Request for batch code generation"""
    prompts: List[str] = Field(..., description="Lista di prompt")
    language: str = Field("python", description="Linguaggio")

    class Config:
        json_schema_extra = {
            "example": {
                "prompts": [
                    "Create a sum function",
                    "Create a multiply function"
                ],
                "language": "python"
            }
        }


class APIResponse(BaseModel):
    """Standard API response"""
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = None


# ============================================
# Authentication
# ============================================

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica il token di autenticazione"""
    if credentials.credentials != SERVER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Brev Client API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check connection to Brev instance
    if isinstance(brev_client, BrevClientPool):
        health_results = brev_client.health_check_all()
        all_healthy = all(r.success for r in health_results.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "instances": {
                k: {"healthy": v.success, "error": v.error}
                for k, v in health_results.items()
            }
        }
    else:
        response = brev_client.health_check()
        return {
            "status": "healthy" if response.success else "unhealthy",
            "brev_instance": response.success,
            "error": response.error
        }


@app.post("/api/generate", response_model=APIResponse)
async def generate_code(
    request: CodeGenerationRequest,
    token: str = Depends(verify_token)
):
    """
    Genera codice da un prompt

    Richiede autenticazione Bearer token.
    """
    logger.info(f"Code generation request: {request.prompt[:50]}...")

    # Get client
    client = brev_client.get_client() if isinstance(brev_client, BrevClientPool) else brev_client

    # Generate code
    response = client.generate_code(
        prompt=request.prompt,
        language=request.language,
        max_length=request.max_length,
        temperature=request.temperature,
        top_p=request.top_p
    )

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {response.error}"
        )

    return APIResponse(
        success=True,
        data=response.data,
        request_id=response.request_id
    )


@app.post("/api/classify", response_model=APIResponse)
async def classify_text(
    request: TextClassificationRequest,
    token: str = Depends(verify_token)
):
    """
    Classifica un testo

    Richiede autenticazione Bearer token.
    """
    logger.info(f"Text classification request: {request.text[:50]}...")

    client = brev_client.get_client() if isinstance(brev_client, BrevClientPool) else brev_client

    response = client.classify_text(
        text=request.text,
        classes=request.classes
    )

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {response.error}"
        )

    return APIResponse(
        success=True,
        data=response.data,
        request_id=response.request_id
    )


@app.post("/api/security", response_model=APIResponse)
async def analyze_security(
    request: SecurityAnalysisRequest,
    token: str = Depends(verify_token)
):
    """
    Analizza codice per vulnerabilità

    Richiede autenticazione Bearer token.
    """
    logger.info(f"Security analysis request for {request.language} code")

    client = brev_client.get_client() if isinstance(brev_client, BrevClientPool) else brev_client

    response = client.analyze_security(
        code=request.code,
        language=request.language,
        scan_type=request.scan_type
    )

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security analysis failed: {response.error}"
        )

    return APIResponse(
        success=True,
        data=response.data,
        request_id=response.request_id
    )


@app.post("/api/batch", response_model=APIResponse)
async def batch_generate(
    request: BatchGenerationRequest,
    token: str = Depends(verify_token)
):
    """
    Genera codice per multiple richieste

    Richiede autenticazione Bearer token.
    """
    logger.info(f"Batch generation request: {len(request.prompts)} prompts")

    client = brev_client.get_client() if isinstance(brev_client, BrevClientPool) else brev_client

    response = client.batch_generate(
        prompts=request.prompts,
        language=request.language
    )

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch generation failed: {response.error}"
        )

    return APIResponse(
        success=True,
        data=response.data,
        request_id=response.request_id
    )


@app.get("/api/model/info", response_model=APIResponse)
async def get_model_info(token: str = Depends(verify_token)):
    """
    Ottiene informazioni sul modello caricato

    Richiede autenticazione Bearer token.
    """
    client = brev_client.get_client() if isinstance(brev_client, BrevClientPool) else brev_client

    response = client.get_model_info()

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {response.error}"
        )

    return APIResponse(
        success=True,
        data=response.data,
        request_id=response.request_id
    )


@app.get("/api/stats", response_model=APIResponse)
async def get_statistics(token: str = Depends(verify_token)):
    """
    Ottiene statistiche di utilizzo

    Richiede autenticazione Bearer token.
    """
    client = brev_client.get_client() if isinstance(brev_client, BrevClientPool) else brev_client

    response = client.get_statistics()

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {response.error}"
        )

    return APIResponse(
        success=True,
        data=response.data,
        request_id=response.request_id
    )


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Evento di startup"""
    logger.info("Brev Client API starting...")
    logger.info(f"BREV_API_URL: {BREV_API_URL}")
    logger.info(f"Server API Key configured: {bool(SERVER_API_KEY)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento di shutdown"""
    logger.info("Brev Client API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
