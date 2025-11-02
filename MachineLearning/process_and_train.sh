#!/bin/bash

###############################################################################
# Process and Train Script
#
# This script automates the complete workflow:
# 1. Processes GitHub repositories to extract code
# 2. Downloads HuggingFace datasets
# 3. Saves all data to cloud storage
# 4. Trains models using cloud datasets
#
# Usage:
#   bash process_and_train.sh [OPTIONS]
#
# Options:
#   --skip-processing   Skip data processing phase
#   --skip-training     Skip model training phase
#   --workers NUM       Number of parallel workers (default: 4)
#   --repos-only        Only process GitHub repos
#   --huggingface-only  Only process HuggingFace datasets
#   --help              Show this help message
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SKIP_PROCESSING=false
SKIP_TRAINING=false
WORKERS=4
REPOS_ONLY=false
HUGGINGFACE_ONLY=false
START_TIME=$(date +%s)

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-processing)
            SKIP_PROCESSING=true
            shift
            ;;
        --skip-training)
            SKIP_TRAINING=true
            shift
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --repos-only)
            REPOS_ONLY=true
            shift
            ;;
        --huggingface-only)
            HUGGINGFACE_ONLY=true
            shift
            ;;
        --help)
            head -n 25 "$0" | tail -n 22
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

log_section() {
    echo -e "${CYAN}"
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo -e "${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Function to show progress
show_progress() {
    local current=$1
    local total=$2
    local percent=$((current * 100 / total))
    local bars=$((percent / 2))

    printf "\r["
    printf "%0.s=" $(seq 1 $bars)
    printf "%0.s " $(seq $bars 49)
    printf "] %d%% (%d/%d)" $percent $current $total
}

# Check system information
check_system() {
    log_section "SYSTEM CHECK"

    # Check Python
    log_info "Checking Python version..."
    python --version

    # Check GPU
    log_info "Checking GPU availability..."
    if command -v nvidia-smi &> /dev/null; then
        log_success "NVIDIA GPU detected:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1
    else
        log_warning "No NVIDIA GPU detected. Processing will use CPU."
    fi

    # Check disk space
    log_info "Checking disk space..."
    df -h . | tail -1

    # Check memory
    log_info "Checking system memory..."
    if command -v free &> /dev/null; then
        free -h | grep "^Mem:" | awk '{print "Total: " $2 ", Available: " $7}'
    fi

    echo ""
}

# Check environment setup
check_environment() {
    log_section "ENVIRONMENT CHECK"

    # Check if .env exists
    if [ ! -f ".env" ]; then
        log_error ".env file not found!"
        log_info "Please create .env from .env.example and configure:"
        echo "  - GITHUB_TOKEN (required for GitHub repos)"
        echo "  - Cloud storage credentials (for dataset storage)"
        exit 1
    fi

    # Check required Python packages
    log_info "Checking Python packages..."
    python -c "import transformers" 2>/dev/null || {
        log_warning "transformers not installed. Installing..."
        pip install transformers
    }

    python -c "import datasets" 2>/dev/null || {
        log_warning "datasets not installed. Installing..."
        pip install datasets
    }

    log_success "Environment check complete"
    echo ""
}

# Process GitHub repositories
process_github_repos() {
    log_section "PROCESSING GITHUB REPOSITORIES"

    if [ ! -f "repo_list.txt" ]; then
        log_error "repo_list.txt not found!"
        return 1
    fi

    # Count total repos
    TOTAL_REPOS=$(grep -c "^https://" repo_list.txt || echo "0")
    log_info "Found $TOTAL_REPOS repositories to process"

    # Process in batches
    log_info "Starting GitHub repository processing with $WORKERS workers..."

    python github_repo_processor.py \
        --repos-file repo_list.txt \
        --workers $WORKERS \
        2>&1 | while IFS= read -r line; do
            echo -e "${MAGENTA}[GitHub]${NC} $line"
        done

    log_success "GitHub repository processing complete"
    echo ""
}

# Process HuggingFace datasets
process_huggingface_datasets() {
    log_section "PROCESSING HUGGINGFACE DATASETS"

    log_info "Downloading and processing HuggingFace datasets..."

    # Code generation datasets
    log_info "Processing code generation datasets..."
    python bulk_processor.py \
        --source huggingface \
        --dataset codeparrot/github-code \
        --max-samples 100000 \
        2>&1 | while IFS= read -r line; do
            echo -e "${MAGENTA}[HuggingFace]${NC} $line"
        done

    # Text classification datasets
    log_info "Processing text classification datasets..."
    for dataset in imdb ag_news yelp_review_full; do
        python bulk_processor.py \
            --source huggingface \
            --dataset $dataset \
            --max-samples 50000 \
            2>&1 | while IFS= read -r line; do
                echo -e "${MAGENTA}[HuggingFace]${NC} $line"
            done
    done

    # Security datasets
    log_info "Processing security classification datasets..."
    python bulk_processor.py \
        --source huggingface \
        --dataset code_x_glue_cc_defect_detection \
        2>&1 | while IFS= read -r line; do
            echo -e "${MAGENTA}[HuggingFace]${NC} $line"
        done

    log_success "HuggingFace dataset processing complete"
    echo ""
}

# Verify cloud datasets
verify_cloud_datasets() {
    log_section "VERIFYING CLOUD DATASETS"

    log_info "Checking datasets on cloud storage..."

    python -c "
from module.storage.storage_manager import StorageManager
import json

storage = StorageManager()
if storage.connect():
    # List dataset files
    for task_type in ['code_generation', 'text_classification', 'security_classification']:
        files = storage.list_files(f'datasets/{task_type}/')
        if not files:
            files = storage.list_files(f'datasets/processed/{task_type}/')
        print(f'{task_type}: {len(files)} files')
        if files:
            print(f'  Sample files: {files[:3]}')
else:
    print('Failed to connect to cloud storage')
" 2>&1 | while IFS= read -r line; do
        echo -e "${CYAN}[Cloud]${NC} $line"
    done

    echo ""
}

# Train models with cloud datasets
train_models() {
    log_section "TRAINING MODELS WITH CLOUD DATASETS"

    log_info "Starting model training using cloud datasets..."

    # Train code generation model
    log_info "Training code generation model..."
    if python main.py --train code_generation; then
        log_success "Code generation model trained successfully"
    else
        log_error "Failed to train code generation model"
    fi

    # Train text classification model
    log_info "Training text classification model..."
    if python main.py --train text_classification; then
        log_success "Text classification model trained successfully"
    else
        log_error "Failed to train text classification model"
    fi

    # Train security classification model
    log_info "Training security classification model..."
    if python main.py --train security_classification; then
        log_success "Security classification model trained successfully"
    else
        log_error "Failed to train security classification model"
    fi

    log_success "All models trained successfully!"
    echo ""
}

# Process all data sources
process_all_data() {
    if [ "$REPOS_ONLY" = true ]; then
        process_github_repos
    elif [ "$HUGGINGFACE_ONLY" = true ]; then
        process_huggingface_datasets
    else
        # Process both sources
        process_github_repos
        process_huggingface_datasets
    fi

    # Verify datasets
    verify_cloud_datasets
}

# Main execution
main() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║           AUTOMATED DATA PROCESSING & TRAINING               ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # System and environment checks
    check_system
    check_environment

    # Phase 1: Data Processing
    if [ "$SKIP_PROCESSING" = false ]; then
        log_section "PHASE 1: DATA PROCESSING"
        process_all_data
    else
        log_info "Skipping data processing phase (--skip-processing)"
    fi

    # Phase 2: Model Training
    if [ "$SKIP_TRAINING" = false ]; then
        log_section "PHASE 2: MODEL TRAINING"
        train_models
    else
        log_info "Skipping model training phase (--skip-training)"
    fi

    # Calculate total time
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    HOURS=$((DURATION / 3600))
    MINUTES=$(((DURATION % 3600) / 60))
    SECONDS=$((DURATION % 60))

    log_section "PROCESSING COMPLETE"
    log_success "Total processing time: ${HOURS}h ${MINUTES}m ${SECONDS}s"

    # Show final statistics
    echo -e "${CYAN}"
    echo "============================================================"
    echo "SUMMARY"
    echo "============================================================"
    echo -e "${NC}"

    if [ "$SKIP_PROCESSING" = false ]; then
        echo "Data Processing:"
        echo "  - GitHub repositories processed"
        echo "  - HuggingFace datasets downloaded"
        echo "  - Data saved to cloud storage"
    fi

    if [ "$SKIP_TRAINING" = false ]; then
        echo ""
        echo "Models Trained:"
        [ -d "models/code_generation" ] && echo "  ✓ Code Generation Model"
        [ -d "models/text_classification" ] && echo "  ✓ Text Classification Model"
        [ -d "models/security_classification" ] && echo "  ✓ Security Classification Model"
    fi

    echo ""
    echo -e "${GREEN}Ready for inference!${NC}"
    echo "Start the GPU server with: uvicorn gpu_server:app --host 0.0.0.0 --port 8000"
}

# Run main function
main

# Exit successfully
exit 0