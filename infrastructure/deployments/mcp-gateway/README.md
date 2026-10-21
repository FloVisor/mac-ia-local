# Docker MCP Gateway sur docker-02

Déploiement du 21 octobre 2026. Autorisation explicite du socket Docker partagé ; aucune migration Codex/OpenClaw, aucun commit/push. **DÉPLOYÉ — recette MCP PASS avant et après recréation contrôlée des trois services.**

## Accès et MCP actifs

| Profil natif / service Swarm | URL HTTPS | MCP activé |
|---|---|---|
| codex / mcp-gateway_codex | https://mcp-gateway.gangneux.org/codex/mcp | time, Context7 |
| pro / mcp-gateway_pro | https://mcp-gateway.gangneux.org/pro/mcp | time, Context7 |
| perso / mcp-gateway_perso | https://mcp-gateway.gangneux.org/perso/mcp | time |

Transport MCP Streamable HTTP (`streaming`). `time` conserve `get_current_time` et `convert_time` sur les trois profils. Context7 est activé uniquement sur Codex et Pro, via l’entrée officielle distante du catalogue Docker ; outils autorisés explicitement : `resolve-library-id`, `query-docs`. La connexion officielle sans clé est prise en charge et les appels réels ont réussi. Aucun secret Context7 créé ; les Bearer Gateway restent inchangés. Voir [la recette Context7 et son rollback](context7-20261021/REPORT.md).

## Architecture et limites

Stack `mcp-gateway`, une réplique de chaque service contrainte à `node.hostname == docker-02`. Traefik existant, provider file, seul fichier ajouté : `/srv/docker-shared/traefik/dynamic/mcp-gateway.yml`. Routage exact des trois chemins et retrait du préfixe de profil avant `/mcp`. Aucun port Gateway publié, aucune exposition de chemin d'administration ou de santé.

**Les trois Gateways partagent `/var/run/docker.sock` du manager docker-02. Les tokens et profils ne restreignent pas les privilèges Docker.** Une Gateway compromise peut agir sur le moteur et le Swarm au-delà de son périmètre fonctionnel ; cette limite a été explicitement acceptée. Les conteneurs MCP sont des conteneurs standalone du moteur docker-02, pas des services Swarm. Ils héritent du réseau attachable `TRAEFIK_BACKEND`, partagé avec d'autres applications : aucune isolation réseau/egress entre profils ou vis-à-vis des backends internes n'est revendiquée.

**Aucune limite CPU/RAM**, conformément à la dernière instruction : absence de `deploy.resources.limits`, Gateway `--cpus 0 --memory 0`, contrôles runtime `Memory=0`, `NanoCpus=0`, `CpuQuota=0`. La Gateway conserve `no-new-privileges`, le contrôle des signatures et le scan de secrets. Sans quota, une charge MCP peut consommer les ressources du nœud partagé.

Volumes indépendants `mcp_gateway_codex`, `mcp_gateway_pro`, `mcp_gateway_perso`, montés sous `/root/.docker`. Ce sont des volumes locaux à docker-02 : aucune HA de leurs données, aucun test de perte du nœud. Création/export/import des profils et import des catalogues uniquement par CLI native ; aucune écriture directe dans une base interne.

Les outils d'administration MCP dynamiques sont désactivés via `docker mcp feature disable dynamic-tools` dans chacun des états. Cela bloque leur exposition aux clients ; les conteneurs des MCP approuvés restent créés à la demande et supprimés après utilisation. Toute nouvelle intégration nécessite une modification administrative explicite du profil et une revue de ses droits/secrets.

## Versions et catalogue central

- Image Gateway : `docker/mcp-gateway@sha256:f5a679a05fc39022a046167bef92aeeb01bcd59485ad27843ae5227db7950688`. Le tag `latest` a servi uniquement à la découverte ; le déploiement est figé au digest. CLI `version` : `HEAD`, donc aucune version sémantique d'image n'est inventée. `serverInfo.version` MCP observé : `2.0.1`.
- Image témoin : `mcp/time@sha256:9c46a918633fb474bf8035e3ee90ebac6bcf2b18ccb00679ac4c179cba0ebfcf`.
- Catalogue OCI officiel importé : `mcp/docker-mcp-catalog:latest`, digest natif observé `c855af4b06ed1cc11fc169cfb752941e9b5a489b1af870221308572611a88035`. Les trois profils enregistrent un snapshot de la définition approuvée avec digest d'image ; aucune activation globale et aucune actualisation automatique du tag.
- Source centrale sur docker-02 : `/srv/docker-local/compose/mcp-gateway/catalog/`, snapshots officiel YAML v2 et export OCI natif. Dossier monté en lecture seule dans les Gateways ; caches/catalogues natifs importés séparément dans leurs états. La centralisation concerne la source de référence, **pas une base mutable commune aux trois processus**.

Fichiers d'exploitation : `/srv/docker-local/compose/mcp-gateway/`. Sources de stack, chargeur et recette dans ce dossier du dépôt. Exports natifs `{codex,pro,perso}-profile.yaml` sur docker-02 ; copies sans secrets dans `evidence/`.

Procédure de mise à jour : sauvegarder les exports et états par les mécanismes supportés ; récupérer une nouvelle version du catalogue dans le dossier central, noter son digest et examiner les définitions ; importer dans les seules instances concernées via CLI native, réattribuer explicitement les seuls serveurs approuvés puis exporter leurs profils. Vérifier les nouveaux digests/signatures et les droits/secrets, redéployer seulement les services concernés et exécuter la recette. Mettre à jour le digest Gateway dans `stack.yml` pour une mise à jour de Gateway. Aucun auto-update de catalogue, d'image ou d'intégration n'est configuré. Un changement de tag en amont ne modifie pas les snapshots actuellement actifs.

## Tokens et journalisation

Trois tokens aléatoires indépendants de 48 octets (encodage URL-safe), secrets Swarm `mcp_gateway_{codex,pro,perso}_token_v1`. Le chargeur lit `/run/secrets/gateway_token`, refuse une valeur vide puis initialise `MCP_GATEWAY_AUTH_TOKEN`. Aucun token dans les labels, arguments, stack, dépôt ou sorties de recette.

Récupération réservée à l'administrateur, dans son terminal personnel :

```sh
ssh root@docker-02 'cat /srv/docker-local/compose/mcp-gateway/secrets/codex.token'
ssh root@docker-02 'cat /srv/docker-local/compose/mcp-gateway/secrets/pro.token'
ssh root@docker-02 'cat /srv/docker-local/compose/mcp-gateway/secrets/perso.token'
```

Dossier 0700, fichiers 0600 root ; copies de récupération en clair sur ce seul hôte, à intégrer à un coffre/sauvegarde chiffrée administrateur si souhaité. Docker Secret ne permet pas de récupérer une valeur avec `docker secret inspect`. Ne pas recopier les tokens dans le chat. Rotation : générer un nouveau token, créer un secret `..._v2`, changer uniquement sa référence dans la stack et mettre à jour le service concerné ; vérifier le nouveau token et le rejet de l'ancien avant suppression de l'ancien secret.

`--log-calls=true` et scan de secrets conservés. Journal natif observé : nom d'outil, résumé du type/nombre de champs et durée, sans valeurs d'arguments. Tokens absents des journaux lors de la recette. Rotation Docker des journaux 10 Mo × 3 par Gateway. Une vérification des journaux doit accompagner toute nouvelle intégration sensible : les journaux propres aux futurs serveurs ne sont pas automatiquement garantis sans secrets.

## Recette et anomalies rencontrées

Script [validate.py](validate.py), exécuté sur docker-02 ; tokens lus en mémoire uniquement. Preuves JSON dans `evidence/`.

- HTTPS : certificat Let's Encrypt YR2, SAN `gangneux.org` et `*.gangneux.org`, valide du 14 septembre au 13 décembre 2026, validation TLS normale.
- Chaque profil : initialisation MCP 200, notification initialized 202, outils attendus uniquement, appel réel `get_current_time` réussi.
- Chaque profil : absence de token et token incorrect 401 ; six combinaisons de tokens croisés 401 ; trois tokens propres 200.
- Pendant chaque appel : conteneur `time` observé sur docker-02, réseau `TRAEFIK_BACKEND`, sans limite CPU/RAM, non privilégié, `no-new-privileges`. Conteneurs éphémères supprimés automatiquement après usage.
- Aucun port Swarm publié ; trois placements vérifiés ; journal d'appel présent, tokens absents.
- Après recréation des trois services : même recette passée, mêmes exports natifs de profils (SHA-256), mêmes catalogues.
- Six services préexistants : mêmes IDs, images et réplicas (5 × 1/1, agent Portainer 3/3). Aucun parcours métier supplémentaire exécuté.
- HTTPS IPv4 et IPv6 : TLS validé, 401 sans token ; `/admin` : 404.

Limites : contrôle depuis le Mac/réseau existant et docker-02 ; aucun poste de test Internet extérieur indépendant. La disponibilité applicative des autres stacks n'est pas qualifiée par un simple relevé de réplicas.

Anomalies résolues pendant préparation : import direct de `time` par URI d'image refusé car image non self-describing, remplacé par la définition du catalogue officiel ; intercepteur `before:exec` non utilisable dans cette image (`json: unsupported type: func(mcp.CloseSSEStreamArgs)`), retiré au profit du journal natif. Aucun patch de la Gateway. Avertissement non bloquant du magasin de secrets Desktop absent sur CE ; `time` n'a besoin d'aucun secret métier. Aucune intégration nécessitant ce magasin n'est déclarée qualifiée.

## Exploitation et rollback

```sh
ssh root@docker-02 'docker stack services mcp-gateway'
ssh root@docker-02 'docker service logs --tail 50 mcp-gateway_codex'
ssh root@docker-02 'python3 /srv/docker-local/compose/mcp-gateway/validate.py'
```

Rollback de cette installation uniquement :

```sh
ssh root@docker-02 'rm /srv/docker-shared/traefik/dynamic/mcp-gateway.yml'
ssh root@docker-02 'docker stack rm mcp-gateway'
```

Attendre l'arrêt des trois services, contrôler la disparition de leurs conteneurs MCP et le refus des endpoints. Conserver volumes, secrets, catalogue et exports pour restauration ; ne lancer aucun `prune` ni suppression par label global. Si un conteneur reste, vérifier son ID et son appartenance à cette installation avant de l'arrêter. Le retrait effectif de la stack n'a pas été exécuté pendant la recette ; la recréation contrôlée des trois services vérifie le redémarrage, pas une restauration après perte de volume. Pour remettre en service : republier seulement ce fichier Traefik et `docker stack deploy -c stack.yml mcp-gateway` depuis le dossier distant, puis refaire la recette.

## Références officielles

[Gateway et Docker CE](https://github.com/docker/mcp-gateway/blob/a34df45d4ec0e941a9853ad768c4f6cd818966b3/docs/mcp-gateway.md), [CLI](https://github.com/docker/mcp-gateway/blob/a34df45d4ec0e941a9853ad768c4f6cd818966b3/docs/generator/reference/mcp_gateway_run.md), [profils](https://github.com/docker/mcp-gateway/blob/a34df45d4ec0e941a9853ad768c4f6cd818966b3/docs/profiles.md).
