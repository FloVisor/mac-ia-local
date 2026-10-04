# Benchmark A/B — Ollama vs vLLM-Metal (corpus identique)

Date : 2026-10-03/04 · Même corpus `evidence/bench-prompts/`, temp 0.6, 3 runs (médiane [min–max]) pour A/B/C, 1 run par niveau de contexte.

## 1. Tableau comparatif global

| Test | Ollama (qwen3.6:35b-coding Q4_K_M 22GB) | vLLM (mlx-community/Qwen3.6-35B-A3B-4bit 20.4GB) | Delta |
|---|---|---|---|
| **Modèle** | qwen3.6:35b-coding (qwen35moe 35.5B) | mlx-community/Qwen3.6-35B-A3B-4bit (qwen3_5_moe) | même base Qwen3.6-35B-A3B |
| **Quantification** | Q4_K_M (GGUF) | 4-bit MLX (safetensors) | équivalent 4-bit |
| **TTFT A (médiane)** | 0.06s | 0.87s [0.14–17.1] | Ollama plus stable à froid |
| **tok/s A (médiane)** | **72.5** [70.0–74.8] | 19.2 [9.0–22.0] | **Ollama 3.8x plus rapide** |
| **TTFT B** | 0.05s | 0.20s | comparable |
| **tok/s B** | **68.2** [65.1–69.7] | 22.1 [21.5–22.6] | **Ollama 3.1x plus rapide** |
| **TTFT C** | 0.05s | 0.15s | comparable |
| **tok/s C** | **56.1** [54.8–61.1] | 17.7 [16.6–19.3] | **Ollama 3.2x plus rapide** |
| **Contexte 16K TTFT** | 16.5s | 14.9s | vLLM légèrement mieux |
| **Contexte 32K TTFT** | 27.3s | 25.4s | vLLM légèrement mieux |
| **Contexte 64K TTFT** | 158.8s | 69.2s | **vLLM 2.3x mieux** |
| **Contexte 96K TTFT** | 239.4s | 274.1s (froid) / 3.3s (cache) | comparable à froid, vLLM écrasant avec prefix cache |
| **Contexte 128K TTFT** | 184.5s | 120.9s (froid) / 3.9s (cache) | **vLLM mieux** |
| **RAM résidente** | llama-server RSS 24.4 GB | EngineCore RSS ~0.1 GB + **~36 GB wired GPU** (Metal) | vLLM ~2.2x moins de RAM process, mais wired GPU élevé |
| **Swap (modèle chargé)** | jusqu'à 4.6 GB churn | stable ~2.9–4.5 GB | comparable |
| **Codex tour simple** | 27–38s | 3m00s–6m09s | **Ollama 5–10x plus rapide** |
| **Responses API** | via proxy patché PR#18413 | native vLLM `/v1/responses` | les deux OK |
| **Tools (API directe)** | PASS (max_tokens 800) | PASS (max_tokens 800, 101 tok) | équivalent |
| **Tools (via Codex)** | PASS 1 appel | PASS 1 appel | équivalent |
| **MCP n8n (via Codex)** | PASS status ok | PASS status ok | équivalent |
| **Session longue 10 tours** | 10/10 PASS ~28s/tour | non rejoué (latence 3–6 min/tour rend le test >30 min) | Ollama praticable, vLLM pénible |

## 2. Détail vLLM (3 runs)

| Test | TTFT médian | Total médian | tok/s médian |
|---|---|---|---|
| A — génération | 0.87s [0.14–17.09] | 13.9s [11.0–26.6] | 19.2 [9.0–22.0] |
| B — raisonnement | 0.20s [0.18–0.75] | 15.6s [15.6–16.2] | 22.1 [21.5–22.6] |
| C — repo task | 0.15s [0.15–0.69] | 16.5s [16.4–16.6] | 17.7 [16.6–19.3] |

## 3. Contexte vLLM (à froid = premier passage, à chaud = prefix cache hit)

| Niveau | TTFT froid | TTFT chaud (cache) |
|---|---|---|
| 16K | 14.9s | — |
| 32K | 25.4s | — |
| 62K | 69.2s | — |
| 99K | 274.1s | 3.3s |
| 125K | 120.9s | 3.9s |

Prefix cache hit rate observé : 33–49% (monte avec les requêtes répétées).

## 4. Analyse factuelle

1. **Décodage (tok/s)** : Ollama nettement supérieur (56–75 vs 17–22 tok/s). Le runner llama.cpp GGUF décode plus vite que le MoE MLX 4-bit sur M4 Max.
2. **Préfill long-contexte** : vLLM-Metal supérieur ≥64K (69s vs 159s à 62K ; 121s vs 185s à 125K) ET le prefix caching rend les requêtes répétées quasi instantanées (3–4s) — avantage décisif pour l'usage agentique Codex où le prompt système (~24k tokens) se répète.
3. **Via Codex** : vLLM reste 5–10x plus lent par tour (3–6 min) car chaque tour `codex exec` est un processus neuf (pas de réutilisation du cache inter-processus) et le modèle think longuement (83k–136k tokens/tour vs 24k).
4. **Mémoire** : vLLM wired GPU ~36 GB (wired_limit 37.4) vs Ollama RSS 24.4 GB — sur 48 GB unifiés, les deux tiennent mais vLLM laisse moins de marge aux autres apps.
5. **Stabilité** : aucun crash, aucune erreur protocole, aucune boucle sur les deux moteurs. Erreurs 400 propres de vLLM quand prompt > max-model-len.
