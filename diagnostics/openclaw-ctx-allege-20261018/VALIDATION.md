# Validation — allègement contexte OpenClaw (2026-10-18 21:45–22:05)

## Actions

1. **Plugins désactivés** (recochables via `openclaw plugins enable <id>`) :
   providers cloud sans credentials : alibaba, apple-fm, azure-speech, deepgram, elevenlabs, fal, huggingface, minimax, nvidia, openrouter, together, xai, runway, senseaudio, litellm, lmstudio, sglang, vllm, kie, google, github, github-copilot, openai, microsoft, microsoft-foundry, copilot-proxy, openai-whisper ;
   plugins fonctionnels : browser, canvas, cua-computer, device-pair, document-extract, file-transfer, geolocation, linux-node, talk-voice, tts-local-cli, web-readability, clawrouter, bonjour, opencode-go.
   **Conservés actifs** : anthropic, memory-core, ollama (modèle utilitaire titres), imessage, microsoft-graph. MCP orion/outline (serveurs `mcp.servers`) et skill `gog` (Gmail) non concernés par les plugins.
   Backup config : `~/.openclaw/openclaw.json.bak.pre-plugins-cleanup-20261018-2152`.
2. **AGENTS.md allégés** (procédures métier déplacées vers skills existants `microsoft-365-pro`/`mcp-raphael`, boilerplate OpenClaw condensé, zéro perte d'information) :
   - Pro : 11 476 → 3 497 octets
   - Perso : 7 831 → 2 034 octets
   - Technique : 6 901 → 1 808 octets
   Backups : `*.bak-pre-allege-20261018` dans chaque workspace. Commits : 247600a (Pro), + Perso/Technique.

## Mesures (prompt tokens 1er tour, session neuve, `openclaw agent --json`)

| Agent | Avant | Après | Gain |
|---|---|---|---|
| main (Pro) | 11 480 | 9 701 | −1 779 (−15,5 %) |
| perso | 6 370 | 5 097 | −1 273 (−20 %) |
| technique | 6 141 | 5 051 | −1 090 (−17,8 %) |

Note : le baseline main mesuré à 21:58 (11 480) inclut déjà l'AGENTS.md étoffé de 21:51 (commit 0ecb397, +187 lignes) ; le baseline historique avant ce commit était ~8 200. Le catalogue d'outils (55) est inchangé : `tools.allow` filtre déjà les schémas hors prompt (tool-search compact), le poste dominant restant l'AGENTS.md.

## Non-régression

- `openclaw config validate` : Config valid.
- `openclaw channels status --probe` : iMessage enabled, configured, running, connected, works.
- Doctor : warnings pré-existants uniquement (device-pair désactivé — attendu, plaintext secrets, bind loopback).
- Modèle utilitaire titres (`ollama/qwen3:0.6b-titre`) intact.

## Retour arrière

- Plugins : `openclaw plugins enable <ids…>` ou restaurer `openclaw.json.bak.pre-plugins-cleanup-20261018-2152`.
- AGENTS.md : restaurer `*.bak-pre-allege-20261018` ou `git revert` dans chaque workspace.
