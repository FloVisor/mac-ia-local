# AGENTS.md — codex/

## Objectif

Audit, recette et intégration de **Codex local** (CLI/VS Code/Desktop) : proxy Ollama `/api/codex/v1`, provider vLLM-Metal, MCP de délégation, sélecteur d'effort.

## Structure

- `README.md` — index complet : architecture, versions, ports, bascule cloud/local, résultats
- `01…17-*.md` — rapports datés de la mission 2026-10-03/04 (baseline, vLLM-Metal, benchmark A/B, rollback) puis 2026-10-17/19 (MCP local_llm, effort, garde 128K)
- `evidence/` — scripts de bench + prompts + logs de démarrage (lecture seule)
- `scripts/` — `retest-vllm-metal.sh` (retest gate ≥ 50 tok/s)

## Règles

- Les rapports `01…16` sont des **captures figées** : ne pas réécrire, ajouter un nouveau document numéroté à la suite.
- vLLM-Metal : plateforme de qualification uniquement — Ollama reste le backend local par défaut. Retest uniquement si release vLLM/vLLM-Metal mentionne Apple Silicon/decode (gate : [08-vllm-metal-conclusion-and-retest.md](08-vllm-metal-conclusion-and-retest.md)).
- Ne pas rebenchmarker Ollama tant que version/modèle/config inchangés.
- Toute modification de config doit être validée par un test témoin (`witness-a/`) et documentée dans `diagnostics/`.