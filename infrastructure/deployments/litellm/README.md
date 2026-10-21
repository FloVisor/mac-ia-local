# LiteLLM — déploiement du 21 octobre 2026

**État courant : trois modèles locaux et dix routes gratuites disponibles ; deux inférences gratuites via LiteLLM VERIFIED. Trois routes payantes activées administrativement, clé enregistrée ; génération et décompte payants NOT_TESTED, aucune clé cliente émise.** Les sections de déploiement ci-dessous conservent leur valeur historique ; la finalisation en fin de rapport décrit le dernier état.

Décision de finalisation du 21 octobre 2026 : seule l'API d'inférence est publique ; dashboard et tous les endpoints administratifs restent privés/VPN. Le cookie natif `token` est Secure mais lisible par JavaScript (`HttpOnly=false`), comportement explicitement accepté dans ce seul périmètre privé. Cette décision ne corrige pas le risque XSS et ne constitue pas une conformité HttpOnly. Aucun patch, fork, réécriture de cookie ou nouveau service d'authentification.

## Implantation réelle

Stack Swarm `litellm`, services `litellm_gateway` et `litellm_postgres`, chacun une réplique contrainte à docker-02, amd64. Trois managers Ready/Active, Docker 29.8.0. Services sans port publié, sans limite mémoire, mises à jour/rollback stop-first, arrêt gracieux 60 secondes. Un worker et une seule instance LiteLLM responsable des migrations natives au démarrage ; aucun Redis.

- Gateway : `ghcr.io/berriai/litellm:v1.104.5@sha256:b86d67931c06f491fdfd9112b5e7c96065a220ecb54dbe0060a0383999707f6c` (manifeste amd64).
- PostgreSQL : `postgres:17-bookworm@sha256:ec4dfc6571f04fe0731ce948c1500d676af49a7224392dcc6995cc1ee33a94bb` ; version réellement exécutée **17.11**.
- `TRAEFIK_BACKEND` : overlay Swarm existant, attachable, inchangé ; LiteLLM et FreeLLMAPI y communiquent.
- `litellm_database` : overlay dédié, internal et chiffré ; PostgreSQL est connecté uniquement à ce réseau.
- Volume local `litellm_postgres_data` : `/srv/docker-local/docker/volumes/litellm_postgres_data/_data`, ext4. Exception volontaire à `/srv/docker-shared` (VirtIOFS), aucun PGDATA sur le partage.

**Aucune HA applicative ou des données : dépendance à docker-02.** Le basculement Traefik n'a pas été provoqué. Résolution et accès au service vérifiés depuis docker-01, sans forcer de bascule.

## URLs et accès

- Administration : <https://litellm.gangneux.org/ui/> — **réseaux privés autorisés uniquement**.
- API : `https://litellm.gangneux.org/v1` — seuls **GET /v1/models**, **POST /v1/chat/completions**, **POST /v1/responses** sont publics, avec authentification native LiteLLM. Toute autre méthode ou tout autre chemin reste privé, y compris embeddings, WebSocket Responses (GET), OPTIONS et les variantes avec slash final.
- Backend Docker : `http://litellm_gateway:4000` ; sondes `/health/liveliness` et `/health/readiness`, sans génération. `/health` n'est pas utilisé comme liveness.
- FreeLLMAPI : `http://freellmapi_api:3001/v1`, jamais son domaine extérieur.
- oMLX futur : le listener observé est uniquement `127.0.0.1:8000` **sur le Mac**, inaccessible depuis LiteLLM. Aucun changement d'écoute, modèle, authentification ou client.

DNS existant déjà correct : `litellm.gangneux.org` et `traefik-10.gangneux.org` résolvent vers A `82.67.206.214`, AAAA `2a01:e0a:8ce:68c5::10`. Aucune écriture DNS nécessaire. HTTPS IPv6 via DNS et IPv4 vers l'ingress privé forcé : 200, certificat validé sans exception ; HTTP redirige 301 vers HTTPS.

Traefik v3.7.13, fournisseur actif `file`. Montage réel vérifié : `/srv/docker-shared/traefik/dynamic` → `/etc/traefik/dynamic`. Nouveau fichier dédié `litellm.yml`, certificat wildcard existant. Route publique exacte `litellm-api-public` priorité 200 ; route de repli `litellm-private` priorité 100 avec `private-networks@file`, même politique que Home Assistant ; route HTTP de redirection priorité 10. Aucun PathPrefix /v1 global, aucun simple test de présence d'Authorization. L'ACL utilise le pair socket, sans ipStrategy fondée sur X-Forwarded-For. Les pairs observés sur Traefik sont `::ffff:192.168.202.131` en IPv4 et `2a01:e0a:8ce:68c2::195` en IPv6. Depuis une origine overlay non autorisée, API publique 401 sans clé/fausse clé, autres routes 403, même avec X-Forwarded-For privé usurpé ; **ceci n'est pas un test depuis Internet**.

CORS limité à l'origine LiteLLM ; PROXY_BASE_URL HTTPS ; plages de proxies de confiance limitées à `172.29.2.2/32`. Throttle natif de login actif (10 échecs/source, fenêtre 60 s, blocage 300 s), worker unique ; pas de campagne de bruteforce exécutée. Protection Traefik de 100 requêtes simultanées, aucun petit plafond de tokens ni de taille de contexte ajouté. L'accès UI est `admin_only`, le login d'environnement est désactivé après vérification du compte en base. Swagger, ReDoc et OpenAPI désactivés (404). Aucune passerelle MCP, agent, pass-through générique ou fallback Cloud configuré.

## Fichiers, secrets et initialisation

Sur docker-02 : `/srv/docker-local/compose/litellm/` contient stack, configuration, chargeur, scripts, politiques et validations. Sources reproductibles dans ce dossier du dépôt. Le chargeur lit les secrets puis exécute `/app/docker/prod_entrypoint.sh` ; CLI et migrations officiels conservés. Le démarrage initial a réussi sans depends_on ; prévoir le démarrage PostgreSQL avant la gateway lors d'une reconstruction complète.

Secrets Swarm durables : `litellm_master_key_v1`, `litellm_salt_key_v1`, `litellm_db_password_v1`, `litellm_bootstrap_password_v1`. Copies root 0600 dans le sous-dossier distant `secrets/` (0700), hors Git. `admin-credentials.json` contient le compte nominatif `florian@gangneux.org` et son mot de passe. Ne jamais régénérer la salt key sur redéploiement. MASTER_KEY réservée à l'opérateur, aucune application cliente modifiée.

Compte administrateur initialisé via `/user/new`, session bootstrap native, invitation et claim natifs, sans envoi d'email. L'invitation a été consommée. Deux incidents initiaux corrigés : identité opérateur non encore persistée pour la FK `created_by`, puis mot de passe aléatoire sans caractère spécial. Aucun accès base en écriture direct ; une lecture ciblée de l'invitation a permis de la réutiliser. Préimages ciblées `config.before-db-login.yaml` et `stack.before-db-login.yml` conservées sur l'hôte. `initialize.py` refuse de recréer une initialisation terminée ; il n'est pas une commande de redéploiement.

La clé dédiée FreeLLMAPI reste conservée à `/srv/docker-local/compose/freellmapi/secrets/litellm-api-key` ; enregistrée via `/credentials` sous `freellmapi-internal`, chiffrée par le mécanisme natif et persistée en base. Aucun secret dans les sources, labels ou rapports. Bootstrap désactivé mais secret conservé ; ne pas réactiver ce login par inadvertance.

## Catalogue, identités et usages

FreeLLMAPI réellement healthy, ping interne et `/v1/models` authentifié 200 : **275 entrées de catalogue, zéro fournisseur configuré** d'après `/api/keys` authentifié. Catalogue ≠ modèles utilisables ou approuvés. Aucun modèle importé, aucun groupe local-only/free-approved factice, aucune génération. Le profil FreeLLMAPI LiteLLM existant et son exposition privée sont conservés ; seule une session de lecture admin a été ouverte puis fermée.

La base est la source des futurs modèles administrables (`STORE_MODEL_IN_DB=True` et `store_model_in_db: true`), sans définitions YAML en double. L'identifiant fournisseur enregistré persiste après redéploiement. Ajout/modification d'un **modèle opérationnel** et son ON/OFF non qualifiés faute de backend ; ni masquer un modèle ni retirer sa visibilité ne prouve son interdiction. Import automatique différé : aucune cible activable autorisée, pas de synchroniseur permanent ajouté.

Identités natives créées, rôle `internal_user`, sans mot de passe ni clé émise : `codex`, `mcp-delegate`, `openclaw-pro`, `openclaw-perso`, `mcp-delegate-cloud-approved`. Politiques préparées dans `client-policies.json` : MCP et Pro local-only, Cloud approuvé distinct, listes explicites avant émission. Pas de clé vide/wildcard ni de MASTER_KEY distribuée. Les tests révocation, catalogue filtré et permissions de clés clientes sont **NOT_RUN**, pas présentés comme validés avec une clé bloquée artificiellement.

Comptage natif/spend logs disponibles ; `turn_off_message_logging=true`, `store_prompts_in_spend_logs=false`, logs ERROR, télémétrie CLI désactivée. Aucun cache sémantique, compression, mémoire partagée, monitoring externe ou plafond de raisonnement. Aucun usage/tokens/coût observé puisque l'inférence n'a pas été exécutée. Gratuité, quota fournisseur, contexte 128K, tools et Responses : **non qualifiés**. Les éventuels retries internes FreeLLMAPI ne seraient pas tous nécessairement visibles dans LiteLLM ; ne pas additionner deux fois la même inférence. Pas de retries/fallbacks LiteLLM ni de suppression globale de paramètres (`drop_params=false`).

## Résultats et limites

PASS : placement, tâches saines, migrations, volume local, aucune publication de port, compte admin en base, conservation de l'identifiant fournisseur et des cinq identités après redéploiement, bootstrap désactivé, API sans clé/mauvaise clé 401, UI HTML et ressource JS 200, docs 404, TLS/redirect, isolation Traefik, accès overlay inter-nœuds, Home Assistant 200 et home.gangneux.org 307. Aucun secret connu ni marqueur synthétique de la requête refusée retrouvé dans les logs gateway contrôlés ; aucune access-log Traefik activée dans les arguments constatés. Ce contrôle n'est pas une qualification de tous les chemins d'erreur d'inférence.

Redémarrage PostgreSQL ciblé : ancien écrivain arrêté avant nouveau, données conservées (7 utilisateurs, 1 identifiant fournisseur). Readiness a transitoirement renvoyé 503 et login 500 pendant la reconnexion Prisma ; le moteur a redémarré automatiquement puis readiness est revenu à 200. Voir les preuves séparées de l'incident et de l'état final ; ne pas interpréter la liveness seule comme disponibilité de la base.

Mémoire/CPU ponctuels après premier redéploiement : gateway **531,7 MiB / 0,21 % CPU**, PostgreSQL **42,17 MiB / 0,54 % CPU**. Observations ponctuelles sans charge ; aucun dimensionnement déduit. Un pic gateway de 19,34 % a aussi été observé pendant la reconnexion DB.

Finalisation : routage public API réalisé, exception HttpOnly limitée à l'administration privée explicitement acceptée. Inférence en attente de fournisseur autorisé ; oMLX reste volontairement en loopback, hors mission. NOT_RUN : recette graphique (aucun navigateur exposé à cua), modification de modèle opérationnel via UI, usages réels, SSE, tools, `/v1/responses`, révocation et autorisations clientes, accès depuis un point Internet extérieur, HA et charge. Aucun succès simulé.

## Finalisation de l’exposition — 21 octobre 2026

Modification unique de routage : `/srv/docker-shared/traefik/dynamic/litellm.yml`, rechargé par le fournisseur fichier sans redémarrage. Source courante `traefik.yml` ; préimage distante `/srv/docker-local/compose/litellm/preimages/20261021-public-api/litellm.yml`. Priorités et méthodes vérifiées dans Traefik et dans le code de la version installée. Aucun autre routeur HTTP ne matche ce domaine ; aucun port LiteLLM, PostgreSQL ou FreeLLMAPI publié. Stack, configuration applicative, images, comptes, secrets et données inchangés ; tests de persistance antérieurs réutilisés sans redémarrage.

31 contrôles ciblés PASS depuis l'overlay non autorisé, avec X-Forwarded-For privé usurpé : six refus 401 sur les trois API publiques (sans clé/fausse clé), 22 refus 403 sur le repli privé et les variantes de chemins/méthodes, trois refus 403 FreeLLMAPI. Échantillon administratif réellement présent dans la version installée : `/ui/`, `/v2/login`, `/credentials`, `/user/list`, `/user/new`, `/key/generate`, `/model/new`, `/global/spend/logs`. Aucun appel fournisseur exécuté : les requêtes synthétiques ont été refusées avant inférence.

Depuis le LAN via HTTPS Traefik et certificat vérifié : UI HTML 200 en IPv4 et IPv6 ; login admin 200 ; `/model/info`, `/credentials`, `/user/list` et `/global/spend/logs` authentifiés 200 ; logout 200. Cookie toujours Secure et non HttpOnly. La recette graphique reste NOT_RUN (aucun navigateur exposé à cua dans la session) ; HTML 200 n'est pas une validation visuelle.

Journaux gateway, FreeLLMAPI et Traefik des 15 dernières minutes contrôlés : aucun secret connu ni marqueur synthétique trouvé. Contrôle borné aux journaux observés, sans prétention sur tous les futurs chemins d'erreur. Protections existantes conservées : TLS, limite de requêtes simultanées compatible streaming, throttle natif de login, aucune authentification interactive sur l'API publique.

DNS vérifié via le résolveur système et `1.1.1.1` : LiteLLM est CNAME vers `traefik-10.gangneux.org`, A `82.67.206.214`, AAAA `2a01:e0a:8ce:68c5::10`. FreeLLMAPI se résout aussi via ce CNAME public préexistant ; cela ne le rend pas accessible hors ACL. Aucun changement de zone publique. La vue interne FreeLLMAPI reste à créer : A `192.168.205.10`, AAAA `2a01:e0a:8ce:68c5::10` ; fichier préparé `../freellmapi/dns-internal.zone`. Aucun accès DNS dédié identifié, aucun secret ACME ou d'une autre application réutilisé.

Intégration FreeLLMAPI conservée : DNS Docker, ping et authentification du profil LiteLLM déjà validés ; aucune vérification manquante à relancer, aucun modèle/fournisseur ajouté. Les cinq identités restent sans clé active faute de cible approuvée. Aucune application cliente modifiée. Prochaines étapes : fournisseur gratuit approuvé, première inférence et tests clients, puis raccordement des applications. La chaîne n'est pas qualifiée de bout en bout.

Preuves : `evidence/exposure-20261021/`. Script ciblé `check-exposure.py` sur docker-02 ; ne pas relancer toute la recette de déploiement pour une simple consultation. Test depuis Internet extérieur NOT_RUN : aucun point externe dédié identifié dans les accès de cette mission.

## Actions restantes et exploitation

1. Contrôler depuis un point Internet externe existant dès qu'il est disponible. Le routage public est appliqué et testé depuis l'overlay ; le parcours Internet externe reste NOT_RUN, sans blocage technique de routage identifié.
2. Configurer manuellement un fournisseur gratuit approuvé dans FreeLLMAPI, ou rendre disponible un endpoint privé oMLX déjà configuré dans une mission distincte. Importer seulement les cibles approuvées, puis créer les groupes et clés explicites et qualifier leurs permissions/inférences.
3. Faire la recette graphique depuis un navigateur autorisé et tester depuis Internet avant de déclarer la publication conforme. Aucun changement Codex/OpenClaw/MCP réalisé.

```sh
# Depuis le Mac : consultation
ssh root@docker-02 'docker stack ps litellm; docker service inspect litellm_gateway --format "{{json .UpdateStatus}}"'
# Redéploiement existant : ne génère aucun secret, ne réinitialise pas les comptes
ssh root@docker-02 'cd /srv/docker-local/compose/litellm && docker stack deploy -c stack.yml litellm'
# Validation ciblée, à relancer seulement après changement pertinent
ssh root@docker-02 'python3 /srv/docker-local/compose/litellm/validate.py'
# Arrêt : gateway avant base ; conservation données, secrets, routage
ssh root@docker-02 'docker service scale litellm_gateway=0'
ssh root@docker-02 'docker service scale litellm_postgres=0'
# Reprise : base d'abord, attendre healthy, puis gateway
ssh root@docker-02 'docker service scale litellm_postgres=1'
ssh root@docker-02 'docker service scale litellm_gateway=1'
```

En cas de modification du contenu d'une config Swarm, utiliser un nouveau nom versionné (configuration courante `litellm_config_v2`). Un rollback d'image **n'annule pas les migrations PostgreSQL**. Aucune sauvegarde supplémentaire, reboot hôte, redémarrage Docker/Traefik ou changement HA effectué. Aucun commit/push.

Sources officielles consultées : [release stable v1.104.5](https://github.com/BerriAI/litellm/releases/tag/v1.104.5), [avis de sécurité](https://github.com/BerriAI/litellm/security/advisories), [cookie natif du tag](https://github.com/BerriAI/litellm/blob/v1.104.5/litellm/proxy/management_endpoints/ui_sso.py), [protections natives SSRF](https://github.com/BerriAI/litellm/blob/v1.104.5/litellm/proxy/auth/auth_utils.py), [sécurité](https://docs.litellm.ai/docs/proxy/security_best_practices). Les plages vulnérables des avis publiés consultés précèdent la version retenue ; aucun scan exhaustif de dépendances ou vérification cosign revendiqué. Tag d'image hypothétique `main-v1.104.5-stable` rejeté, tag réellement publié et digest utilisés. Preuves filtrées dans `evidence/`.

Règles Traefik : [méthodes, chemins exacts et priorités](https://doc.traefik.io/traefik/v3.7/reference/routing-configuration/http/routing/rules-and-priority/).

## Intégration oMLX — contrôle préalable du 21 octobre 2026

**Historique : BLOCKED lors du contrôle initial, levé par acceptation explicite du risque réseau par l’utilisateur.** À ce stade initial, aucun relais 8000, secret, modèle ou alias ajouté. Résultat de l’intégration ci-dessous.

Constats directs, sans génération ni consultation de secrets :

- oMLX écoute toujours uniquement sur `127.0.0.1:8000` (listener Python PID 49904).
- Tailscale Mac 1.104.1 : `serve status --json` contient uniquement TCP 11434 → `127.0.0.1:11434`, sans Funnel dans cette configuration. L’aide installée supporte `serve --bg --tcp=8000 tcp://127.0.0.1:8000` ; commande non exécutée.
- Sur docker-01, `Tailscale-Ollama` n’a aucun port Docker publié. Sa règle NAT effective est `PREROUTING ! -i tailscale0 -j DNAT --to-destination 100.123.68.99`, sans restriction de port ni de source overlay. Le SNAT vers le Mac utilise `100.103.26.43`. Les politiques INPUT/FORWARD sont ACCEPT. Cette passerelle relaie donc potentiellement d’autres ports du Mac, selon leurs listeners et les contrôles en aval ; aucun accès effectif à ces autres services n’a été testé.
- Persistance observée : état Tailscale monté sur `/srv/docker-shared/openwebui/tailscale-ollama/state`, restart `unless-stopped`, lancement `/usr/local/bin/containerboot`, `TS_USERSPACE=false`. Le mécanisme persistant qui recrée le DNAT n’est pas encore établi ; aucune règle modifiée.
- `tailscale debug netmap`, filtré aux règles de paquets : filtre entrant IPv4/IPv6 couvrant tous les ports 0–65535, protocoles TCP/UDP/ICMP, depuis de larges plages Tailscale. Il s’agit du filtre distribué au Mac, pas d’une lecture de la politique source ni d’une preuve de restriction à la seule passerelle Docker.

Le contrôle demandé « la passerelle Docker n’expose pas un relais non authentifié vers d’autres services du Mac » n’est pas satisfait par les règles observées. Ne pas étendre Serve dans cet état. Étape nécessaire : établir la configuration persistante de la passerelle et la politique Tailscale source, puis limiter durablement le transit aux ports nécessaires (11434 existant, 8000 prévu), en préservant Ollama et les autres usages autorisés. Toute modification de la politique globale du tailnet doit rester distincte des changements ciblés de cette mission.

Tests API authentifiée depuis LiteLLM, refus sans clé, catalogue exact, génération, SSE, provenance du modèle, absence de fallback et refus d’une clé cliente non autorisée : **NOT_RUN**. Test Ollama depuis OpenWebUI : **NOT_RUN** pendant cette intervention ; preuve historique fournie par la mission uniquement. Timeouts oMLX et restriction des clés LiteLLM : **non configurés**, à valider après résolution du contrôle réseau. Aucun succès d’intégration revendiqué.

## Raccordement des modèles locaux — résultat du 21 octobre 2026

Périmètre étendu explicitement par l’utilisateur à Ollama et à tous ses modèles installés. Le contrôle initial ci-dessus est historique. Le risque de transit large de la passerelle et des ACL est accepté pour cette mission ; son durcissement est reporté. Aucun changement des règles NAT, de la politique Tailscale globale, de Traefik ou du DNS.

### Nommage et définitions

Convention : backend logique `local-omlx`, `local-ollama`, futurs `remote-ollama-<serveur>` ; alias de modèle `<backend>/<identifiant exact API>`. Il ne s’agit pas de nouveaux objets natifs « backend ». La séparation utilise les alias, les métadonnées `model_info.backend` et les groupes d’accès aux modèles `local-omlx` / `local-ollama`. Ces groupes servent au regroupement et aux autorisations explicites ; ils n’annulent pas les droits d’une éventuelle future clé wildcard.

Les fournisseurs internes sont `openai` pour oMLX, `ollama_chat` pour le chat Ollama et `ollama` pour ses embeddings. Le credential natif oMLX est nommé `local-omlx-auth` : il est distinct de l’alias, du fournisseur et des UUID internes des déploiements. Aucun objet connexion autonome inventé. Les définitions réellement relues par API sont dans [local-models.json](local-models.json), sans secret. C’est un instantané documentaire, pas une commande d’import à rejouer sans contrôle des doublons.

| Alias LiteLLM | Mode | Qualification réalisée |
|---|---|---|
| `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit` | chat | Catalogue, génération et SSE PASS |
| `local-ollama/qwen3:4b-instruct` | chat | Génération et SSE PASS |
| `local-ollama/embeddinggemma:latest` | embedding | Un vecteur de 768 dimensions PASS |
| `local-ollama/muse-glimmer:30b-mlx` | chat | Catalogue et inscription PASS ; inférence NOT_RUN |

Le second modèle du catalogue oMLX (`mlx-community--Qwen3-Coder-30B-A3B-Instruct-4bit`) n’a pas été exposé ni chargé. Qwen3.6 était déjà chargé et épinglé. Les capacités Ollama du fichier JSON viennent de `/api/tags` ; tools, vision et raisonnement ne sont pas qualifiés par ces tests courts. Aucun téléchargement, changement de modèle, contexte, cache, mémoire ou effort de raisonnement configuré. Les inférences de validation ont naturellement chargé les modèles Ollama légers ; aucun chargement de muse-glimmer provoqué.

### Réseau et authentification

- Ajout ciblé : `tailscale serve --bg --tcp=8000 tcp://127.0.0.1:8000`. Configuration relue : TCP 8000 vers loopback 8000 **et** TCP 11434 vers loopback 11434 conservé. Aucun Funnel ; Serve annonce uniquement le tailnet. Le listener oMLX reste sur `127.0.0.1:8000`. Aucun redémarrage oMLX ou Ollama.
- Chemin oMLX vérifié : conteneur LiteLLM docker-02 → DNS overlay `ollama-tailscale` (`172.29.2.27`) port 8000 → DNAT/SNAT existant sur docker-01 → Tailscale Mac `100.123.68.99:8000` → Serve → `127.0.0.1:8000`. Base LiteLLM `http://ollama-tailscale:8000/v1`.
- Depuis LiteLLM : `/v1/models` authentifié 200 ; sans clé, `/v1/models` et `/v1/chat/completions` 401. Configuration oMLX : `skip_api_key_verification=false`, `allow_unauthenticated_inference=false`.
- Clé oMLX existante réutilisée sans modification, transmise par stdin SSH, jamais par argument shell ni fichier temporaire contenant la clé. Stockage par API native `/credentials`, valeurs chiffrées en base LiteLLM avec le mécanisme de salt existant ; aucune lecture/écriture directe de cette base. Aucune clé inventée pour Ollama, qui conserve son fonctionnement sans authentification API native sur le chemin privé.
- Ollama : le nom HTTP `ollama-tailscale` provoque 403 avec le listener loopback et son contrôle `Host`. La source locale `server/routes.go`, `allowedHostsMiddleware`, explique ce refus. Le catalogue répond 200 avec un Host local ; toutefois l’adaptateur embeddings Ollama de LiteLLM installé ne transmet pas de headers personnalisés. Les trois entrées utilisent donc `http://172.29.2.27:11434`, adresse privée overlay acceptée nativement par Ollama. Aucun assouplissement du serveur. **Limite opérationnelle : si l’IP de la passerelle change à sa recréation, actualiser les trois `api_base` via `/model/update`.**
- La passerelle utilise `TS_TAILNET_TARGET_FQDN=macbook-pro-de-florian-3.tail06f5f5.ts.net`, avec containerboot, volume d’état persistant et restart `unless-stopped`. Le DNAT effectif vers `100.123.68.99` est inchangé après les tests. Recréation/reboot et persistance après redémarrage : NOT_RUN ; aucun arrêt imposé aux connexions existantes.

Risque résiduel accepté : transit large depuis l’overlay vers les services joignables du Mac et filtre Tailscale large. L’authentification oMLX est une protection applicative, pas un cloisonnement réseau. Aucun port Docker de la gateway LiteLLM publié. Les routes publiques/privées existantes restent inchangées ; `/v1/embeddings` reste accessible uniquement par le chemin privé existant. Aucun test depuis Internet externe effectué ; aucune nouvelle route publique créée. OpenWebUI exclu de la qualification finale à la demande de l’utilisateur.

### Tests et exploitation

- oMLX : catalogue 200 ; génération courte 200 ; SSE `text/event-stream`, 25 événements et `[DONE]`. Le premier plafond de test de 128 tokens limitait surtout le raisonnement ; un unique complément à 512 tokens a produit `2+2 equals 4.`, arrêt `stop`, 218 tokens de sortie. Aucun paramètre de raisonnement modifié.
- Ollama Qwen : `2 + 2 = 4.`, arrêt `stop` ; streaming 11 événements et `[DONE]`. Embeddinggemma : 200, 768 dimensions.
- Refus d’une clé sans droit oMLX : 403. Refus de muse-glimmer avec une clé autorisée seulement à Qwen/Embeddinggemma : 403, sans génération de muse-glimmer.
- Toutes les clés de validation étaient temporaires et limitées par liste explicite, puis supprimées via `/key/delete`. Contrôle final `/key/list` : **zéro clé cliente**. Les identités et comptes existants restent inchangés ; aucune clé cliente permanente créée.
- Journaux natifs `/spend/logs` : succès attribués au modèle Qwen3.6 et à la base oMLX privée, au chat Qwen avec `/api/chat` sur la passerelle privée, et à l’adaptateur Ollama pour les embeddings. Aucun succès fournisseur Cloud observé dans la fenêtre des validations. La configuration Swarm active conserve `router_settings.num_retries: 0`, `fallbacks: []`. Les quatre déploiements ont `max_retries: 0`, aucun modèle alternatif ou fallback ajouté ; FreeLLMAPI n’a reçu aucun modèle ni appel d’inférence de cette mission.
- Timeouts des déploiements : 300 secondes hors streaming, 3600 secondes pour le streaming ; aucun timeout global Nginx modifié. Indisponibilité du Mac non simulée. Le comportement exact du timeout de l’adaptateur embeddings natif, qui utilise un client partagé dans cette version, n’est pas qualifié.
- LiteLLM `/health/liveliness` et `/health/readiness` : 200. Quatre entrées relues par `/model/info`. Sources de fonctionnement consultées : [gestion native des modèles et credentials](https://docs.litellm.ai/docs/proxy/model_management), [paramètres Docker Tailscale](https://tailscale.com/docs/features/containers/docker/docker-params) ; comportement fournisseur vérifié dans le code installé.

Aucune modification des applications clientes, de FreeLLMAPI, d’OpenClaw ou du MCP. Aucun commit/push. Arrêt de la mission après ce raccordement ; muse-glimmer reste explicitement non qualifié en inférence.

## Mission catalogue et accès — 21 octobre 2026

État relu par API native après création à chaud de dix déploiements PostgreSQL : **13 alias actifs, un modèle local bloqué, zéro clé cliente**. Aucune écriture SQL, aucun redémarrage, changement d’image, de réseau ou d’application cliente. Sources : [catalogue filtré](catalogue-finalization.json), [tests ciblés](mission1-validation.json), [politiques préparées](client-policies.json). Les UUID locaux et leurs paramètres restent identiques avant/après. Muse-Glimmer reste enregistré avec `blocked=true` et absent de `/v1/models` ; aucune suppression, activation ou inférence.

### Catalogue final

Chaque ligne gratuite utilise exclusivement `http://freellmapi_api:3001/v1`, l’adaptateur `openai/` et le credential natif chiffré `freellmapi-internal`. Aucune clé fournisseur recopiée. `max_retries=0`, timeout 300 s et streaming 3600 s par déploiement. Aucune nouvelle politique de raisonnement. `CONFIGURED` décrit la configuration relue ; `VERIFIED` précise une preuve fonctionnelle bornée, sans qualifier toutes les capacités.

| Alias | Destination exacte | Type | État / preuve |
|---|---|---|---|
| `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit` | oMLX, identifiant inchangé | chat local | CONFIGURED ; génération/SSE VERIFIED antérieurement |
| `local-ollama/qwen3:4b-instruct` | Ollama `qwen3:4b-instruct` | chat local | CONFIGURED ; génération/SSE VERIFIED antérieurement |
| `local-ollama/embeddinggemma:latest` | Ollama `embeddinggemma:latest` | embeddings locaux | CONFIGURED ; vecteur 768 VERIFIED antérieurement ; route privée conservée |
| `local-ollama/muse-glimmer:30b-mlx` | entrée conservée bloquée | chat local désactivé | BLOCKED administrativement ; absent du catalogue actif |
| `free-groq/qwen3.8-27b` | `groq:qwen/qwen3.8-27b` | chat gratuit | CONFIGURED / VERIFIED via LiteLLM |
| `free-groq/gpt-oss-120b` | `groq:openai/gpt-oss-120b` | chat gratuit | CONFIGURED ; backend VERIFIED antérieurement, alias NOT_TESTED en génération |
| `free-openrouter/dots-3-note-preview:free` | `openrouter:dots-studio/dots-3-note-preview:free` | chat gratuit | CONFIGURED ; backend VERIFIED, alias individuel NOT_TESTED |
| `free-openrouter/north-mini-code:free` | `openrouter:cohere/north-mini-code:free` | chat gratuit | CONFIGURED ; backend VERIFIED, alias NOT_TESTED |
| `free-mistral/ministral-8b-2512` | `mistral:ministral-8b-2512` | chat gratuit | CONFIGURED ; backend VERIFIED, alias NOT_TESTED |
| `free-mistral/codestral-2508` | `mistral:codestral-2508` | chat gratuit | CONFIGURED ; backend VERIFIED, alias NOT_TESTED |
| `free/task-fast` | `auto:task-fast` | pool gratuit | CONFIGURED / streaming VERIFIED via LiteLLM |
| `free/task-coding` | `auto:task-coding` | pool gratuit | CONFIGURED ; backend VERIFIED antérieurement, alias NOT_TESTED |
| `free/task-reasoning` | `auto:task-reasoning` | pool gratuit | CONFIGURED ; backend génération VERIFIED, qualité non validée (calcul incorrect antérieur), alias NOT_TESTED |
| `free/task-long-context` | `auto:task-long-context` | pool gratuit | CONFIGURED ; backend petit document VERIFIED, grand contexte NOT_TESTED |

Les identifiants stricts fournisseur/modèle viennent des qualifications FreeLLMAPI existantes et des six scopes relus. Le catalogue OpenAI public utilise des noms courts différents (`dots3-note-preview`, `ministral-8b`, etc.) : ne pas remplacer les identifiants stricts par ces noms. Premier précontrôle arrêté sur cette différence avant toute création ; contrôle corrigé puis création unique, sans doublons.

Les quatre chaînes natives sont relues sans modification : trois membres chacune, exactement les six couples approuvés ; Google désactivé ; `balanced` et `Default` conservés, aucun ajout automatique. Ordre et membres détaillés dans le [rapport FreeLLMAPI](../freellmapi/README.md#application-validée--21-octobre-2026-vers-1000-cest). Aucun fallback LiteLLM sur ces pools, aucune route locale vers Cloud, aucun retry imbriqué ajouté. La lacune native de scopes embeddings/media FreeLLMAPI demeure ; ces alias sont de type chat, aucune qualification de ces autres endpoints.

### Capacités, contexte et confidentialité

Local : preuves antérieures réutilisées, paramètres modèle/contexte/KV/mémoire/raisonnement inchangés. La valeur 131072 renvoyée par les métadonnées LiteLLM oMLX n’est pas une capacité maximale qualifiée. Outils et raisonnement locaux non qualifiés ici ; budgets oMLX 512/2048/8192/16384 inchangés.

Gratuits : outils VERIFIED côté backend seulement pour GPT-OSS, North et Codestral ; outils Qwen/Dots/Ministral NOT_TESTED. Raisonnement de tous les modèles sans qualification générale ; échec sémantique connu du pool conservé. Streaming VERIFIED uniquement sur le chemin `free/task-fast` de cette mission ; autres alias NOT_TESTED en streaming. Contextes annoncés : Qwen 131072 documentaire / 262144 catalogue divergent ; GPT-OSS 131072 ; Dots 512000 ; North 256000 ; Ministral 262144 ; Codestral 256000 API / 128K fiche publique divergent. Aucun maximum qualifié, y compris pour les pools : utiliser uniquement si tous les membres satisfont le besoin. Aucune compression ou troncature ajoutée ; absence universelle de transformation par chaque adaptateur non qualifiée.

Quotas : Groq configuration 30 RPM / 8000 TPM, Qwen 250 RPD, GPT-OSS 1000 RPD ; OpenRouter gratuit 20 RPM / 50 RPD partagés, pas par modèle ; Mistral 2 RPM / 500000 TPM de configuration, quotas réels compte inconnus. Soldes actuels non garantis. Les preuves détaillées et divergences sont conservées dans le rapport FreeLLMAPI. Aucun benchmark supplémentaire.

Confidentialité : LOCAL reste sur le chemin privé du Mac ; FREE transmet aux fournisseurs Cloud membres de la chaîne, PAID transmettrait à OpenRouter et son fournisseur. Ne pas affecter automatiquement les tâches confidentielles aux pools Cloud. Métadonnées de compatibilité non inventées ; aucune suppression globale de paramètres.

### Payant : préparation inactive et budget

[Définitions en attente](paid-models.pending.json) enregistrées localement et sur docker-02, **non importées dans le routeur actif**, sans clé fictive. Le catalogue public [OpenRouter](https://openrouter.ai/api/v1/models), consulté le 21 octobre 2026, confirme les deux modèles exacts :

| Alias préparé | Modèle API | Prix USD / million tokens entrée / sortie / cache lu | Contexte / sortie annoncés | État |
|---|---|---|---|---|
| `paid-openrouter/deepseek-v4.1-flash-1017` | `deepseek/deepseek-v4.1-flash-1017` | 0,30 / 1,20 / 0,006 ; plages réduites 0,15 / 0,60 / 0,003 selon calendrier UTC enregistré | 1048576 / 393216 | BLOCKED ; génération NOT_TESTED |
| `paid-openrouter/glm-5.3` | `z-ai/glm-5.3` standard | 0,079 / 1,40 / 0,078 | 1048576 / 943718 | BLOCKED ; génération NOT_TESTED |
| `paid/task-advanced` | exclusivement `deepseek/deepseek-v4.1-flash-1017` | même modèle et mêmes prix | idem DeepSeek | BLOCKED ; génération NOT_TESTED |

Prix instantanés, non garantis pour une activation ultérieure ; prix d’écriture de cache non exposé. Outils, appels parallèles et raisonnement annoncés pour les deux ; raisonnement obligatoire annoncé pour GLM, facultatif pour DeepSeek. Streaming annoncé par l’[API OpenRouter](https://openrouter.ai/docs/api_reference/streaming), jamais testé ici. Fenêtres, outils, raisonnement, streaming et accès avec la clé dédiée : NOT_TESTED. Catalogue public ≠ disponibilité authentifiée ni succès fournisseur. Aucun remplacement Flash/FlashX/Prime, aucun fallback vers GLM ou autre modèle.

**CONFIGURED / VERIFIED par relecture :** équipe native unique `paid-openrouter-shared`, `max_budget=10.0`, `budget_duration=1mo`, `blocked=true`, `spend=0`, prochaine remise à zéro annoncée `2026-11-01T00:00:00Z`. Trois alias explicitement autorisés sur l’équipe, aucune clé cliente associée. Le créateur opérateur `default_user_id` est ajouté automatiquement comme administrateur natif ; aucune des identités clientes n’y est affectée. L’API `/team/new` a répondu 200 sur l’installation actuelle sans ajout de licence. Modification future du plafond par `/team/update`, même `team_id`, puis relecture ; ne pas multiplier les équipes ou budgets par client/modèle. [Documentation des budgets d’équipe](https://docs.litellm.ai/docs/proxy/team_budgets).

**BLOCKED avant activation :** clé dédiée non déposée, plafond fournisseur non vérifié, disponibilité authentifiée non vérifiée, décompte des prix/cache variables et refus à épuisement NOT_TESTED. Une équipe limite ses clés rattachées, pas les appels opérateur/master ou les clés hors équipe : ce seul objet ne garantit pas tous les appels payants. Le plafond fournisseur partagé sur l’unique clé dédiée doit donc être vérifié, puis le suivi LiteLLM qualifié avant déblocage. Les compteurs asynchrones ne garantissent pas une coupure au centime. Aucun test facturable, dépense artificielle ou manipulation de base effectué pour prétendre lever ce blocage.

OpenRouter expose `limit=10` USD et `limit_reset=monthly`, vérifiables par [GET /api/v1/key](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key). La [gestion des clés](https://openrouter.ai/docs/api/api-reference/api-keys/update-keys) permet de modifier le plafond. Une clé de gestion serait nécessaire pour modifier par API une autre clé ; elle n’est pas demandée ici : régler la clé dédiée dans la console. Ne pas réutiliser la clé Copilot ou la clé gratuite FreeLLMAPI. Aucune recharge automatique activée.

### Dépôt sécurisé manuel de la clé dédiée

Sur docker-02 : dossier `secrets/` root:root 0700 ; emplacement réservé `secrets/openrouter-paid-api-key` root:root 0600, vide à la préparation, jamais monté ni enregistré comme credential actif. Le fichier de dépôt n’est pas une clé fictive utilisée en production. Script [deposit-openrouter-key.sh](deposit-openrouter-key.sh), installé root:root 0700 et contrôlé avec `sh -n` ; saisie masquée par `systemd-ask-password`, fichier temporaire 0600 remplacé après saisie réussie. Ne pas saisir la clé dans le chat, les arguments ou un `export` journalisé.

1. Dans la console OpenRouter, créer une clé **dédiée LiteLLM**, plafond **10 USD**, renouvellement **mensuel**. Conserver les autres usages sur leurs propres clés.
2. Depuis votre terminal, lancer (commande sans secret) :

```sh
ssh -t root@docker-02 /srv/docker-local/compose/litellm/deposit-openrouter-key.sh
```

3. Coller la clé uniquement dans la saisie masquée puis valider. Le script ne contacte aucun fournisseur et n’active rien. Informer ensuite Codex que le dépôt est terminé ; la validation non générative pourra lire ce fichier en mémoire, vérifier `/key` et l’accès aux modèles, puis enregistrer le credential natif chiffré `openrouter-paid`. Ne pas transmettre la clé elle-même.

### Permissions et recette

Identités Codex, MCP, OpenClaw Pro et Perso conservées séparées, sans clé permanente distribuée. Politiques LOCAL/FREE explicites préparées dans le JSON, non attribuées aux applications ; PAID correspond à l’équipe bloquée, sans affectation cliente. `access_groups` facilite le regroupement, mais ne remplace pas une liste explicite sur chaque future clé et ne neutralise pas une wildcard administratrice.

Clé temporaire `llm_api`, durée 10 minutes, limitée à Qwen gratuit et `free/task-fast` : catalogue filtré exactement à ces deux alias ; refus **403** pour oMLX, Muse-Glimmer, Codestral non accordé, pool payant et GLM payant. Ces deux derniers refus prouvent l’absence de droit de la clé temporaire, pas le fonctionnement d’un modèle payant inexistant dans le routeur. Clé révoquée par `/key/delete` 200 ; `/key/list` final zéro. Aucune clé payante de test émise.

Génération individuelle gratuite HTTP 200, contenu non vide, 17 tokens entrée / 2 sortie. Pool gratuit en SSE HTTP 200, 21 événements JSON, contenu non vide et `[DONE]`. Journal natif FreeLLMAPI : id 19 à 09:08:56 UTC, Groq Qwen ; id 20 à 09:08:59 UTC, OpenRouter Dots ; succès, une tentative chacun. LiteLLM remplace le champ `model` par son alias et ne restitue pas `_routed_via` ici : le modèle réellement exécuté se retrouve dans le journal natif, corrélé par heure/source/séquence. Le futur MCP ne devra pas considérer l’alias comme la preuve du fournisseur choisi ; corrélation stable par identifiant à qualifier.

Santé finale LiteLLM `healthy`, DB `connected` ; FreeLLMAPI `ok`, trois upstreams prêts. Configuration active relue : retries 0, fallbacks vides, journalisation des messages désactivée, prompts exclus des spend logs, credentials clientes interdits. Aucun credential FreeLLMAPI ni marqueur synthétique de refus dans les logs gateway des 20 dernières minutes ; contrôle borné, pas audit universel. Anciennes preuves TLS/ACL/persistance réutilisées ; aucun redémarrage DB pour les répéter.

Mission MCP **non commencée**. Préparation LOCAL/FREE disponible ; PAID reste BLOCKED jusqu’au dépôt, aux contrôles fournisseur/budget et à une future autorisation explicite limitée. Aucun mécanisme de confirmation ponctuelle implémenté dans LiteLLM : aucune clé cliente autorisée au payant ne sera émise dans cette mission. Aucun changement FreeLLMAPI, Codex, OpenClaw, MCP, oMLX, Ollama, Tailscale, Traefik ou DNS ; aucun commit/push.

### Contrôle de la clé déposée — 21 octobre 2026

**BLOCKED : plafond fournisseur incompatible avec la décision validée.** Fichier déposé root:root 0600, non vide ; secret lu uniquement en mémoire sur docker-02, jamais affiché. GET authentifié OpenRouter `/api/v1/key` : HTTP 200, `limit=50`, `limit_reset=weekly`, `limit_remaining=20.612831758`, `usage=98.436141889`, `usage_monthly=98.436141889`, `is_management_key=false`, `is_free_tier=false`. La clé fonctionne pour l’authentification, mais n’est pas démontrée dédiée à LiteLLM et ne respecte pas 10 USD/mois. Aucun nom d’application existante déduit de ces compteurs.

GET `/api/v1/models/user` : HTTP 200, références exactes `deepseek/deepseek-v4.1-flash-1017` et `z-ai/glm-5.3` présentes, contexte annoncé 1048576 chacune. Prix authentifiés au moment du contrôle, USD/million tokens entrée/sortie/cache lu : DeepSeek **0,049 / 0,375 / 0,001176** ; GLM **0,079 / 1,40 / 0,078**. Ces tarifs authentifiés diffèrent de l’instantané public DeepSeek précédent : ne pas considérer celui-ci comme un tarif garanti. Aucune génération réalisée ; disponibilité effective d’inférence NOT_TESTED.

Arrêt avant enregistrement du credential et import des trois routes payantes. Équipe LiteLLM précédemment créée toujours laissée bloquée ; aucun déblocage, aucune clé cliente émise, aucune modification des autres services. La clé d’inférence fournie n’est pas une clé de gestion : aucun essai d’élévation ou de modification du plafond fournisseur par cette clé.

Action minimale : créer dans la console OpenRouter une **clé distincte dédiée LiteLLM**, `limit=10`, `limit_reset=monthly`, puis remplacer le dépôt par le même script masqué. Ne modifier la clé existante que si son exclusivité LiteLLM est confirmée et si ses autres usages sont compris. Reprendre ensuite les contrôles non génératifs ; la génération reste soumise à l’accord explicite sur le modèle et le coût.


### Rectificatif utilisateur : plafond côté LiteLLM — 21 octobre 2026

Cette décision remplace le blocage précédent lié au plafond fournisseur : **utiliser la clé déposée existante**, conserver son réglage OpenRouter et appliquer le plafond partagé dans LiteLLM. Budget d’équipe `paid-openrouter-shared` modifié via `/team/update`, puis relu : **40 USD / `1mo`**, `spend=0`, prochaine remise à zéro `2026-11-01T00:00:00Z`. LiteLLM comptabilise en USD ; ce montant n’est pas présenté comme une conversion exacte de 40 EUR. Le fournisseur conserve 50 USD/semaine et les dépenses antérieures : ce plafond fournisseur n’est pas celui de LiteLLM et ne sert plus de condition d’intégration après le rectificatif utilisateur.

Credential natif **`openrouter-paid` enregistré**, clé chiffrée en PostgreSQL, aucun secret affiché. Trois déploiements enregistrés, correspondances relues :

| Alias | Destination | UUID | État |
|---|---|---|---|
| `paid-openrouter/deepseek-v4.1-flash-1017` | `openrouter/deepseek/deepseek-v4.1-flash-1017` | `da5756d6-eb2d-4659-9eac-c14de0f3bab2` | CONFIGURED, BLOCKED |
| `paid-openrouter/glm-5.3` | `openrouter/z-ai/glm-5.3` | `d5d88408-1eaa-4a3f-9da6-a41b458b2d8c` | CONFIGURED, BLOCKED |
| `paid/task-advanced` | exclusivement `openrouter/deepseek/deepseek-v4.1-flash-1017` | `5f76d89e-fbad-46f9-b3f6-412ef557a4ea` | CONFIGURED, BLOCKED |

Attention version installée : `model_info.blocked=true` dans `/model/new` est ignoré à la création. Le contrôle de relecture l’a détecté ; les trois déploiements ont ensuite été bloqués par l’API native **`/model/block`** et relus `blocked=true`. Aucune clé cliente n’existait durant cet intervalle, aucune génération effectuée. L’équipe reste également bloquée. Catalogue actif final : 13 alias LOCAL/FREE, aucune route PAID et aucun Muse-Glimmer ; `/key/list` : zéro clé cliente ; santé `healthy`, DB `connected`. Réutiliser `/model/block` pour ce besoin, sans supposer que le champ du payload de création suffit.

Authentification OpenRouter et présence des deux références exactes dans `/models/user` VERIFIED lors du contrôle précédent. Génération facturable **NOT_TESTED**, aucun coût de génération approuvé. Aucune clé permanente ou temporaire autorisée au payant émise. L’enregistrement des modèles ne constitue pas leur activation ni une preuve de décompte : prix/cache variables, cumul réel et coupure à épuisement restent NOT_TESTED. Le budget d’équipe s’applique aux futures clés rattachées à cette équipe ; il ne bride pas automatiquement une clé hors équipe ni l’opérateur/master. Les routes restent bloquées pour ne pas créer un accès payant qui contourne la politique d’accord explicite. Aucun raccordement client/MCP engagé.


### Activation administrative autorisée — 21 octobre 2026

**État courant : CONFIGURED / VERIFIED administrativement.** Sur clarification explicite de l’utilisateur, la confirmation par tâche relève du futur MCP et ne justifie pas le blocage administratif des modèles. Appels natifs `/model/unblock` sur les trois UUID payants et `/team/update` avec `blocked=false` pour `paid-openrouter-shared`. Relecture indépendante : les trois alias sont `blocked=false` et présents dans `/v1/models` ; 16 alias actifs au total. `paid/task-advanced` pointe exclusivement sur DeepSeek V4.1 Flash 1017, aucun fallback ajouté. Muse-Glimmer reste bloqué et absent du catalogue actif.

Budget partagé relu **40 USD/mois**, prochaine remise à zéro annoncée `2026-11-01T00:00:00Z`, dépense équipe 0. Équipe PAID active, aucune clé cliente émise (`/key/list` : zéro). Santé `healthy`, DB `connected`. Preuve filtrée : [paid-activation.json](paid-activation.json). Les sections BLOCKED antérieures décrivent les étapes historiques et sont remplacées par cette décision pour l’activation administrative.

Aucune génération facturable effectuée : **inférence, décompte réel et coupure à épuisement restent NOT_TESTED**. Le contrôle de confirmation par tâche n’est pas implémenté ici ; il sera traité dans la mission MCP, non commencée. Le budget d’équipe ne s’applique qu’aux clés qui lui seront rattachées, pas automatiquement aux appels master/opérateur ou aux clés hors équipe ; les futures autorisations devront donc imposer ce rattachement côté serveur. Activation administrative ne signifie ni distribution de clé, ni preuve d’inférence réussie, ni qualification de l’approbation MCP. Aucun changement des autres services.
