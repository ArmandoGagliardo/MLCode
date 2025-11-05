# Glossario (nomenclatura ufficiale)

## Architettura & Pattern

| Concetto            | Nome standard | Note                                               |
| ------------------- | ------------- | -------------------------------------------------- |
| Servizi applicativi | Manager       | Es. ModelManager, StorageManager, DuplicateManager |
| Helper generici     | Utils         | Evitare duplicati con Helpers                      |
| Interfacce          | IXxx          | Es. IParser, IQualityFilter, IStorageProvider      |
| Use Cases           | XxxUseCase    | Application layer orchestration                    |

## Componenti Core

| Componente       | Responsabilità                       | Layer          |
| ---------------- | ------------------------------------ | -------------- |
| TreeSitterParser | Parsing AST multi-linguaggio         | Infrastructure |
| ModelManager     | Gestione modelli ML HuggingFace      | Module/Model   |
| StorageManager   | Upload/download cloud storage        | Infrastructure |
| DuplicateManager | Deduplicazione hash-based            | Module/Utils   |
| AdvancedTrainer  | Training pipeline con FP16/multi-GPU | Module/Model   |
| QualityFilter    | Validazione qualità codice           | Domain         |

## Task Types

| Task                | Descrizione               | Status              |
| ------------------- | ------------------------- | ------------------- |
| code_generation     | Generazione codice da NL  | ✅ Implementato     |
| text_classification | Classificazione testo     | ✅ Implementato     |
| security_analysis   | Rilevamento vulnerabilità | ❌ Pianificato (0%) |

## Linguaggi Supportati

Python, JavaScript, Java, C++, Go, Ruby, Rust (7 totali)

## Storage Providers

AWS S3, DigitalOcean Spaces, MinIO, Azure Blob, GCP Storage, Backblaze B2 (6 totali)

Aggiornare man mano che il dominio evolve.
