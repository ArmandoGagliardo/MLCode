"""
Enhanced configuration management for the Machine Learning project.
Supports multiple environments and unified variable naming.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base paths
BASE_PATH = Path(__file__).resolve().parent
CONFIG_PATH = BASE_PATH / "config"
DATASET_PATH = BASE_PATH / "datasets"
MODELS_PATH = BASE_PATH / "models"
RAW_DATA_PATH = DATASET_PATH / "raw"

class Config:
    """
    Unified configuration manager that loads environment-specific settings.
    """

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            environment: Environment name (local, gpu, production).
                        If None, detects from ENVIRONMENT variable or defaults to 'local'.
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "local")
        self.config = {}
        self._load_configuration()
        self._validate_configuration()

    def _load_configuration(self):
        """Load configuration files based on environment."""

        # Load common configuration first
        common_env = CONFIG_PATH / ".env.common"
        if common_env.exists():
            load_dotenv(common_env, override=False)
            logger.info(f"Loaded common configuration from {common_env}")

        # Load environment-specific configuration
        env_file = CONFIG_PATH / f".env.{self.environment}"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            logger.info(f"Loaded {self.environment} configuration from {env_file}")
        else:
            # Fallback to root .env if exists
            root_env = BASE_PATH / ".env"
            if root_env.exists():
                load_dotenv(root_env, override=True)
                logger.warning(f"Using legacy .env file. Please migrate to config/.env.{self.environment}")
            else:
                logger.warning(f"No configuration file found for environment: {self.environment}")

        # Load all configuration values
        self._load_github_config()
        self._load_cuda_config()
        self._load_training_config()
        self._load_dataset_config()
        self._load_storage_config()
        self._load_api_config()
        self._load_logging_config()

    def _load_github_config(self):
        """Load GitHub configuration."""
        self.config["github"] = {
            "token": os.getenv("GITHUB_TOKEN"),
            "api_url": "https://api.github.com/repos"
        }

    def _load_cuda_config(self):
        """Load CUDA/GPU configuration."""
        self.config["cuda"] = {
            "visible_devices": os.getenv("CUDA_VISIBLE_DEVICES", "-1"),
            "alloc_conf": os.getenv("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True"),
            "launch_blocking": os.getenv("CUDA_LAUNCH_BLOCKING", "0")
        }

    def _load_training_config(self):
        """Load training configuration."""
        self.config["training"] = {
            "batch_size": int(os.getenv("DEFAULT_BATCH_SIZE", "4")),
            "epochs": int(os.getenv("DEFAULT_EPOCHS", "4")),
            "learning_rate": float(os.getenv("DEFAULT_LEARNING_RATE", "5e-5")),
            "max_seq_length": int(os.getenv("MAX_SEQ_LENGTH", "256")),
            "gradient_accumulation_steps": int(os.getenv("GRADIENT_ACCUMULATION_STEPS", "1")),
            "use_amp": os.getenv("USE_AMP", "false").lower() == "true",
            "num_workers": int(os.getenv("NUM_WORKERS", "2")),
            "pin_memory": os.getenv("PIN_MEMORY", "false").lower() == "true",
            "cudnn_benchmark": os.getenv("CUDNN_BENCHMARK", "false").lower() == "true"
        }

    def _load_dataset_config(self):
        """Load dataset configuration."""
        self.config["dataset"] = {
            "max_files_per_repo": int(os.getenv("MAX_FILES_PER_REPO", "20")),
            "min_function_length": int(os.getenv("MIN_FUNCTION_LENGTH", "10")),
            "max_dataset_size": int(os.getenv("MAX_DATASET_SIZE", "1000000")),
            "web_crawl_max_pages": int(os.getenv("WEB_CRAWL_MAX_PAGES", "100")),
            "crawl_timeout": int(os.getenv("CRAWL_TIMEOUT", "30")),
            "crawl_delay": float(os.getenv("CRAWL_DELAY", "1.5"))
        }

    def _load_storage_config(self):
        """Load storage configuration with standardized naming."""
        provider = os.getenv("STORAGE_PROVIDER", "local")

        self.config["storage"] = {
            "provider": provider,
            "local_dataset_dir": os.getenv("LOCAL_DATASET_DIR", "datasets"),
            "local_models_dir": os.getenv("LOCAL_MODELS_DIR", "models"),
            "remote_dataset_prefix": os.getenv("REMOTE_DATASET_PREFIX", "datasets"),
            "remote_models_prefix": os.getenv("REMOTE_MODELS_PREFIX", "models"),
            "auto_sync_on_startup": os.getenv("AUTO_SYNC_ON_STARTUP", "false").lower() == "true",
            "auto_backup_after_training": os.getenv("AUTO_BACKUP_AFTER_TRAINING", "false").lower() == "true",
            "auto_download_datasets": os.getenv("AUTO_DOWNLOAD_DATASETS", "false").lower() == "true"
        }

        # Load provider-specific credentials with standardized naming
        self._load_storage_credentials()

    def _load_storage_credentials(self):
        """Load cloud storage credentials with standardized naming."""

        # Backblaze B2
        self.config["storage"]["backblaze"] = {
            "bucket_name": os.getenv("BACKBLAZE_BUCKET_NAME"),
            "key_id": os.getenv("BACKBLAZE_KEY_ID"),
            "application_key": os.getenv("BACKBLAZE_APPLICATION_KEY"),
            "endpoint_url": os.getenv("BACKBLAZE_ENDPOINT_URL", "https://s3.us-west-002.backblazeb2.com")
        }

        # Wasabi
        self.config["storage"]["wasabi"] = {
            "bucket_name": os.getenv("WASABI_BUCKET_NAME"),
            "access_key_id": os.getenv("WASABI_ACCESS_KEY_ID"),
            "secret_access_key": os.getenv("WASABI_SECRET_ACCESS_KEY"),
            "region": os.getenv("WASABI_REGION", "us-east-1"),
            "endpoint_url": os.getenv("WASABI_ENDPOINT_URL", "https://s3.wasabisys.com")
        }

        # AWS S3
        self.config["storage"]["aws"] = {
            "bucket_name": os.getenv("AWS_BUCKET_NAME"),
            "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "region": os.getenv("AWS_REGION", "us-east-1")
        }

        # DigitalOcean Spaces (Standardized from DO_SPACES_*)
        # Support both old and new variable names for backward compatibility
        self.config["storage"]["digitalocean"] = {
            "bucket_name": os.getenv("DO_BUCKET_NAME") or os.getenv("DO_SPACES_NAME"),
            "access_key_id": os.getenv("DO_ACCESS_KEY_ID") or os.getenv("DO_SPACES_KEY"),
            "secret_access_key": os.getenv("DO_SECRET_ACCESS_KEY") or os.getenv("DO_SPACES_SECRET"),
            "region": os.getenv("DO_REGION") or os.getenv("DO_SPACES_REGION", "nyc3"),
            "endpoint_url": os.getenv("DO_ENDPOINT_URL", "https://nyc3.digitaloceanspaces.com")
        }

        # Cloudflare R2 (Standardized from CLOUDFLARE_R2_*)
        # Support both old and new variable names for backward compatibility
        self.config["storage"]["cloudflare"] = {
            "bucket_name": os.getenv("CLOUDFLARE_BUCKET_NAME") or os.getenv("CLOUDFLARE_R2_BUCKET"),
            "account_id": os.getenv("CLOUDFLARE_ACCOUNT_ID") or os.getenv("CLOUDFLARE_R2_ACCOUNT_ID"),
            "access_key_id": os.getenv("CLOUDFLARE_ACCESS_KEY_ID") or os.getenv("CLOUDFLARE_R2_ACCESS_KEY"),
            "secret_access_key": os.getenv("CLOUDFLARE_SECRET_ACCESS_KEY") or os.getenv("CLOUDFLARE_R2_SECRET_KEY"),
            "endpoint_url": os.getenv("CLOUDFLARE_ENDPOINT_URL")
        }

    def _load_api_config(self):
        """Load API server configuration."""
        self.config["api"] = {
            "port": int(os.getenv("API_PORT", "8000")),
            "host": os.getenv("API_HOST", "127.0.0.1"),
            "enable_auth": os.getenv("ENABLE_AUTH", "false").lower() == "true",
            "api_key": os.getenv("API_KEY"),
            "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
            "max_request_size": int(os.getenv("MAX_REQUEST_SIZE", "10485760")),
            "request_timeout": int(os.getenv("REQUEST_TIMEOUT", "60")),
            "rate_limit": int(os.getenv("RATE_LIMIT", "60")),
            "enable_rate_limit": os.getenv("ENABLE_RATE_LIMIT", "false").lower() == "true"
        }

    def _load_logging_config(self):
        """Load logging configuration."""
        self.config["logging"] = {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file": os.getenv("LOG_FILE"),
            "colors": os.getenv("LOG_COLORS", "true").lower() == "true",
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        }

    def _validate_configuration(self):
        """Validate critical configuration settings."""

        # Check GitHub token only if needed
        if not self.config["github"]["token"] and self.environment != "local":
            logger.warning(
                "GITHUB_TOKEN not found. Some features may be limited. "
                "Set it in config/.env.common or config/.env.{} file.".format(self.environment)
            )

        # Create required directories
        DATASET_PATH.mkdir(exist_ok=True)
        MODELS_PATH.mkdir(exist_ok=True)
        RAW_DATA_PATH.mkdir(exist_ok=True)

        # Create logs directory if logging to file
        if self.config["logging"]["file"]:
            log_dir = Path(self.config["logging"]["file"]).parent
            log_dir.mkdir(exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'training.batch_size')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_github_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        token = self.config["github"]["token"]
        if not token:
            raise ValueError(
                f"GitHub token not configured for environment: {self.environment}. "
                f"Please set GITHUB_TOKEN in config/.env.common or config/.env.{self.environment}"
            )

        return {
            "Accept": "application/vnd.github.v3.raw",
            "Authorization": f"token {token}",
            "User-Agent": "ml-code-crawler"
        }

    def is_gpu_available(self) -> bool:
        """Check if GPU is available based on configuration."""
        return self.config["cuda"]["visible_devices"] != "-1"

    def get_storage_credentials(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get storage credentials for specified provider.

        Args:
            provider: Storage provider name. If None, uses configured provider.

        Returns:
            Dictionary of credentials for the provider
        """
        provider = provider or self.config["storage"]["provider"]

        if provider not in self.config["storage"]:
            raise ValueError(f"Unknown storage provider: {provider}")

        return self.config["storage"][provider]

    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"Config(environment='{self.environment}', gpu={self.is_gpu_available()})"


# Create global configuration instance
config = Config()

# Export commonly used values for backward compatibility
GITHUB_TOKEN = config.get("github.token")
GITHUB_API_URL = config.get("github.api_url")
CUDA_VISIBLE_DEVICES = config.get("cuda.visible_devices")
PYTORCH_CUDA_ALLOC_CONF = config.get("cuda.alloc_conf")
MAX_FILES_PER_REPO = config.get("dataset.max_files_per_repo")
MIN_FUNCTION_LENGTH = config.get("dataset.min_function_length")
WEB_CRAWL_MAX_PAGES = config.get("dataset.web_crawl_max_pages")
CRAWL_TIMEOUT = config.get("dataset.crawl_timeout")
DEFAULT_BATCH_SIZE = config.get("training.batch_size")
DEFAULT_EPOCHS = config.get("training.epochs")
DEFAULT_LEARNING_RATE = config.get("training.learning_rate")

# Model and file configurations (unchanged)
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

MODEL_PATHS = {
    "code_generation": ("Salesforce/codet5-base", str(DATASET_PATH / "dataset_migrated.json")),
    "text_classification": ("microsoft/codebert-base", str(DATASET_PATH / "dataset_classification_v2.json")),
    "security_classification": ("microsoft/codebert-base", str(DATASET_PATH / "dataset_security.json")),
    "text_generation": ("gpt2", str(DATASET_PATH / "dataset_text_gen.json"))
}

# Legacy functions for backward compatibility
def validate_config():
    """Legacy validation function."""
    return True

def get_github_headers():
    """Legacy function to get GitHub headers."""
    return config.get_github_headers()

# Log configuration status
logger.info(f"Configuration loaded: {config}")
logger.info(f"Environment: {config.environment}")
logger.info(f"GPU Available: {config.is_gpu_available()}")
logger.info(f"Storage Provider: {config.get('storage.provider')}")