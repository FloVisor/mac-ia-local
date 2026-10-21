# P3-C — Rattachement et historique MCP (2026-10-21)

Correction installée : Agent Standup `1.40.0-p3c.4`, Observer `0.1.1`.
La fenêtre quotidienne déjà ouverte doit être rechargée pour activer ces versions.

## Incident exact

`09efc115-3ba5-4070-bd2d-e94164cbcf89` existe dans le stockage routeur Codex
et dans la projection du collecteur : failed, truncated_or_invalid_completion,
parent_session null, actual_model null. Sans parent, enrich() ne la sélectionnait
jamais parmi les descendants d'une session. La collecte fonctionnait ; le défaut
était le rattachement et l'accès à la projection Live Call.

Le JSONL de la session `01a15ecf-973d-78a3-a421-dc6d0ed69740` contient un
`event_msg/mcp_tool_call_end`, invocation llm-router.submit et résultat réussi
structuré avec task_id exact et identity=codex. Cette preuve permet le rattachement
sans inférence temporelle et sans modifier la base du routeur. Une mention dans
un message, un appel status/result, ou plusieurs créateurs concurrents ne suffit pas.
La tâche s'est terminée le 21 octobre à 16:14:55 (Paris) : son absence ultérieure
de la scène active ne constitue pas une anomalie en elle-même.

## Comportement corrigé

- Parent explicite conservé ; sinon créateur unique trouvé dans les événements MCP
  structurés des traces lues. Provenance exposée dans parent_evidence.
- Sans preuve : tâche racine dans Observer, conteneur de navigation « Délégations
  MCP non rattachées » dans Standup. Ce conteneur n'est pas une session Codex ;
  parent reste null dans les métadonnées de la tâche.
- Les tâches routeur ne sont plus exclues après 14 jours ni au-delà de 200 tâches.
  La conservation reste celle de la base source ; aucun stockage supplémentaire.
  Les transitions affichées restent bornées aux 20 dernières par tâche. Les traces
  Codex restent bornées à 200 fichiers/14 jours ; une preuve hors fenêtre peut
  manquer et la tâche reste alors non rattachée.
- failed/completed/cancelled restent dans Tree et Sessions. Sélection/relecture
  sans réexécution ; retrait visuel piloté par la préférence existante.
- Les événements terminaux alimentent doneAt/doneIdx et libèrent l'attente du parent.
  Le rafraîchissement des métadonnées ne force plus la réapparition des personnages.
- Alias demandé et modèle confirmé restent distincts ; actual_model null demeure
  « inconnu ». Aucun modèle exécuté n'est déduit de response_model.

## Vérification

17 tests Python et 7 tests Node PASS ; construction et syntaxe PASS.
Chrome headless sur serveur local candidat, lecture des traces réelles, endpoints
de génération désactivés et requêtes externes bloquées : tâche exacte retrouvée,
session sélectionnable, Tree contenant llm-router, personnage visible avec retrait
désactivé ; personnage masqué mais données et Tree conservés avec retrait activé.
Aucune erreur JavaScript. Capture examinée visuellement.
Les cas non rattachés et conflits sont couverts par tests synthétiques sans génération.
Le test graphique du retrait vérifie le masquage via l'état gone ; il n'attend pas
les deux minutes ni ne qualifie l'animation complète de disparition.

Preuves locales : `artifacts/agent-standup-p3c/history-ui-check.json`,
`history-real-task.png`, `task-history-snapshot.json`.
Installations par CLI réussies ; quatre fichiers runtime principaux comparés aux
artefacts construits : identiques. Validation graphique de la fenêtre quotidienne
après rechargement : NOT_RUN. Aucun commit/push, aucune génération, aucun changement
P4, permissions, modèles, budgets, RTK ou sélecteur P3-A.
