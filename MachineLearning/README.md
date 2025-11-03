# Machine Learning Multi-Language Code Extraction & Training System

A system for extracting code from GitHub repositories and training ML models across 7 programming languages, with advanced quality filtering, cloud storage integration, and automated training pipeline.

> **📊 Project Status: Development (v0.8 - 80% Complete)**
> Core extraction and training pipelines are functional. Some features are experimental.
> See [Project Status](#-project-status) below for details.

> **🎉 NEW: Complete Training Pipeline Implemented!**
> Train ML models with your extracted data in 30 minutes. See [SISTEMA_COMPLETO.md](SISTEMA_COMPLETO.md) for full details.

## ✨ Features

### Data Extraction ✅ 100% Working
- **7 Programming Languages**: Python, JavaScript, Java, C++, Go, Ruby, Rust
- **GitHub Integration**: Automatic repository cloning and processing
- **Tree-Sitter Parsing**: Advanced AST-based code extraction
- **Quality Filtering**: Language-specific validation and complexity checks
- **Duplicate Detection**: Hash-based deduplication system
- **Progress Monitoring**: Real-time progress bars and statistics
- **6,674+ Functions**: Already extracted and ready for training

### Machine Learning Training ✅ Implemented
- **Code Generation Models**: Train models to generate code from natural language
- **Multi-Task Support**: Code generation, classification
- **Security Analysis**: ⚠️ Experimental (In Development - 25% complete)
- **GPU Acceleration**: Automatic multi-GPU training support
- **Model Fine-tuning**: Pre-trained model fine-tuning (CodeGen, CodeT5, etc.)
- **Quick Demo**: Train a model in 30 minutes with `example_training.py`
- **Production Pipeline**: Complete training with `main.py --train`
- **Inference Ready**: Use trained models with `example_use_trained_model.py`

## 📊 Proven Results

Successfully tested on real-world repositories:
- **Python**: 225 functions from psf/requests
- **JavaScript**: 259 functions from axios/axios
- **Go**: 216 functions from spf13/cobra
- **Rust**: 506 functions from clap-rs/clap
- **Java**: 713 functions from google/gson
- **C++**: 566 functions from nlohmann/json
- **Ruby**: 640 functions from rails/rails

**Total: 3,125+ functions extracted** across 7 languages

## 🚀 Quick Start

**NEW**: See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for a 5-minute tutorial!

### 1. Installation

```bash
git clone <repository-url>
cd MachineLearning
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. First Extraction (Choose One)

**Option A: Interactive Interface** (Easiest)
```bash
python main.py
# Choose 1, enter: https://github.com/psf/requests
```

**Option B: Example Script**
```bash
python example_single_repo.py
```

**Option C: Bulk Processing**
```bash
# Create repo_list.txt with URLs
python bulk_processor.py --source github --repos repo_list.txt
```

### 3. View Results

```bash
# Check output
dir datasets\local_backup\code_generation\*.json

# Analyze results
python example_analyze_output.py
```

## 📚 Documentation

### Quick Start Guides
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - ⚡ Data extraction in 5 minutes
- **[QUICK_START_TRAINING.md](QUICK_START_TRAINING.md)** - 🎓 Model training in 10 minutes
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - 📋 Command cheat sheet

### Complete Guides
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - 📖 Complete data extraction guide
- **[GUIDA_TRAINING.md](GUIDA_TRAINING.md)** - 🚀 Complete training pipeline guide
- **[debug/README.md](debug/README.md)** - 🐛 Testing and debugging
- **[docs/README.md](docs/README.md)** - 📚 Technical documentation

## 📖 Example Scripts

### Data Extraction
- `example_single_repo.py` - Extract from single GitHub repository
- `example_bulk_processing.py` - Batch process multiple repositories
- `example_analyze_output.py` - Analyze extraction results and statistics

### Model Training
- `example_training.py` - Simple training demo with your extracted data
- `main.py --train` - Production training pipeline
- `gpu_server.py` - REST API inference server

## 🛠️ Requirements

### Core Dependencies
- Python 3.8+
- tree-sitter 0.25.0+ (7 language parsers)
- boto3 (cloud storage)
- GitPython (repository cloning)

### Tree-sitter Language Parsers

All parsers are automatically installed via pip:
```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-java tree-sitter-cpp tree-sitter-go tree-sitter-ruby tree-sitter-rust
```bash
# Install dependencies
pip install -r requirements.txt

# Activate virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### Configuration

1. **GitHub Token** (Optional, for higher rate limits)
   Create `.env` file:
   ```env
   GITHUB_TOKEN=your_github_token_here
   ```

2. **Cloud Storage** (Optional, for automatic upload)
   Configure in `.env`:
   ```env
   DO_SPACES_KEY=your_digitalocean_key
   DO_SPACES_SECRET=your_digitalocean_secret
   DO_SPACES_REGION=nyc3
   DO_SPACES_BUCKET=your-bucket-name
   ```

### Basic Usage

**Extract from a single repository:**
```bash
python main.py
# Then select option: Process GitHub Repository
# Enter repository URL: https://github.com/user/repo
```

**Bulk processing from a list:**
```bash
python bulk_processor.py --source github --repos repo_list.txt
```

**Process with specific language:**
```bash
python bulk_processor.py --source github --repos repo_list.txt --language python
```

### Advanced Usage

**Custom repository list (`repo_list.txt`):**
```
https://github.com/psf/requests
https://github.com/axios/axios
https://github.com/spf13/cobra
```

**Bulk processing options:**
```bash
# Process from GitHub
python bulk_processor.py --source github --repos repo_list.txt

# Process local directory
python bulk_processor.py --source local --path /path/to/code

# Custom batch size
python bulk_processor.py --source github --repos repo_list.txt --batch_size 200
```

**Output locations:**
- Local: `dataset_storage/local_backup/code_generation/`
- Cloud: Automatic upload to configured storage (if enabled)
- Logs: `logs/` directory

## 📁 Project Structure

```
MachineLearning/
├── main.py                          # Main entry point
├── bulk_processor.py                # Bulk repository processing
├── github_repo_processor.py         # GitHub repository handler
├── config.py                        # Configuration management
├── requirements.txt                 # Python dependencies
├── repo_list.txt                    # Repository list for bulk processing
│
├── module/                          # Core modules
│   ├── preprocessing/              
│   │   ├── universal_parser_new.py # Multi-language AST parser
│   │   ├── function_parser.py      # Function extraction logic
│   │   ├── code_quality_filter.py  # Quality validation
│   │   └── ...
│   ├── storage/                    
│   │   └── storage_manager.py      # Cloud storage integration
│   └── utils/                      
│       └── duplicate_manager.py    # Deduplication system
│
├── datasets/                        # Output datasets
│   ├── local_backup/               # Local storage
│   │   └── code_generation/        # Extracted functions
│   └── duplicates_cache.json       # Duplicate tracking
│
├── debug/                           # Test & debug files
│   ├── test_*.py                   # Test scripts
│   ├── debug_*.py                  # Debug utilities
│   └── README.md                   # Debug documentation
│
├── docs/                            # Documentation
│   ├── BUG_FIXES_*.md             # Fix documentation
│   ├── IMPLEMENTATION_STATUS.md    # Feature status
│   └── ...                         # Technical docs
│
└── logs/                            # Log files
```

## 🔧 Supported Languages

| Language   | Parser Status | Extraction | Quality Filter | Test Results |
|------------|--------------|------------|----------------|--------------|
| Python     | ✅ Working    | ✅ Yes     | ✅ Yes         | 225 functions |
| JavaScript | ✅ Working    | ✅ Yes     | ✅ Yes         | 259 functions |
| Go         | ✅ Working    | ✅ Yes     | ✅ Yes         | 216 functions |
| Rust       | ✅ Working    | ✅ Yes     | ✅ Yes         | 506 functions |
| Java       | ✅ Working    | ✅ Yes     | ✅ Yes         | 713 functions |
| C++        | ✅ Working    | ✅ Yes     | ✅ Yes         | 566 functions |
| Ruby       | ✅ Working    | ✅ Yes     | ✅ Yes         | 640 functions |

### Language-Specific Features

- **AST Parsing**: Tree-sitter based parsing for accurate code structure analysis
- **Function Extraction**: Signature, body, parameters, return types, documentation
- **Quality Filtering**: Language-aware complexity checks and validation
- **Indentation**: Automatic normalization for Python
- **Nested Structures**: Support for methods in classes, nested functions

## 🛠️ Technical Features

### Code Extraction
- **Tree-Sitter Integration**: Modern AST parsing for 7 languages
- **Smart Extraction**: Function signatures, bodies, parameters, return types
- **Documentation**: Automatic docstring/comment extraction
- **Quality Control**: Multi-stage validation and filtering

### Quality Filtering
- Length validation (min/max characters and lines)
- Complexity scoring (unique tokens, structure keywords)
- Boilerplate detection and removal
- Syntax validation (language-specific)
- Meaningful content verification

### Data Management
- **Deduplication**: Hash-based with persistent cache
- **Batch Processing**: Configurable batch sizes for memory efficiency
- **Progress Tracking**: Real-time progress bars and statistics
- **Graceful Shutdown**: CTRL+C handling with cleanup

### Cloud Integration
- **Storage**: S3-compatible (DigitalOcean Spaces, AWS S3, MinIO)
- **Auto-Upload**: Automatic dataset synchronization
- **Backup**: Local + cloud redundancy
- **Metadata**: Timestamps, repository info, language tags

## 📊 Output Format

Each extracted function is saved as JSON:
```json
{
  "task_type": "code_generation",
  "language": "python",
  "func_name": "calculate_sum",
  "name": "calculate_sum",
  "body": "{\n    return sum(numbers)\n}",
  "signature": "def calculate_sum(numbers):",
  "input": "Write a python function called 'calculate_sum' with arguments: (numbers)",
  "output": "def calculate_sum(numbers):\n    return sum(numbers)"
}
```

## 🧪 Testing & Debugging

All test and debug files are in the `debug/` folder:
- `test_all_languages_final.py` - Complete multi-language test
- `debug_*_ast.py` - AST structure analysis for each language
- `test_*_extraction.py` - Language-specific extraction tests

See `debug/README.md` for full documentation.

## 📚 Documentation

Technical documentation is in the `docs/` folder:
- Implementation details
- Bug fixes and improvements
- Security guidelines
- Setup guides

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

[Your License Here]

## 🙋 Support

For issues, questions, or contributions, please open an issue on GitHub.

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

## 📊 Project Status

### Overall Completion: ~80%

| Component | Status | Completion | Notes |
|-----------|--------|------------|-------|
| **Data Extraction Pipeline** | ✅ Production Ready | 95% | Fully functional, tested on 7 languages |
| Universal Parser | ✅ Working | 90% | Tree-sitter based, supports 8+ languages |
| Quality Filter | ✅ Working | 85% | Language-specific validation |
| Duplicate Detection | ✅ Working | 85% | Hash-based deduplication |
| GitHub Crawler | ✅ Working | 80% | Repository cloning and processing |
| Bulk Processor | ✅ Working | 75% | Parallel processing, needs more testing |
| **Machine Learning** | ✅ Functional | 70% | Core training works, needs validation |
| Model Training | ✅ Working | 75% | Basic training functional |
| Advanced Trainer | ⚠️ Partial | 60% | Needs end-to-end testing |
| Model Manager | ✅ Working | 80% | Load/save functionality works |
| Inference Pipeline | ⚠️ Partial | 50% | Needs more testing |
| **Storage & Cloud** | ✅ Functional | 85% | Multi-provider support |
| Storage Manager | ✅ Working | 85% | 5 cloud providers supported |
| Local Storage | ✅ Working | 100% | Fully functional |
| Cloud Sync | ⚠️ Partial | 70% | Needs credentials testing |
| **Security Features** | ⚠️ Experimental | 25% | In early development |
| Security Crawler | ⚠️ Partial | 30% | NVD API integration works |
| Pattern Detection | ❌ Not Implemented | 0% | Planned feature |
| ML-based Detection | ❌ Not Implemented | 0% | Planned feature |
| Security Dashboard | ❌ Not Implemented | 0% | Planned feature |
| **Testing & Quality** | ⚠️ Basic | 40% | Improved recently |
| Unit Tests | ⚠️ Basic | 50% | 34 tests added, more needed |
| Integration Tests | ⚠️ Basic | 30% | Basic pipeline tests |
| Validation Scripts | ✅ Working | 80% | End-to-end validation available |
| CI/CD Pipeline | ❌ Not Configured | 0% | Not set up yet |

### Production Readiness

**Ready for Production:**
- Data extraction from GitHub repositories
- Code parsing for Python, JavaScript, Java, Go, Rust, Ruby, C++
- Quality filtering and deduplication
- Local storage and dataset creation
- Basic model training (with supervision)

**Not Ready for Production:**
- Security vulnerability detection (25% complete)
- Automated model validation
- Cloud storage (needs credential configuration)
- Advanced training features (needs testing)
- UI/Dashboard components

### Known Issues

1. **Encoding Bug**: Fixed in v0.8.1 - `check_dependencies.py` now works on Windows
2. **Empty Dataset Directory**: Sample dataset added in v0.8.1
3. **Mixed Language Comments**: Partially fixed - main files converted to English
4. **No CI/CD**: Tests exist but no automated runner configured
5. **Large Model Files**: 481MB in models/ directory, should use Git LFS

### Validation

To validate your installation:
```bash
# Check dependencies
python check_dependencies.py

# Validate complete pipeline
python validate_pipeline.py

# Run test suite
pytest -v
```

### Roadmap

**Short Term (v0.9 - Next 4 weeks):**
- [ ] Complete end-to-end testing
- [ ] Add model validation metrics
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Complete English translation of all comments
- [ ] Add more unit tests (target: 80% coverage)

**Medium Term (v1.0 - Next 3 months):**
- [ ] Production-ready model training
- [ ] Complete security features or remove from docs
- [ ] Docker configuration
- [ ] Performance benchmarks
- [ ] Comprehensive documentation

**Long Term (v2.0+):**
- [ ] Web UI for monitoring
- [ ] Real-time training dashboard
- [ ] API server for inference
- [ ] Multi-node distributed training
- [ ] Support for 20+ programming languages

### Getting Help

- **Installation Issues**: Run `python check_dependencies.py`
- **Pipeline Issues**: Run `python validate_pipeline.py`
- **Test Failures**: See [tests/README.md](tests/README.md)
- **General Questions**: Check [docs/README.md](docs/README.md)

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
