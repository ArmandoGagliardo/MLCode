"""
Constants and magic numbers used throughout the project.
Centralizes configuration values for easier maintenance.
"""

# ============================================
# PARSING CONSTANTS
# ============================================

# Minimum valid lengths
MIN_FUNCTION_NAME_LENGTH = 2
MIN_FUNCTION_BODY_LENGTH = 10
MIN_CODE_LENGTH = 10
MIN_DOCSTRING_LENGTH = 5

# Maximum search ranges
MAX_DOCSTRING_LINES_ABOVE = 10  # How many lines to search upward for docstrings
MAX_FUNCTION_LINES = 1000  # Maximum lines for a single function

# Code quality thresholds
MIN_CHARACTERS_FOR_SENTENCE = 30  # Minimum chars for valid sentence
MIN_CHARACTERS_FOR_BLOCK = 200  # Minimum chars for text block
MAX_IDENTIFIER_LENGTH = 100  # Maximum length for valid identifier

# ============================================
# CRAWLING CONSTANTS
# ============================================

# GitHub crawler
DEFAULT_BRANCH = "main"
FALLBACK_BRANCHES = ["master", "develop"]
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Web crawler
USER_AGENT_ROTATION_SIZE = 10
REQUEST_TIMEOUT = 30  # seconds
MAX_REDIRECT_FOLLOW = 5
CRAWL_DELAY = 1  # seconds between requests

# File filtering patterns
EXCLUDED_PATTERNS = [
    "test", "tests", "__test__",
    "setup", "__init__",
    "mock", "fixture",
    "example", "sample",
    ".min.", "bundle"
]

EXCLUDED_EXTENSIONS = [
    ".pyc", ".pyo", ".pyd",
    ".so", ".dll", ".dylib",
    ".class", ".jar",
    ".min.js", ".bundle.js"
]

# ============================================
# TRAINING CONSTANTS
# ============================================

# Default hyperparameters
DEFAULT_BATCH_SIZE = 4
DEFAULT_NUM_EPOCHS = 4
DEFAULT_LEARNING_RATE = 5e-5
DEFAULT_WARMUP_RATIO = 0.1
DEFAULT_WEIGHT_DECAY = 0.01
DEFAULT_MAX_GRAD_NORM = 1.0

# Gradient accumulation
GRADIENT_ACCUMULATION_STEPS = 4

# Early stopping
EARLY_STOPPING_PATIENCE = 3
EARLY_STOPPING_MIN_DELTA = 0.001

# Data splits
TRAIN_SPLIT_RATIO = 0.8
VALIDATION_SPLIT_RATIO = 0.2

# Generation parameters
MAX_GENERATION_LENGTH = 128
NUM_BEAMS = 5
TEMPERATURE = 0.8
TOP_P = 0.95  # Nucleus sampling
TOP_K = 50

# ============================================
# MODEL CONSTANTS
# ============================================

# Pre-trained model names
MODEL_CODET5 = "Salesforce/codet5-base"
MODEL_CODEBERT = "microsoft/codebert-base"
MODEL_GPT2 = "gpt2"

# Tokenizer special tokens
PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"
BOS_TOKEN = "<s>"
EOS_TOKEN = "</s>"

# Maximum sequence lengths
MAX_SOURCE_LENGTH = 512
MAX_TARGET_LENGTH = 128

# ============================================
# TASK IDENTIFICATION CONSTANTS
# ============================================

# Similarity thresholds
TASK_SIMILARITY_THRESHOLD = 0.5
MIN_CONFIDENCE_SCORE = 0.6

# Task types
TASK_CODE_GENERATION = "code_generation"
TASK_CODE_EXPLANATION = "code_explanation"
TASK_TEXT_CLASSIFICATION = "text_classification"
TASK_SECURITY_CLASSIFICATION = "security_classification"

# ============================================
# FILE SYSTEM CONSTANTS
# ============================================

# Dataset filenames
DATASET_GITHUB = "dataset_github.json"
DATASET_LOCAL_PREFIX = "from_local_"
DATASET_CLASSIFICATION = "dataset_classification_v2.json"
DATASET_SECURITY = "dataset_security.json"
DATASET_MIGRATED = "dataset_migrated.json"

# Directory names
DIR_DATASET = "dataset"
DIR_RAW = "raw"
DIR_MODELS = "models"
DIR_LOGS = "logs"
DIR_CACHE = ".cache"

# ============================================
# LOGGING CONSTANTS
# ============================================

# Log levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================
# TEXT PROCESSING CONSTANTS
# ============================================

# Unicode normalization
UNICODE_NORMALIZATION_FORM = "NFKD"  # Compatibility decomposition

# Sentence splitting patterns
SENTENCE_ENDINGS = [".", "!", "?", "。", "！", "？"]
MIN_SENTENCE_WORDS = 3

# Text cleaning
REMOVE_PATTERNS = [
    r'\[\[.*?\]\]',  # Wiki links
    r'\{\{.*?\}\}',  # Wiki templates
    r'<ref>.*?</ref>',  # References
    r'<.*?>',  # HTML tags
]

# Language codes
SUPPORTED_LANGUAGES = ["en", "it", "de", "fr", "es"]

# ============================================
# HASH CONSTANTS
# ============================================

# Hashing for deduplication
HASH_ALGORITHM = "sha256"
CONTENT_HASH_PREFIX_LENGTH = 50  # First N chars for long content
CONTENT_HASH_SUFFIX_LENGTH = 50  # Last N chars for long content

# ============================================
# API CONSTANTS
# ============================================

# GitHub API
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_RAW_URL = "https://raw.githubusercontent.com"
GITHUB_API_VERSION = "v3"

# Rate limiting
API_RATE_LIMIT_MARGIN = 100  # Keep N requests as buffer
API_RATE_LIMIT_CHECK_INTERVAL = 60  # Check every N seconds

# ============================================
# SECURITY CONSTANTS
# ============================================

# Security classification levels
SECURITY_LEVEL_SAFE = 0
SECURITY_LEVEL_LOW = 1
SECURITY_LEVEL_MEDIUM = 2
SECURITY_LEVEL_HIGH = 3
SECURITY_LEVEL_CRITICAL = 4

SECURITY_LABELS = {
    0: "Safe",
    1: "Low Risk",
    2: "Medium Risk",
    3: "High Risk",
    4: "Critical"
}

# ============================================
# VALIDATION CONSTANTS
# ============================================

# Valid programming language identifier patterns
VALID_IDENTIFIER_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'

# File size limits
MAX_FILE_SIZE_MB = 10
MAX_DATASET_SIZE_MB = 1000

# JSON validation
MAX_JSON_NESTING_DEPTH = 10
