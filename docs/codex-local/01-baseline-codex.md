# Baseline Codex — audit avant migration vLLM-Metal

Date : 2026-10-03 · Mission : audit + migration Ollama → vLLM-Metal + benchmark A/B

## 1. Environnement système (observé)

| Élément | Valeur |
|---|---|
| Hostname | MacBook-Pro-de-Florian-123.local |
| macOS | 27.0 (Build 26A428) |
| Architecture | arm64 (Apple Silicon) |
| Chip | Apple M4 Max — 16 cœurs CPU (12P+4E), 40 cœurs GPU, Metal 4 |
| Mémoire unifiée | 48 GB |
| Disque | 926 GiB, 118 GiB libres |
| Git | 2.54.0 (Apple Git-157) |
| VS Code | 1.140.0 |
| Extensions Codex | openai.chatgpt-26.5928.31416, openai.codex-audio-26.930.21537/31730 |
| Codex CLI | 0.160.0 (standalone, `~/.local/bin/codex`) |
| Ollama | 0.35.1 (API) — serveur = binaire patché v0.35.0-pr18413 |
| Python | 3.14.2 (Homebrew) |
| Homebrew | 7.0.7 |
| Shell | /bin/bash 3.2.57 |

## 2. Dépôt Git courant (observé)

- Repo : `/Users/fngux2/mac-ia-local` (identifié via `git rev-parse --show-toplevel`)
- Branche : `main` · HEAD : `644a6ef4ab37addce5f86df2b61a41d0ef233544`
- Modifications non suivies avant mission : `.vscode/`, `AGENTS.md` (non liées à la mission, ne seront pas commitées)
- Historique : 3 commits (environnement IA local macOS)

## 3. Architecture d'inférence actuelle (observée)

**Point clé** : Codex ne parle PAS directement à Ollama. TOUT le trafic Codex (cloud + local) passe par le **proxy Codex d'Ollama** exposé par le binaire patché :

```
Codex (CLI/VS Code/Desktop)
  → openai_base_url = http://127.0.0.1:11434/api/codex/v1   [config.toml ligne 1]
  → Ollama patché v0.35.0-pr18413 (proxy Codex / Responses API)
      ├─ modèles locaux (qwen3.6:35b-coding, …)
      └─ relais ChatGPT cloud (auth chatgpt, tokens dans ~/.codex/auth.json)
```

- `codex doctor` : default model provider = `openai`, wire API = `responses`, endpoint = `http://127.0.0.1:11434/api/...` (HTTP 401 sans auth = normal, route existe).
- WebSocket : non supporté par le proxy (`supports_websockets = false` pour ollama_codex ; handshake 426 attendu — fallback HTTPS fonctionne).

### Binaire Ollama

- Serveur actif : `/Applications/Ollama.app/Contents/Resources/ollama serve` (PID 18214) écoute sur 127.0.0.1:11434.
- LaunchAgent `org.gangneux.ollama-serve` : pointe vers `/Users/fngux2/.local/lib/ollama-codex-patched/v0.35.0-pr18413/ollama` (RunAtLoad=false, KeepAlive=false — actuellement le serveur de l'app Ollama détient le port).
- LaunchAgent `org.gangneux.ollama-ssh-tunnel` : tunnel SSH inverse `-R 127.0.0.1:11434:127.0.0.1:11434 docker-01` (expose l'Ollama local à un hôte distant docker-01).
- Env serveur (plist) : `OLLAMA_CONTEXT_LENGTH=131072`, `OLLAMA_HOST=127.0.0.1:11434`, `OLLAMA_KEEP_ALIVE=10m`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NO_CLOUD=1`, `OLLAMA_ORIGINS=http://ollama-tailscale,…`.

## 4. Configuration Codex (`~/.codex/config.toml`, 326 lignes) — observée

| Élément | Valeur |
|---|---|
| openai_base_url | `http://127.0.0.1:11434/api/codex/v1` (tout le trafic via proxy Ollama) |
| model par défaut | `gpt-5.6-sol` |
| model_reasoning_effort | `medium` (global) — pas d'override par modèle |
| model_catalog_json | `~/.codex/ollama-launch-models.json` (14 modèles) |
| enabled-reasoning-efforts | none, minimal, low, medium, high, xhigh, max, ultra |
| show-context-window-usage | true |
| notify | SkyComputerUseClient (turn-ended) |
| memories | generate + use = true |
| sandbox | restricted fs + restricted network, approval OnRequest |
| MCP configurés (config.toml) | node_repl, n8n-mcp |
| Plugins activés | visualize, documents, outlook-calendar, teams, pdf, spreadsheets, presentations, template-creator, codex-app-tools, browser, unified-computer-use, code-review |
| Projects trusted | ~60 (dont super-agent, mac-ia-local implicite) |

### Provider déclaré

```toml
[model_providers.ollama_codex]
name = "Ollama Local Codex"
base_url = "http://127.0.0.1:11434/api/codex/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
```

### Fichiers de bascule (observés)

- `~/.codex/qwen-local.config.toml` : `model = "qwen3.6:35b-mlx"`, `model_provider = "ollama_codex"`
- `~/.codex/gpt-cloud.config.toml` : `model = "gpt-5.6-sol"`, `model_provider = "openai"`

### Catalogue modèles (`ollama-launch-models.json`)

| Slug | Contexte |
|---|---|
| qwen3-coder:30b | 262144 |
| muse-glimmer:30b-mlx | 128000 |
| qwen3.6:35b-mlx | 128000 |
| **qwen3.6:35b-coding** | **262144** |
| gpt-6.1-sol, gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-reserve, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, gpt-5.5, codex-auto-review | 272000 |

### Overrides & routing (observés)

- `ollama-codex-local-overrides.json` : qwen3.6:35b-coding → `use_responses_lite=false`, `tool_mode=null`, `supports_search_tool=true`
- `ollama-launch-codex-routing.json` : thinking none/high pour qwen3.6:35b-mlx (default false) et qwen3.6:35b-coding (default **true**) ; auto_review_model=selected, fallback qwen3-coder:30b
- `apply-qwen-codex-fix.sh` : script de re-patch idempotent du catalogue

## 5. Modèle local principal (observé)

`qwen3.6:35b-coding` :
- Architecture qwen35moe, 35.5B paramètres, Q4_K_M, 22 GB
- Contexte 262144 (serveur : 131072 via OLLAMA_CONTEXT_LENGTH)
- Capabilities : completion, vision, tools, thinking (levels false/true, default true)
- Paramètres : temperature 0.6, top_p 0.95, top_k 20, min_p 0, draft_num_predict 2
- Renderer/Parser : qwen3.5

## 6. Secrets (PRESENCE uniquement)

| Secret | État |
|---|---|
| auth.json : tokens ChatGPT (id/access/refresh, account_id) | PRESENT |
| auth.json : OPENAI_API_KEY | ABSENT |
| Env : ANTHROPIC_ADVISOR | PRESENT (nom seulement) |
| Env : aucune clé API en clair | vérifié |

## 7. Optimisations déjà appliquées (observées)

1. Binaire Ollama patché PR #18413 (proxy Codex / Responses API natif) — SHA b2c89a64…, artefact qualifié dans `artifacts/ollama-v0.35.0-pr18413-release`
2. Routage unifié cloud+local via proxy Ollama (openai_base_url)
3. Catalogue modèles custom (14 modèles, contextes étendus 262K/272K)
4. Overrides tool calling pour qwen3.6:35b-coding (use_responses_lite=false, tool_mode=null)
5. Thinking par modèle (routing JSON) avec default=true pour coding
6. OLLAMA_CONTEXT_LENGTH=131072, KEEP_ALIVE=10m, MAX_LOADED_MODELS=1
7. Tunnel SSH inverse vers docker-01 + origines Tailscale
8. LaunchAgent dédié avec binaire patché versionné
9. Script de re-patch idempotent (apply-qwen-codex-fix.sh)
10. Memories activées, context window usage affiché, reasoning efforts étendus (jusqu'à ultra)

## 8. Hypothèses (non prouvées)

- Le serveur de l'app Ollama (PID 18214) est probablement aussi le binaire patché (l'app a été mise à jour en 0.35.1 qui inclut peut-être le patch) — **non vérifié** (SHA du PID 18214 non comparé).
- `OLLAMA_NO_CLOUD=1` dans la plist s'applique au LaunchAgent, pas nécessairement au serveur de l'app actuellement actif.
- Le proxy Codex relaie le cloud via les tokens ChatGPT — mécanisme exact non audité (hors périmètre).

## 9. Non déterminable

- Version exacte de l'extension Codex VS Code utilisée à l'instant T (plusieurs versions présentes).
- Si le port 11434 sera détenu par le LaunchAgent patché ou l'app Ollama après un reboot (concurrence documentée dans diagnostics/reconciliation-20261002).

## 10. Sauvegardes créées avant modification

Suffixe `.bak-mission-20261003-225030` dans `~/.codex/` pour : config.toml, ollama-launch-models.json, ollama-launch-codex-routing.json, ollama-codex-local-overrides.json, qwen-local.config.toml, gpt-cloud.config.toml.

SHA256 (avant modification) :

```
653b280f7c177aaf1ab4564d48746fa1925517bcc8e9453812f6d8bb492d43b7  config.toml
a623a26f938db2deabf3075f175da08090e4b87e6c893e1c6f287405c6148c82  ollama-launch-models.json
5b3bb70b8117c722f99f8ff7e17957d1bf75a76cfd7f5a2a4ced9fcf259d40c0  ollama-launch-codex-routing.json
a95a9f2bd80398cacd5ff0c5c14b3b3e7a144b003b25ba66c40001373d5fa338  ollama-codex-local-overrides.json
8311b8250d26abf66369137f96b09a9bf842692e296ccc6ded343de7c3a8f37b  qwen-local.config.toml
3767b17640d6a95af761bb916d8eeee0adc8bdd0a53b3b67ef1baf32e1741cc3  gpt-cloud.config.toml
```
