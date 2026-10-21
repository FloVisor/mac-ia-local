---
name: ponytail
description: >-
  Guide source-code development, refactoring and simplification toward reuse and
  maintainable minimal changes. Use when asked to create or modify application,
  library or developer-tool source code, or explicitly invoke Ponytail. Do not
  auto-select for infrastructure diagnostics, production incidents, system
  administration, configuration-only tasks, code explanations or read-only reviews.
license: MIT
---

# Ponytail — développement proportionné

À l'activation, lire [la référence évaluée](references/ponytail.md), adaptée de
DietrichGebert/ponytail v5.3.2, commit `16352ac229eb08a9598dcae48fe9f2b342567d86`
([licence MIT](LICENSE)). Appliquer ces précisions aux formulations amont :

- Guider uniquement la tâche de développement concernée ; aucun mode persistant,
  hook, carte automatique ou commande de changement de mode.
- Choisir le changement minimal **complet et maintenable**. La longueur du diff
  n'est pas une cible : préférer un code plus long si sa lisibilité, ses contrats,
  sa sécurité ou son évolution le justifient. Ne pas imposer la solution la plus courte.
- Garder la profondeur d'analyse nécessaire, les contrôles de sécurité, la gestion
  d'erreurs et les tests pertinents. Réutiliser les composants après examen de leurs
  contrats et des appelants ; achever les adaptations nécessaires.
- Les instructions utilisateur, globales et locales priment sur ce skill. Suivre
  les règles existantes de délégation MCP llm-router, RTK, Graphify, approbations et
  validation sans les recopier, les remplacer ou créer un chemin de délégation direct.
- Respecter le périmètre autorisé ; les choix courants n'exigent pas de confirmation
  supplémentaire. Signaler les limites et les vérifications non exécutées.

Hors des tâches visées, ne pas poursuivre l'application du skill au seul motif
qu'il a été chargé dans un tour précédent. Une invocation explicite reste possible.
