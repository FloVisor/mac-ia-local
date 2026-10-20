# 21 — Régression mémoire Ollama : `num_ctx` repassé à 32768 (2026-10-20)

**Machine** : MacBook Pro M4 Max, 48 Go · macOS 27.0.1
**Serveur** : Ollama `0.35.0-pr18413-upstream` (LaunchAgent `org.gangneux.ollama-serve`)
**Modèle** : `qwen3:0.6b-titre` (Q4_K_M, 0,52 Go) — usage unique : titres de session OpenClaw

## 1. Symptôme

`llama-server` consommait ~4 Go de footprint pour un modèle de 0,5 Go, alors que
le plist impose `OLLAMA_CONTEXT_LENGTH=4096`.

Mesure avant correction :

```
llama-server [78159]  Footprint: 3992 MB
cmd: ... -c 32768 -np 1 ... -b 1024 -ub 1024
```

## 2. Cause racine

`OLLAMA_CONTEXT_LENGTH` n'est qu'un **défaut**. Toute requête portant
`options.num_ctx` l'emporte (`api.DefaultOptions()` → `opts.FromMap(requestOpts)`).

OpenClaw injecte `num_ctx` sur chaque appel Ollama :

| Chemin | Résolution | Fichier |
|---|---|---|
| natif `/api/chat` | `params.num_ctx` → `contextTokens` → rien | `dist/stream.runtime-*.mjs` (`resolveOllamaNativeNumCtx`) |
| OpenAI-compat | `params.num_ctx` → `contextTokens` → `contextWindow` → `maxTokens` → 200 000 | `dist/stream-compat-*.mjs` (`resolveOllamaNumCtx`) |

La config ne fixait que `contextWindow: 2048`, **sans `params.num_ctx` ni
`contextTokens`**. Selon le snapshot de registre utilisé (config mergée vs
catalogue découvert), `contextTokens` valait `min(32768, contextWindow découvert)`
= **32768** (`OLLAMA_LOCAL_CONTEXT_TOKENS`, `dist/defaults-*.mjs`), d'où le
`-c 32768`.

Preuve dans les logs — alternance 2048 / 32768 sur la même journée :

```
09:12:47  ctx=32768
09:17:41  ctx=2048
09:17:47  ctx=32768
09:18:14  ctx=2048
```

## 3. Correction

Épingler explicitement les trois champs sur l'entrée modèle
(`~/.openclaw/openclaw.json`), `params.num_ctx` ayant la priorité maximale :

```json
{
  "id": "qwen3:0.6b-titre",
  "name": "Qwen3 0.6B titres (ctx 4096)",
  "contextWindow": 4096,
  "contextTokens": 4096,
  "maxTokens": 256,
  "params": { "num_ctx": 4096 }
}
```

Appliqué via `openclaw config set` (aucun redémarrage du gateway requis).
Sauvegarde : `~/.openclaw/openclaw.json.bak-pre-numctx-pin-20261020-*`.

**Pourquoi 4096 et pas 2048** : le garde-fou OpenClaw refuse `< 4000` tokens
(`CONTEXT_WINDOW_HARD_MIN_TOKENS`, `dist/context-window-guard-*.mjs`), et les
logs montraient des prompts de titre jusqu'à 3 523 tokens rejetés à 2048
(`request (3523 tokens) exceeds the available context size (2048 tokens)`).

## 4. Validation

| Étape | Résultat |
|---|---|
| `openclaw config validate` | Config valid |
| `openclaw models list` | `ollama/qwen3:0.6b-titre  text  4k` |
| Tour agent réel (`openclaw agent --session-key probe-ctx-6`) | `-c 4096` |
| Après rafraîchissement découverte (`/api/tags` + `/api/show`) | `-c 4096` (stable) |
| `openclaw infer model run --local` | `-c 4096` |
| `python3 -m unittest discover -s witness-a` | 2 tests OK |

Mémoire mesurée :

| Contexte | Footprint | RSS |
|---|---|---|
| 32768 | 3 992 Mo | 4 293 Mo |
| 4096 | 542 Mo | ~1 030 Mo |

Gain ≈ **3,4 Go** de mémoire résidente pour le même service.

## 5. Retour arrière

```sh
cp ~/.openclaw/openclaw.json.bak-pre-numctx-pin-20261020-* ~/.openclaw/openclaw.json
```

## 6. Règle à retenir

Pour tout modèle Ollama local piloté par OpenClaw, **toujours** épingler
`params.num_ctx` (et `contextTokens`) dans `models.providers.ollama.models[]`.
`OLLAMA_CONTEXT_LENGTH` côté serveur ne suffit pas : il est écrasé par le
`num_ctx` injecté par le client.
