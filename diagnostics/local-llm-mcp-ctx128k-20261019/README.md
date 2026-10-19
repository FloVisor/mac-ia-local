# MCP local_llm — garde de contexte 32K → 128K (2026-10-19)

## Changement appliqué

| Fichier | Changement |
|---|---|
| `mcp/local-llm-mcp/local-llm-mcp.py` | `MAX_TASK_TOKENS` défaut `32768` → `131072` (env `LOCAL_LLM_MCP_MAX_TASK_TOKENS` inchangée) |
| `~/.codex/bin/local-llm-mcp` | redéployé depuis la source versionnée (diff vide) ; sauvegarde `local-llm-mcp.bak-20261019-ctx128k` |

**Non modifiés** (vérifiés) :

- `~/.codex/config.toml` — bloc `[mcp_servers.local_llm]` inchangé (commande + `startup_timeout_sec = 30`).
- `~/.omlx/settings.json` et `~/.omlx/model_settings.json` — cap serveur déjà à `131072` pour `mlx-community--Qwen3.6-35B-A3B-4bit`.
- `~/.codex/ollama-launch-models.json` — entrée `qwen36-omlx` déjà à `131072`.
- **Ollama** (`127.0.0.1:11434`, `qwen3.6:35b-coding`, `muse-glimmer:30b-mlx`) : aucun contact, aucune modification.

## Pourquoi 131072 et pas 128000

`131072` est le cap réel du serveur oMLX pour ce modèle (`/v1/models` →
`max_model_len: 131072`, `/tokenize` → `max_model_len: 131072`). Aligner la
garde MCP sur cette valeur évite de rejeter une tâche que le serveur accepterait.
Le plafond dur reste le serveur : prompt système du profil + tâche > 131072 →
HTTP 400 `context_length_exceeded`.

## Validation (probe JSON-RPC stdio direct)

Script : [probe.py](probe.py) · sorties : [probe.stdout.jsonl](probe.stdout.jsonl),
[probe-40k.stdout.jsonl](probe-40k.stdout.jsonl)

| Test | Résultat |
|---|---|
| `initialize` | PASS — `local-llm-mcp 1.1.0`, proto `2024-11-05` |
| `tools/list` | PASS — description de l'outil annonce « rejected above 131072 tokens » |
| `delegate` tâche courte (`testing`) | PASS — `isError=false`, `completion_tokens=1`, 0,9 s |
| `delegate` tâche **40 000 tokens** (au-delà de l'ancienne garde 32K) | PASS — `isError=false`, réponse réelle, 35,1 s (préfill froid) |
| `delegate` tâche **150 000 tokens** | PASS — `isError=true`, « Task is 150000 tokens > local MCP limit 131072 », aucun appel modèle |
| `uvx pytest witness-a/ -q` | PASS — 2 passed |
| oMLX `/health` | `healthy`, modèle par défaut `mlx-community--Qwen3.6-35B-A3B-4bit`, 21,4 Go |
| Ollama `/api/version` | `0.35.0-pr18413-upstream` (inchangé, non sollicité) |

## Conséquence opérationnelle

Les tâches déléguées peuvent désormais inclure jusqu'à ~128K tokens de contexte
(fichiers entiers, diffs volumineux). Attention au coût : le préfill froid à
128K est mesuré à ~244 s ([perf/qwen36-context-qualification.md](../../perf/qwen36-context-qualification.md)) ;
le cache de préfixe oMLX ramène le TTFT chaud à ~1,2 s. Pour les tâches
répétitives, préférer un préfixe stable.

## Retour arrière

```sh
cp ~/.codex/bin/local-llm-mcp.bak-20261019-ctx128k ~/.codex/bin/local-llm-mcp
chmod +x ~/.codex/bin/local-llm-mcp
```

Puis redémarrer la session Codex (le serveur MCP est lancé au démarrage de session).
