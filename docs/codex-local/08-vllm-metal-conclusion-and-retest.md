# vLLM-Metal — Conclusion et procédure de requalification

Date : 2026-10-04 · Statut : **qualification close** — Ollama conservé, vLLM-Metal gardé comme plateforme de qualification uniquement.

**TL;DR (30 secondes)** : Ollama + `qwen3.6:35b-coding` reste le backend local par défaut (decode 56–75 tok/s, tour Codex 27–38 s). vLLM-Metal décode 3x trop lentement (17–34 tok/s, tours Codex 3–14 min) — cause racine : le chemin mono-requête vLLM-Metal, pas le modèle ni la mémoire. Ne retester vLLM-Metal que si une release mentionne Apple Silicon/Metal/decode/kernels ; gate API : **≥ 50 tok/s au test B** (baseline vLLM ~22, Ollama ~68). Ne **pas** rebenchmarker Ollama tant que sa version/modèle/config n'ont pas changé.

Sources (chiffres immuables, commits `9dd058c`, `77983e1`) : [08-benchmark.md](08-benchmark.md), [07-vllm-model-comparison.md](07-vllm-model-comparison.md), [13-final-report.md](13-final-report.md), [03-ollama-baseline.md](03-ollama-baseline.md).

## 1. Verdict actuel

- **Ollama + `qwen3.6:35b-coding` reste le backend local par défaut** : usage quotidien Codex, MCP, repo coding, terminal.
- **vLLM-Metal reste installé uniquement comme backend de test/laboratoire** : qualification des futures versions vLLM/vLLM-Metal. Non démarré en permanence, aucun LaunchAgent nécessaire.
- **Aucune régression fonctionnelle majeure** sur vLLM-Metal : Responses API native, tool calling, MCP — tous PASS.
- **Mais les performances mono-requête sont insuffisantes** pour l'usage Codex interactif (decode 3x derrière Ollama, tours 5–10x plus lents).

Nuances — vLLM-Metal n'est pas "mauvais" partout :

| Dimension | vLLM-Metal vs Ollama |
|---|---|
| **Decode** (mono-requête) | nettement inférieur : 17–34 vs 56–75 tok/s |
| **Prefill long** (≥64K, froid) | supérieur : 69s vs 159s à 64K ; 121s vs 185s à ~125K (Qwen3.6) |
| **Prefix cache** (warm) | écrasant : 1.3–3.9s vs rien d'équivalent côté Ollama |
| **Mémoire** | plus contraint : ~36–49 GB wired GPU vs 24.4 GB RSS |
| **Intégration Codex** | fonctionnel mais lent : 3–14 min/tour vs 27–38s (facteur intégration possible, cf. §4.6) |
| **Multi-request / batching** | avantage théorique sans usage ici : un seul Codex actif à la fois |

## 2. Baseline figée (M4 Max 48 GB, 2026-10-03/04)

Chiffres extraits des rapports existants — **ne pas recalculer, ne pas rebenchmarker Ollama** tant que sa version (0.35.1 patché PR#18413), son modèle (`qwen3.6:35b-coding`) et sa configuration n'ont pas changé. La baseline Git (`9dd058c`, `77983e1`) fait foi.

| Mesure | Ollama Qwen3.6 | vLLM Qwen3.6 | vLLM Qwen3-Coder |
|---|---:|---:|---:|
| A tok/s | **72.5** [70.0–74.8] | 19.2 [9.0–22.0] | 23.4 [22.3–23.7] |
| B tok/s | **68.2** [65.1–69.7] | 22.1 [21.5–22.6] | 34.1 [33.9–34.8] |
| C tok/s | **56.1** [54.8–61.1] | 17.7 [16.6–19.3] | 18.9 [17.4–22.5] |
| Prefill ~64K (froid) | 158.8s | **69.2s** | 290.3s |
| Prefill ~128K (froid) | 184.5s | **120.9s** | 514.3s |
| Prefix cache warm | — | 3.3–3.9s | 1.3–1.9s |
| Mémoire | 24.4 GB RSS | ~36 GB wired GPU | ~48.9 GB wired / 18 GB footprint |
| Swap | churn jusqu'à 4.6 GB | stable ~2.9–4.5 GB | 0.25 MB (bench) → 1.7 GB (Codex) |
| Tool calling | PASS | PASS | PASS |
| MCP (n8n_health_check) | PASS | PASS | PASS |
| Vrai tour Codex | **27–38s** | 3–6 min | 4.5–14.5 min |

Versions de la baseline : macOS 27.0 (M4 Max 48 GB, Metal 4) · vLLM 0.30.0 · vllm-metal 0.30.0.dev20261003204550 · MLX 0.32.1 · Python 3.12.14 (`~/.venv-vllm-metal`) · modèle `mlx-community/Qwen3.6-35B-A3B-4bit` (SHA repo 38740b84) · témoin `mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit` (SHA `6e302ea6`).

## 3. Conclusions techniques démontrées

1. **Le mauvais decode vLLM n'est pas principalement causé par le swap.** Qwen3-Coder a été testé avec swap quasi nul (0.25 MB pendant les benchs) et budget mémoire réduit (0.78, −8% de decode seulement) : le decode reste 2.4–3x derrière Ollama.
2. **Le problème n'est pas spécifique à Qwen3.6/GDN.** Qwen3-Coder (qwen3_moe standard) n'améliore que partiellement le decode (22 → 34 tok/s au test B) — le plafond est le chemin mono-requête vLLM-Metal (hypothèse H3, supportée).
3. **vLLM-Metal est très performant sur certaines opérations** : gros prefill avec Qwen3.6 (2.3x mieux à 64K), prefix caching (3–4s), Responses API native, tool calling, MCP.
4. **Ces avantages ne compensent pas la faiblesse du decode mono-requête** pour notre usage interactif : chaque tour attend la génération token par token.
5. **Le multi-request / continuous batching n'est pas un critère ici** : usage prévu = un seul Codex actif à la fois.
6. **Les très longues durées Codex avec vLLM peuvent comporter un facteur d'intégration Codex supplémentaire** (processus neuf par tour → pas de réutilisation du prefix cache inter-processus, thinking long 83k–136k tokens/tour). Mais même l'API directe reste significativement derrière Ollama (22 vs 68 tok/s au test B) : corriger uniquement l'intégration Codex ne suffirait pas à atteindre les performances Ollama actuelles.

Aucune hypothèse non prouvée n'est présentée comme un fait (limitations documentées dans [07-vllm-model-comparison.md](07-vllm-model-comparison.md) §14).

## 4. État final de l'architecture

```
                    Codex
                      |
       +--------------+--------------+
       |              |              |
     Cloud         Ollama          vLLM
                     |               |
             qwen3.6:35b-coding     LAB
                     |
                  DEFAULT
```

**Ollama** (port 11434, LaunchAgent existant) : backend local principal — usage quotidien, Codex, MCP, repo coding, terminal. Inchangé.

**vLLM-Metal** (port 11400, démarrage manuel uniquement) : non démarré en permanence ; aucun LaunchAgent nécessaire ; utilisé uniquement pour la qualification de nouvelles versions ; checkpoints conservés ; provider Codex `vllm_metal` conservé dans la config.

## 5. Quand faut-il retester vLLM-Metal ?

Pas à chaque micro-version. Un retest est justifié lorsqu'une release vLLM ou vLLM-Metal mentionne au moins un élément pertinent :

- Apple Silicon · Metal · MLX
- single-request / single-sequence decode · decode performance
- paged attention · attention kernel · memory bandwidth
- MoE performance · Qwen3.6 · Qwen3.x · qwen3_moe · qwen3_5_moe · GDN · hybrid attention
- KV cache performance
- Responses API · Codex · tool calling · prefix caching

Une simple correction sans lien avec macOS/Metal/performance d'inférence ne justifie pas une campagne.

## 6. Protocole de retest rapide

Ne **pas** rejouer la campagne historique d'emblée.

**Étape 1 — Versions** : relever `vllm --version`, version vllm-metal (`pip show vllm-metal`), version MLX (`python -c "import mlx.core as mx; print(mx.__version__)"`), macOS (`sw_vers`), modèle exact + SHA/revision — comparer à la baseline (§2).

**Étape 2 — Démarrage** : uniquement `mlx-community/Qwen3.6-35B-A3B-4bit` avec les paramètres de la baseline :

```sh
source ~/.venv-vllm-metal/bin/activate
vllm serve mlx-community/Qwen3.6-35B-A3B-4bit \
  --port 11400 --max-model-len 131072 \
  --tool-call-parser qwen3_coder --reasoning-parser qwen3 \
  --enable-auto-tool-choice
```

**Étape 3 — Tests API directs A/B/C** (3 runs chacun), mesurer TTFT, tok/s, total, mémoire, swap :

```sh
python3 docs/codex-local/evidence/bench.py \
  --endpoint http://127.0.0.1:11400/v1 \
  --model mlx-community/Qwen3.6-35B-A3B-4bit \
  --prompt-file docs/codex-local/evidence/bench-prompts/B-reasoning.md --runs 3
```

(idem avec `A-generation.md` et `C-repo-task.md`)

## 7. Gate de performance (test B, cette machine uniquement)

Baseline : vLLM Qwen3.6 ~22 tok/s · Ollama ~68 tok/s.

| Test B tok/s | Décision |
|---|---|
| < 30 | **STOP** — amélioration insuffisante, ne pas retester Codex |
| 30–40 | amélioration réelle mais insuffisante — documenter ; Codex complet non nécessaire sauf changement important Responses/tooling |
| 40–50 | intéressant — faire ensuite un test Codex simple |
| ≥ 50 | **requalification complète justifiée** |
| ≥ 60 | candidat sérieux pour comparaison directe avec Ollama |

Ces seuils ne sont pas des benchmarks universels : ils servent uniquement à décider si une campagne vaut le temps sur ce Mac.

## 8. Si le gate est franchi (≥ 50 tok/s au test B)

Rejouer : 1) A/B/C complets ; 2) 64K cold ; 3) 128K cold ; 4) 128K warm / prefix cache ; 5) tool call ; 6) MCP `n8n_health_check` ; 7) un tour Codex simple ; 8) un tour shell ; 9) un tour MCP. Ne refaire la session 10 tours que si les temps deviennent raisonnables.

## 9. Gate Codex

Comparaison au baseline Ollama : **27–38 s par tour représentatif**.

| Tour Codex | Interprétation |
|---|---|
| < 60s | très intéressant |
| 60–90s | compétitif selon autres avantages |
| 90–120s | amélioration importante mais Ollama reste préférable pour l'interactif |
| > 120s | ne pas poursuivre la migration |

Ne pas rebenchmarker Ollama si sa baseline reste valable.

## 10. Mémoire (contrainte M4 Max 48 GB)

- Mémoire unifiée = contrainte forte ; éviter les configurations qui poussent durablement macOS au swap.
- **RSS seul n'est pas une mesure fiable des allocations MLX/Metal** (vLLM vit en wired GPU).
- Utiliser : `memory_pressure -Q`, `sysctl vm.swapusage`, logs vLLM (startup : "Metal memory available"), mémoire wired/Metal quand disponible.
- **Critère** : une amélioration de tok/s obtenue au prix d'un swap massif n'est pas une amélioration exploitable.

## 11. Tester un autre modèle ?

Ne pas chercher systématiquement un nouveau modèle pour contourner une version vLLM lente. Qwen3-Coder-30B-A3B a déjà servi de témoin architectural : léger gain de decode, préfill 4x plus lent, tours Codex encore moins pratiques. Un autre modèle (Qwen3.8, etc.) ne doit être testé que si :

1. la nouvelle version vLLM-Metal apporte une amélioration pertinente ; **OU**
2. le modèle est explicitement optimisé dans la release ; **OU**
3. une mesure API directe laisse penser qu'il peut atteindre la zone ≥ 50 tok/s.

## 12. Checklist future (copiable)

```markdown
[ ] nouvelle version vLLM/vLLM-Metal pertinente
[ ] release notes lues
[ ] amélioration Apple Silicon/Metal identifiée
[ ] versions enregistrées
[ ] swap initial relevé
[ ] Qwen3.6 chargé
[ ] test A x3
[ ] test B x3
[ ] test C x3
[ ] résultat B >= 50 tok/s ?
[ ] si NON -> STOP + documenter
[ ] si OUI -> contexte 64K/128K
[ ] tool call
[ ] MCP
[ ] Codex simple
[ ] comparer baseline Git
[ ] décision
[ ] commit résultats
```

## 13. Commandes de référence

```sh
# Démarrer vLLM-Metal (~30s)
source ~/.venv-vllm-metal/bin/activate
vllm serve mlx-community/Qwen3.6-35B-A3B-4bit \
  --port 11400 --max-model-len 131072 \
  --tool-call-parser qwen3_coder --reasoning-parser qwen3 \
  --enable-auto-tool-choice

# Arrêter vLLM
ps aux | grep -E "vllm|EngineCore"   # puis kill <PID> des process vllm/EngineCore

# Health checks
curl -s http://127.0.0.1:11400/health
curl -s http://127.0.0.1:11400/v1/models
curl -s http://127.0.0.1:11434/api/version   # Ollama (référence)

# Processus
ps aux | grep -E "llama-server|EngineCore"

# Mémoire
sysctl vm.swapusage
memory_pressure -Q

# Benchmarks A/B/C (3 runs, médiane)
python3 docs/codex-local/evidence/bench.py \
  --endpoint http://127.0.0.1:11400/v1 \
  --model mlx-community/Qwen3.6-35B-A3B-4bit \
  --prompt-file docs/codex-local/evidence/bench-prompts/A-generation.md --runs 3
# (idem B-reasoning.md, C-repo-task.md)

# Contexte 64K/128K (si gate franchi)
python3 docs/codex-local/evidence/bench-context.py --help
```

Script de retest optionnel : [scripts/codex-local/retest-vllm-metal.sh](../../scripts/codex-local/retest-vllm-metal.sh) — relève versions/mémoire puis lance A/B/C (n'installe rien, ne supprime rien).

## 14. Protection des preuves

Les données historiques ([08-benchmark.md](08-benchmark.md), [07-vllm-model-comparison.md](07-vllm-model-comparison.md), [evidence/](evidence/)) sont immuables. Ce document les référence sans les réécrire. Tout retest futur produit de **nouveaux** documents/evidence, jamais une modification des existants.
