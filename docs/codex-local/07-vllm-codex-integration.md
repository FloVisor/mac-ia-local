# Intégration Codex — provider vLLM-Metal

Date : 2026-10-03/04 · Statut : **TERMINÉE**

## 1. Modification apportée (minimale)

Un seul bloc ajouté à `~/.codex/config.toml` (après `[model_providers.ollama_codex]`, inchangé) :

```toml
[model_providers.vllm_metal]
name = "vLLM Metal Local"
base_url = "http://127.0.0.1:11400/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
```

Rien d'autre modifié : MCP, permissions, profiles, Cloud, reasoning, AGENTS.md, hooks, workspace settings intacts (validé par `tomllib` + `codex doctor` : 2 MCP servers, providers ollama_codex + vllm_metal).

## 2. Tests post-modification (tous PASS)

| Test | Commande | Résultat | Durée | Tokens |
|---|---|---|---|---|
| Syntaxe TOML | `python3 tomllib` | PASS | <1s | — |
| Réponse simple | `codex exec -c model_provider=vllm_metal -c model=mlx-community/Qwen3.6-35B-A3B-4bit "Réponds uniquement: VLLM_CODEX_OK"` | **PASS** (réponse exacte) | 3m00s | 83 457 |
| Tool shell (date) | idem + "affiche la date" | **PASS** — 1 commande `date`, réponse correcte | 4m19s | 87 640 |
| MCP n8n_health_check | idem | **PASS** — 1 appel MCP, status `ok` | 6m09s | 135 634 |
| Cloud (défaut gpt-5.6-sol) | `codex exec "Réponds uniquement: CLOUD_STILL_OK"` | **PASS** | 4.6s | 26 051 |

Note : le test Cloud initial (23:56) avait été interrompu sans réponse — re-testé le 2026-10-04 matin : PASS immédiat. L'interruption était due à la saturation mémoire transitoire (swap 9.3 GB) pendant les tests vLLM 128K, pas à un défaut de configuration.

## 3. Observations importantes

- **Latence vLLM via Codex** : 3–6 min par tour vs 27–38s pour Ollama. Cause : le prompt système Codex (~24k tokens) doit être re-préfillé à chaque tour car le prefix caching ne s'applique pas entre processus `codex exec` séparés, ET le préfill long-contexte vLLM-Metal est lent sur ce prompt volumineux (voir benchmark Phase 10).
- **Consommation tokens** : 83k–136k tokens/tour vLLM vs 24k–26k Ollama — le modèle MLX 4-bit "think" beaucoup plus longuement (reasoning non tronqué) et le tokenizer diffère.
- Les 3 tests fonctionnels sont néanmoins **tous exacts** : tool calling, MCP, et respect des instructions.

## 4. Bascule des providers (tous disponibles simultanément)

```sh
# Cloud (défaut)
codex exec "..."

# Ollama local (rollback)
codex exec -c model_provider=ollama_codex -c model=qwen3.6:35b-coding "..."

# vLLM-Metal local (nouveau)
codex exec -c model_provider=vllm_metal -c model=mlx-community/Qwen3.6-35B-A3B-4bit "..."
```
