# Context7 via MCP Gateway — 21 octobre 2026

Intégration appliquée et recette fonctionnelle PASS pour Codex CLI, OpenClaw Pro et exclusion Perso, avant/après redémarrage ciblé. Aucun commit ni push.

## Configuration

Entrée officielle `catalog://mcp/docker-mcp-catalog:latest/context7`, importée par `docker mcp profile server add` dans les seuls profils `codex` et `pro`. Snapshot conservé dans leurs exports ; aucun nouveau service ou conteneur serveur Context7. Serveur distant officiel Streamable HTTP `https://mcp.context7.com/mcp`, version annoncée à l’initialisation `4.4.3`. Gateway inchangée : digest `sha256:f5a679a05fc39022a046167bef92aeeb01bcd59485ad27843ae5227db7950688`, CLI `HEAD`, protocole serveur Gateway précédemment qualifié `2.0.1`.

Les seuls outils Context7 autorisés par `profile tools --enable` sont `resolve-library-id` et `query-docs`. `time` reste présent. Filtres clients existants élargis à ces deux noms exacts ; URLs, headers et tokens inchangés. Perso : configuration cliente inchangée et export natif du profil strictement identique avant/après.

Aucune clé Context7 créée ou utilisée. Aucun secret Context7 dans Swarm ; magasin Docker natif inaccessible sur CE (`docker pass has not been installed`), donc aucune prétention d’inventaire global des coffres du Mac. L’entrée officielle déclare maintenant `required: false`. Initialisation et consultations réelles sans clé réussies : une clé ne bloque pas cette intégration. Les Bearer Gateway restent indépendants et servent exclusivement à l’authentification des trois profils.

## Politique et instructions

`send-approval/lib/mcp-reads.js` : exception pour les noms exacts `docker_gateway_pro__resolve-library-id` et `docker_gateway_pro__query-docs`, seulement `ctx.agentId=main`. Contrats découverts réellement, annotations `readOnlyHint=true`, `destructiveHint=false`, `idempotentHint=true`, `openWorldHint=true`. Arguments obligatoires non vides, types chaînes et clés strictes ; `language` facultatif uniquement sur `query-docs`. Aucun droit pour de futurs outils, autres serveurs ou Perso. Protections emails, messages, fichiers, commandes et administration conservées. Rechargement natif du plugin réussi, génération 3.

Instructions d’usage précis et proportionné ajoutées à `~/.codex/AGENTS.md` et `~/.openclaw/workspace/AGENTS.md`. Aucun AGENTS individuel Codex ni workspace Perso modifié. Aucune mémoire OpenClaw modifiée par cette mission. Les requêtes documentaires ne doivent contenir aucun secret, donnée personnelle ou code confidentiel.

## Contrôles déjà exécutés

- Codex CLI `app-server` natif : découverte exacte de quatre outils, appel time, recherche React et lecture useState, avant et après recréation des Gateways. Zéro tour de modèle Codex.
- Gateway HTTPS : mêmes opérations documentaires sur Codex/Pro ; seulement les deux outils time sur Perso. Appels réels time sur les trois profils. Après redémarrage : 12 refus 401 attendus (anonyme, token incorrect, deux tokens croisés par endpoint).
- Source documentaire réellement reçue : `https://react.dev/reference/react/useState`, identifiant `/websites/react_dev`, exemple `setAge(a => a + 1)` et explication de l’état précédent. Les réponses complètes sont dans les preuves ; aucun succès déduit d’un seul HTTP 200.
- OpenClaw Pro avant redémarrage : découverte native, recherche, lecture documentaire et time réellement exécutés, via outils différés, sans dialogue d’approbation ; fournisseur `omlx`, coût reçu 0.
- Tests `send-approval` : 33/33 PASS. Témoins `witness-a` : 2/2 PASS via unittest. Validation config : PASS. Comparaison structurée : seuls les filtres attendus changent dans les configurations clients.
- Contrôle des 100 dernières lignes des trois journaux Gateway : les trois tokens Gateway sont absents.
- Doctor : 36 contrôles, cinq avertissements navigateur/node-hosting/security hors périmètre ; aucune réparation exécutée. Santé RPC après redémarrage : ok, plugins sans erreur.

- OpenClaw après redémarrage : Pro réussit recherche, documentation et time ; appel vers time Perso bloqué (`Profil Docker MCP réservé à son agent`). Perso découvre seulement ses outils time, exécute time et reçoit un refus réel sur `docker_gateway_pro__query-docs` (`Context7 Pro réservé à son agent`). Traces natives et reçus filtrés conservés, pas seulement les affirmations du modèle. Coûts reçus 0, fournisseur oMLX.
- Aucun événement d’approbation dans les reçus Pro de la recette après redémarrage. Les deux consultations sont bien effectuées par le parcours différé natif, sans confirmation.
- Revue déléguée locale : tâche `f801de3a-e237-46e2-b3a9-9f6f6acd8dfe`, route `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit`, fournisseur modèle non confirmé (`alias_only_unconfirmed`). Suggestions invalides de champ `ctx.server` et de retour `null` pour argument invalide écartées ; les tests réellement exécutés font foi.

## Persistance et limites

Recréation ciblée de `mcp-gateway_codex` et `mcp-gateway_pro`, sans redémarrer Perso ; nouvelle recette HTTP complète et nouveaux processus Codex réussis. Fermeture puis réouverture normale d’OpenClaw : PID Gateway 43434 → 46030. La première réouverture pendant la fermeture a renvoyé macOS `-600` ; arrêt effectif vérifié avant une unique relance réussie.

Serveur Context7 hébergé : version et contenu susceptibles d’évoluer côté fournisseur, limites anonymes non qualifiées. Aucun test de quota/charge, aucun modèle payant supplémentaire. La session Desktop courante n’a pas été fermée : interface Desktop non qualifiée par ces essais CLI. La séparation des profils conserve les limites de l’installation initiale (socket Docker partagé, absence d’isolation système).

Les trois sessions de recette ont été supprimées par `openclaw sessions delete`, avec archivage normal de l’application. Aucun accès direct en écriture à une base interne ni nettoyage de mémoire. Les exports temporaires complets ont été retirés après extraction des seuls reçus d’outils.

## Rollback ciblé

Sauvegardes privées locales : `~/.local/state/context7-gateway-20261021/` (0700, fichiers 0600). Sauvegardes des trois exports natifs sur docker-02 : `/srv/docker-local/compose/mcp-gateway/backups/context7-20261021/`.

1. Dans chaque conteneur Gateway Codex/Pro, exécuter `/docker-mcp profile server remove <profil> context7`, puis recréer uniquement ces deux services avec `docker service update --force`. Conserver time, tokens, volumes et catalogue.
2. Retirer seulement `resolve-library-id` et `query-docs` du filtre Codex et du filtre `docker_gateway_pro` par `openclaw mcp tools`. Ne toucher ni à Perso ni aux connexions.
3. Retirer le bloc Context7 des deux fichiers d’instructions ; restaurer uniquement l’ajout Context7 de `mcp-reads.js` depuis la sauvegarde, en préservant les évolutions concurrentes. Retirer son test dédié, recharger `send-approval`, puis `openclaw mcp reload`.
4. Vérifier time, refus croisés et santé. Aucun rollback complet exécuté pendant la recette.

## Sources officielles

- [Catalogue Docker : clé facultative](https://github.com/docker/mcp-registry/blob/main/servers/context7/server.yaml)
- [Context7 : noms et contrats des outils](https://context7.com/docs/resources/all-clients)
- [Docker : profils et sélection des outils](https://github.com/docker/mcp-gateway/blob/main/docs/profiles.md)
- [Codex : instructions globales](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
