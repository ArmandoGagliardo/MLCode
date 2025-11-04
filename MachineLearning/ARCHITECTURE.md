# 🏗️ Architecture Documentation

**Progetto**: ML Code Intelligence System
**Versione**: 2.0.0
**Data**: 2025-11-04
**Architettura**: Clean Architecture + SOLID + DDD

---

## 📋 Table of Contents

1. [Panoramica](#panoramica)
2. [Principi Architetturali](#principi-architetturali)
3. [Struttura Layer](#struttura-layer)
4. [Design Patterns](#design-patterns)
5. [Flussi Principali](#flussi-principali)
6. [Componenti Chiave](#componenti-chiave)
7. [Dependency Injection](#dependency-injection)
8. [Testing Strategy](#testing-strategy)
9. [Decisioni Architetturali](#decisioni-architetturali)

---

## 🎯 Panoramica

### Obiettivo
Sistema modulare per raccogliere, processare e trainare modelli ML su codice sorgente.

### Caratteristiche Chiave
- **Modulare**: Componenti indipendenti con responsabilità ben definite
- **Testabile**: Dependency injection e interfaces permettono easy mocking
- **Estendibile**: Nuovi parser, storage provider, quality filter facilmente aggiungibili
- **Manutenibile**: Clean Architecture separa business logic da implementazioni

---

## 🏛️ Principi Architetturali

### SOLID Principles

#### 1. Single Responsibility Principle (SRP)
Ogni classe ha una sola ragione per cambiare.

**Esempio**:
- `ParserService` → Orchestrazione parsing
- `TreeSitterParser` → Implementazione parsing
- `RadonQualityFilter` → Calcolo quality metrics

#### 2. Open/Closed Principle (OCP)
Aperto all'estensione, chiuso alla modifica.

**Esempio**:
```python
# Nuovo parser: estendi IParser, non modificare esistenti
class MyCustomParser(IParser):
    def parse(self, code, language):
        # Nuova implementazione
        pass
```

#### 3. Liskov Substitution Principle (LSP)
Le sottoclassi devono essere sostituibili con le classi base.

**Esempio**:
```python
# Qualsiasi IParser può essere usato
parser: IParser = TreeSitterParser()  # o
parser: IParser = RegexParser()       # o
parser: IParser = ASTParser()
```

#### 4. Interface Segregation Principle (ISP)
Interfacce specifiche invece di una generale.

**Esempio**:
- `IParser` → Solo metodi di parsing
- `IQualityFilter` → Solo metodi quality
- NON: `IMegaService` con 50 metodi

#### 5. Dependency Inversion Principle (DIP)
Dipendi da astrazioni, non da concrete implementations.

**Esempio**:
```python
class ParserService:
    def __init__(self, parser: IParser):  # Dipende da interfaccia
        self._parser = parser              # NON: TreeSitterParser()
```

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│      Presentation Layer             │  ← CLI, API, UI
│  (presentation/)                    │
├─────────────────────────────────────┤
│      Application Layer              │  ← Use Cases, Services
│  (application/)                     │
├─────────────────────────────────────┤
│      Domain Layer                   │  ← Business Logic, Models
│  (domain/)                          │
├─────────────────────────────────────┤
│      Infrastructure Layer           │  ← DB, APIs, File System
│  (infrastructure/)                  │
└─────────────────────────────────────┘
```

### Dependency Rule
**Le dipendenze puntano SEMPRE verso l'interno (Domain).**

```
Presentation → Application → Domain ← Infrastructure
```

Domain non conosce nulla degli altri layer!

---

## 📁 Struttura Layer

### 1. Domain Layer (`domain/`)

**Responsabilità**: Business logic puro, nessuna dipendenza esterna

```
domain/
├── interfaces/          # Abstract Base Classes
│   ├── parser.py
│   ├── storage.py
│   ├── quality_filter.py
│   └── duplicate_manager.py
├── models/              # Domain entities
│   ├── code_sample.py
│   ├── repository.py
│   ├── training_config.py
│   └── results.py
├── validation/          # Validators
│   └── validators.py
└── exceptions.py        # Custom exceptions
```

**Regole**:
- ❌ NO import da application, infrastructure, presentation
- ❌ NO dipendenze esterne (requests, boto3, etc.)
- ✅ Solo Python standard library
- ✅ Definisce interfacce e regole business

**Esempio**:
```python
# domain/models/code_sample.py
@dataclass
class CodeSample:
    language: str
    code: str
    name: str

    def validate(self) -> List[str]:
        # Pure business validation
        pass
```

### 2. Application Layer (`application/`)

**Responsabilità**: Orchestrazione, use cases

```
application/
├── services/            # Application services
│   ├── parser_service.py
│   ├── data_collection_service.py
│   ├── training_service.py
│   └── storage_service.py
└── use_cases/           # Specific use cases
    ├── collect_github_data.py
    ├── train_model.py
    └── build_dataset.py
```

**Regole**:
- ✅ Può usare domain
- ✅ Dipende da interfaces (non implementations)
- ❌ NO dipendenze dirette su infrastructure
- ✅ Coordina tra domain e infrastructure

**Esempio**:
```python
# application/services/parser_service.py
class ParserService:
    def __init__(self, parser: IParser, quality: IQualityFilter):
        self._parser = parser        # Interface, non implementation
        self._quality = quality

    def parse_and_filter(self, code, lang):
        samples = self._parser.parse(code, lang)
        return [s for s in samples if self._quality.is_acceptable(s)]
```

### 3. Infrastructure Layer (`infrastructure/`)

**Responsabilità**: Implementazioni concrete

```
infrastructure/
├── parsers/             # Parser implementations
│   ├── tree_sitter_parser.py
│   └── language_parsers/
├── storage/             # Storage implementations
│   ├── storage_factory.py
│   └── providers/
│       ├── digitalocean.py
│       ├── s3.py
│       └── local.py
├── quality/             # Quality filter implementations
│   ├── radon_filter.py
│   └── simple_filter.py
├── github/              # GitHub integration
│   └── repository_fetcher.py
├── huggingface/         # HuggingFace integration
│   └── stack_loader.py
└── utils/               # Utility implementations
    ├── duplicate_manager.py
    └── cache_manager.py
```

**Regole**:
- ✅ Implementa interfaces da domain
- ✅ Può usare librerie esterne
- ❌ NON conosce application o presentation
- ✅ Implementazioni sostituibili

**Esempio**:
```python
# infrastructure/parsers/tree_sitter_parser.py
class TreeSitterParser(IParser):  # Implementa interfaccia domain
    def parse(self, code: str, language: str) -> List[Dict]:
        # Implementazione concreta con tree-sitter
        pass
```

### 4. Presentation Layer (`presentation/`)

**Responsabilità**: Interfacce utente

```
presentation/
└── cli/
    ├── main.py          # Entry point
    └── commands/
        ├── collect.py
        ├── train.py
        └── dataset.py
```

**Regole**:
- ✅ Usa application services
- ❌ NO business logic qui
- ✅ Solo parsing argomenti e formattazione output

---

## 🎨 Design Patterns

### 1. Dependency Injection

**Problema**: Tight coupling tra classi
**Soluzione**: Inietta dipendenze via constructor

```python
# ❌ BAD: Tight coupling
class ParserService:
    def __init__(self):
        self.parser = TreeSitterParser()  # Hardcoded!

# ✅ GOOD: Dependency Injection
class ParserService:
    def __init__(self, parser: IParser):
        self.parser = parser  # Injected!

# Usage
service = ParserService(parser=TreeSitterParser())
# OR
service = ParserService(parser=MockParser())  # Easy testing!
```

### 2. Factory Pattern

**Problema**: Creazione complessa di oggetti
**Soluzione**: Factory che gestisce la creazione

```python
# infrastructure/storage/storage_factory.py
class StorageProviderFactory:
    _providers = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[IStorageProvider]):
        cls._providers[name] = provider_class

    @classmethod
    def create(cls, config: StorageConfig) -> IStorageProvider:
        provider_class = cls._providers[config.provider_type]
        return provider_class(config)

# Registration
StorageProviderFactory.register('s3', S3Provider)
StorageProviderFactory.register('digitalocean', DigitalOceanProvider)

# Usage
provider = StorageProviderFactory.create(config)
```

### 3. Repository Pattern

**Problema**: Accoppiamento con data access
**Soluzione**: Repository abstraction

```python
# domain/interfaces/repository.py
class IDatasetRepository(ABC):
    @abstractmethod
    def save(self, samples: List[CodeSample]) -> bool:
        pass

    @abstractmethod
    def load(self, filters: Dict) -> List[CodeSample]:
        pass

# infrastructure/repositories/local_dataset_repository.py
class LocalDatasetRepository(IDatasetRepository):
    def save(self, samples):
        # Save to local filesystem
        pass
```

### 4. Service Layer

**Problema**: Business logic sparsa
**Soluzione**: Services che orchestrano

```python
# application/services/parser_service.py
class ParserService:
    """Orchestrates: parse → quality → dedup"""

    def parse_and_filter(self, code, lang):
        samples = self._parser.parse(code, lang)
        filtered = self._quality_filter.filter(samples)
        unique = self._dedup_manager.deduplicate(filtered)
        return unique
```

---

## 🔄 Flussi Principali

### Data Collection Flow

```
CLI Command
    ↓
CollectDataUseCase (application)
    ↓
DataCollectionService (application)
    ↓
├─→ GitHubClient (infrastructure)     # Fetch repos
├─→ ParserService (application)        # Parse code
│   ├─→ TreeSitterParser (infra)      # Parse
│   ├─→ RadonQualityFilter (infra)    # Filter
│   └─→ DuplicateManager (infra)      # Dedup
└─→ StorageService (application)       # Save
    └─→ StorageProvider (infra)        # Upload
```

### Training Flow

```
CLI Command
    ↓
TrainModelUseCase (application)
    ↓
TrainingService (application)
    ↓
├─→ DatasetLoader (infrastructure)     # Load data
├─→ ModelLoader (infrastructure)       # Load model
├─→ Trainer (infrastructure)           # Train
└─→ Validator (infrastructure)         # Validate
```

---

## 🔑 Componenti Chiave

### ParserService (Reference Implementation)

**File**: `application/services/parser_service.py`

**Responsabilità**:
1. Orchestrazione pipeline parsing
2. Coordinazione quality filtering
3. Gestione duplicate detection

**Pattern Dimostrati**:
- Dependency Injection
- Single Responsibility
- Interface Segregation

**Codice**:
```python
class ParserService:
    def __init__(self, parser: IParser, quality: IQualityFilter, dedup: IDuplicateManager):
        self._parser = parser
        self._quality = quality
        self._dedup = dedup

    def parse_and_filter(self, code, lang, min_quality=60):
        # 1. Parse
        samples = self._parser.parse(code, lang)

        # 2. Quality filter
        filtered = [s for s in samples if self._quality.calculate_score(s) >= min_quality]

        # 3. Dedup
        unique = [s for s in filtered if not self._dedup.is_duplicate(s)]

        return unique
```

**Test**:
```python
def test_parser_service():
    # Mock dependencies
    parser = MockParser()
    quality = MockQualityFilter()
    dedup = MockDuplicateManager()

    # Inject
    service = ParserService(parser, quality, dedup)

    # Test
    result = service.parse_and_filter("code", "python")
    assert len(result) > 0
```

---

## 💉 Dependency Injection

### Container Setup

**File**: `config/container.py`

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Infrastructure
    parser = providers.Singleton(TreeSitterParser)
    quality_filter = providers.Singleton(RadonQualityFilter, min_score=60)
    dedup_manager = providers.Singleton(ASTDuplicateManager)

    # Application Services
    parser_service = providers.Factory(
        ParserService,
        parser=parser,
        quality_filter=quality_filter,
        dedup_manager=dedup_manager
    )
```

### Usage

```python
# Setup container
container = Container()
container.config.from_yaml('config/config.yaml')

# Get services
parser_service = container.parser_service()
samples = parser_service.parse_and_filter(code, 'python')
```

---

## 🧪 Testing Strategy

### Unit Tests
**Target**: Domain logic, no dependencies

```python
# tests/unit/domain/test_code_sample.py
def test_code_sample_validation():
    sample = CodeSample('python', 'def f(): pass', CodeType.FUNCTION, 'f')
    assert sample.is_valid()
```

### Integration Tests
**Target**: Services with real dependencies

```python
# tests/integration/test_parser_service.py
def test_parser_service_integration():
    parser = TreeSitterParser()  # Real implementation
    quality = RadonQualityFilter()
    dedup = ASTDuplicateManager()

    service = ParserService(parser, quality, dedup)
    samples = service.parse_and_filter(code, 'python')
    assert len(samples) > 0
```

### E2E Tests
**Target**: Full workflows

```python
# tests/e2e/test_data_collection.py
def test_full_data_collection_workflow():
    # Collect → Parse → Filter → Save
    result = collect_data_from_repos('python', count=5)
    assert result.success
    assert len(result.samples) > 0
```

---

## 📝 Decisioni Architetturali (ADR)

### ADR-001: Adozione Clean Architecture

**Data**: 2025-11-04
**Status**: Accepted

**Context**:
Il progetto era cresciuto organicamente con main.py monolitico (1388 righe).

**Decision**:
Adottare Clean Architecture con 4 layer separati.

**Consequences**:
✅ Migliore testabilità
✅ Chiara separazione responsabilità
✅ Facilità di estensione
❌ Più file da gestire
❌ Curva di apprendimento iniziale

### ADR-002: Dependency Injection

**Data**: 2025-11-04
**Status**: Accepted

**Context**:
Tight coupling tra componenti rendeva testing difficile.

**Decision**:
Usare DI container per gestire dipendenze.

**Consequences**:
✅ Easy mocking per test
✅ Flessibilità nell'uso di implementazioni
✅ Disaccoppiamento
❌ Setup iniziale più complesso

### ADR-003: Interface-First Design

**Data**: 2025-11-04
**Status**: Accepted

**Context**:
Implementazioni concrete sparse, nessun contratto.

**Decision**:
Definire interfacce (ABC) prima di implementations.

**Consequences**:
✅ Contratti chiari
✅ Sostituibilità
✅ Documentazione implicita
❌ Più file da mantenere

---

## 📚 Risorse

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)
- [Design Patterns](https://refactoring.guru/design-patterns)

---

**Ultimo Aggiornamento**: 2025-11-04
**Versione**: 2.0.0
**Autore**: ML Code Intelligence Team
