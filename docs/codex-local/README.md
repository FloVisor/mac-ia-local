# Codex Local — Audit, vLLM-Metal et Benchmark A/B

Mission 2026-10-03/04 : audit complet de la configuration Codex locale, baseline Ollama, installation vLLM-Metal, benchmark A/B reproductible.

**Verdict : Ollama conservé comme backend local par défaut ; vLLM-Metal installé, qualifié et disponible.** Voir [11-switch-criteria.md](11-switch-criteria.md).

## Architecture AVANT (inchangée, toujours active)

```
Codex (CLI/VS Code/Desktop)
  → openai_base_url = http://127.0.0.1:11434/api/codex/v1
  → Ollama 0.35.1 patché PR#18413 (proxy Codex / Responses API)
      ├─ local : qwen3.6:35b-coding (Q4_K_M 22GB, ctx 131072)
      └─ relais cloud ChatGPT (gpt-5.6-sol, tokens dans ~/.codex/auth.json)
```

## Architecture APRÈS (ajout, sans suppression)

```
Codex (CLI/VS Code/Desktop)
  ├─ [défaut] openai_base_url → proxy Ollama (cloud + local, inchangé)
  ├─ provider ollama_codex → Ollama local (rollback, inchangé)
  └─ provider vllm_metal [NOUVEAU] → http://127.0.0.1:11400/v1
        vLLM 0.30.0 + vllm-metal 0.30.0.dev + MLX 0.32.1
        mlx-community/Qwen3.6-35B-A3B-4bit (20.4GB, ctx 128K)
```

## Versions

| Composant | Version |
|---|---|
| macOS | 27.0 (M4 Max, 48 GB, 40 cœurs GPU, Metal 4) |
| Codex CLI | 0.160.0 |
| Ollama | 0.35.1 (binaire patché v0.35.0-pr18413) |
| vLLM / vllm-metal | 0.30.0 / 0.30.0.dev20261003204550 |
| MLX | 0.32.1 |
| Python (venv vllm) | 3.12.14 (`~/.venv-vllm-metal`) |

## Modèles

- **Ollama** : `qwen3.6:35b-coding` — qwen35moe 35.5B, Q4_K_M, 22 GB, ctx 131072
- **vLLM** : `mlx-community/Qwen3.6-35B-A3B-4bit` — qwen3_5_moe, 4-bit MLX, 20.4 GB, ctx 128K (SHA repo 38740b84)

## Ports

| Port | Service |
|---|---|
| 11434 | Ollama (proxy Codex inclus) |
| 11400 | vLLM-Metal (API OpenAI-compatible + Responses) |
| 5678 | n8n (conteneur docker via colima) |

## Démarrage / Arrêt

```sh
# vLLM-Metal (démarrage ~30s)
source ~/.venv-vllm-metal/bin/activate
vllm serve mlx-community/Qwen3.6-35B-A3B-4bit \
  --port 11400 --max-model-len 131072 \
  --tool-call-parser qwen3_coder --reasoning-parser qwen3 \
  --enable-auto-tool-choice
# Arrêt : kill des PID vllm/EngineCore (ps aux | grep -E "vllm|EngineCore")

# Ollama : déjà actif (LaunchAgent + app)
ollama stop qwen3.6:35b-coding   # décharger le modèle de la RAM
# (le modèle se recharge automatiquement à la prochaine requête)
```

## Health checks

```sh
curl -s http://127.0.0.1:11434/api/version        # Ollama
curl -s http://127.0.0.1:11400/health             # vLLM
curl -s http://127.0.0.1:11400/v1/models          # vLLM modèles
ollama ps                                         # modèle chargé ?
```

## Bascule Cloud / local

```sh
codex exec "..."                                                  # Cloud (défaut)
codex exec -c model_provider=ollama_codex -c model=qwen3.6:35b-coding "..."   # Ollama
codex exec -c model_provider=vllm_metal -c model=mlx-community/Qwen3.6-35B-A3B-4bit "..."  # vLLM
```

Dans VS Code : sélecteur de modèle (catalogue commun via proxy Ollama pour cloud+ollama ; vLLM accessible via overrides `-c`).

## Vérifier la mémoire

```sh
sysctl vm.swapusage
memory_pressure -Q
ps aux | grep -E "llama-server|EngineCore"   # RSS Ollama ; vLLM vit en wired GPU
```

## Résultats clés (détail : [08-benchmark.md](08-benchmark.md))

| Métrique | Ollama | vLLM-Metal |
|---|---|---|
| tok/s (décodage) | **56–75** | 17–22 |
| Prefill 62K | 159s | **69s** |
| Prefill 128K | 185s | **121s** (3.9s avec prefix cache) |
| Tour Codex | **27–38s** | 3–6 min |
| RAM | 24.4 GB RSS | ~36 GB wired GPU |

## Documents

1. [01-baseline-codex.md](01-baseline-codex.md) — audit initial complet
2. [02-mcp-matrix.md](02-mcp-matrix.md) — matrice MCP avant
3. [03-ollama-baseline.md](03-ollama-baseline.md) — baseline Ollama
4. [04-vllm-metal-verification.md](04-vllm-metal-verification.md) — vérification docs/checkpoint
5. [05-vllm-metal-installation.md](05-vllm-metal-installation.md) — installation
6. [06-vllm-model-configuration.md](06-vllm-model-configuration.md) — configuration modèle
7. [07-vllm-codex-integration.md](07-vllm-codex-integration.md) — intégration Codex
8. [08-benchmark.md](08-benchmark.md) — benchmark A/B
9. [09-mcp-post-migration.md](09-mcp-post-migration.md) — MCP post-migration
10. [10-vllm-optimization.md](10-vllm-optimization.md) — optimisation
11. [11-switch-criteria.md](11-switch-criteria.md) — critère de bascule
12. [12-rollback.md](12-rollback.md) — rollback

## Troubleshooting

- **vLLM 400 "maximum context length"** : prompt+output > max-model-len — réduire le prompt.
- **n8n NO_RESPONSE** : vérifier la VM colima (`colima stop && colima start`, conteneur n8n-kit) — ne jamais kill brutalement un process group attaché à docker.
- **Codex lent avec vLLM** : attendu (préfill système ~24k tokens par processus + thinking long) — voir benchmark.
- **Warning ffmpeg/cv2** : cosmétique.

## Rollback

Voir [12-rollback.md](12-rollback.md) — testé, opérationnel, sans réinstallation.
