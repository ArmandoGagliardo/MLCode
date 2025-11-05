# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ML Code Intelligence System v2.0** - A production-ready system for extracting code from GitHub repositories, parsing multi-language codebases, filtering for quality, and training ML models. Built with Clean Architecture, SOLID principles, and dependency injection.

**Status**: v2.0.0 (70% complete) - Production-ready core infrastructure
**Languages Supported**: Python, JavaScript, Java, C++, Go, Ruby, Rust

## Quick Commands

### Development

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run CLI (new v2.0 interface)
python -m presentation.cli --help
python -m presentation.cli info
python -m presentation.cli collect --language python --count 10
python -m presentation.cli train --dataset data/dataset.json

# Legacy main.py is DEPRECATED (use CLI instead)
```

### Testing

```bash
# Run integration example (tests the entire stack)
python examples/integration_example.py

# Run full stack example
python examples/full_stack_example.py

# Manual component tests
python -c "from infrastructure.parsers import TreeSitterParser; p = TreeSitterParser(); print(f'OK - {len(p.get_supported_languages())} languages')"
python -c "from infrastructure.quality import HeuristicQualityFilter; f = HeuristicQualityFilter(); print('OK')"
python -c "from infrastructure.duplicate import ASTDuplicateManager; m = ASTDuplicateManager(); print('OK')"

# Note: pytest is not installed - use example scripts for testing
```

### Data Collection

```bash
# Collect code from GitHub repositories
python -m presentation.cli collect --language python --count 20 --min-stars 1000

# Process with quality filtering
python -m presentation.cli collect --language rust --count 5 --min-quality 70

# Output location: datasets/local_backup/code_generation/
```

## Architecture

This project follows **Clean Architecture** with strict separation of concerns across 4 layers:

```
┌─────────────────────────────────────┐
│   Presentation Layer                │  CLI (presentation/cli/), Legacy main.py
│   - CLI commands                    │
│   - User interaction                │
├─────────────────────────────────────┤
│   Application Layer                 │  Services & Use Cases (application/)
│   - ParserService                   │
│   - DataCollectionService           │
│   - StorageService                  │
├─────────────────────────────────────┤
│   Domain Layer                      │  Business Rules (domain/)
│   - 5 Interfaces (IParser, etc.)    │
│   - 4 Models (CodeSample, etc.)     │
│   - 13 Custom Exceptions            │
│   - Validators                      │
├─────────────────────────────────────┤
│   Infrastructure Layer              │  Implementations (infrastructure/)
│   - TreeSitterParser                │
│   - GitHubFetcher                   │
│   - HeuristicQualityFilter          │
│   - ASTDuplicateManager             │
│   - Storage Providers (Local, S3)   │
└─────────────────────────────────────┘
```

### Key Architectural Principles

1. **Dependency Rule**: Dependencies always point inward. Domain has no dependencies. Infrastructure depends on Domain interfaces.

2. **Dependency Injection**: All services receive dependencies via constructor:
   ```python
   # CORRECT - Interface injection
   def __init__(self, parser: IParser, quality_filter: IQualityFilter):
       self._parser = parser

   # INCORRECT - Direct instantiation
   def __init__(self):
       self._parser = TreeSitterParser()  # Don't do this!
   ```

3. **Container Pattern**: Use `config/container.py` for wiring dependencies:
   ```python
   from config.container import Container
   container = Container()
   service = container.parser_service()  # Fully wired with dependencies
   ```

4. **Interface Segregation**: Each interface has a single, focused responsibility. Don't add methods to interfaces unless all implementations need them.

### Layer Responsibilities

**Domain Layer** (`domain/`):
- Defines interfaces (IParser, IStorageProvider, IQualityFilter, IDuplicateManager, IRepositoryFetcher)
- Defines models (CodeSample, Repository, TrainingConfig, Results)
- Contains validators and custom exceptions
- **NO external dependencies** - pure business logic

**Application Layer** (`application/`):
- Services orchestrate between infrastructure components
- Use cases implement specific business workflows
- All dependencies injected via interfaces
- Reference: `application/services/parser_service.py` (canonical example)

**Infrastructure Layer** (`infrastructure/`):
- TreeSitterParser: AST-based multi-language parsing
- GitHubFetcher: GitHub API v3 integration with rate limiting
- HeuristicQualityFilter: Fast quality scoring (0-100)
- ASTDuplicateManager: Detects duplicates ignoring formatting
- Storage providers: Local filesystem, S3-compatible clouds

**Presentation Layer** (`presentation/`):
- CLI interface (primary entry point)
- Legacy `main.py` is DEPRECATED - migrate to CLI

## Common Development Workflows

### Adding a New Parser

1. Create interface implementation in `infrastructure/parsers/`:
   ```python
   from domain.interfaces.parser import IParser

   class MyNewParser(IParser):
       def parse(self, code: str, language: str) -> List[CodeSample]:
           # Implementation
           pass
   ```

2. Register in container (`config/container.py`):
   ```python
   def my_parser(self) -> IParser:
       return MyNewParser()
   ```

3. Use via dependency injection:
   ```python
   service = ParserService(parser=container.my_parser(), ...)
   ```

### Adding a New Storage Provider

1. Implement `IStorageProvider` in `infrastructure/storage/providers/`
2. Register in `StorageProviderFactory` (`infrastructure/storage/storage_factory.py`)
3. Configure in `.env` with `STORAGE_PROVIDER=your_provider`

### Adding a New Quality Filter

1. Implement `IQualityFilter` in `infrastructure/quality/`
2. Inject into `ParserService` via container
3. Quality scoring should return 0-100 (higher = better)

## Configuration

### Environment Variables (`.env` file)

```bash
# GitHub (optional, for higher rate limits)
GITHUB_TOKEN=ghp_xxxxx

# Storage Provider Selection
STORAGE_PROVIDER=local  # Options: local, s3, digitalocean, wasabi, backblaze, cloudflare

# Local Storage Paths
STORAGE_PATH=data/storage
CACHE_PATH=data/cache
TEMP_DIR=data/temp

# Quality Settings
MIN_QUALITY_SCORE=60.0

# AWS S3 (if STORAGE_PROVIDER=s3)
AWS_BUCKET_NAME=your-bucket
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_REGION=us-east-1

# DigitalOcean Spaces (if STORAGE_PROVIDER=digitalocean)
DO_SPACES_NAME=your-space
DO_SPACES_KEY=xxxxx
DO_SPACES_SECRET=xxxxx
DO_SPACES_REGION=nyc3
```

See `.env.example` for complete configuration template.

## Important Files & Locations

### Reference Implementations
- `application/services/parser_service.py` - **Canonical service implementation** (study this first!)
- `infrastructure/parsers/tree_sitter_parser.py` - Multi-language parser
- `infrastructure/github/github_fetcher.py` - GitHub API integration
- `config/container.py` - Dependency injection container

### Documentation
- `CLEAN_ARCHITECTURE_COMPLETE.md` - **Primary architecture reference**
- `README_v2.0.md` - Project overview and quick start
- `MIGRATION_GUIDE.md` - Migration from main.py to CLI
- `docs/architecture.md` - Detailed architecture documentation

### Entry Points
- `python -m presentation.cli` - **Primary CLI** (use this)
- `main.py` - DEPRECATED, will be removed in v3.0.0
- `examples/integration_example.py` - Full working example
- `examples/full_stack_example.py` - Complete demo

### Output Locations
- `datasets/local_backup/code_generation/` - Extracted code samples (JSON)
- `data/storage/` - Local storage base path
- `data/cache/` - Cache files (duplicate hashes, etc.)
- `data/temp/` - Temporary cloned repositories
- `logs/` - Log files

## Design Patterns in Use

1. **Dependency Injection** - Constructor-based injection throughout
2. **Factory Pattern** - `StorageProviderFactory` for creating storage providers
3. **Service Layer** - Services orchestrate business logic
4. **Repository Pattern** - `IRepositoryFetcher` abstracts data source
5. **Retry Pattern** - `@retry` decorator with exponential backoff
6. **Singleton** - Container manages single instances of services

## Code Quality Standards

### When Writing New Code

1. **Always use interfaces** - Depend on `IParser`, not `TreeSitterParser`
2. **Constructor injection** - Pass dependencies via `__init__`
3. **No direct imports between layers** - Use container for wiring
4. **Comprehensive docstrings** - All public methods need examples
5. **Type hints** - Use type annotations everywhere
6. **Error handling** - Use custom exceptions from `domain/exceptions.py`

### Quality Scoring (for code samples)

Quality scores range 0-100:
- **20 pts**: Valid length (10-10000 chars)
- **10 pts**: Valid line count (3-500 lines)
- **20 pts**: No bad patterns (TODO, FIXME, etc.)
- **20 pts**: Has complexity (unique tokens, structure keywords)
- **10 pts**: Not boilerplate
- **10 pts**: Meaningful content
- **10 pts**: Valid syntax

Default minimum: 60.0 (configurable via `MIN_QUALITY_SCORE`)

## Known Issues & Limitations

1. **main.py is deprecated** - Use `python -m presentation.cli` instead
2. **pytest not installed** - Use example scripts for testing
3. **Some comments in Italian** - Ongoing translation to English
4. **Training features incomplete** - Core extraction works, ML training is 60% complete
5. **No CI/CD** - Manual testing required
6. **Cloud storage needs credentials** - Local storage works out of the box

## Migration Notes

### From main.py to CLI

```bash
# OLD (deprecated)
python main.py --collect-data --language python --count 20

# NEW (v2.0+)
python -m presentation.cli collect --language python --count 20

# OLD
python main.py --train code_generation

# NEW
python -m presentation.cli train --dataset data/dataset.json

# OLD
python main.py --validate

# NEW
python -m presentation.cli info --validate
```

See `MIGRATION_GUIDE.md` for complete migration instructions.

## Extending the System

### Adding a New Language Parser

Tree-sitter already supports 7 languages. To add more:

1. Install tree-sitter grammar: `pip install tree-sitter-{language}`
2. Add to `TreeSitterParser._init_parsers()` in `infrastructure/parsers/tree_sitter_parser.py`
3. Add language-specific extraction logic if needed
4. Test with sample code

### Adding a New Use Case

1. Create in `application/use_cases/{your_use_case}.py`
2. Implement with constructor-injected dependencies
3. Register in container if needed
4. Add CLI command in `presentation/cli/commands/`

### Adding Tests

Currently uses example scripts instead of pytest:
- Create runnable example in `examples/`
- Add validation logic with clear success/failure output
- Document in `README_v2.0.md`

## Troubleshooting

### Import Errors
- Ensure virtual environment is activated
- Check `sys.path` includes project root
- Verify all dependencies installed: `pip install -r requirements.txt`

### GitHub Rate Limiting
- Add `GITHUB_TOKEN` to `.env`
- Authenticated: 5000 requests/hour
- Unauthenticated: 60 requests/hour

### Tree-sitter Parse Errors
- Ensure correct language specified
- Check code is syntactically valid
- TreeSitterParser returns empty list on parse failure (doesn't raise)

### Storage Issues
- Default local storage works without configuration
- Cloud storage requires credentials in `.env`
- Check `STORAGE_PROVIDER` environment variable

### Quality Filter Too Strict
- Adjust `MIN_QUALITY_SCORE` in `.env` (lower = more permissive)
- Default is 60.0, valid range is 0-100
- Or pass `min_quality` parameter to service methods

## Project Status

**Overall**: 70% complete - Production-ready for data extraction, partial ML training

| Component | Status | Completion |
|-----------|--------|------------|
| Domain Layer | ✅ Complete | 100% |
| Application Services | ✅ Functional | 75% |
| Infrastructure | ✅ Production Ready | 60% |
| Data Extraction | ✅ Complete | 95% |
| ML Training | ⚠️ Partial | 60% |
| CLI Interface | ✅ Functional | 80% |

**Ready for production**: Code extraction, parsing, quality filtering, GitHub integration
**Not ready**: Advanced ML training, full test coverage, CI/CD

## Additional Resources

- Clean Architecture (Robert C. Martin) - Foundational principles
- SOLID Principles - Applied throughout the codebase
- Tree-sitter Documentation - https://tree-sitter.github.io/tree-sitter/
- GitHub API v3 - https://docs.github.com/en/rest

---

**Last Updated**: 2025-11-05
**Project Version**: 2.0.0
**Architecture**: Clean Architecture + SOLID + Dependency Injection
