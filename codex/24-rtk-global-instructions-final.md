# RTK — finalisation globale, 21 octobre 2026

Statut **PARTIAL** : RTK fonctionne explicitement, instructions globales chargées ; dernier fichier de transition à supprimer après redémarrage des sessions qui conservent l'ancien hook en mémoire.

## Configuration et test

RTK 1.0.1 conservé. Bloc balisé RTK ajouté à ~/.codex/AGENTS.md sans altérer les instructions existantes ; copie versionnée actualisée dans codex/global-instructions.md. Préfixer RTK seulement pour git status, git log, ls simples destinés à une lecture humaine. Diff, rg, tests, logs, JSON, scripts, commandes complexes et données P3-C/Standup/llm-router restent natifs. Bypass et recall conservés. Cette méthode utilise les instructions de l'agent, indépendamment de PreToolUse ; aucun installateur de hook relancé.

Test unique : argv /opt/homebrew/bin/rtk git status, binaire résolu /opt/homebrew/Cellar/rtk/1.0.1/bin/rtk, code retour 0. Les 112 entrées de git status --short sont toutes présentes avec leurs états dans la sortie RTK (5647 octets). Preuves : artifacts/rtk-final-20261021/test.json et status.rtk.txt. Le contrôle natif appartient au même test comparatif, aucun benchmark répété.

Le bloc global a été réinjecté explicitement dans les instructions de cette session : chargement confirmé. La sélection spontanée systématique de RTK n'est pas démontrée. Le test prouve l'exécution explicite via RTK depuis cette session, sans certifier une autre surface Desktop indépendante.

## Nettoyage

- Unique entrée RTK retirée de ~/.codex/hooks.json ; fichier supprimé car devenu vide. Aucun hook tiers présent ni supprimé.
- Unique confiance RTK identifiée par chemin et hash retirée de config.toml. Comparaison TOML : toutes les autres valeurs préservées, y compris MCP et modèles.
- Ancien script actif supprimé, puis remplacé par un fichier de transition **inerte** au même chemin ~/.codex/hooks/rtk-selective.py : une commande ultérieure a révélé que la session gardait le hook en mémoire et bloquait faute de fichier. Le fichier de transition ne lance rien, ne réécrit rien et ne produit rien. Une commande de vérification a ensuite réussi.
- Après fermeture/redémarrage des anciennes sessions, supprimer uniquement ce fichier de transition. La configuration sur disque ne l'enregistre plus. Ne pas supprimer ce fichier tant qu'une session tente encore de l'appeler.
- Aucun RTK.md ni pipeline utilisateur n'existait. Sources historiques codex/scripts/rtk-selective-hook.py et rtk-manage.py conservées pour rollback, pas chargées par Codex.
- Binaire, historique et preuves de recette conservés. Aucun fichier P3-C, événement structuré ou service modifié. Aucun commit/push ni inférence supplémentaire payante.

## Sauvegarde et rollback ciblé

Sauvegarde privée des configurations initiales et du script : /Users/fngux2/.codex/backups/rtk-final-20261021-143343 (fichiers 0600).

Désactiver les instructions : enlever seulement le bloc BEGIN/END RTK SELECTIVE GLOBAL dans AGENTS.md global et actualiser sa copie versionnée. Conserver tout ajout concurrent. Pour restaurer l'ancienne intégration, utiliser codex/scripts/rtk-manage.py install puis approuver seulement son entrée via /hooks du CLI ; ne pas restaurer intégralement config.toml depuis la sauvegarde. L'ancien parcours Desktop reste non qualifié.

Dernière action requise pour nettoyage complet : redémarrer les sessions ayant chargé l'ancien hook, puis supprimer ~/.codex/hooks/rtk-selective.py. Aucun autre test RTK requis.
