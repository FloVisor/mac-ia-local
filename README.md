# mac-ia-local

Environnement IA local sur macOS : build et validation d'ollama v0.35.0 (PR #18413), intégrations Codex/OpenClaw, tests de performance et diagnostics d'activation.

## Contenu

- `ollama-v0.35.0/` — source ollama v0.35.0 (fork local de [ollama/ollama](https://github.com/ollama/ollama))
- `codex/` — audit et recette Codex local : [README](codex/README.md)
- `openclaw/` — pièges d'intégration d'outils dans OpenClaw (TCC, tools.allow, politique Graph, saturation de session) et checklist : [integration-pitfalls.md](openclaw/integration-pitfalls.md)
- `perf/` — tests de performance de l'IA locale : [qwen36-engine-comparison.md](perf/qwen36-engine-comparison.md) · [qwen36-context-qualification.md](perf/qwen36-context-qualification.md)
- `mcp/local-llm-mcp/` — serveur MCP de délégation vers le LLM local (oMLX) : [README](mcp/local-llm-mcp/README.md)
- `diagnostics/` — captures de validation (auth-check, live-high, live-none, ollama-0.35.1-live, post-activation, reconciliation-20261002, local-llm-mcp, qwen36-cap-128k, openclaw-ctx-allege, [omlx-memory-guard-20261019](diagnostics/omlx-memory-guard-20261019/README.md))
- `witness-a/`, `witness-none/` — projets témoins de test (calcul.py + tests)
- `post-activation-validation/` — validation post-activation (consolidé depuis l'ancien repo dédié)
- `artifacts/`, `toolchains/`, `.cache/`, `isolated-home/` — binaires et caches locaux (exclus via `.gitignore`)

## Historique

Ce dépôt consolide les anciens dépôts `witness-a` et `witness-none`, dont les `.git` locaux ont été supprimés pour fusionner l'ensemble dans un dépôt unique.
