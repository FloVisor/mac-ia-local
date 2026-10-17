# mac-ia-local

Environnement IA local sur macOS : build et validation d'ollama v0.35.0 (PR #18413), toolchains isolées et diagnostics d'activation.

## Contenu

- `diagnostics/` — captures de validation (auth-check, live-high, live-none, ollama-0.35.1-live, post-activation, reconciliation-20261002, local-llm-mcp)
- `witness-a/`, `witness-none/` — projets témoins de test (calcul.py + tests)
- `post-activation-validation/` — validation post-activation (consolidé depuis l'ancien repo dédié)
- `ollama-v0.35.0/` — source ollama v0.35.0 (fork local de [ollama/ollama](https://github.com/ollama/ollama))
- `mcp/local-llm-mcp/` — serveur MCP de délégation vers le LLM local (muse-glimmer:30b-mlx) : [README](mcp/local-llm-mcp/README.md)
- `docs/codex-local/` — documentation d'audit et de recette Codex local : [README](docs/codex-local/README.md)
- `artifacts/`, `toolchains/`, `.cache/`, `isolated-home/` — binaires et caches locaux (exclus via `.gitignore`)

## Historique

Ce dépôt consolide les anciens dépôts `witness-a` et `witness-none`, dont les `.git` locaux ont été supprimés pour fusionner l'ensemble dans un dépôt unique.
