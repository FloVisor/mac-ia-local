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

## Anomalies MCP orion (frontal de Raphaël) vs agent local — routage des corrections

Quand Florian remonte un comportement fautif d'un agent utilisant le MCP orion (ou tout MCP tiers), **déterminer d'abord le côté responsable**, puis appliquer la règle :

1. **Reproduire l'appel fautif en direct** (client MCP, sans l'agent — ex. `diagnostics/mcp-mixtrio-orion-030-20261019/orion_mcp_client.py`) pour isoler frontal vs modèle.
2. **Bug côté MCP (frontal/passerelle)** → **ne PAS bricoler l'agent**. Le documenter dans `diagnostics/` + `openclaw/integration-pitfalls.md` et **le remonter à Raphaël** (mail récapitulatif : symptôme, reproduction, cause, fix demandé). Parade agent uniquement en attendant le fix, marquée comme temporaire.
3. **Bug côté agent/modèle local** (formatage d'appels, arguments omis, hallucination) → corriger **dans l'agent** : `AGENTS.md` du workspace OpenClaw concerné (injecté en permanence dans le system prompt), skill local si besoin. Documenter dans `openclaw/integration-pitfalls.md`.
4. **Règle d'or** : un paramètre accepté mais silencieusement ignoré, ou une réponse fausse sans erreur, est presque toujours un bug **MCP** — jamais compensable durablement côté agent.

Exemples tranchés (2026-10-19) : `exec_tool` ignorant `args` → MCP (remonté) ; `tool_search` avec `limit` au niveau batch → modèle Qwen (parade AGENTS.md des 3 workspaces).
