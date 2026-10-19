# 17 — MCP local_llm : garde de contexte 32K → 128K (2026-10-19)

Suite de [15-local-llm-mcp-delegation-policy.md](15-local-llm-mcp-delegation-policy.md).
Capture complète : [diagnostics/local-llm-mcp-ctx128k-20261019/](../diagnostics/local-llm-mcp-ctx128k-20261019/README.md).

## Contexte

Le MCP `local_llm` délègue vers **oMLX** (`127.0.0.1:8000`), modèle
`mlx-community--Qwen3.6-35B-A3B-4bit`. Ollama (`127.0.0.1:11434`,
`qwen3.6:35b-coding`, `muse-glimmer:30b-mlx`) est un **autre** backend, non
concerné par ce changement et non modifié.

Le cap serveur oMLX de ce modèle était déjà à 131 072 tokens
(`~/.omlx/model_settings.json` → `max_context_window`, catalogue Codex
`qwen36-omlx` → `context_window`/`max_context_window`), mais le MCP appliquait
sa propre garde à 32 768 tokens : toute tâche de 32K à 128K était rejetée côté
MCP alors que le serveur l'aurait acceptée.

## Changement

| Fichier | Avant | Après |
|---|---|---|
| `mcp/local-llm-mcp/local-llm-mcp.py` | `MAX_TASK_TOKENS = 32768` | `MAX_TASK_TOKENS = 131072` |
| `~/.codex/bin/local-llm-mcp` | garde 32K | redéployé (diff vide avec la source) |

Sauvegarde du binaire déployé : `~/.codex/bin/local-llm-mcp.bak-20261019-ctx128k`.

**Non modifiés** : `~/.codex/config.toml` (bloc `[mcp_servers.local_llm]`
inchangé), `~/.omlx/settings.json`, `~/.omlx/model_settings.json`,
`~/.codex/ollama-launch-models.json`, et l'ensemble de la configuration Ollama.

## Pourquoi 131072

C'est la valeur réelle annoncée par le serveur (`/v1/models` et `/tokenize` →
`max_model_len: 131072`). Une garde plus basse rejetterait des tâches valides ;
une garde plus haute serait inopérante (le serveur renvoie HTTP 400
`context_length_exceeded`). La garde MCP reste utile : elle échoue **avant**
l'appel modèle, avec un message actionnable, et reste fail-closed si `/tokenize`
est indisponible.

## Validation

| Test | Résultat |
|---|---|
| `initialize` / `tools/list` | PASS — `local-llm-mcp 1.1.0`, description « rejected above 131072 tokens » |
| `delegate` tâche courte (`testing`) | PASS — `isError=false`, 0,9 s |
| `delegate` tâche 40 000 tokens | PASS — `isError=false`, réponse réelle, 35,1 s (préfill froid) |
| `delegate` tâche 150 000 tokens | PASS — `isError=true`, rejet propre, aucun appel modèle |
| `uvx pytest witness-a/ -q` | PASS — 2 passed |
| oMLX `/health` | `healthy`, 21,4 Go, modèle par défaut inchangé |
| Ollama `/api/version` | `0.35.0-pr18413-upstream` (inchangé, non sollicité) |

## Conséquences

- Les délégations peuvent inclure jusqu'à ~128K tokens de contexte (fichiers
  entiers, gros diffs) sans découpage manuel.
- Coût : préfill froid ~244 s à 128K
  ([perf/qwen36-context-qualification.md](../perf/qwen36-context-qualification.md)) ;
  TTFT chaud ~1,2 s grâce au cache de préfixe oMLX. Privilégier un préfixe
  stable pour les tâches répétitives.
- La politique de délégation du document 15 reste valable : la garde n'autorise
  pas plus de contexte, elle ne fait que retirer un plafond devenu obsolète.

## Retour arrière

```sh
cp ~/.codex/bin/local-llm-mcp.bak-20261019-ctx128k ~/.codex/bin/local-llm-mcp
chmod +x ~/.codex/bin/local-llm-mcp
```

Redémarrer ensuite la session Codex (le serveur MCP est lancé au démarrage).
