"""
Configuration management for the Machine Learning project.
Loads settings from environment variables with fallback defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base paths
BASE_PATH = Path(__file__).resolve().parent
DATASET_PATH = BASE_PATH / "dataset"
MODELS_PATH = BASE_PATH / "models"
RAW_DATA_PATH = DATASET_PATH / "raw"

# GitHub API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com/repos"

# Model Training Configuration
CUDA_VISIBLE_DEVICES = os.getenv("CUDA_VISIBLE_DEVICES", "0,1")
PYTORCH_CUDA_ALLOC_CONF = os.getenv("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

# Dataset Configuration
MAX_FILES_PER_REPO = int(os.getenv("MAX_FILES_PER_REPO", "20"))
MIN_FUNCTION_LENGTH = int(os.getenv("MIN_FUNCTION_LENGTH", "10"))

# Crawling Configuration
WEB_CRAWL_MAX_PAGES = int(os.getenv("WEB_CRAWL_MAX_PAGES", "100"))
CRAWL_TIMEOUT = int(os.getenv("CRAWL_TIMEOUT", "30"))

# Training Configuration
DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "4"))
DEFAULT_EPOCHS = int(os.getenv("DEFAULT_EPOCHS", "4"))
DEFAULT_LEARNING_RATE = float(os.getenv("DEFAULT_LEARNING_RATE", "5e-5"))

# Supported file extensions and languages
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".java": "java",
    ".sh": "shell",
    ".cpp": "cpp",
    ".php": "php",
    ".rb": "ruby",
    ".go": "go",
}

# Model paths configuration
MODEL_PATHS = {
    "code_generation": ("Salesforce/codet5-base", str(DATASET_PATH / "dataset_migrated.json")),
    "text_classification": ("microsoft/codebert-base", str(DATASET_PATH / "dataset_classification_v2.json")),
    "security_classification": ("microsoft/codebert-base", str(DATASET_PATH / "dataset_security.json")),
    "text_generation": ("gpt2", str(DATASET_PATH / "dataset_text_gen.json"))
}

def validate_config():
    """
    Validates critical configuration settings.
    Raises ValueError if required settings are missing.
    """
    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN not found in environment variables. "
            "Please copy .env.example to .env and add your GitHub token."
        )

    # Create required directories
    DATASET_PATH.mkdir(exist_ok=True)
    MODELS_PATH.mkdir(exist_ok=True)
    RAW_DATA_PATH.mkdir(exist_ok=True)

    return True

def get_github_headers():
    """
    Returns headers for GitHub API requests.
    """
    if not GITHUB_TOKEN:
        raise ValueError("GitHub token not configured. Please set GITHUB_TOKEN in .env file.")

    return {
        "Accept": "application/vnd.github.v3.raw",
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": "ml-code-crawler"
    }
