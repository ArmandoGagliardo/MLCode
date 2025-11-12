SEI UN AGENTE DI CODICE CON MEMORIA DI PROGETTO.

REGOLE OPERATIVE (NON NEGOZIABILI):

1. PRIMA DI AGIRE:
   - Leggi `/.agent/memory/memory.jsonl`, `decisions.md`, `glossary.md`, `objectives.md`, `open_threads.md`.
   - Evita codice duplicato in fase di Refactoing.
   - Consulta `architecture.md` per coerenza architetturale.
   0. PER OGNI TASK:
   - Sintetizza il contesto in 3–5 bullet pertinenti al task.
   - Per ogni anomalia o task aprire un thread in `open_threads.md`.
   - Consulta `objectives.md` per allineamento con KPI.
   - Consulta `decisions.md` per allineamento con decisioni precedenti.
   - Consulta `glossary.md` per definizioni di termini chiave.
   - Consulta la cache nella cartella `.agent/cache/` per la struttura delle classi e funzioni.
   - Aggiorna la cache quando crei nuove classi/funzioni, con le relative chiamate e docstring.
2. OGNI MODIFICA È UN “CHANGESET”:
   - Crea/aggiorna `/changesets/YYYYMMDD-<slug>.yml` con: scope, rationale, file_toccati, step_di_test, rollback, status.
   - Modifica SOLO i file dichiarati nel changeset.
3. ATOMICITÀ:
   - Completa le modifiche end-to-end (build/test OK) prima di aprire un altro changeset.
   - Vietato lasciare TODO/FIXME senza creare una voce `type: "todo"` in `memory.jsonl` (status: open).
4. TRAIL DI MEMORIA:
   - Ogni decisione/fatto/todo → append JSON line in `memory.jsonl`.
   - Aggiorna `decisions.md` per impatti architetturali.
5. BOUNDARIES:
   - Non creare file fuori da `application`, `domain`, `infrastructure`, `presentation`, `changesets`, `.agent` senza decisione registrata.
     OUTPUT PER OGNI TASK:
   - diff patch per file toccati
   - changeset YAML aggiornato
   - append a `memory.jsonl` (se rilevante)
   - comandi di test/verifica
