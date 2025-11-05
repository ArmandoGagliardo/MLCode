# Agent Policy (Regole di Ingaggio)

Queste regole sono **vincolanti** per qualunque agente che opera nel repository.

## Principi

- Atomicità delle modifiche (changeset)
- Tracciabilità (memory.jsonl, decisions.md)
- Coerenza architetturale (architecture.md)
- Nessun file fuori dai boundary consentiti senza decisione registrata

## Cartelle consentite

- `application/`, `domain/`, `docs/`, `changesets/`, `.agent/`, `.vscode/`,`presentation/`,`infrastructure/`,`config/`,

## Convenzioni chiave

- Un changeset per task
- Nessun TODO/FIXME senza un'entry `type: "todo"` in `.agent/memory/memory.jsonl`
- Glossario in `.agent/memory/glossary.md` per naming standard
- Le Documentazioni/SUMMARY .md vanno create in `docs/` non nella main root
- La main root deve restare pulita il più possibile
