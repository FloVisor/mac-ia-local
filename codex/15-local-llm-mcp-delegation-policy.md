# Politique de délégation automatique — local-llm-mcp

Proposition du 2026-10-17. **Non appliquée** : conformément à la contrainte de la
mission, `~/.codex/AGENTS.md` n'a pas été modifié. Le diff ci-dessous est proposé
pour revue avant application éventuelle.

## Principe

Codex (GPT-6) conserve l'architecture, les décisions complexes et la validation
finale. Les tâches simples, indépendantes ou répétitives sont déléguées au modèle
local via l'outil `mcp__local_llm__delegate` (muse-glimmer:30b-mlx, raisonnement
high), pour économiser le contexte et les tokens cloud.

## Critères de délégation

Déléguer quand **toutes** les conditions sont réunies :

1. La tâche est **autonome** : tout le contexte nécessaire tient dans le paramètre
   `task` (le serveur est sans état et ne voit pas le dépôt).
2. La tâche est **simple, indépendante ou répétitive** : reformulation, résumé,
   brouillon de doc, analyse d'un extrait fourni, revue d'un diff fourni,
   génération de cas de test pour un changement fourni.
3. Le résultat est **vérifiable** par GPT-6 avant utilisation (la sortie du modèle
   local n'est jamais appliquée sans relecture).

Ne **jamais** déléguer :

- Décisions d'architecture, arbitrages, planification multi-étapes.
- Toute tâche nécessitant l'accès au dépôt, aux fichiers ou à l'historique.
- Tâches où la délégation coûterait plus de tokens que l'exécution directe
  (contexte à copier > réponse attendue).
- Secrets, credentials, données sensibles — jamais dans `task`.

## Économie de contexte

- Déléguer **une** tâche autonome plutôt que d'itérer localement sur un sujet
  secondaire.
- Ne pas déléguer plusieurs micro-tâches séparément : regrouper en une seule
  délégation cohérente.
- Si la réponse déléguée est insuffisante, reformuler **une fois** ; au second
  échec, traiter la tâche directement (règle anti-boucle AGENTS.md).

## Diff proposé pour ~/.codex/AGENTS.md

À insérer après la section « Tool batching » (ligne ~296), avant
« Mandatory tool-to-response transition » :

```diff
 ## Tool batching
 
 Avoid long uninterrupted tool-call sequences.
@@
 Do not read every potentially relevant document preemptively.
 
 Read the minimum documentation required for the current task.
 
+## Local LLM delegation (mcp__local_llm__delegate)
+
+Delegate simple, independent, or repetitive self-contained tasks to the local
+LLM (muse-glimmer:30b-mlx, reasoning high) via the local_llm MCP server.
+
+Delegate only when ALL hold:
+- the task is fully self-contained (all context fits in the task argument;
+  the server is stateless and sees no repository files);
+- the task is simple, independent, or repetitive (rewording, summarizing,
+  doc drafts, analysis of a provided excerpt, review of a provided diff,
+  test cases for a provided change);
+- the output can be verified by you before use.
+
+Never delegate:
+- architecture decisions, trade-offs, multi-step planning;
+- anything requiring repository, file, or conversation-history access;
+- tasks where copying the context costs more tokens than doing it directly;
+- anything containing secrets or credentials.
+
+Batch related micro-tasks into a single delegation. If a delegated answer is
+insufficient, rephrase once; on second failure, do the task directly.
+Always review delegated output before applying it.
+
 ## Mandatory tool-to-response transition
```

## Statut

- **Délégation automatique : NON activée.** Aucune instruction globale n'ordonne
  actuellement à GPT-6 de déléguer ; l'outil est disponible mais son usage reste
  à la discrétion du modèle ou d'une demande explicite.
- Pour activer : appliquer le diff ci-dessus dans `~/.codex/AGENTS.md` (après
  sauvegarde : `cp ~/.codex/AGENTS.md ~/.codex/AGENTS.md.bak-delegation-$(date +%Y%m%d-%H%M%S)`).
- Validation post-application : une session Codex avec une tâche simple doit
  montrer un appel `mcp__local_llm__delegate` dans le rollout (preuve
  `function_call` + `function_call_output`), pas une réponse simulée.
