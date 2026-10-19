# Comparaison vLLM-Metal — Qwen3.6-35B-A3B vs Qwen3-Coder-30B-A3B

Date : 2026-10-04 · Mission : qualifier `mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit` comme modèle témoin vLLM-Metal et déterminer l'origine du mauvais décodage observé avec Qwen3.6.

Baselines lues dans le repo (aucun benchmark Ollama relancé) : [03-ollama-baseline.md](03-ollama-baseline.md), [08-benchmark.md](08-benchmark.md), [13-final-report.md](13-final-report.md).

## 1. Modèle testé

| Élément | Valeur (vérifiée sur HF + code installé) |
|---|---|
| Slug | `mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit` |
| SHA repo | `6e302ea604ad9ab206367e2c501d1571023e7b6d` |
| Architecture | `Qwen3MoeForCausalLM` (qwen3_moe) — **supportée** par vllm-metal 0.30.0 (registry.py:203) |
| Quantification | 4-bit group 64 (gates MoE en 8-bit) |
| Poids | 17.2 GB (4 shards safetensors) |
| Contexte natif | 262 144 (bridé serveur à 131 072) |
| MoE | 128 experts, 8 actifs/tok, 48 couches, GQA 4 KV heads |
| Tool-call parser | `qwen3_coder` (Qwen3EngineToolParser, format XML — vérifié dans `vllm/tool_parsers/__init__.py:185`) |
| Reasoning parser | **AUCUN** — le modèle Instruct n'émet pas de think tags (template sans balise think, vérifié). Le parser `qwen3` détourne TOUT le contenu vers `reasoning` → retiré pour rester comparable à la baseline Ollama (contenu streamé dans `content`). |

## 2. Paramètres vLLM (run comparable)

```sh
vllm serve mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit \
  --port 11400 --max-model-len 131072 --max-num-batched-tokens 2048 \
  --tool-call-parser qwen3_coder --enable-auto-tool-choice
```

Identiques à la campagne Qwen3.6 (port, max-model-len, batched tokens, tool parser), **sauf** `--reasoning-parser qwen3` retiré (voir §1). Startup complet : [evidence/qwen3-coder-vllm-startup.log](evidence/qwen3-coder-vllm-startup.log).

## 3. Mémoire au démarrage (extraite du log startup)

| Métrique | Qwen3-Coder 30B | Qwen3.6 35B (baseline) |
|---|---|---|
| Metal total | 51.5 GB | 51.5 GB |
| Dispo avant chargement | 40.3 GB | — |
| Dispo après chargement | 2.6 GB → **wired ~48.9 GB** | ~36 GB wired |
| wired_limit | 37.4 GB (auto) | 37.4 GB |
| KV cache CPU | 192 576 tokens (12 036 blocks) | 752 413 tokens |
| Concurrence 128K | 1.47x | 5.74x |
| EngineCore RSS | 14.7 GB (phys_footprint 18 GB) | 9.8–11.1 GB |
| gpu-memory-utilization | 0.92 (défaut) | 0.92 |

Note : le wired Metal mesuré (~48.9 GB) dépasse le wired_limit 37.4 — la limite est indicative sur le chemin MLX (poids + KV CPU mappés). Qwen3-Coder occupe **plus** de wired que Qwen3.6 (48.9 vs ~36 GB) malgré un modèle plus petit : le KV cache CPU est plus gros par token (48 couches × 4 KV heads × 128 dim vs architecture GDN plus économe).

## 4. Résultats A/B/C (3 runs, médiane [min–max], temp 0.6, bench.py identique)

| Test | Ollama Qwen3.6 (baseline repo) | vLLM Qwen3.6 (baseline repo) | **vLLM Qwen3-Coder** |
|---|---:|---:|---:|
| A tok/s | **72.5** [70.0–74.8] | 19.2 [9.0–22.0] | **23.4** [22.3–23.7] |
| A TTFT | 0.06s | 0.87s [0.14–17.1] | 0.06s [0.06–0.61] |
| B tok/s | **68.2** [65.1–69.7] | 22.1 [21.5–22.6] | **34.1** [33.9–34.8] |
| B TTFT | 0.05s | 0.20s | 0.07s |
| C tok/s | **56.1** [54.8–61.1] | 17.7 [16.6–19.3] | **18.9** [17.4–22.5] |
| C TTFT | 0.05s | 0.15s | 0.06s |
| Qualité A/B/C | PASS | PASS | **PASS** (fizzbuzz correct ; bug division par zéro identifié ; fonction + test unitaire proposés — réponse en anglais, nom `subtraction` au lieu de `soustraction`, tâche remplie) |

Qwen3-Coder décode **1.2x à 1.5x plus vite** que Qwen3.6 sur vLLM-Metal, mais reste **2.4x à 3x derrière Ollama**.

## 5. Contexte 64K / 128K (froid = 1er passage, chaud = prefix cache)

| Niveau | vLLM Qwen3.6 (baseline) | **vLLM Qwen3-Coder** |
|---|---:|---:|
| 64K cold TTFT | **69.2s** | 290.3s |
| 64K warm TTFT | — | **1.3s** |
| ~125K cold TTFT | **120.9s** | 514.3s (prompt 115k tokens réels) |
| ~125K warm TTFT | 3.9s | **1.9s** |

Le préfill long-contexte de Qwen3-Coder est **~4x plus lent** que Qwen3.6 à froid (290s vs 69s à 64K ; 514s vs 121s à ~125K). Le prefix cache compense au 2e passage (1.3–1.9s). Erreur 400 propre quand le prompt dépasse max-model-len (comportement correct).

## 6. Effet de la limitation mémoire (budget vLLM)

| Config | Test B tok/s | KV cache | Swap |
|---|---:|---|---|
| 0.92 (défaut) | 34.1 | 192 576 tok | 0.25 MB |
| 0.65 | **échec démarrage** : KV requis 12 GiB > dispo 7.52 GiB (max-model-len estimé 82 144) | — | — |
| 0.75 | **échec démarrage** : KV requis 12 GiB > dispo 11.27 GiB (max-model-len estimé 123 040) | — | — |
| 0.78 (minimum viable) | **31.3** [30.5–31.6] | 135 328 tok (concurrence 1.03x) | 0.25 MB |

Logs : [evidence/qwen3-coder-vllm-mem065-startup.log](evidence/qwen3-coder-vllm-mem065-startup.log), [evidence/qwen3-coder-vllm-mem075-startup.log](evidence/qwen3-coder-vllm-mem075-startup.log), [evidence/qwen3-coder-vllm-mem078-startup.log](evidence/qwen3-coder-vllm-mem078-startup.log).

**Conclusion mémoire** : réduire le budget vLLM de 0.92 à 0.78 ne dégrade le décodage que de ~8% (34.1 → 31.3 tok/s) et le swap reste nul. La pression mémoire n'explique **pas** le mauvais décodage.

## 7. Swap avant/après

| Moment | Swap used |
|---|---|
| Avant tout test (Mac au repos) | 0.00 MB |
| Modèle chargé + A/B/C | 0.25 MB |
| Tests contexte 64K/128K | 196.9 MB |
| Après 3 tours Codex | 1 664.9 MB (churn transitoire, mem free 36%) |

Le swap reste marginal pendant les benchmarks API ; il croît pendant les tours Codex (prompt système ~24k tokens + contexte MCP par processus neuf).

## 8. Tool calling (test D, API directe, max_tokens 800)

**PASS** — finish_reason=tool_calls, exactement 1 appel `get_weather(city="Paris")`, 22 tokens, aucune répétition. Équivalent aux baselines Ollama/vLLM Qwen3.6.

## 9. MCP via Codex (n8n_health_check, read-only)

**PASS** — 1 appel MCP, status "ok" rapporté correctement. Aucun workflow n8n modifié.

## 10. Tours Codex réels (provider vllm_metal, défaut inchangé)

| Tâche | Durée | Tokens | Résultat |
|---|---:|---:|---|
| Réponse simple (VLLM_CODEX_TEST_OK) | 7m48s | 15 865 | PASS |
| Tool shell (date) | 4m30s | 29 821 | PASS — 1 commande, sortie correcte |
| MCP n8n_health_check | 14m25s | 26 267 | PASS — 1 appel, status ok |

Aucune boucle, aucun reasoning excessivement long visible, mais latence par tour **pire que Qwen3.6** (3–6 min → 4.5–14.5 min). Un "ERROR: Reconnecting... 1/5" apparaît au démarrage de chaque tour (timeout de la 1re requête, récupéré ensuite) — non bloquant mais symptomatique de la lenteur du préfill du prompt système.

## 11. Tableau final comparatif

| Mesure | Ollama Qwen3.6 (repo) | vLLM Qwen3.6 (repo) | **vLLM Qwen3-Coder** |
|---|---:|---:|---:|
| Poids modèle | 22 GB (Q4_K_M GGUF) | 20.4 GB | 17.2 GB |
| A tok/s | **72.5** | 19.2 | 23.4 |
| B tok/s | **68.2** | 22.1 | 34.1 |
| C tok/s | **56.1** | 17.7 | 18.9 |
| TTFT A/B/C | 0.05–0.06s | 0.15–0.87s | 0.06–0.07s |
| 64K cold | 158.8s | **69.2s** | 290.3s |
| ~125K cold | 184.5s | **120.9s** | 514.3s |
| Prefix warm | — | 3.3–3.9s | **1.3–1.9s** |
| Mémoire | 24.4 GB RSS | ~36 GB wired | ~48.9 GB wired / 18 GB footprint |
| Swap delta | jusqu'à 4.6 GB churn | stable ~2.9–4.5 GB | 0.25 MB (bench) → 1.7 GB (Codex) |
| Tool call | PASS | PASS | PASS |
| MCP | PASS | PASS | PASS |
| Codex réel | **27–38s** | 3–6 min | 4.5–14.5 min |

## 12. Hypothèses H1–H4

**H1 — Le mauvais decode de Qwen3.6 venait de l'architecture Qwen3.6/GDN : NON SUPPORTEE (partiellement).**
Qwen3-Coder (qwen3_moe standard, pas GDN) ne décode que 1.2–1.5x plus vite (23.4/34.1/18.9 vs 19.2/22.1/17.7 tok/s). L'architecture explique une petite part, pas la cause principale. En revanche le préfill Qwen3-Coder est 4x plus lent que Qwen3.6 — l'architecture GDN de Qwen3.6 est en réalité **meilleure** pour le préfill long-contexte sur ce chemin.

**H2 — Le mauvais decode venait de la pression mémoire/swap : NON SUPPORTEE.**
Swap quasi nul pendant tous les benchmarks (0.25 MB). Bridage mémoire 0.92→0.78 : seulement −8% tok/s. Le Mac n'est pas sous pression pendant le décodage mono-requête.

**H3 — Le mauvais decode est une limitation générale du chemin mono-requête vLLM-Metal : SUPPORTEE.**
Deux architectures MoE différentes (qwen3_5_moe/GDN et qwen3_moe) plafonnent toutes deux à 17–34 tok/s en décodage mono-requête, loin des 56–75 tok/s d'Ollama/llama.cpp sur le même matériel. Le plafond est le chemin vLLM-Metal lui-même (overhead par step, pas de batching utile en mono-requête), pas le modèle.

**H4 — Qwen3-Coder offre un meilleur compromis réel pour Codex : NON SUPPORTEE.**
Décodage légèrement meilleur (B : 34 vs 22 tok/s) mais préfill 4x plus lent, wired mémoire plus élevée (48.9 vs 36 GB), tours Codex plus lents (4.5–14.5 min vs 3–6 min). Pour l'usage Codex (prompt système ~24k tokens par tour, préfill dominant), Qwen3.6 reste le meilleur choix vLLM — et Ollama les domine tous les deux.

## 13. Décision Qwen3.8-27B-4bit : NON TESTÉ

Critères de la Phase 13 non remplis :
1. Qwen3-Coder ne montre **pas** que vLLM peut dépasser significativement Qwen3.6 (gain décodage modeste, préfill 4x pire, Codex pire) ;
2. La cause identifiée est le chemin vLLM-Metal lui-même (H3), pas le modèle — changer encore de modèle n'apporterait rien ;
3. Aucune vérification de compatibilité qwen3.8 avec vllm-metal 0.30.0 n'a été faite (hors périmètre une fois H3 supportée).

**Qwen3.8-27B-4bit n'a PAS été téléchargé.**

## 14. Limitations non prouvées

- Le wired Metal ~48.9 GB est déduit de "Metal memory available" du log startup, pas d'un compteur direct (pas d'outil macOS fiable pour le wired GPU par processus).
- Le test B sous 0.78 a été fait avec un KV cache réduit (135k tokens) — l'effet KV vs budget n'est pas isolé.
- Session longue 10 tours non rejouée (latence 4.5–14.5 min/tour → >1h de test).
- Qualité du reasoning long-contexte non évaluée au-delà du test de rappel simple.
- Le "ERROR: Reconnecting 1/5" en début de tour Codex n'a pas été diagnostiqué en profondeur (récupéré systématiquement).

## 15. Recommandation

**Garder Ollama Qwen3.6 comme backend local.** Qwen3-Coder sur vLLM-Metal n'est pas un remplacement : décodage encore 2.4–3x derrière Ollama, préfill long-contexte 4x plus lent que Qwen3.6 sur le même moteur, empreinte mémoire plus grande, tours Codex plus lents. La cause racine du mauvais décodage vLLM est le chemin mono-requête vLLM-Metal (H3) — **attendre une amélioration de vLLM-Metal** (batching mono-requête, kernels MoE MLX) avant de réévaluer. vLLM-Metal reste pertinent uniquement pour le préfill ≥64K avec prefix cache sur requêtes répétées intra-processus, usage où Qwen3.6 (pas Qwen3-Coder) est le bon modèle.
