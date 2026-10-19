# AGENTS.md — perf/

## Objectif

**Tests de performance de l'IA locale** (M4 Max 48 Go) : comparatifs de moteurs et qualification de fenêtres de contexte.

## Structure

- `qwen36-engine-comparison.md` — Ollama vs oMLX (tok/s, TTFT, mémoire)
- `qwen36-context-qualification.md` — qualification 128K sur oMLX (préfill/retenue/terminaison)
- `scripts/qwen36-context/` — `gen_input.py` (entrées à longueur contrôlée) + `measure_level.py` (protocole 32K→256K)

## Règles

- Les données produites par les campagnes vont dans `toolchains/` (non versionné).
- Mesures sur instance de test isolée (`--base-path ~/.omlx-test`, port 8001), production arrêtée pendant les fenêtres de mesure.
- Verdicts normalisés : QUALIFIÉ / QUALIFIÉ AVEC RÉSERVES / NON QUALIFIÉ (critères dans `measure_level.py`).
- Nouvelle campagne = nouveau document + captures dans `diagnostics/`.