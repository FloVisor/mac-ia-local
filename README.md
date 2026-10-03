# mac-ia-local

Environnement IA local sur macOS : build et validation d'ollama v0.35.0 (PR #18413), toolchains isolées et diagnostics d'activation.

## Contenu

- `diagnostics/` — captures de validation (auth-check, live-high, live-none, ollama-0.35.1-live, post-activation, reconciliation-20261002)
- `witness-a/`, `witness-none/` — projets témoins de test (calcul.py + tests)
- `post-activation-validation/` — validation post-activation (consolidé depuis l'ancien repo dédié)
- `ollama-v0.35.0/` — source ollama (non versionné ici : clone upstream, voir [ollama/ollama](https://github.com/ollama/ollama))
- `artifacts/`, `toolchains/`, `.cache/`, `isolated-home/` — binaires et caches locaux (exclus via `.gitignore`)

## Historique

Ce dépôt consolide les anciens dépôts `witness-a` et `witness-none`, dont les `.git` locaux ont été supprimés pour fusionner l'ensemble dans un dépôt unique.
