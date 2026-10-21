# Raccordement des clients — 21 octobre 2026

Configuration appliquée, sans commit ni push. Aucun changement de stack, Traefik, catalogue, profil ou token Gateway.

## Configuration appliquée

- Codex : une seule entrée globale `docker-mcp-gateway` dans `~/.codex/config.toml`, URL `/codex/mcp`, deux outils autorisés. Desktop et CLI partagent cette configuration. Authentification par `http_headers_helper`, mécanisme natif qui lit `~/.config/docker-mcp-gateway/codex.env` (0600, dossier 0700). Le helper local `codex-headers.py` est privé, sans token dans son code. Aucune dépendance à une variable héritée par l'application. Les ajouts temporaires aux profils shell et au LaunchAgent ont été retirés.
- OpenClaw : serveurs natifs `docker_gateway_pro` et `docker_gateway_perso`, URLs `/pro/mcp` et `/perso/mcp`. Headers avec références `${DOCKER_MCP_PRO_TOKEN}` / `${DOCKER_MCP_PERSO_TOKEN}` ; valeurs dans `~/.openclaw/.env` (0600). Chaque serveur expose seulement `get_current_time` et `convert_time`.
- Pro (`main`) : ajout de `docker_gateway_pro__*` dans `tools.alsoAllow`, refus de `docker_gateway_perso__*` dans `tools.deny`. Perso : configuration inverse. Ces refus de serveur entier s'appliquent avant connexion dans le runtime natif. Métadonnées `codex.agents` également limitées au bon agent pour une éventuelle projection Codex ; elles ne constituent pas à elles seules l'isolation du runtime embarqué.
- Avec accord explicite reçu pendant la mission : exception dans `openclaw/send-approval/lib/mcp-reads.js`, limitée aux deux noms exacts des outils time, au bon profil/agent et aux arguments attendus. Aucun autre outil nouveau autorisé ; confirmations d'envoi, droits existants et blocages conservés. Couverture ajoutée dans `test/docker-time.test.mjs`.
- Les tokens existants ont été transférés par SSH vérifié, sans affichage, génération ou réutilisation entre profils. Aucun secret dans les fichiers du dépôt.

Comparaison structurée avec sauvegardes : tous les MCP préexistants et les autres réglages OpenClaw/Codex sont identiques après retrait des seules additions ci-dessus. Modèles, routage, mémoire et historiques préexistants non modifiés. Les sessions de recette sont distinctes.

## Validation

Codex CLI installé : `0.160.0`. Binaire embarqué Desktop : `0.163.0-alpha.10.2`. OpenClaw : `2026.10.5`.

Les essais Codex utilisent les vrais binaires et leur app-server natif : `thread/start` éphémère, `mcpServerStatus/list`, puis `mcpServer/tool/call`. Aucune génération de modèle. La même configuration et le helper privé sont utilisés, sans injection de token dans l'environnement de test. Nouvelle exécution dans de nouveaux processus pour la persistance du moteur.

Les essais OpenClaw passent par `openclaw agent`, les agents existants et leurs modèles oMLX configurés. Découverte par `tool_search`, appel par `tool_call`, vérification du reçu et de la trace native de l'outil. Les profils opposés sont absents des résultats de découverte. Après fermeture/réouverture normale d'OpenClaw, nouveaux appels réels et tentatives croisées refusées. Les reçus indiquent le fournisseur local oMLX et un coût nul.

La commande `openclaw gateway restart` n'est pas adaptée ici : service LaunchAgent non chargé, application propriétaire de la Gateway. L'application a donc été fermée puis rouverte normalement. PID Gateway `97183` avant, `43434` après, RPC saine. Une soumission pendant le démarrage a échoué ; l'absence de nouveau tour et de message en attente a été vérifiée avant sa réémission.

`/tools/invoke` a répondu 404 pour `tool_search` : cette surface core/plugin/canal n'a pas été utilisée comme preuve MCP. Aucun contournement de politique.

32 tests du plugin de protection : PASS. Deux tests témoins `witness-a` via `unittest` : PASS ; `pytest` non installé, aucun paquet ajouté. Contrôle des tokens dans les sorties de recette, configurations sans valeurs, code changé et journal OpenClaw : PASS. Contrôle des 100 dernières lignes de chaque service Gateway : aucun token trouvé.

**Limite Desktop :** les appels du binaire embarqué prouvent le moteur et sa configuration persistante. Ils ne prouvent pas la reconnexion depuis l'interface graphique déjà ouverte. Cette application héberge la session de travail en cours ; elle n'a pas été fermée. Une réouverture de Desktop et un appel time dans une nouvelle conversation restent nécessaires pour qualifier complètement ce client.

Les tokens et refus constituent une séparation logique sous le même compte macOS, pas une isolation système. Les refus HTTP de tokens croisés sont déjà établis dans la recette Gateway du README ; les profils et tokens n'ayant pas changé, ces requêtes n'ont pas été répétées.

## Rollback ciblé

Sauvegardes privées : `~/.local/state/docker-mcp-client-20261021/`, permissions 0700/0600, manifeste des fichiers initiaux. Ne pas les publier : certaines configurations préexistantes peuvent contenir d'autres secrets.

1. Retirer uniquement la table Codex `[mcp_servers.docker-mcp-gateway]` puis le helper et `codex.env` du dossier privé lorsqu'ils ne sont plus référencés. Aucun profil shell ni LaunchAgent propre à cette mission ne reste installé.
2. Retirer uniquement les deux nouvelles entrées `mcp.servers`, leurs ajouts `tools.alsoAllow` / `tools.deny` par agent et les deux variables dédiées de `~/.openclaw/.env`. Ne supprimer ce fichier que s'il ne contient aucune autre entrée.
3. Restaurer uniquement le bloc ajouté à `mcp-reads.js` depuis `repo-mcp-reads.js` dans la sauvegarde, en préservant toute évolution ultérieure ; retirer le seul nouveau test `docker-time.test.mjs`. Recharger `send-approval` avec `openclaw plugins reload send-approval --json`.
4. Rouvrir normalement les clients puis contrôler leur santé. Ne pas utiliser le rollback de la stack Gateway, qui est hors périmètre de cette mission.

Références : [MCP Codex et configuration partagée](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [helper HTTP natif](https://learn.chatgpt.com/docs/config-file/config-reference). Pour OpenClaw, documentation et schémas livrés avec la version installée : `docs/cli/mcp/registry.md`, `docs/gateway/config-extensions.md`, `docs/help/environment.md`.

## État final vérifié

| Client | Connexion | Découverte | Appel time | Persistance |
|---|---|---|---|---|
| Codex Desktop | PASS moteur embarqué | PASS moteur embarqué | PASS moteur embarqué | PASS moteur ; interface NON TESTÉE |
| Codex CLI | PASS | PASS | PASS | PASS nouveau processus |
| OpenClaw Pro | PASS agent réel | PASS | PASS | PASS après réouverture application |
| OpenClaw Perso | PASS agent réel | PASS | PASS | PASS après réouverture application |

Appels natifs après redémarrage : Pro `17:21:56+02:00`, Perso `17:22:53+02:00`. Refus croisés vérifiés dans les deux sens par les erreurs réelles de `tool_call`, pas par le texte du modèle. L'agent Perso a initialement décrit un refus sans appel natif correspondant ; cette affirmation a été rejetée, puis un unique essai ciblé a fourni la preuve réelle.

Sessions de test supprimées par `openclaw sessions delete`, avec archivage normal géré par OpenClaw ; aucune base interne modifiée directement. Preuves compactes : `diagnostics/openclaw-docker-mcp-gateway-20261021/validation.json`. Les sauvegardes et fichiers de secrets restent hors dépôt.

**Qualification globale partielle** : pour terminer Desktop, rouvrir l'application puis exécuter `docker-mcp-gateway.get_current_time` (`Europe/Paris`) dans une nouvelle conversation, en vérifiant son appel réel et son résultat. Aucune validation GUI n'est déduite des essais du moteur.


## Extension Context7 — 21 octobre 2026

La recette ci-dessus décrit le raccordement initial `time`. Depuis cette extension, les filtres existants Codex et `docker_gateway_pro` incluent aussi exactement `resolve-library-id` et `query-docs`. URLs, headers et tokens ne changent pas. Perso reste limité aux deux outils `time`. La politique `send-approval` reconnaît les deux contrats documentaires uniquement sous le serveur Pro et pour `main`, avec validation stricte des arguments ; aucun wildcard nouveau. Instructions ajoutées dans `~/.codex/AGENTS.md` et le seul workspace Pro. [Résultats et limites](context7-20261021/REPORT.md).
