# AGENTS.md

## Objectif

Dépôt de maintenance de la configuration IA locale (macOS) : serveur **Ollama** v0.35.0 (patch PR #18413), **Codex local** (proxy + MCP), **OpenClaw** et tests de performance de l'IA locale. Les agents doivent produire des réponses concises et limiter la consommation de tokens.

## Routage

Chaque domaine a son `AGENTS.md`, chargé uniquement quand l'agent y travaille :

- [ollama-v0.35.0/](ollama-v0.35.0/) — sources ollama (AGENTS.md local prioritaire dans ce sous-dossier)
- [codex/](codex/) — audit et recette Codex local (proxy, vLLM-Metal, MCP `local_llm`)
- [openclaw/](openclaw/) — pièges d'intégration OpenClaw + checklist
- [perf/](perf/) — tests de performance de l'IA locale (moteurs, fenêtres de contexte)

## Structure

- `diagnostics/` — captures de validation (lecture seule, ne jamais modifier)
- `witness-a/`, `witness-none/`, `post-activation-validation/` — projets témoins de test
- `mcp/local-llm-mcp/` — serveur MCP de délégation vers le LLM local (oMLX)
- `artifacts/`, `toolchains/`, `.cache/`, `isolated-home/` — non versionnés (voir `.gitignore`)

## Commandes

```sh
# Serveur Ollama local (LaunchAgent org.gangneux.ollama-serve)
curl -s http://127.0.0.1:11434/api/version

# Serveur oMLX (LaunchAgent org.gangneux.omlx-serve)
curl -s http://127.0.0.1:8000/health

# Tests témoins
python -m pytest witness-a/ -q
```

## Règles

- Réponses en français, courtes, sans répéter le contexte.
- Ne pas committer binaires, caches ni clés API ; vérifier `.gitignore` avant tout commit.
- Toute modification de config Ollama/vLLM/oMLX doit être validée par un test témoin (`witness-a/`) et documentée dans `diagnostics/`.
- Ne pas reconstruire ollama sans demande explicite : utiliser l'artefact qualifié existant.
