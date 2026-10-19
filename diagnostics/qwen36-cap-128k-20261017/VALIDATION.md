# Cap 128K — modèle local Qwen3.6-35B-A3B-4bit (2026-10-17)

## Changements appliqués (retour arrière : `.bak-20261017-230427`)

| Fichier | Changement |
|---|---|
| `~/.omlx/model_settings.json` | `models["mlx-community--Qwen3.6-35B-A3B-4bit"].max_context_window = 131072` (tier 1, par modèle — seul ce modèle est plafonné) |
| `~/.codex/ollama-launch-models.json` | Entrée `qwen36-omlx` : `context_window`/`max_context_window` = 131072 ; `auto_compact_token_limit` inchangé (1000000, inerte) |
| `~/.codex/config.toml` | Commentaire compaction mis à jour (32K → 128K) ; aucun réglage fonctionnel modifié |
| `~/.omlx/settings.json` | **Non modifié** (diff vide) |

Modèles cloud (gpt-*) : **non touchés** (vérifié par diff catalogue : seule l'entrée `qwen36-omlx` diffère).

## Validation du cap serveur (prod, port 8000, après redémarrage LaunchAgent)

- Rejet attendu : `overflow` 345 576 tokens → HTTP 400 `context_length_exceeded` (« Prompt is too long: 345576 tokens > 131072 maximum context length ») ✅
- Acceptation : `ack` 128 452 tokens → HTTP 200, `finish_reason=stop`, TTFT 241 s (cohérent campagne : 243,5 s natif à 128K) ✅
- Santé : `status=healthy`, mémoire modèle 21 422 314 484 o (identique avant/après), swap stable (4 214 Mo utilisés, préexistant).

## Compaction : décision motivée (source codex-rs)

- `remote_compaction = V2` si provider `is_openai()` (base URL redirigée vers le local) → la compaction v2 exige un item propriétaire OpenAI, échoue sur modèle local (« expected exactly one compaction output item, got 0 »).
- Pas de switch par modèle → abaisser `auto_compact_token_limit` déclencherait une compaction qui plante. Maintien à 1 000 000 (> 128K) = jamais déclenchée.
- Garde-fou effectif : rejet serveur oMLX 400 `context_length_exceeded` au-delà de 131 072 tokens.
- Fallback `auto_compact_fallback_prompt` (checkpoint `notes`) : message utilisateur local, fonctionnerait sur tout modèle — non dépendant du seuil.

## Témoins

- `uvx pytest witness-a/ -q` : **2 passed** (2026-10-17).
- Requête ACK prod : HTTP 200, `finish_reason=stop`.

## Retour arrière

1. Restaurer les 4 `.bak-20261017-230427` (retirer la clé `max_context_window`, catalogue `qwen36-omlx` → 32768).
2. `launchctl bootout/bootstrap gui/$(id -u) ~/Library/LaunchAgents/org.gangneux.omlx-serve.plist`.
3. Revalider : ACK ≤32K accepté, >32K rejeté ; `uvx pytest witness-a/ -q`.

## Validation MCP local-llm (2026-10-17 23:20)

Aucune modification : script installé `~/.codex/bin/local-llm-mcp` **identique** au dépôt (diff vide), config.toml déjà câblé (`[mcp_servers.local_llm]`). Test bout-en-bout stdio :

- `initialize` → `local-llm-mcp 1.1.0`, proto `2024-11-05` ✅
- `tools/list` → `delegate`, 5 profils (analysis/coding/documentation/review/testing) ✅
- `tools/call` réel → oMLX prod :8000, `isError=false`, réponse non vide (request_id `chatcmpl-4216f1ee`, 28 s) ✅
- Garde-fous : profil inconnu → `isError=true` propre ; outil inconnu → `-32601` ; `ping` → OK ✅
- Prod saine après test (`healthy`, 21,4 Go), aucun process orphelin.

## Thinking natif par profil (2026-10-17 23:50)

`local-llm-mcp.py` : `PROFILE_THINKING` — thinking ON pour `analysis`/`coding`/`review`, OFF (`chat_template_kwargs: {"enable_thinking": false}`) pour `testing`/`documentation`. Mesuré : OFF ≈ 0,2 s vs ON ≈ 28 s sur tâche courte (×3-4 latence et tokens).

Validation : `testing` 0,2 s (completion 3) ; `analysis` 28,2 s (completion 1192) ; garde 32K toujours active (33 006 tokens rejeté proprement) ; `2 passed` témoins ; prod `healthy` ; aucun orphelin. Script installé = dépôt (diff vide).

## Garde 32K côté MCP (2026-10-17 23:40)

`local-llm-mcp.py` : `MAX_TASK_TOKENS = 32768` (env `LOCAL_LLM_MCP_MAX_TASK_TOKENS`), comptage **exact** via `POST /tokenize` oMLX (tokeniseur réel du modèle), fail-closed si `/tokenize` indisponible. **Aucun impact** : cap serveur (131072) et catalogue Codex (`qwen36-omlx` 131072) inchangés — vérifiés après édition.

Validation : tâche courte → `isError=false` (réponse réelle) ; tâche 67 507 tokens → `isError=true` « Task is 67507 tokens > local MCP limit 32768 » ; description de l'outil documente la garde ; `2 passed` témoins ; script installé = dépôt (diff vide).