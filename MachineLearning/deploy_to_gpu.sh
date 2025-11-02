#!/bin/bash

###############################################################################
# GPU Instance Deployment Script
#
# This script sets up the ML project on a GPU instance (e.g., Brev, AWS, GCP)
# and runs the complete workflow: setup → train → inference
#
# Usage:
#   bash deploy_to_gpu.sh [OPTIONS]
#
# Options:
#   --skip-training    Skip model training (use existing models)
#   --skip-datasets    Skip dataset download from cloud storage
#   --port PORT        API server port (default: 8000)
#   --help             Show this help message
#
# Environment Variables (set these before running):
#   GITHUB_TOKEN       Required for private repos
#   STORAGE_PROVIDER   Cloud storage provider (optional)
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SKIP_TRAINING=false
SKIP_DATASETS=false
API_PORT=8000

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-training)
            SKIP_TRAINING=true
            shift
            ;;
        --skip-datasets)
            SKIP_DATASETS=true
            shift
            ;;
        --port)
            API_PORT="$2"
            shift 2
            ;;
        --help)
            head -n 25 "$0" | tail -n 18
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

###############################################################################
# Main Deployment Script
###############################################################################

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║           GPU Instance Deployment Script                     ║"
echo "║           Machine Learning Training & Inference              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Check prerequisites
log_info "Checking prerequisites..."
check_command python3
check_command pip
check_command git

# Check CUDA availability
if command -v nvidia-smi &> /dev/null; then
    log_success "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    log_warning "nvidia-smi not found. GPU may not be available."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Setup Python virtual environment
log_info "Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    log_success "Virtual environment created"
else
    log_warning "Virtual environment already exists, skipping creation"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source .venv/bin/activate || {
    log_error "Failed to activate virtual environment"
    exit 1
}
log_success "Virtual environment activated"

# Step 3: Install dependencies
log_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    log_success "Dependencies installed successfully"
else
    log_error "requirements.txt not found!"
    exit 1
fi

# Step 4: Setup environment configuration
log_info "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_warning "Created .env from .env.example"
        log_warning "⚠️  Please edit .env and add your GITHUB_TOKEN and other credentials"
        log_warning "⚠️  Required: GITHUB_TOKEN for dataset access"
        read -p "Press Enter after you've configured .env, or Ctrl+C to exit..."
    else
        log_error ".env.example not found!"
        exit 1
    fi
else
    log_success ".env already exists"
fi

# Step 5: Build tree-sitter grammars
log_info "Building tree-sitter language grammars..."
if [ -f "build_languages.py" ]; then
    python build_languages.py || {
        log_warning "Failed to build tree-sitter grammars (continuing anyway)"
    }
    log_success "Tree-sitter grammars built"
else
    log_warning "build_languages.py not found, skipping tree-sitter setup"
fi

# Step 6: Download datasets (optional)
if [ "$SKIP_DATASETS" = false ]; then
    log_info "Checking for dataset files..."

    # Check if datasets directory exists and has files
    if [ -d "datasets" ] && [ "$(ls -A datasets 2>/dev/null)" ]; then
        log_success "Datasets directory exists and is not empty"
    else
        log_warning "Datasets directory is empty or missing"
        read -p "Do you want to download datasets from cloud storage? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Downloading datasets from cloud storage..."
            python main.py --storage-download || {
                log_error "Failed to download datasets"
                log_warning "You may need to configure cloud storage credentials in .env"
                exit 1
            }
            log_success "Datasets downloaded successfully"
        else
            log_warning "Skipping dataset download. Make sure datasets are available before training."
        fi
    fi
else
    log_info "Skipping dataset download (--skip-datasets flag)"
fi

# Step 7: Train models
if [ "$SKIP_TRAINING" = false ]; then
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                  Starting Model Training                     ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Train code generation model
    log_info "Training code generation model..."
    if python main.py --train code_generation; then
        log_success "Code generation model trained successfully"
    else
        log_error "Failed to train code generation model"
        exit 1
    fi

    # Train text classification model
    log_info "Training text classification model..."
    if python main.py --train text_classification; then
        log_success "Text classification model trained successfully"
    else
        log_error "Failed to train text classification model"
        exit 1
    fi

    # Train security classification model
    log_info "Training security classification model..."
    if python main.py --train security_classification; then
        log_success "Security classification model trained successfully"
    else
        log_error "Failed to train security classification model"
        exit 1
    fi

    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              All Models Trained Successfully!                ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
else
    log_info "Skipping training (--skip-training flag)"

    # Verify models exist
    log_info "Verifying trained models exist..."
    missing_models=0
    for model in code_generation text_classification security_classification; do
        if [ ! -d "models/$model" ]; then
            log_error "Model not found: models/$model"
            missing_models=$((missing_models + 1))
        else
            log_success "Found model: models/$model"
        fi
    done

    if [ $missing_models -gt 0 ]; then
        log_error "Some models are missing. Please train them first or remove --skip-training flag."
        exit 1
    fi
fi

# Step 8: Start inference server
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              Starting Inference API Server                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

log_info "Starting GPU Inference Server on port $API_PORT..."
log_info "Server will be available at: http://0.0.0.0:$API_PORT"
log_info "Health check: http://0.0.0.0:$API_PORT/health"
log_info "API docs: http://0.0.0.0:$API_PORT/docs"
echo ""
log_warning "Press Ctrl+C to stop the server"
echo ""

# Start server with uvicorn
if command -v uvicorn &> /dev/null; then
    uvicorn gpu_server:app --host 0.0.0.0 --port $API_PORT --reload
else
    log_error "uvicorn not installed. Installing..."
    pip install uvicorn
    uvicorn gpu_server:app --host 0.0.0.0 --port $API_PORT --reload
fi
