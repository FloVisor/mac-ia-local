# Baseline Ollama — qwen3.6:35b-coding

Date : 2026-10-03 · Serveur : Ollama 0.35.1 (API) sur 127.0.0.1:11434 · Modèle chargé : qwen3.6:35b-coding (22 GB, 100% GPU, contexte 131072)

## 1. Modèle (observé)

| Élément | Valeur |
|---|---|
| Slug | qwen3.6:35b-coding |
| ID | 017eda0b7c34 |
| Architecture | qwen35moe, 35.5B params, Q4_K_M |
| Taille | 22 GB |
| Contexte serveur | 131072 (OLLAMA_CONTEXT_LENGTH du LaunchAgent) |
| Capabilities | completion, vision, tools, thinking (default true) |
| Paramètres | temp 0.6, top_p 0.95, top_k 20, min_p 0, draft_num_predict 2 |
| keep_alive | 10m (OLLAMA_KEEP_ALIVE) |
| max_loaded_models | 1 |
| Mémoire runner | llama-server RSS ≈ 24.4–24.8 GB |

## 2. Résultats quantitatifs (3 runs, médiane [min–max])

Corpus : `docs/codex-local/evidence/bench-prompts/` · temp 0.6 · bench.py (streaming, TTFT sur premier delta content/reasoning)

| Test | TTFT médian | Total médian | Tokens out | tok/s médian |
|---|---|---|---|---|
| A — génération simple (400 max tok) | 0.06s [0.06–0.14] | 3.38s [3.28–3.64] | ~245 | 72.5 [70.0–74.8] |
| B — raisonnement code (600 max tok) | 0.05s [0.05–0.22] | 4.99s [4.92–5.28] | ~320–360 | 68.2 [65.1–69.7] |
| C — repo task (600 max tok) | 0.05s [0.05–0.23] | 5.25s [4.93–5.28] | ~277–321 | 56.1 [54.8–61.1] |

Note : TTFT très bas car le modèle est déjà en mémoire et le prompt est court ; le "reasoning" (thinking) est streamé en premier.

## 3. Tests de contexte (H) — 1 run par niveau

Prompt synthétique croissant + question de rappel (bench-context.py) :

| Niveau | TTFT | Total | tok/s | Swap avant→après | Mem free |
|---|---|---|---|---|---|
| 16K | 16.5s | 17.5s | 4.2 | 3874→4337 MB | 15% |
| 32K | 27.3s | 28.5s | 2.6 | 4337→4586 MB | 14% |
| 64K | 158.8s | 161.5s | 0.5 | 4754→3295 MB | 13→17% |
| 96K | 239.4s | 242.1s | 0.3 | 3295→2102 MB | 17→24% |
| 128K | 184.5s | 186.9s | 0.4 | 2102→1062 MB | 24→18% |

Observations :
- Prompt processing très lent au-delà de 32K (2.6 à 4 minutes de TTFT à 64–128K) : le prefill long-contexte est le point faible d'Ollama ici.
- Le Mac a tenu sans crash, mais swap utilisé jusqu'à ~4.6 GB avec le modèle 22 GB + contexte 128K.
- Après les tests 128K, le test A retombe à ~50 tok/s puis récupère ~70 tok/s après ~60s d'idle (effet pression mémoire/swap).

## 4. Tool calling (D) — API directe

- Avec max_tokens=200 : finish_reason=length, tool_calls=null (le thinking consomme le budget).
- Avec max_tokens=800 : **PASS** — finish_reason=tool_calls, `get_weather(city="Paris")` correctement émis, 121 tokens.

## 5. Chemin réel Codex CLI (I) — via proxy Ollama (`codex exec -c model_provider=ollama_codex`)

| Test | Résultat | Durée | Tokens |
|---|---|---|---|
| Réponse simple | PASS (BASELINE_CODEX_LOCAL_OK) | 27.4s | 24 349 |
| Tool shell (date) | PASS — 1 commande `date`, réponse correcte | 28.2s | 24 537 |
| MCP n8n_health_check (E) | PASS après restauration n8n — status "ok", 1 appel MCP | 38.5s | 24 965 |
| Agentic terminal (F) | PASS avec adaptation — sandbox interdit /tmp, exécution inline python, résultat PASS, pas de fichier à nettoyer | 34.7s | 25 555 |
| Cloud (défaut gpt-5.6-sol) | PASS (CLOUD_OK) | 4.0s | 26 047 |

Note : ~24–26k tokens par tour = overhead système Codex (instructions, AGENTS.md, contexte) ; le coût prompt est dominant.

## 6. Session longue (G) — 10 tours

10 tours `codex exec` consécutifs : 10/10 PASS (réponses exactes), aucune erreur protocole, aucun reconnecting, aucune boucle. Durée par tour ~28s (dominée par le prompt système de ~24k tokens).

## 7. Incident et correction (documenté)

- À 22:55:50, la VM colima (Virtualization.framework, PID 3786, uptime ~14h) hébergeant le conteneur n8n (port 5678) a été tuée par SIGKILL — envoyé par le shell de mon probe `docker ps` bloqué que j'ai stoppé (kill du process group a atteint la VM).
- Conséquence : n8n_health_check → NO_RESPONSE (le test E initial a échoué pour cette raison, pas à cause du LLM).
- Correction : `colima stop` + `colima start` → conteneur n8n-kit redémarré, healthz HTTP 200, n8n_health_check → success=true status=ok (0.15s).
- Re-test E via Codex : PASS.
- Leçon : ne jamais stopper brutalement un probe attaché à docker/colima ; utiliser des timeouts (perl alarm) au lieu de kill de process group.

## 8. État système (Phase 4)

| Moment | Swap used | Mem free | Notes |
|---|---|---|---|
| Avant chargement modèle | 1723 MB | 81% | — |
| Modèle chargé (22 GB) | 3645 MB | 18% | wired 1947k pages |
| Pendant 64–128K | 4754→1062 MB | 13–24% | swap churn important |
| Fin baseline | 2616 MB | 33% | modèle toujours en RAM (keep_alive 10m) |
