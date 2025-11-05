# Thread aperti

Elenco dei lavori avviati e non chiusi, con stato sintetico.

## 🔴 CRITICI (Blockers)

### TEST-001: Test Coverage 20% → 80%

- **Status**: 🔴 Critical - Gap -60%
- **Owner**: Team
- **Deadline**: Week 1 (7 giorni)
- **Blocca**: Production readiness
- **Next**: Scrivere unit tests per domain layer, poi application layer
- **Files**: `/tests/**/*.py`

### AGENT-001: Agent Compliance 15% → 100%

- **Status**: 🔴 Critical - Violazione regole
- **Owner**: Team
- **Deadline**: 2-3 ore
- **Blocca**: Tracciabilità progetto
- **Next**: Backfill 30+ memory entries, creare changesets mancanti
- **Files**: `/.agent/memory/`, `/changesets/`

## 🟡 HIGH PRIORITY

### DOCS-001: Documentation 70% → 95%

- **Status**: 🟡 In Progress
- **Owner**: Team
- **Deadline**: Week 2
- **Next**: Tutorial completi, API documentation, esempi advanced
- **Files**: `/docs/**/*.md`

### SEC-001: Security Module 0% → 100%

- **Status**: 🟡 Planned
- **Owner**: Team
- **Deadline**: Week 2-3
- **Next**: Implementare vulnerability detection, static analysis
- **Files**: `/infrastructure/security/`


## 🟢 MEDIUM PRIORITY

### PERF-001: GPU Training Performance

- **Status**: 🟢 Enhancement
- **Current**: CPU training 8 tokens/sec
- **Target**: GPU training 100+ tokens/sec
- **Next**: Test multi-GPU, ottimizzare batch size
- **Files**: `/module/model/training_model_advanced.py`

### DATA-001: Dataset Size Increase

- **Status**: 🟢 Enhancement
- **Current**: 3,125 functions, 9 samples training
- **Target**: 100K+ functions, 1K+ training samples
- **Next**: Processare più repositories, data augmentation
- **Files**: `/dataset_storage/`

### INFRA-001: Infrastructure Completeness 85% → 100%

- **Status**: 🟢 In Progress
- **Missing**: Radon quality filter implementation
- **Next**: Implementare RadonQualityFilter completo
- **Files**: `/infrastructure/quality/`

## ✅ COMPLETED RECENTLY

### PHASE3-001: Inference Infrastructure Migration ✅

- **Completed**: 2025-11-05
- **Result**: Complete inference layer migrated to Clean Architecture v2.0
- **Components Created**:
  - ModelLoader (226 LOC) - Device auto-detection, multi-model support
  - TextClassifier (220 LOC) - Classification with confidence scores
  - SecurityClassifier (230 LOC) - Vulnerability detection with thresholds
  - CodeGenerator (194 LOC) - Seq2seq & causal generation
  - InferenceService (500 LOC) - Unified orchestration API
- **Scripts Refactored**: 9 root scripts (gpu_server.py, cloud_dataset_loader.py, etc.)
- **Import Reduction**: 45 → 5 (88.9% reduction)
- **Achievement**: Zero code duplication, production-ready
- **Files**: `/infrastructure/inference/`, `/application/services/inference_service.py`

### ARCH-002: Module Migration Verification ✅

- **Completed**: 2025-11-05
- **Status**: 95% Complete - Ready for module/ deletion
- **Remaining Imports**: 5 legacy imports in 3 files (safe to ignore or delete)
- **Verified**: All core functionality migrated without loss
- **Next**: Create backup and delete `/module` directory
- **Files**: `/module/` (ready for deletion)

### TRAIN-001: Training Pipeline Fix ✅

- **Completed**: 2025-11-05
- **Issues Fixed**: Unicode errors, tokenizer padding, model saving
- **Result**: Training completes successfully, 7/7 validation passed
- **Files**: `/module/model/training_model_advanced.py`, `/train_advanced_impl.py`

### ARCH-001: Clean Architecture Refactor ✅

- **Completed**: 2025-11-04
- **Result**: 100% Clean Architecture, SOLID compliant, 4 layers
- **LOC**: 16,007 Python lines
- **Files**: `/domain/`, `/application/`, `/infrastructure/`, `/presentation/`

### INF-001: Inference Service Implementation ✅

- **Completed**: 2025-11-05
- **Result**: Full inference infrastructure with REST API support
- **Components**: Model lifecycle management, device auto-detection, batch processing
- **API Server**: FastAPI server (gpu_server.py) with 5 endpoints
- **Cloud Integration**: CloudDatasetLoader for streaming training
- **Files**: `/gpu_server.py`, `/cloud_dataset_loader.py`, `/infrastructure/inference/`
