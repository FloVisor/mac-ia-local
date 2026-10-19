# Campagne Qwen3.6-35B-A3B — Ollama vs vLLM-Metal vs oMLX

Date : 2026-10-17 · Machine : MacBook Pro Mac16,5, Apple M4 Max (40 cœurs GPU), 48 Go, macOS 27.0.1 (26A434) · Codex CLI 0.160.0

## 1. Périmètre

Modèle logique unique : `Qwen/Qwen3.6-35B-A3B`. Comparaison pratique de distributions du même modèle, **non strictement iso-quantification** (GGUF Q4_K_M + projector MTP pour Ollama ; MLX 4-bit pour vLLM-Metal et oMLX — même checkpoint HF partagé).

| Élément | Ollama | vLLM-Metal | oMLX |
|---|---|---|---|
| Distribution | `qwen3.6:35b-coding` (digest `017eda0b7c34`, manifeste distant = local, layers `d372de8e…` 21.7 GB + projector MTP `a62390d2…` 0.9 GB, source `qwen3.6-source:35b-a3b-mtp-q4_K_M-20260824`, runner llamacpp, format GGUF Q4_K_M) | `mlx-community/Qwen3.6-35B-A3B-4bit` (révision `38740b84`, 4 safetensors ~19 GB, cache HF partagé) | idem vLLM (même checkpoint, même cache HF) |
| Moteur | Ollama 0.35.1 (binaire qualifié existant, non modifié) | vLLM 0.31.0 + vllm-metal 0.31.0 (wheel officiel `vllm_metal-0.31.0-cp312`, MLX 0.32.1, venv isolé `toolchains/qwen36-campaign/.venv-vllm031`, Python 3.12.14) | oMLX 0.7.1rc1 (DMG officiel `oMLX-0.7.1rc1-macos26-27.dmg`, SHA-256 `a9efb6ea…af352e`, app copiée dans `toolchains/qwen36-campaign/oMLX.app`, kernels natifs précompilés) |
| Port | 11434 (production, LaunchAgent) | 11400 (test) | 8000 (test, headless) |

Sources consultées le 2026-10-17 : ollama.com/v2/library/qwen3.6 (manifeste), huggingface.co/mlx-community/Qwen3.6-35B-A3B-4bit, github.com/vllm-project/vllm-metal/releases (v0.31.0 du 2026-10-13), github.com/vllm-project/vllm-metal/issues/695 et PR #960 (MERGED, incluse dans v0.31.0), github.com/jundot/omlx/releases (v0.7.1rc1 du 2026-10-15), developers.openai.com/codex/config-advanced.

## 2. Kernels et accélérations

- **vLLM-Metal 0.31.0** : PR #960 (routage GQA decode P256/P512, issue #695) **publiée dans la version exécutée**. Déclenchement **vérifié empiriquement** par test différentiel (`VLLM_METAL_DISABLE_GQA_DECODE=1`) : contexte 32K froid — TTFT 34.8s → 41.8s et total 38.0s → 46.7s sans GQA, soit ~+20 % de débit avec GQA actif ; à contexte court le GQA actif est aussi plus rapide (39–40 vs 29–30 tok/s au test B). Aucune trace explicite dans les logs (routage silencieux) — la preuve est comportementale.
- **oMLX 0.7.1rc1** : kernels natifs vérifiés chargés (`native_kernel_status()` : bonsai, decode_fast, glm_moe_dsa, minimax_m3, qwen35_prefill — tous `available: true`). Kernels précompilés du DMG officiel (pas de Xcode complet sur cette machine).
- **Ollama** : runner llamacpp GGUF avec projector MTP (`draft_num_predict 2`), inchangé.

## 3. Méthode de mesure (v2)

Nouveau script `toolchains/qwen36-campaign/bench2.py` (+ `bench2-context.py`, tests unitaires `test_bench2.py` 9/9 OK) : horloge monotone, compteurs natifs uniquement (SSE `usage`), aucun repli mots→tokens, TTFT sur premier contenu utile, séparation content/reasoning/tool_calls, erreurs et troncatures visibles. L'ancien `bench.py` (repli mots, débit sur temps total) n'a pas été réutilisé ; les anciennes mesures restent dans leur historique et ne sont pas comparables directement (changement de méthode + état système).

Limites : `max_tokens=512` atteint partout (`finish_reason=length`) car le thinking consomme le budget — les débits restent valides (tokens réellement générés), mais les réponses sont tronquées par construction. Débit natif de génération : **NON MESURABLE** (aucun des trois moteurs n'expose la durée de génération via `usage.duration`). Le débit affiché est **bout-en-bout** (tokens de sortie / temps total, préfill inclus).

## 4. Résultats API (3 runs, médiane)

| Test | Ollama tok/s (e2e) | vLLM tok/s (e2e) | oMLX tok/s (e2e) |
|---|---:|---:|---:|
| A — génération | **126.8** | 40.1 | **169.8** |
| B — raisonnement | **111.8** | 39.5 | **165.9** |
| C — repo task | **103.6** | 39.0 | **168.4** |
| TTFT (A) | 0.074s | 0.136s | 0.040s |

### Contexte (froid / préfixe réutilisé)

| Niveau | Ollama TTFT froid→chaud | vLLM TTFT froid→chaud | oMLX TTFT froid→chaud |
|---|---|---|---|
| 8K | 6.0s → 0.06s | 6.8s → 0.19s | **5.0s → 0.14s** |
| 32K | 36.0s → 0.14s | 34.8s → 1.09s | **22.6s → 0.29s** |

oMLX domine le préfill long (22.6s à 32K froid, −36 % vs Ollama) et le cache chaud. Ollama et vLLM sont comparables à froid ; le cache de préfixe d'Ollama (chaud) est plus rapide que celui de vLLM.

## 5. Résultats Codex (profils `qwen36-*-test`, reasoning effort low conservé)

| Scénario | Ollama | vLLM-Metal | oMLX |
|---|---|---|---|
| A — analyse (3 runs) | 48/34/31s — **2/3 exacts** (run 1 : a cité la 1re ligne de calcul.py au lieu de temoin.txt) | 235s — exact (1 run) | 133/10/11s — **3/3 exacts** (run 1 à froid, runs 2-3 cache chaud) |
| B — code+tests (3 runs) | 65/31/50s — 3/3 OK | 354s — OK (1 run) | 27/33/28s — 3/3 OK |
| C — outils multi-tours (3 runs) | 40/44/6s — 3/3 exacts | 25s — exact (1 run) | 17/8/8s — 3/3 exacts |
| Réussite | 8/9 | 3/3 (runs longs limités, cf. §7) | **9/9** |

Observations :
- **Reasoning** : les trois moteurs reçoivent `model_reasoning_effort = "low"` ; oMLX génère néanmoins du thinking substantiel même sur requêtes triviales (160 tokens reasoning sur « 2+2 ») — le réglage n'est pas interprété comme une réduction par oMLX. Aucune boucle de reasoning, aucun blocage post-outil, aucun « no last agent message », aucun faux succès détecté sur les trois moteurs.
- **vLLM** : fonctionnellement correct (Responses API, outils, multi-tours) mais 4–10x plus lent sur les tâches avec thinking ; tours A/B à 3m55–5m54. Tests longs arrêtés après qualification minimale (règle des limites de campagne).
- **Ollama** : une erreur d'exactitude au run A1 (mauvais fichier cité) — à surveiller, non reproduite avec prompt clarifié.

## 6. Mémoire et swap

| Mesure | Ollama | vLLM-Metal | oMLX |
|---|---|---|---|
| Modèle chargé | ~23.1 GB VRAM (llama-server RSS ~24 GB) | wired Metal 37.4 GB (limite), KV cache réduit à 7.8 GB (361k tokens) | plafond process 34.3 GB (guard balanced), RSS service ~7.8 GB + allocations Metal |
| Swap pendant tests | stable ~2.4–3.0 GB | **montée à ~26 GB pendant les tours Codex** (pression forte, documentée) | ~4.9–5.2 GB |
| Note | — | 2e démarrage a nécessité `--gpu-memory-utilization 0.85` (OOM Metal au premier essai à 0.92 avec swap résiduel) | memory guard balanced actif |

## 7. Limites et adaptations

- vLLM-Metal : qualification Codex limitée à 1 run par scénario (A/B/C) — les durées (3m55–5m54s) dépassent >2x la baseline sans autre avantage mesuré sur les tâches interactives ; arrêt des tests longs conformément aux limites de campagne.
- oMLX : la clé API (settings `~/.omlx/settings.json`) a été injectée via `http_headers` du provider Codex — mécanisme documenté, testé, isolé dans le provider `omlx_test`.
- MCP de délégation locale (`local_llm` → muse-glimmer production) : **NON TESTÉ** — sa configuration de production n'a pas été modifiée ; le routage vers les moteurs évalués n'a pas été vérifié en isolation.
- Le swap résiduel (~25 GB après campagne vLLM) se résorbera paresseusement ; aucune mesure n'en a dépendu après stabilisation (81–87 % mémoire libre).
- Contexte de production (131072) non revalidé : les tests de contexte se sont limités à 8K/32K conformément au protocole.

## 8. Tableau comparatif unique

| Critère | Ollama | vLLM-Metal | oMLX |
|---|---|---|---|
| Distribution exacte | qwen3.6:35b-coding (GGUF Q4_K_M + MTP projector) | mlx-community/Qwen3.6-35B-A3B-4bit (MLX 4-bit, rév. 38740b84) | idem vLLM |
| Moteur réel | Ollama 0.35.1 / llama-server | vLLM 0.31.0 + vllm-metal 0.31.0 | oMLX 0.7.1rc1 (kernels natifs OK) |
| TTFT (test A) | 0.074s | 0.136s | **0.040s** |
| Decode natif | NON MESURABLE | NON MESURABLE | NON MESURABLE |
| Débit bout-en-bout (B) | 111.8 tok/s | 39.5 tok/s | **165.9 tok/s** |
| Latence 32K froid / chaud | 36.0s / 0.14s | 34.8s / 1.09s | **22.6s / 0.29s** |
| Tâche Codex réussie (B) | 31–65s | 354s | **27–33s** |
| Réussite Codex | 8/9 | 3/3 (limité) | **9/9** |
| Outils et MCP | OK (MCP prod non retesté) | OK | OK |
| Reasoning | OK, effort low respecté | OK, effort low respecté | OK mais thinking non réduit par « low » |
| Stabilité | 1 réponse inexacte (A1) | stable mais lent ; OOM au 1er démarrage (corrigé par budget 0.85) | stable |
| Mémoire / swap | ~24 GB / swap stable | 37.4 GB wired / swap 26 GB en campagne | ~34 GB plafond / swap ~5 GB |
| Adaptations nécessaires | aucune (existant) | venv dédié, budget mémoire 0.85, provider existant | app dédiée, provider + http_headers clé API |
| Coût de maintenance | nul (service existant) | moyen (version à suivre, venv dédié) | moyen (app tierce, rc) |

## 9. Verdicts

- **Ollama : GO** — baseline fiable, déjà en production, 8/9 ; l'erreur A1 est un point de vigilance, pas un bloquant.
- **vLLM-Metal : GO AVEC LIMITATIONS** — fonctionnellement complet (Responses API, outils, GQA #960 vérifié), mais 3–4x derrière sur le débit interactif et pression mémoire/swap forte ; à garder comme plateforme de qualification (conforme à la conclusion 08 existante).
- **oMLX : GO** — le plus rapide sur tous les critères mesurés (débit, TTFT, préfill 32K, cache chaud), 9/9 Codex, kernels natifs vérifiés ; limites : version rc, thinking non réductible via effort, app tierce à maintenir.

## 10. Recommandation finale

**Qwen3.6-35B-A3B sur oMLX, avec `mlx-community/Qwen3.6-35B-A3B-4bit` (révision 38740b84) servi par oMLX 0.7.1rc1 (kernels natifs), profil Codex `qwen36-omlx-test`.**

Nuance : oMLX gagne sur toutes les mesures, mais la marge de confiance sur la stabilité long terme est plus faible qu'Ollama (version rc, éditeur tiers). Ollama reste un repli immédiat et éprouvé. Aucune bascule automatique effectuée — la décision t'appartient.

## 11. Commandes vérifiées

```sh
# --- Ollama (production, déjà démarré via LaunchAgent) ---
curl -s http://127.0.0.1:11434/api/version
codex exec --profile qwen36-ollama-test --skip-git-repo-check "…"

# --- vLLM-Metal (test) ---
cd /Users/fngux2/mac-ia-local/toolchains/qwen36-campaign
nohup .venv-vllm031/bin/vllm serve mlx-community/Qwen3.6-35B-A3B-4bit \
  --port 11400 --max-model-len 131072 --gpu-memory-utilization 0.85 \
  --tool-call-parser qwen3_coder --reasoning-parser qwen3 --enable-auto-tool-choice \
  > vllm-codex-run2.log 2>&1 &
codex exec --profile qwen36-vllm-metal-test --skip-git-repo-check "…"
# arrêt : ps aux | grep -E "vllm|EngineCore" puis kill <PIDs>

# --- oMLX (test) ---
cd /Users/fngux2/mac-ia-local/toolchains/qwen36-campaign
nohup ./oMLX.app/Contents/MacOS/omlx-cli serve --port 8000 --headless --memory-guard balanced \
  > omlx-startup.log 2>&1 &
codex exec --profile qwen36-omlx-test --skip-git-repo-check "…"
# arrêt : ps aux | grep -i omlx puis kill <PIDs>

# --- Rejouer les benchmarks ---
python3 toolchains/qwen36-campaign/bench2.py --endpoint http://127.0.0.1:8000/v1 \
  --model mlx-community--Qwen3.6-35B-A3B-4bit --api-key <clé ~/.omlx/settings.json> \
  --prompt-file codex/evidence/bench-prompts/B-reasoning.md --runs 3
python3 toolchains/qwen36-campaign/bench2-context.py --endpoint … --label … --api-key …
python3 -m unittest toolchains/qwen36-campaign/test_bench2.py  # (depuis le dossier campagne)
```

## 12. État de fin de mission

- Serveurs temporaires vLLM (11400) et oMLX (8000) : **arrêtés**.
- Ollama production : **opérationnel** (vérifié, modèle rechargeable à la demande).
- Aucun modèle préexistant supprimé ; aucun commit Git effectué ; dépôt principal sans modification.
- Config Codex : provider `omlx_test` + 3 profils `qwen36-*-test` ajoutés (sauvegarde : `toolchains/qwen36-campaign/config.toml.bak-20261017-201849`) ; profil par défaut intact.
- Données brutes : `toolchains/qwen36-campaign/results/*.json` (non versionnés).
