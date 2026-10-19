# 20 — SpecPrefill vs cache KV + plafond mémoire oMLX (Qwen3.6-35B-A3B-4bit)

**Date** : 2026-10-19 (soirée) · **Machine** : MacBook Pro M4 Max, 48 Go (40 cœurs GPU), macOS 27.0.1
**Modèle** : `mlx-community--Qwen3.6-35B-A3B-4bit` (4-bit affine, group 64, gates 8-bit, 19,95 Go)
**Serveur** : oMLX **0.7.1rc1** (build 3310), moteur `vlm` (VLMBatchedEngine), port 8000, LaunchAgent `org.gangneux.omlx-serve`

## 1. Objet

Deux questions distinctes, traitées séparément :

1. **SpecPrefill dégrade-t-il le prefill** en empêchant la réutilisation du cache KV (bug [jundot/omlx#4225](https://github.com/jundot/omlx/issues/4225)) ?
2. **Le plafond mémoire** (`memory_guard_custom_ceiling_gb`) est-il réellement appliqué, et à quelle valeur ?

## 2. Configuration auditée (lue, non supposée)

| Paramètre | Valeur réelle | Source |
|---|---|---|
| SpecPrefill | **`false`**, `draft_model = null` | `model_settings.json` + `/admin/api/models` |
| TurboQuant KV | `false` (bits 4.0, skip_last) | idem |
| MTP | `false` — **incompatible** : poids MTP absents du safetensors | `/admin/api/models` |
| DFlash | `false` | idem |
| Prefix / Prompt cache | actifs — paged SSD 154 Go auto, `initial_cache_blocks=256` | `settings.json` |
| Prefill | `prefill_step_size=2048`, `chunked_prefill=false` | `scheduler.py:1856` |
| Contexte | natif 262 144, **cap effectif 131 072** | `model_settings.json` |

**Précondition SpecPrefill non remplie** : aucun draft model chargé (`_specprefill_draft_model is None`), et le seul candidat local (`Qwen3-Coder-30B`) a un tokenizer incompatible (vocab 151 643 vs 248 044). SpecPrefill exige un tokenizer partagé.

## 3. Bug #4225 : NON reproduit

Le bug exige **SpecPrefill + TurboQuant KV + draft model**. Aucun des trois n'est actif.

- 0 occurrence de `Cache layer type mismatch`, `Truncating cached prefix`, `Cache corruption detected`, `sparse prefill failed`, `cached 0` sur les 3 fichiers de logs (17, 18, 19 oct.).
- Test per-request `specprefill: true` (option supportée, `openai_models.py:380`) : **no-op total**. `_try_specprefill_scoring` sort immédiatement sur `_specprefill_draft_model is None` ([scheduler.py:11196](/Applications/oMLX.app/Contents/Resources/omlx/scheduler.py:11196)). 0 ligne SpecPrefill dans les logs pendant les runs ON.

## 4. Benchmark SpecPrefill ON/OFF

Prompts synthétiques à longueur exacte (tokeniseur réel, marqueurs DEBUT/MILIEU/FIN), nonce unique par requête pour garantir le cache froid. A/B/A interleavé (3 cycles) pour neutraliser la dérive.

### Prefill froid

| Contexte | Tokens réels | OFF | ON | Gain |
|---|---|---|---|---|
| 8K | 8 236 | 5,29 s — 1 557 tok/s | 5,69 s — 1 448 tok/s | −7,6 % |
| 32K | 32 808 | 30,08 s — 1 090 tok/s (σ=0,40) | 30,28 s — 1 083 tok/s (σ=0,48) | −0,7 % |
| 64K | 65 581 | 73,80 s — 889 tok/s | 76,90 s — 853 tok/s | −4,2 % |

### Prefill chaud (même prompt rejoué)

| Contexte | OFF TTFT | ON TTFT | Cache réutilisé |
|---|---|---|---|
| 8K | 0,45 s | 0,35 s | 8 229 / 8 236 |
| 32K | 0,81–1,43 s | 1,08–1,15 s | 32 801 / 32 808 |
| 64K | 2,37 s | 1,72 s | 65 574 / 65 581 |

### Multi-tour (préfixe 32K + 4 tours ~815 tokens)

| Tour | OFF cached / TTFT | ON cached / TTFT |
|---|---|---|
| 1 | 0 / 29,54 s | 0 / 28,29 s |
| 2 | 32 768 / 2,85 s | 32 768 / 2,71 s |
| 3 | 32 768 / 3,41 s | 32 768 / 3,49 s |
| 4 | 34 816 / 2,04 s | 34 816 / 2,10 s |

**Rétention** : 3/3 marqueurs exacts aux 3 niveaux, dans les deux modes, `finish_reason=stop` partout.

**Conclusion** : écarts dans le bruit inter-run (contrôle 64K : 79,75 s puis 79,35 s sans changement). SpecPrefill est un **no-op** sur cette installation. **Aucun gain à attendre de sa désactivation — elle était déjà effective.**

## 5. Plafond mémoire : le paramètre était inerte

### Cause racine

[process_memory_enforcer.py:717](/Applications/oMLX.app/Contents/Resources/omlx/process_memory_enforcer.py:717) :

```python
if self._memory_guard_tier == "custom":
    return max(0, self._memory_guard_custom_ceiling_bytes)
return self._dynamic_ceiling_terms()["dynamic"]
```

Avec `tier = balanced`, `memory_guard_custom_ceiling_gb` est **ignoré**. Le plafond 24,5 Go configuré n'a jamais été appliqué : plafond effectif mesuré **38,18 Go**, avec des `dynamic ceiling` variant de 22,01 à 30,03 Go selon la pression des autres apps.

### Second piège : le LaunchAgent écrasait `settings.json`

Le plist passait `--memory-guard balanced` en ligne de commande. Priorité documentée dans `settings.py:1086` : **CLI > env > fichier > défauts**. Au redémarrage, le tier revenait donc à `balanced` et le plafond custom redevenait inerte.

Vérifié par simulation de `GlobalSettings.load()` :

| Plist | tier résolu | ceiling |
|---|---|---|
| avec `--memory-guard balanced` | `balanced` | 30,0 (ignoré) |
| sans `--memory-guard` | `custom` | **30,0 (appliqué)** |

### Correction appliquée

1. `settings.json` : `memory_guard_tier = "custom"`, `memory_guard_custom_ceiling_gb = 30.0`
2. `org.gangneux.omlx-serve.plist` : suppression de `--memory-guard balanced` → `settings.json` devient la source de vérité
3. Redémarrage réel via `launchctl unload/load` pour valider la persistance

Sauvegardes : `~/.omlx/settings.json.bak-20261019-211707`, `~/Library/LaunchAgents/org.gangneux.omlx-serve.plist.bak-20261019-213213`.

### Validation après redémarrage

```
Memory guard tier: custom (guard on)
Process memory enforcer started (tier=custom, ceiling=30.0GB, interval=1.0s)
final_ceiling: 30.00 Go | model_memory: 19.95 Go
```

### Effet mesuré

| Contexte | Avant (balanced) | Après (custom 30 Go) | Gain |
|---|---|---|---|
| 32K | 30,08 s — 1 090 tok/s | 28,47 s — 1 153 tok/s | **+5,8 %** |
| 64K | 73,80 s — 889 tok/s | 67,50 s — 972 tok/s | **+9,3 %** |

Throttles `Prefill throttled` : 76 sur la journée avant, **0 après** le changement. Cache chaud intact (65 566 / 65 573 tokens, TTFT 1,31 s).

## 6. Analyse mémoire macOS

### Répartition des 48 Go (état mesuré)

| Catégorie | Go | Nature |
|---|---|---|
| Wired | 24,3 | dont **20,4 oMLX** (poids modèle Metal, non paginable) + noyau |
| Active | 8,0 | apps au premier plan |
| Inactive | 9,7 | **récupérable instantanément** (cache, pas de la perte) |
| Compressed | 3,7 | pages compressées (ratio 2–3×) |
| Free | 1,4 | |

**Disponible réel : ~11 Go.** macOS laisse `free` bas par conception (« free memory is wasted memory ») ; les pages `inactive` sont rendues à la première demande.

### Consommateurs réels (footprint, pas RSS)

| Processus | Go |
|---|---|
| omlx-server | 20,4 |
| VS Code (21 process) | 3,05 |
| ChatGPT/Codex (23 process) | 2,35 |
| Codex standalone | 2,01 |
| Ollama (au repos) | 0,02 |

### Swap : 2,25 Go utilisés mais **inactif**

- `swapouts` delta mesuré sur 10 s et 8 s : **0 page**.
- Les 2,25 Go sont un **résidu historique** : uptime 15 jours, 18,6 M pages swapout cumulées (~284 Go écrits depuis le boot), dont les pics de la campagne 256K du 17/10 et des backups Time Machine.
- macOS ne libère pas les swapfiles tant qu'il n'a pas besoin de l'espace disque ; ce n'est pas un signe de pression.

### Facteurs externes identifiés

- **Time Machine actif** pendant les mesures : 56 % d'un backup de 883 Go, ~77 Mo/s d'écriture, snapshots APFS locaux (`com.apple.TimeMachine.2026-10-19-210004.local`).
- **Ollama tourne en parallèle** (port 11434, PID 5221, `org.gangneux.ollama-serve`) alors qu'oMLX est le moteur principal. Au repos 17 Mo, mais plusieurs Go s'il charge un modèle.

### Optimisations macOS utiles (non appliquées)

| Action | Gain | Risque |
|---|---|---|
| Laisser Time Machine finir | ~1–2 Go + I/O | aucun |
| `sudo sysctl iogpu.wired_limit_mb=40960` | +3 Go GPU (défaut Apple 37,4 Go) | modéré, non persistant |
| Arrêter Ollama si inutilisé | 0,02 Go repos, plusieurs Go en charge | aucun |
| Fermer ChatGPT.app (Codex standalone suffit) | ~2,3 Go | aucun |

**À ne pas faire** : `purge`, désactiver Spotlight, « libérer » les pages inactive — dégradation sans gain.

## 7. Configuration finale

| Paramètre | Valeur |
|---|---|
| `memory_guard_tier` | `custom` |
| `memory_guard_custom_ceiling_gb` | `30.0` |
| `prefill_memory_guard` | `true` |
| `soft_threshold` / `hard_threshold` | 0,85 / 0,95 |
| `prefill_safe_zone_ratio` / `min_chunk_tokens` | 0,8 / 32 |
| SpecPrefill | `false` (inchangé) |
| TurboQuant KV / MTP / DFlash | `false` (inchangés) |
| Prefix / Prompt cache | actifs (inchangés) |

Marge au-dessus du modèle : **10 Go** (pic mesuré 25 Go à 64K). Ne pas dépasser 37,4 Go (plafond Metal Apple) sous peine de jetsam.

## 8. Scripts

- [gen_prompts.py](gen_prompts.py) — prompts synthétiques à longueur exacte (tokeniseur réel, marqueurs positionnés aux offsets)
- [run_bench.py](run_bench.py) — mesures cold/warm/multi-tour via `usage` natif oMLX
- [aba_test.py](aba_test.py) — A/B/A interleavé (neutralise la dérive)

Interpréteur : Python embarqué oMLX (`/Applications/oMLX.app/Contents/Resources/Python/cpython-3.11/bin/python3`) pour `tokenizers`/`transformers`.

## 9. Limites

- Mesures sur l'instance de **production** (port 8000), pas sur une instance isolée : Time Machine et les apps de bureau ont influencé la variance (σ jusqu'à 2,3 s à 32K).
- `sudo powermetrics` indisponible (pas de sudo non interactif) — consommation GPU non mesurée séparément.
- Le débit de génération (31–50 tok/s) n'a pas été comparé rigoureusement : la variance inter-run dépasse l'écart ON/OFF.
