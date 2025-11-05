
#!/usr/bin/env python3
"""
Bootstrap agente con memoria persistente per VS Code/git.

Esegue il provisioning della seguente struttura:
  /.agent/
    policy.md
    instructions.prompt.md
    /memory/
      memory.jsonl
      decisions.md
      glossary.md
      objectives.md
      open_threads.md
  /changesets/
    (placeholder .gitkeep)
  /docs/
    architecture.md
    module_ownership.md
  /.vscode/
    settings.json
  .gitignore  (append di regole)
  .git/hooks/pre-commit  (guard-rails qualità)
  /scratch, /out (aree di lavoro)

Utilizzo:
  python bootstrap_agent_memory.py --project-root . [--force]

Note:
  - Idempotente: non sovrascrive file esistenti a meno di --force.
  - Imposta l'eseguibilità dell'hook su sistemi POSIX.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BANNER = "🔧 Bootstrap agente con memoria persistente"

# ------------------------- Template content -------------------------

POLICY_MD = """# Agent Policy (Regole di Ingaggio)

Queste regole sono **vincolanti** per qualunque agente che opera nel repository.

## Principi
- Atomicità delle modifiche (changeset)
- Tracciabilità (memory.jsonl, decisions.md)
- Coerenza architetturale (architecture.md)
- Nessun file fuori dai boundary consentiti senza decisione registrata

## Cartelle consentite
- `src/`, `tests/`, `docs/`, `changesets/`, `.agent/`, `.vscode/`

## Convenzioni chiave
- Un changeset per task
- Nessun TODO/FIXME senza un'entry `type: "todo"` in `.agent/memory/memory.jsonl`
- Glossario in `.agent/memory/glossary.md` per naming standard
"""

INSTRUCTIONS_PROMPT = """SEI UN AGENTE DI CODICE CON MEMORIA DI PROGETTO.

REGOLE OPERATIVE (NON NEGOZIABILI):
1) PRIMA DI AGIRE:
   - Leggi `/.agent/memory/memory.jsonl`, `decisions.md`, `glossary.md`, `objectives.md`, `open_threads.md`.
   - Sintetizza il contesto in 3–5 bullet pertinenti al task.
2) OGNI MODIFICA È UN “CHANGESET”:
   - Crea/aggiorna `/changesets/YYYYMMDD-<slug>.yml` con: scope, rationale, file_toccati, step_di_test, rollback, status.
   - Modifica SOLO i file dichiarati nel changeset.
3) ATOMICITÀ:
   - Completa le modifiche end-to-end (build/test OK) prima di aprire un altro changeset.
   - Vietato lasciare TODO/FIXME senza creare una voce `type: "todo"` in `memory.jsonl` (status: open).
4) TRAIL DI MEMORIA:
   - Ogni decisione/fatto/todo → append JSON line in `memory.jsonl`.
   - Aggiorna `decisions.md` per impatti architetturali.
5) BOUNDARIES:
   - Non creare file fuori da `src`, `tests`, `docs`, `changesets`, `.agent` senza decisione registrata.
OUTPUT PER OGNI TASK:
   - diff patch per file toccati
   - changeset YAML aggiornato
   - append a `memory.jsonl` (se rilevante)
   - comandi di test/verifica
"""

DECISIONS_MD = """# Decision Log
Registro umano-legibile delle decisioni architetturali e di processo.
- Formato sintetico: data, titolo, contesto, alternative, decisione, conseguenze, follow-up.

## Esempio (ADR breve)
- **Data:** 2025-11-05
- **Titolo:** Nomenclatura Manager vs Service
- **Contesto:** Incoerenza naming layer applicativo
- **Alternative:** Mantenere ibrido / Uniformare su *Manager*
- **Decisione:** Uniformare su *Manager*
- **Conseguenze:** Refactor nei moduli core
- **Follow-up:** Aggiornare glossary, eseguire migrazione in un unico changeset
"""

GLOSSARY_MD = """# Glossario (nomenclatura ufficiale)
| Concetto | Nome standard | Note |
|---------|----------------|------|
| Servizi applicativi | Manager | Es. UserManager, OrderManager |
| Helper generici | Utils | Evitare duplicati con Helpers |

Aggiungere voci man mano che il dominio evolve.
"""

OBJECTIVES_MD = """# Objectives & KPI Tecnici
- Riduzione debito tecnico (refactor pianificati)
- Coverage test >= 80%
- Time-to-merge < 24h per changeset standard
"""

OPEN_THREADS_MD = """# Thread aperti
Elenco dei lavori avviati e non chiusi, con stato sintetico.

- [ ] Migrazione async layer API — in attesa revisione
- [ ] Allineamento schema DB — dipende da decisione #2025-11-05-DB
"""

ARCHITECTURE_MD = """# Architecture Overview
Vista macro dei confini, dipendenze e componenti chiave.
Includere diagrammi, contratti tra moduli, pattern architetturali.
"""

MODULE_OWNERSHIP_MD = """# Module Ownership
Mappa di responsabilità per moduli/pacchetti (anche se owner unico).
| Path | Owner | Note |
|------|-------|------|
| src/api | armando | Interfacce HTTP |
"""

VSCODE_SETTINGS = {
  "files.exclude": {
    "**/out": True,
    "**/scratch": True
  },
  "editor.codeActionsOnSave": {
    "source.organizeImports": True,
    "source.fixAll": True
  },
  "git.enableSmartCommit": False,
  "editor.formatOnSave": True
}

GITIGNORE_APPEND = """
# === agent bootstrap ===
out/
scratch/
.agent/cache/
.agent/*.log
"""

PRE_COMMIT = """#!/usr/bin/env bash
set -euo pipefail

# 1) TODO/FIXME senza entry 'todo' in memory.jsonl
if git diff --cached -U0 | grep -E '^(\\+|\\+)?.*(TODO|FIXME|TBD)'; then
  if ! grep -q '"type":"todo"' ./.agent/memory/memory.jsonl 2>/dev/null; then
    echo "❌ TODO/FIXME rilevati ma nessuna entry 'todo' in .agent/memory/memory.jsonl"
    exit 1
  fi
fi

# 2) changeset richiesto per modifiche a src/tests
if git diff --cached --name-only | grep -E '^(src|tests)/' >/dev/null 2>&1; then
  if ! ls changesets/* >/dev/null 2>&1; then
    echo "❌ Nessun changeset presente in /changesets per modifiche a src/tests"
    exit 1
  fi
fi

# 3) blocco file fuori dalle aree consentite senza decisione esplicita
if git diff --cached --name-only | grep -Ev '^(src|tests|docs|changesets|\\.agent|\\.vscode|\\.gitignore|README\\.md)' | grep -q '.'; then
  if ! grep -q '"type":"decision".*"topic":"repository-structure"' ./.agent/memory/memory.jsonl 2>/dev/null; then
    echo "❌ Nuovi file fuori dalle aree consentite senza decisione registrata"
    exit 1
  fi
fi

echo "✅ pre-commit OK"
"""

CHANGESET_SAMPLE = """id: {date}-bootstrap-validazione
owner: {owner}
scope: "Bootstrap struttura memoria agente"
rationale: "Introdurre regole di qualità e persistenza conoscenza"
files:
  - .agent/policy.md
  - .agent/instructions.prompt.md
  - .agent/memory/memory.jsonl
  - docs/architecture.md
tests:
  - "pytest -q || echo 'nessun test definito'"
  - "git status --porcelain"
rollback:
  - "git checkout -- .agent docs .vscode changesets || true"
status: "ready"
"""

# ------------------------- Helpers -------------------------

def safe_write(path: Path, content: str, force: bool=False, is_json: bool=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return False
    if is_json:
        with path.open("w", encoding="utf-8") as f:
            json.dump(json.loads(content) if isinstance(content, str) else content, f, ensure_ascii=False, indent=2)
    else:
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    return True

def append_gitignore(path: Path, snippet: str):
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if snippet.strip() not in existing:
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write("\n" + snippet.strip() + "\n")

def posix_chmod_executable(path: Path):
    try:
        mode = os.stat(path).st_mode
        os.chmod(path, mode | 0o111)
    except Exception:
        pass

# ------------------------- Main -------------------------

def main():
    parser = argparse.ArgumentParser(description=BANNER)
    parser.add_argument("--project-root", default=".", help="Root del progetto (default: .)")
    parser.add_argument("--force", action="store_true", help="Sovrascrive file esistenti")
    parser.add_argument("--owner", default=os.getenv("GIT_AUTHOR_NAME", "armando"), help="Owner predefinito per il changeset di esempio")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    print(f"{BANNER} → {root}")

    # Cartelle target
    agent_dir = root / ".agent"
    memory_dir = agent_dir / "memory"
    cache_dir = agent_dir / "cache"
    changesets_dir = root / "changesets"
    docs_dir = root / "docs"
    vscode_dir = root / ".vscode"
    scratch_dir = root / "scratch"
    out_dir = root / "out"

    for d in [agent_dir, memory_dir, cache_dir, changesets_dir, docs_dir, vscode_dir, scratch_dir, out_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # File contenuti
    created = []

    if safe_write(agent_dir / "policy.md", POLICY_MD, force=args.force):
        created.append(".agent/policy.md")
    if safe_write(agent_dir / "instructions.prompt.md", INSTRUCTIONS_PROMPT, force=args.force):
        created.append(".agent/instructions.prompt.md")
    if safe_write(memory_dir / "decisions.md", DECISIONS_MD, force=args.force):
        created.append(".agent/memory/decisions.md")
    if safe_write(memory_dir / "glossary.md", GLOSSARY_MD, force=args.force):
        created.append(".agent/memory/glossary.md")
    if safe_write(memory_dir / "objectives.md", OBJECTIVES_MD, force=args.force):
        created.append(".agent/memory/objectives.md")
    if safe_write(memory_dir / "open_threads.md", OPEN_THREADS_MD, force=args.force):
        created.append(".agent/memory/open_threads.md")
    if safe_write(docs_dir / "architecture.md", ARCHITECTURE_MD, force=args.force):
        created.append("docs/architecture.md")
    if safe_write(docs_dir / "module_ownership.md", MODULE_OWNERSHIP_MD, force=args.force):
        created.append("docs/module_ownership.md")

    # memory.jsonl iniziale (append-only)
    mem_path = memory_dir / "memory.jsonl"
    if not mem_path.exists() or args.force:
        ts = datetime.now(timezone.utc).astimezone().isoformat()
        init_lines = [
            json.dumps({
                "ts": ts,
                "type": "fact",
                "topic": "bootstrap",
                "summary": "Inizializzata struttura memoria agente",
                "impacts": ["/.agent", "/docs", "/changesets"],
                "status": "active"
            }, ensure_ascii=False)
        ]
        safe_write(mem_path, "\n".join(init_lines) + "\n", force=True)
        created.append(".agent/memory/memory.jsonl")

    # .vscode/settings.json
    settings_path = vscode_dir / "settings.json"
    if settings_path.exists() and not args.force:
        pass
    else:
        safe_write(settings_path, json.dumps(VSCODE_SETTINGS, ensure_ascii=False, indent=2), force=True, is_json=False)
        created.append(".vscode/settings.json")

    # .gitignore append
    append_gitignore(root / ".gitignore", GITIGNORE_APPEND)
    created.append(".gitignore (append)")

    # changeset di esempio
    cs_path = changesets_dir / f"{datetime.now().strftime('%Y%m%d')}-bootstrap-validazione.yml"
    if safe_write(cs_path, CHANGESET_SAMPLE.format(date=datetime.now().strftime('%Y%m%d'), owner=args.owner), force=args.force):
        created.append(str(cs_path.relative_to(root)))

    # pre-commit hook
    git_dir = root / ".git"
    hooks_dir = git_dir / "hooks"
    if hooks_dir.exists():
        pre_commit_path = hooks_dir / "pre-commit"
        if safe_write(pre_commit_path, PRE_COMMIT, force=True):
            posix_chmod_executable(pre_commit_path)
            created.append(".git/hooks/pre-commit")
    else:
        print("ℹ️  Repository git non inizializzato (manca .git). Salto l'installazione del pre-commit.")

    # Placeholders
    (changesets_dir / ".gitkeep").write_text("", encoding="utf-8")

    # Report
    if created:
        print("✅ Creati/aggiornati:")
        for p in created:
            print(f"  - {p}")
    else:
        print("ℹ️ Nulla da creare: struttura già presente. Usa --force per sovrascrivere.")

    print("\nProssimi step consigliati:")
    print("  1) git init (se non ancora inizializzato)")
    print("  2) Verifica .git/hooks/pre-commit sia eseguibile su POSIX")
    print("  3) Apri .agent/instructions.prompt.md e incollalo nel system dell'agente in VS Code")
    print("  4) Usa /changesets per ogni modifica e aggiorna .agent/memory/memory.jsonl per decisioni/todo")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\nInterrotto dall'utente.", file=sys.stderr)
        sys.exit(130)
