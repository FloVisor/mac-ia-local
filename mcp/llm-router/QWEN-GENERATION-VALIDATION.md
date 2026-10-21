# Correction génération Qwen — 2026-10-21

## Cause établie

Tâche initiale `09efc115-3ba5-4070-bd2d-e94164cbcf89` :
`max_output_tokens=1200`, raisonnement Medium implicite, `thinking_budget=2048`,
`chat_template_kwargs.enable_thinking=true`. Le routeur envoyait
`max_tokens=1200` pour la génération totale, pensée comprise.
Usage : 150 tokens d'entrée, 1200 de génération, `finish_reason=length`.
Le journal oMLX du 21 octobre à 16:14:55 confirme `request_max_tokens=1200`
et le même usage. La qualité était `not_checked` : troncature réelle, et non
échec du validateur JSON. Le compteur de pensée initial n'était pas conservé ;
sa valeur exacte ne peut pas être reconstruite depuis ces métadonnées.

## Changement limité au routeur

Pour l'alias Qwen seulement, plafond total = réserve de réponse + budget de
raisonnement. La sélection réserve ce total dans le contexte inchangé de
131072 tokens. Budgets inchangés : Off/Minimal 0, Low 512, Medium 2048,
High 8192, Max 16384, Ultra adapté à High 8192. Aucun `reasoning_effort`
envoyé : `thinking_budget` et `chat_template_kwargs` portent le mapping explicite.
Les autres routes conservent leurs paramètres.

Le code oMLX disponible dans `toolchains/qwen36-campaign/oMLX.app/Contents/Resources/omlx/`
confirme la priorité de `request.max_tokens`, la reconnaissance de
`thinking_budget` par `_resolve_thinking_budget` et de `chat_template_kwargs`
par `_merge_chat_template_kwargs`. La preuve de transport réelle ci-dessous
complète cette inspection ; aucune configuration LiteLLM/oMLX n'a été changée.

Erreurs distinctes : `completion_truncated`, `empty_completion`,
`unexpected_finish_reason`, `objective_quality_failed`. Le texte rejeté reste
privé et récupérable par `result`, sans publication dans les événements.
Le compteur upstream `completion_tokens_details.reasoning_tokens` est conservé.

## Validation

- `python3 -m unittest discover -s mcp/llm-router -q` : 70 tests PASS.
  Avertissements ResourceWarning de connexions SQLite non fermées dans les tests,
  sans échec ; aucun changement hors périmètre pour les corriger.
- `python3 -m unittest discover -s witness-a -q` : 2 tests PASS.
- Un seul appel réel local accepté, aucun retry ni fallback.
  Le premier appel antérieur avait été refusé par les permissions MCP avant soumission.
- Tâche réelle : `b0f6ef45-fe51-4411-a6f7-823b02698ec7`.
- Sujet initial repris, sortie JSON imposée avec cinq propriétés requises.
- `max_output_tokens=1200`, Medium, `max_tokens_sent=3248`, pensée 2048.
- `completed`, `finish_reason=stop`, `quality=passed`, durée 104080 ms.
- Usage : entrée 191, génération totale 2737, pensée déclarée 2049.
  Le compteur de pensée est recalculé par oMLX depuis le texte ; il ne constitue
  pas une preuve d'égalité exacte au budget configuré.
- `request_id=chatcmpl-e719701f`, `x-litellm-call-id=4b5cb56d-8804-463c-9d44-86b2598228ad`,
  déploiement `17720d29-9da3-4888-aef8-f6db0cc5bd96`, retries/fallbacks 0.
- `llm-router.result` appelé depuis Codex : 2647 caractères, JSON complet,
  `next_offset=null`, `isError=false`. Aucun second appel de génération.
- Journal oMLX à 16:28:09 : modèle fournisseur Qwen3.6, entrée 191,
  génération 2737, `finish_reason=stop`, `request_max_tokens=3248`.
  Cela confirme le plafond transmis à travers LiteLLM jusqu'à oMLX.
- Santé oMLX après le test : HTTP 200, `status=healthy`, modèle par défaut
  `mlx-community--Qwen3.6-35B-A3B-4bit`, un modèle chargé.

`actual_model=null` reste honnête : LiteLLM renvoie l'alias, pas une confirmation
fournisseur dans son champ `model`. Le succès valide production, structure et
récupération ; les recommandations du contenu restent des propositions à revoir,
pas une qualification du déploiement Docker décrit dans le prompt.

Aucun appel payant, commit/push, changement Agent Standup/P3-A/P4, permissions,
RTK ou OpenClaw. Aucune configuration globale de modèle modifiée.
