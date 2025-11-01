# Machine Learning Multi-Task NLP System

A comprehensive system for collecting, preprocessing, and training transformer models for code generation, classification, and security analysis across multiple programming languages.

## Features

- **Multi-Language Support**: Python, JavaScript, Java, C++, PHP, Go, Ruby, Shell
- **Data Collection**: GitHub crawler, local folder scanner, web text crawler, Wikipedia crawler
- **Advanced Parsing**: Tree-sitter based AST parsing for accurate code extraction
- **ML Tasks**:
  - Code generation (Seq2Seq with CodeT5)
  - Text/Code classification (CodeBERT)
  - Security vulnerability classification (multi-class)
- **Smart Pipeline**: Automatic task identification using SBERT embeddings
- **Training Features**: Multi-GPU, Mixed Precision, Gradient Accumulation, Early Stopping
- **Duplicate Detection**: SHA-256 hash-based deduplication

## Project Structure

```
MachineLearning/
├── config.py                      # Configuration management
├── main.py                        # Main entry point with CLI
├── build_languages.py             # Tree-sitter grammar compiler
├── requirements.txt               # Python dependencies
├── dataset/                       # Training datasets
│   ├── dataset_github.json       # GitHub crawled data
│   ├── dataset_classification*.json
│   ├── dataset_security.json
│   └── raw/                      # Raw crawled files
├── module/
│   ├── data/                     # Dataset loaders
│   ├── model/                    # Model management & training
│   ├── preprocessing/            # Data collection & parsing
│   │   ├── crawlers/            # GitHub, local, web crawlers
│   │   ├── parsers/             # Language-specific parsers
│   │   ├── cleaning/            # Text normalization
│   │   └── searcher/            # Search implementations
│   ├── tasks/                   # ML task implementations
│   ├── scripts/                 # Utility scripts
│   └── ui/                      # Streamlit interface
└── models/                       # Trained model storage
```

## Installation

### 1. Prerequisites

- Python 3.8+
- Git
- (Optional) CUDA-capable GPU for training

### 2. Clone & Install

```bash
git clone <repository-url>
cd MachineLearning
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Build Tree-sitter Grammars

Required for code parsing:

```bash
python build_languages.py
```

### 4. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your GitHub token:

```env
GITHUB_TOKEN=your_github_token_here
```

**How to get a GitHub token:**
1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `public_repo` (for public repos) or `repo` (for private)
4. Copy the token to your `.env` file

⚠️ **SECURITY**: Never commit your `.env` file or expose your token!

## Usage

### Data Collection

**Crawl GitHub repositories:**
```bash
python main.py --crawl_git
```
Crawls 40+ major repositories, extracts functions/classes, saves to `dataset/dataset_github.json`.

**Crawl local folder:**
```bash
python main.py --crawl_local
```
Scans local directories for source files (configure path in `main.py`).

**Crawl web text:**
```bash
python main.py --crawl_web        # DuckDuckGo search
python main.py --crawl_wiki       # Wikipedia articles
python main.py --crawl_website    # Specific website scraping
```

### Model Training

**Train code generation model:**
```bash
python main.py --train code_generation
```

**Train text classifier:**
```bash
python main.py --train text_classification
```

**Train security classifier:**
```bash
python main.py --train security_classification
```

Training configuration in `config.py`:
- Batch size: 4 (default)
- Epochs: 4 (default)
- Learning rate: 5e-5 (default)
- Multi-GPU support enabled
- Mixed precision training (AMP)

### Inference

**Interactive CLI pipeline:**
```bash
python main.py --pipeline
```
Automatically identifies task type and routes to appropriate model.

**Streamlit UI:**
```bash
python main.py --ui
```
Opens web interface at `http://localhost:8501`

### Dataset Validation

```bash
python main.py --validate
```
Validates dataset structure and quality.

## Configuration

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub API token (required) | - |
| `MAX_FILES_PER_REPO` | Max files per repository | 20 |
| `MIN_FUNCTION_LENGTH` | Min chars for valid function | 10 |
| `WEB_CRAWL_MAX_PAGES` | Max pages for web crawling | 100 |
| `DEFAULT_BATCH_SIZE` | Training batch size | 4 |
| `DEFAULT_EPOCHS` | Training epochs | 4 |
| `DEFAULT_LEARNING_RATE` | Training learning rate | 5e-5 |
| `CUDA_VISIBLE_DEVICES` | GPU devices to use | 0,1 |

### Model Paths

Models are saved to `models/` with task-specific subdirectories:
- `models/code_generation/`
- `models/text_classification/`
- `models/security_classification/`

## Supported Languages

| Language | Extension | Parser |
|----------|-----------|--------|
| Python | .py | Tree-sitter |
| JavaScript | .js | Tree-sitter |
| Java | .java | Tree-sitter |
| C++ | .cpp | Tree-sitter |
| PHP | .php | Tree-sitter |
| Go | .go | Tree-sitter |
| Ruby | .rb | Tree-sitter |
| Shell | .sh | Tree-sitter |

## Architecture

### Data Pipeline

1. **Collection**: Crawlers fetch code/text from sources
2. **Parsing**: Tree-sitter extracts functions, classes, docstrings
3. **Cleaning**: Normalize, deduplicate, quality filter
4. **Storage**: JSON datasets with metadata

### Training Pipeline

1. **Dataset Loading**: Custom collate with dynamic padding
2. **Model**: Pre-trained transformer (CodeT5/CodeBERT/GPT-2)
3. **Training**: Custom trainer with advanced features
4. **Checkpointing**: Saves best model based on validation

### Inference Pipeline

1. **Input**: User provides text/code
2. **Task Identification**: SBERT embeddings + cosine similarity
3. **Model Selection**: Routes to appropriate model
4. **Generation**: Beam search with nucleus sampling
5. **Output**: Generated code/classification result

## Advanced Features

### Duplicate Detection
- SHA-256 hashing of content
- Persistent hash storage across runs
- Metadata and path deduplication

### Stealth Crawling
- Rotating user agents
- Retry mechanism with backoff
- Request throttling

### Quality Filtering
- Valid identifier check
- Minimum length requirements
- Structure validation
- Language detection

### Training Optimizations
- Multi-GPU with DataParallel
- Automatic Mixed Precision (AMP)
- Gradient Accumulation (4 steps)
- Early Stopping (patience=3)
- Linear LR Scheduler with warmup

## Troubleshooting

### Common Issues

**"GITHUB_TOKEN not found"**
- Create `.env` file from `.env.example`
- Add your GitHub token

**"Parser not found for extension"**
- Run `python build_languages.py` to build grammars
- Ensure Tree-sitter is installed correctly

**"CUDA out of memory"**
- Reduce batch size in training configuration
- Disable multi-GPU: set `use_gpu=False` in `main.py`
- Reduce `MAX_FILES_PER_REPO` in `.env`

**"Rate limit exceeded" (GitHub API)**
- GitHub API has rate limits
- Authenticated requests: 5000/hour
- Wait or use multiple tokens

**Import errors**
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Activate virtual environment

## Dependencies

Key libraries:
- `transformers==4.51.3` - HuggingFace models
- `torch==2.2.2` - Deep learning
- `tree_sitter` - Code parsing
- `sentence-transformers==4.1.0` - Task identification
- `beautifulsoup4==4.12.2` - Web scraping
- `selenium==4.31.0` - Browser automation
- `streamlit==1.31.1` - Web UI

See `requirements.txt` for complete list.

## Development

### Adding New Languages

1. Add language grammar to `build_languages.py`
2. Add extension mapping in `config.py` → `SUPPORTED_EXTENSIONS`
3. Create parser in `module/preprocessing/parsers/`
4. Update `function_parser.py` with language-specific logic

### Adding New Tasks

1. Create task implementation in `module/tasks/`
2. Add model configuration in `config.py` → `MODEL_PATHS`
3. Update `task_pipeline.py` with task routing
4. Add training logic in `main.py`

### Adding New Crawlers

1. Inherit from `BaseCrawler` in `module/preprocessing/crawlers/`
2. Implement `crawl()` method
3. Add CLI argument in `main.py`
4. Create corresponding function in `main.py`

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Citation

[Add citation information if applicable]

## Contact

[Add contact information]

---

**Built with**: Python, PyTorch, Transformers, Tree-sitter

**Supported by**: HuggingFace, OpenAI, GitHub
