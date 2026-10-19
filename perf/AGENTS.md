# AGENTS.md — perf/

## Objectif

**Tests de performance de l'IA locale** (M4 Max 48 Go) : comparatifs de moteurs et qualification de fenêtres de contexte.

## Structure

- `qwen36-engine-comparison.md` — Ollama vs oMLX (tok/s, TTFT, mémoire)
- `qwen36-context-qualification.md` — qualification 128K sur oMLX (préfill/retenue/terminaison)
- `scripts/qwen36-context/` — `gen_input.py` (entrées à longueur contrôlée) + `measure_level.py` (protocole 32K→256K)

## Configuration de production oMLX (2026-10-19)

- **Plafond mémoire** : `memory_guard_tier = custom`, `memory_guard_custom_ceiling_gb = 30.0` dans `~/.omlx/settings.json`.
  Le plafond custom n'est lu **que** si le tier vaut `custom` (`process_memory_enforcer.py:717`) — avec `balanced` il est ignoré.
- **Le LaunchAgent ne doit pas passer `--memory-guard`** : la priorité CLI > fichier (`settings.py:1086`) écraserait `settings.json` à chaque démarrage. Vérifier `~/Library/LaunchAgents/org.gangneux.omlx-serve.plist`.
- Validation après redémarrage : log `Process memory enforcer started (tier=custom, ceiling=30.0GB)` et `/health → engine_pool.final_ceiling = 30.00 Go`.
- Détail et mesures : [diagnostics/omlx-memory-guard-20261019](../diagnostics/omlx-memory-guard-20261019/README.md).

## Règles

- Les données produites par les campagnes vont dans `toolchains/` (non versionné).
- Mesures sur instance de test isolée (`--base-path ~/.omlx-test`, port 8001), production arrêtée pendant les fenêtres de mesure.
- Verdicts normalisés : QUALIFIÉ / QUALIFIÉ AVEC RÉSERVES / NON QUALIFIÉ (critères dans `measure_level.py`).
- Nouvelle campagne = nouveau document + captures dans `diagnostics/`.