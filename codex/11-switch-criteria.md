# Critère de bascule — évaluation factuelle

Date : 2026-10-04

## Les 10 critères

| # | Critère | Résultat | Preuve |
|---|---|---|---|
| 1 | Codex démarre normalement | **PASS** | `codex exec` OK avec vllm_metal, ollama_codex, openai (cloud) |
| 2 | Responses API fonctionne | **PASS** | `/v1/responses` status completed, texte exact (07-vllm-codex-integration.md) |
| 3 | Tool calling fonctionne | **PASS** | API directe : get_weather correct ; via Codex : shell + MCP OK |
| 4 | Tous les MCP importants fonctionnent | **PASS** | Zéro régression (09-mcp-post-migration.md) |
| 5 | Le Cloud reste disponible | **PASS** | CLOUD_STILL_OK 4.6s (re-testé 2026-10-04) |
| 6 | Aucune perte fonctionnelle majeure | **PASS avec réserve** | Toutes les fonctions marchent, MAIS latence 5–10x |
| 7 | Pas de boucle/reconnecting anormal | **PASS** | Aucune boucle, aucune erreur protocole observée |
| 8 | Mémoire acceptable | **MITIGÉ** | wired GPU ~36/37.4 GB — fonctionne mais marge serrée sur 48 GB |
| 9 | Swap acceptable | **MITIGÉ** | stable ~2.9–4.5 GB avec vLLM seul ; pic 9.3 GB pendant tests simultanés |
| 10 | Qualité au moins équivalente sur la majorité des tests essentiels | **PASS** | Réponses exactes sur tous les tests (A-F, MCP), corrections techniques correctes |

## Verdict

**9 PASS, 2 MITIGÉ (8, 9), 0 FAIL.** Techniquement, vLLM-Metal est un backend qualifié et fonctionnel.

## MAIS — la recommandation factuelle

Le critère décisif non listé mais mesuré : **la latence par tour via Codex** :
- Ollama : 27–38s/tour, 24–26k tokens
- vLLM : 3–6 min/tour, 83–136k tokens (thinking non tronqué + préfill système répété à chaque processus)

Pour un usage agentique quotidien (Codex), vLLM-Metal est **5–10x plus lent par tour** dans les conditions réelles mesurées. Le décodage brut est 3x plus lent (17–22 vs 56–75 tok/s).

**Décision : NE PAS FORCER LA MIGRATION.**
- Backend par défaut conservé : **Ollama** (qwen3.6:35b-coding) pour le local, Cloud pour le reste — inchangé.
- vLLM-Metal **conservé installé et qualifié** pour investigation (prefix caching supérieur ≥64K, préfill long-contexte 2x plus rapide, Responses API native).
- Les deux providers restent disponibles dans config.toml (ollama_codex, vllm_metal) + Cloud.

Conforme à la règle : « Si vLLM est moins bon : NE FORCE PAS LA MIGRATION. Remets Codex sur le backend précédent par défaut et conserve vLLM installé pour investigation. »
