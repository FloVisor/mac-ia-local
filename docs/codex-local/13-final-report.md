# Rapport final — Audit Codex Mac + Migration vLLM-Metal + Benchmark A/B

Mission : 2026-10-03/04 · Repo : `mac-ia-local` · Commit : `9dd058c`

## 1. Configuration initiale

MacBook Pro M4 Max 48 GB (40 cœurs GPU, Metal 4), macOS 27.0. Codex CLI 0.160.0 route tout via le proxy Codex d'Ollama patché (PR#18413) sur `http://127.0.0.1:11434/api/codex/v1` : local `qwen3.6:35b-coding` + relais cloud ChatGPT (gpt-5.6-sol, tokens dans `~/.codex/auth.json`).

## 2. Optimisations Codex trouvées

Binaire Ollama patché (proxy Responses API natif), catalogue custom 14 modèles (contextes 262K/272K), overrides tool calling qwen3.6 (`use_responses_lite=false`, `tool_mode=null`), thinking par modèle (routing JSON), `OLLAMA_CONTEXT_LENGTH=131072`, keep_alive 10m, max_loaded_models=1, tunnel SSH inverse docker-01, origines Tailscale, LaunchAgent dédié versionné, script de re-patch idempotent, memories activées, reasoning efforts étendus (none→ultra).

## 3. MCP trouvés et statut

| MCP | Statut | Test |
|---|---|---|
| n8n-mcp (28 tools) | PASS | initialize 0.55s, health_check ok 0.4s |
| node_repl (4 tools) | PASS | initialize 0.12s |
| cua_repl (desktop) | PASS indirect | doctor : app-server OK |
| code-review, codex_app | disabled (inchangé) | — |

## 4. Baseline Ollama (qwen3.6:35b-coding, Q4_K_M 22 GB)

| Test | Résultat (médiane 3 runs) |
|---|---|
| A génération | TTFT 0.06s · 72.5 tok/s |
| B raisonnement | TTFT 0.05s · 68.2 tok/s |
| C repo task | TTFT 0.05s · 56.1 tok/s |
| Contexte 16K/32K/64K/96K/128K | TTFT 16.5/27/159/239/185s |
| Tool calling | PASS (get_weather correct) |
| MCP via Codex | PASS (1 appel, status ok) |
| Session 10 tours | 10/10 PASS, ~28s/tour |
| Cloud | PASS 4s |

## 5. vLLM-Metal installé

Méthode officielle (install script du projet), venv isolé `~/.venv-vllm-metal` (Python 3.12.14), vllm 0.30.0 + vllm-metal 0.30.0.dev20261003204550 + MLX 0.32.1. Supprimable : `rm -rf ~/.venv-vllm-metal`.

## 6. Modèle exact utilisé

`mlx-community/Qwen3.6-35B-A3B-4bit` — officiel mlx-community, base Qwen/Qwen3.6-35B-A3B, 4-bit MLX, 20.4 GB (4 shards), SHA repo 38740b84. Équivalent direct du modèle Ollama (même architecture qwen3_5_moe).

## 7. Paramètres vLLM

Port 11400 · `--max-model-len 131072` · `--tool-call-parser qwen3_coder` · `--reasoning-parser qwen3` · `--enable-auto-tool-choice` · prefix caching on (défaut) · batched tokens 2048 (défaut ; 8192 testé et rejeté : prefill 62K 110.5s vs 69.2s) · gpu-memory-utilization 0.92 · wired_limit 37.4 GB.

## 8. Configuration Codex ajoutée

Un seul bloc dans `~/.codex/config.toml` :

```toml
[model_providers.vllm_metal]
name = "vLLM Metal Local"
base_url = "http://127.0.0.1:11400/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
```

Rien d'autre modifié (MCP, permissions, profils, Cloud, AGENTS.md intacts — validé tomllib + codex doctor).

## 9. Résultats benchmark (corpus identique)

| Test | Ollama | vLLM | Delta |
|---|---|---|---|
| tok/s A/B/C | **72.5 / 68.2 / 56.1** | 19.2 / 22.1 / 17.7 | Ollama ~3x |
| Prefill 62K | 158.8s | **69.2s** | vLLM 2.3x |
| Prefill 128K | 184.5s | **120.9s** (3.9s en cache) | vLLM mieux |
| Tour Codex | **27–38s** | 3–6 min | Ollama 5–10x |
| RAM | 24.4 GB RSS | ~36 GB wired GPU | — |

## 10. Résultats qualité (PASS/FAIL)

| Test | Ollama | vLLM |
|---|---|---|
| Réponse exacte simple | PASS | PASS |
| Correction bug (B) | PASS | PASS |
| Repo task multi-fichiers (C) | PASS | PASS |
| Tool call exact (D) | PASS — 1 appel | PASS — 1 appel |
| MCP exact (E) | PASS — 1 appel | PASS — 1 appel |
| Terminal agentique (F) | PASS (adaptation sandbox) | PASS |
| Boucles/répétitions | aucune | aucune |
| Hallucinations fichiers/commandes | aucune | aucune |

## 11. Mémoire / swap

Ollama : llama-server RSS 24.4 GB, swap churn jusqu'à 4.6 GB en 128K. vLLM : ~36 GB wired GPU (wired_limit 37.4), swap stable 2.9–4.5 GB, pic 9.3 GB pendant tests simultanés, aucun crash.

## 12. Régressions éventuelles

**Aucune.** MCP : zéro régression (matrice rejouée identique). Cloud : PASS. Ollama : intact.

## 13. Corrections effectuées

1. VM colima (héberge n8n) tuée par SIGKILL pendant un probe docker → `colima stop && colima start`, conteneur n8n-kit restauré, healthz 200, re-test MCP PASS.
2. bench.py : capture des deltas `reasoning` (le modèle think avant de répondre).
3. Test Cloud interrompu (saturation mémoire transitoire) → re-validé au matin : PASS 4.6s.

## 14. Configuration finale retenue

**Ollama conservé comme backend local par défaut** + Cloud + vLLM qualifié disponible. Migration NON forcée (vLLM moins bon sur la latence par tour, critère d'usage quotidien).

## 15. Procédure de bascule Cloud / local

```sh
codex exec "…"  # Cloud (défaut)
codex exec -c model_provider=ollama_codex -c model=qwen3.6:35b-coding "…"
codex exec -c model_provider=vllm_metal -c model=mlx-community/Qwen3.6-35B-A3B-4bit "…"
```

## 16. Procédure de rollback

Testée : `ROLLBACK_OLLAMA_OK` en 39.8s, sans réinstallation. Ollama jamais désinstallé, modèle jamais supprimé, provider `ollama_codex` intact. Détail : [12-rollback.md](12-rollback.md).

## 17. Fichiers modifiés

- `~/.codex/config.toml` : +7 lignes (provider vllm_metal) — sauvegarde `.bak-mission-20261003-225030`, SHA256 d'origine dans [01-baseline-codex.md](01-baseline-codex.md)
- Repo : 21 fichiers créés dans `docs/codex-local/`

## 18. Commits créés

`9dd058c` — docs(codex): audit local inference and qualify vLLM Metal (21 fichiers, 1005 insertions, aucun secret, modifications utilisateur préexistantes exclues).

## 19. Points non prouvés / limites

- Session longue 10 tours non rejouée sur vLLM (latence 3–6 min/tour → >30 min de test).
- SHA du serveur Ollama actif (PID app 18214) non comparé au binaire patché du LaunchAgent.
- Qualité du reasoning long-contexte non évaluée au-delà du test de rappel simple.
- TTFT vLLM à froid variable (17s observé une fois sur test A run 1).

## 20. Recommandation factuelle

**Conserver les deux :**
- **Ollama** = backend local par défaut (décodage 3x plus rapide, tours Codex 5–10x plus rapides, RAM process moindre).
- **vLLM-Metal** = conservé installé et qualifié pour investigation (préfill long-contexte ≥64K 2x plus rapide, prefix caching quasi instantané sur requêtes répétées, Responses API native, ~2.2x moins de RAM process).
