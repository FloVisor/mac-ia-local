# AGENTS.md

## Objectif

Dépôt de maintenance de la configuration IA locale (macOS) : serveur **Ollama** v0.35.0 (patch PR #18413) et config **vLLM** à tester. Les agents doivent produire des réponses concises et limiter la consommation de tokens.

## Structure

- `ollama-v0.35.0/` — sources ollama (a son propre AGENTS.md, prioritaire dans ce sous-dossier)
- `diagnostics/` — captures de validation (lecture seule, ne jamais modifier)
- `witness-a/`, `witness-none/`, `post-activation-validation/` — projets témoins de test
- `artifacts/`, `toolchains/`, `.cache/`, `isolated-home/` — non versionnés (voir `.gitignore`)

## Commandes

```sh
# Serveur Ollama local (LaunchAgent org.gangneux.ollama-serve)
curl -s http://127.0.0.1:11434/api/version

# Tests témoins
python -m pytest witness-a/ -q
```

## Règles

- Réponses en français, courtes, sans répéter le contexte.
- Ne pas committer binaires, caches ni clés API ; vérifier `.gitignore` avant tout commit.
- Toute modification de config Ollama/vLLM doit être validée par un test témoin (`witness-a/`) et documentée dans `diagnostics/`.
- Ne pas reconstruire ollama sans demande explicite : utiliser l'artefact qualifié existant.
