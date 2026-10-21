# Serena — recette du 21 octobre 2026

État : PASS pour le périmètre testé : Serena via Docker MCP Gateway, Codex natif et OpenClaw Pro. Les treize dépôts ne sont pas tous indexés ; le septième primaire est vide. Aucun commit ni push.

## Inventaire et droits

Identité GitHub docker-02 : FloVisor, authentifiée par le parcours navigateur de `gh`. Git installé, `gh` 2.46.0 installé par apt. Les 13 dépôts ont `permissions.pull=true` sur docker-02. Le compte possède également des droits d'écriture : ce jeton OAuth n'est pas strictement read-only. `gh` annonce un stockage en clair ; fichier `/root/.config/gh/hosts.yml`, root, mode 0600. Aucun identifiant dans les URLs ou les artefacts. Les conteneurs Serena ne reçoivent ni ce fichier ni les identifiants GitHub.

| Dépôt | Priorité | Branche GitHub | Clone | HEAD du clone | Analyse exécutée |
|---|---|---|---|---|---|
| FloVisor/XITHI-Infrastructure-Ops | primary | main | oui | d2f9c0aec87717d8ef73e48613e2590fde97ad2e | symbole Python ciblé |
| FloVisor/nodectra | primary | main | oui | ae39f5845de6e52cd95201402a93fec717321b9d | aucune |
| FloVisor/Plateforme-CaaS-XITHI | primary | main | oui | 14e7988433e1b1d7f3f89145a9b7cbb649b5c8de | aucune |
| FloVisor/Plateforme-SD-WAN-XITHI | primary | main | oui | 1e0f650b63b4f3cd3bef9aaa4437bb4ce4027cc0 | aucune |
| FloVisor/mac-ia-local | primary | main | oui | 366df4d41ae13f84647efbb6170de584828005d6 | symboles Python ciblés + références |
| FloVisor/super-agent | primary | migration/candidate-0.8.0-no-deploy | oui | b83d006606669e00919f1a09c6d51969ee8a56ed | aucune |
| FloVisor/post-activation-validation | primary | main | oui | vide, aucun commit | aucune |
| rldet9/m3-si-mixtrio-kit | secondary | main | oui | 5a0349a6922f53016beda5ab463825e71a5e8868 | lecture texte seulement |
| rldet9/n8n-nodes-advanced | secondary | master | non | non lu | aucune |
| rldet9/m3-si-xithi | secondary | main | non | non lu | aucune |
| rldet9/m3-orionai-patterns | secondary | main | non | non lu | aucune |
| rldet9/m3-workspace | secondary | main | non | non lu | aucune |
| xithi-fr/AlerteSmiden | secondary | main | non | non lu | aucune |

Les sept primaires sont clonés, dont post-activation-validation vide : GitHub déclare main mais aucune référence Git n'existe. Un seul secondaire est cloné pour la recette ; les cinq autres restent à la demande. Ne pas assimiler ces vérifications de droits à un clonage des treize projets.

## Architecture effectivement déployée

Serena v2.1.0, source officielle `5e4f5cd173c7ff3eed37ee3f1de6c266b937c5dc`, image de base locale et adaptateur `local/serena-reader:2.1.0-5e4f5cd`, image finale `sha256:a5cb79fcb9d7bc6094a0bdf4b39e58051c12b8ae414d92e687de19018e5b1cbb`. Docker MCP Gateway démarre l'adaptateur en stdio ; il lance un processus Serena par appel d'analyse, à projet fixe en contexte single_project, puis le ferme. Les outils d'édition, d'exécution de shell et de changement de projet ne sont pas exposés. Chaque appel porte explicitement owner/repository ; aucun projet actif implicite par session. Le verrou fichier partagé sérialise les analyses et les mises à jour Git entre processus/clients. Le Skill est une procédure, pas un outil MCP.

Clones persistants sous `/srv/docker-local/serena/repositories/primary/FloVisor/` et `/srv/docker-local/serena/repositories/secondary/{rldet9,xithi-fr}/`. Bind `/repositories` en lecture seule. Seul `/srv/docker-local/serena/state` est autorisé rw pour métadonnées, caches LSP et dépendances uv/Python. Aucun socket Docker, home root ou identifiant GitHub monté dans Serena. Les chemins autorisés sont déclarés explicitement dans les services Gateway Codex/Pro. Perso inchangé.

Limites Gateway : 1 CPU et 2 Gio **par conteneur MCP**, pas un quota global Swarm. Le verrou partagé empêche deux analyses simultanées, mais les conteneurs adaptateurs de plusieurs clients ont leur propre mémoire de repos. Aucun groupe de treize serveurs permanents. Échantillon pendant analyse : 100,45 % CPU et 276,3 Mio / 2 Gio (mesure instantanée, pas un pic garanti). Clones : 194 Mio ; state : 171 Mio au relevé. Le même plafond Gateway borne désormais aussi le serveur Time des profils Codex/Pro ; ses appels réels restent valides. Les autres services Swarm ne sont pas redéployés.

Les deux projets Python sont configurés pour des analyses ciblées Python, pas pour tous leurs langages. Le secondaire JavaScript a servi à une lecture textuelle. Les autres projets/langages ne sont pas qualifiés. Les caches de symboles sont persistants pour les fichiers consultés : **aucune indexation complète des dépôts n'est revendiquée**.

## Preuves réelles

- `evidence/tests.json` : `main` sur mac-ia-local, `fingerprint` sur XITHI-Infrastructure-Ops, références de count_task_tokens, lecture de tests/n8n-factice.js sur le secondaire ; Time et résolution Context7 réels.
- `evidence/source-verification.json` : corps et plages de lignes renvoyés identiques aux fichiers réellement présents, SHA des clones vérifiés.
- `codex-native.jsonl` : découverte et appel Serena par app-server du binaire Codex installé, zéro génération de modèle. Cela ne prouve pas une reconnexion de la fenêtre Desktop actuellement ouverte.
- `codex-skill.json` : découverte native de la source centralisée du Skill via skills/list.
- `evidence/profile-check.json` : neuf outils dans Pro ; Perso conserve seulement get_current_time et convert_time. Appels Time réels sur les deux profils.
- `evidence/isolation-test.json` : deux sessions MCP indépendantes visant deux projets, puis retour au premier sans changement de dépôt/SHA. Ce contrôle porte sur les métadonnées ; l'isolation des processus d'analyse repose aussi sur le lancement à projet fixe et l'absence de activate_project.
- OpenClaw skills info : source centralisée visible pour main, `blockedByAgentFilter=true` et `modelVisible=false` pour perso.
- Politique send-approval : 34 tests réels Node passent, dont contrats Serena Pro stricts, arguments, refus Perso, Time, Context7 et refus de mutations MCP.
- Orion direct préservé : get_skill(orion) et list_registries réels réussis depuis Codex. Aucun transfert d'Orion vers la Gateway ni changement de ses credentials.

## Exploitation

Sélection : charger le Skill `/Users/fngux2/AI/skills/shared/serena/SKILL.md`, puis découvrir les outils serena_* via docker-mcp-gateway (Codex) ou docker_gateway_pro (OpenClaw Pro). Toujours lire serena_repository_status et conserver le SHA retourné. Les clones distants n'incluent pas les changements non poussés ni non committés du Mac ; les analyser localement avec Git/rg/Graphify si nécessaire.

Cloner un secondaire autorisé : `ssh root@docker-02 'python3 /srv/docker-local/serena/repository.py rldet9/m3-workspace'`. Le script vérifie les droits existants et la branche par défaut GitHub ; aucun élargissement. Un dépôt hors liste nécessite d'abord son autorisation, puis l'ajout explicite dans repositories.json, la reconstruction de l'adaptateur et le remplacement ciblé de l'entrée serena dans Codex/Pro. Recharger ces deux services et les clients, vérifier Perso et les témoins. Le catalogue est chargé au démarrage : pas de rechargement implicite.

Actualiser seulement le dépôt utile : ajouter `--update` à la commande. Le verrou partagé attend la fin de l'analyse ; le script refuse un clone sale, des commits locaux, une divergence et un changement de branche par défaut. Fetch puis merge --ff-only, sans reset/clean/commit/push. Aucun cron. Garder le SHA précédent dans le ticket d'exploitation avant actualisation. Dépôt vide : aucune révision analysable ; attendre un premier commit créé par son propriétaire.

Rollback de révision : attendre les analyses, prendre le même verrou, vérifier clone propre et absence de commits locaux, puis `git switch --detach <SHA-précédent-vérifié>` ; aucune suppression de fichiers ni reset --hard. Revenir ensuite explicitement à la branche par défaut avant une nouvelle actualisation. Vérifier status et SHA puis une recherche ciblée. Cette procédure est documentée, **pas exécutée** en recette.

Rollback de l'intégration : `/docker-mcp profile server remove codex serena` et équivalent pro dans les bons conteneurs Gateway, retirer seulement les deux variables de bind ajoutées et remettre cpus/memory aux valeurs précédentes d'après les sauvegardes, puis recharger ces deux services. Retirer uniquement les cinq filtres serena_* Codex/Pro et serena de la liste de skills main ; retirer le seul bloc Serena de mcp-reads.js, recharger send-approval et MCP. Préserver Time/Context7/Orion et Perso, ainsi que tous les changements concurrents. Sauvegardes locales privées : `~/.local/state/serena-20261021/` ; exports profils distants : `/srv/docker-local/compose/mcp-gateway/backups/serena-20261021/`. Ne pas restaurer aveuglément une configuration entière. Garder les clones et index tant qu'ils restent utiles ; aucune suppression dans le rollback normal.

## Incidents et limites

Le prototype HTTP privé a été refusé par la Gateway (HTTPS obligatoire). Il a été supprimé et remplacé par le transport conteneur/stdio officiellement supporté ; aucun contrôle HTTPS désactivé. L'image minimale manquait de uv, ajouté pour Pyright. L'adaptateur a été corrigé pour MCP SDK 2 (`is_error` côté Python). Les erreurs antérieures n'ont pas été retenues comme des validations.

Délégations locales réelles : fe435614-84dd-433c-b990-ac681a55bb90 (grille préparatoire), 78847a70-c9d4-40c4-8b54-82871bee68cf (revue). Propositions non étayées rejetées : JSON serait incompatible YAML, traversal malgré allowlist, sémaphore suffirait à imposer CPU/RAM. Les preuves d'exécution priment. Aucun secret transmis.

Sources officielles consultées : [Serena Docker](https://github.com/oraios/serena/blob/v2.1.0/DOCKER.md), [configuration Serena](https://github.com/oraios/serena/tree/v2.1.0/src/serena/resources), [contrat des entrées Gateway](https://github.com/docker/mcp-gateway/blob/main/docs/server-entry-spec.md). SDK et CLI installés inspectés pour confirmer les signatures effectives.

## Qualification finale OpenClaw et Skill

Nouvelle session Pro `agent:main:serena-validation-final-20261021` : lecture réelle du Skill centralisé via read, découverte via tool_search, appels tool_call réels de serena_repository_status, serena_find_symbol et serena_symbols_overview. Les trois reçus natifs indiquent isError=false et le SHA `366df4d41ae13f84647efbb6170de584828005d6`. Preuve : `evidence/openclaw-pro-tool-receipts.json` (événements d'outils seulement, pas de raisonnement du modèle). Le modèle a d'abord tenté un outil skills_read inexistant, puis a chargé le Skill via read. La première session, ouverte pendant l'évolution du profil, utilisait un catalogue incomplet ; arrêt par chat.abort, puis probe natif (neuf outils), mcp reload et une nouvelle session ont fourni la preuve réelle. Aucun patch du modèle ou des connexions Orion/Perso pour compenser.

Source du Skill découverte par le moteur Codex : `/Users/fngux2/AI/skills/shared/serena/SKILL.md`, scope user, enabled=true. OpenClaw main : modelVisible=true ; perso : modelVisible=false. Refus Perso et mutations également couverts par les tests de politique. Profil Gateway Perso inchangé par comparaison d'export ; absence de Serena confirmée dans son vrai tools/list. Les configurations clientes Perso et Orion sont identiques aux préimages. Les deux tests témoins witness-a passent via unittest.

Limites conservées : Desktop GUI déjà ouvert non reconnecté dans cette recette ; les appels natifs et le chargement du Skill sont prouvés par un nouveau processus Codex, pas par un redémarrage de la fenêtre en cours. Aucun test d'analyse sémantique de tous les langages/projets, aucun rollback ni restauration après reboot exécutés. Les caches existent et sont conservés dans le bind persistant ; pas de prétention d'index global complet. L'authentification OAuth GitHub reste plus large que la lecture seule.

Contrôle final : seules les additions Serena attendues distinguent les configurations clientes des préimages ; export natif Perso identique avant/après. Les services Swarm contrôlés affichent leurs répliques attendues. Les deux sessions de recette ont été supprimées par le cycle de vie natif OpenClaw avec archivage normal ; exports temporaires nettoyés après conservation des reçus d’outils.
