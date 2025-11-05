# Decision Log

Registro umano-legibile delle decisioni architetturali e di processo.

- Formato sintetico: data, titolo, contesto, alternative, decisione, conseguenze, follow-up.

## 2025-11-05 - Fix Training Pipeline Unicode & Tokenizer

- **Data:** 2025-11-05
- **Titolo:** Risoluzione errori critici nel training pipeline
- **Contesto:** Training pipeline falliva con errori Unicode (Windows cp1252), tokenizer senza pad_token, e model saving non implementato
- **Alternative:**
  - Disabilitare emoji completamente
  - Usare encoding UTF-8 forzato
  - Implementare tokenizer custom
- **Decisione:**
  - Sostituire tutti Unicode emoji con ASCII equivalenti
  - Auto-configurare pad_token = eos_token nel AdvancedTrainer.**init**()
  - Implementare model saving con save_pretrained() nativo HuggingFace
  - Correggere f-string formatting in training_metrics.py
- **Conseguenze:**
  - Training ora completa con successo (CodeGen-350M, 8 samples, 1 epoch)
  - Validation automatica passa 7/7 checks
  - Quality score: 0.89/1.00
  - ~8 tokens/sec su CPU
- **Follow-up:**
  - Considerare GPU training per performance
  - Aumentare dataset size per production
  - Aggiungere unit tests per training pipeline

## 2025-11-05 - Nomenclatura Manager vs Service

- **Data:** 2025-11-05
- **Titolo:** Nomenclatura Manager vs Service
- **Contesto:** Incoerenza naming layer applicativo
- **Alternative:** Mantenere ibrido / Uniformare su _Manager_
- **Decisione:** Uniformare su _Manager_
- **Conseguenze:** Refactor nei moduli core
- **Follow-up:** Aggiornare glossary, eseguire migrazione in un unico changeset
