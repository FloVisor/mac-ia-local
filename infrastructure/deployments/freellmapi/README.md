# FreeLLMAPI — déploiement du 21 octobre 2026

**DÉPLOYÉ, privé par ACL. Actualisation du 21 octobre 2026 : quatre chaînes CONFIGURED et appelées avec succès, six modèles autorisés par scopes natifs de chat.** `Default` et `balanced` conservés. Trois tests de contenu corrects ; le test de raisonnement a généré une réponse arithmétique fausse. Aucune capacité 128K/256K garantie. Voir le bilan d’application en fin de rapport.

Les sections de déploiement et de finalisation de l’exposition ci-dessous sont historiques : leurs mentions « zéro fournisseur » et « inférence NOT_RUN » décrivent ces étapes initiales. Le bilan d’application en fin de rapport fait foi pour l’état actuel ; la qualification et ses propositions intermédiaires sont conservées comme historique.

## Implantation

- Stack `freellmapi`, service `freellmapi_api`, une réplique contrainte à `docker-02`.
- Image `ghcr.io/tashfeenahmed/freellmapi:v0.16.6@sha256:e8df41162f807488ff01309a23f37411e7815c4128db14deb31a00feaa183534`, manifeste Linux amd64 téléchargé et vérifié.
- Overlay externe existant `TRAEFIK_BACKEND`, attachable, non internal, inchangé.
- API interne LiteLLM : `http://freellmapi_api:3001/v1` depuis ce même overlay (alias supplémentaire `freellmapi-internal`). Ce DNS Docker n'est pas une adresse utilisable directement depuis une VM extérieure.
- Dashboard et alternative API extérieure au Swarm : `https://freellmapi.gangneux.org/` et `https://freellmapi.gangneux.org/v1`, réseaux autorisés uniquement.
- Aucun port publié, aucun socket Docker, aucune option privilégiée, aucune limite de RAM ou heap ajoutée.
- Entrypoint officiel conservé derrière un chargeur de secret ; processus applicatif PID 1 UID/GID 1000. Un `docker exec` par défaut démarre quant à lui en root.

## Fichiers, données et secrets

Sur docker-02 : `/srv/docker-local/compose/freellmapi/` contient `stack.yml`, `secret-entrypoint.sh`, `traefik.yml`, les résultats `initial-validation.json` et `final-validation.json`.

Volume local externe `freellmapi_data`, monté à `/app/server/data`, chemin hôte `/srv/docker-local/docker/volumes/freellmapi_data/_data` sur ext4. Base observée `freeapi.db`, fichiers WAL/SHM inclus dans le répertoire persistant. Un seul écrivain, update et rollback `stop-first`, grâce arrêt 30 s. Données dépendantes de docker-02 : aucune HA automatique ni sauvegarde supplémentaire créée.

Secret Swarm durable `freellmapi_encryption_key_v1` (64 caractères hexadécimaux aléatoires), lu au démarrage et transmis à l'entrypoint officiel par environnement. Copie de conservation : `/srv/docker-local/compose/freellmapi/secrets/encryption-key`.

Identifiants administrateur : `/srv/docker-local/compose/freellmapi/secrets/admin-credentials.json` ; compte technique `admin@freellmapi.gangneux.org`. Clé d'inférence dédiée au profil `LiteLLM` id 1 : `/srv/docker-local/compose/freellmapi/secrets/litellm-api-key`. Ces trois fichiers root sont hors Git, mode 0600, répertoire 0700. Aucun contenu de secret dans les sources ou ce rapport.

Bootstrap `FREEAPI_CONFIG_PATH` appliqué avant ouverture HTTP, puis retiré du service après initialisation. Secret Swarm bootstrap, fichier JSON bootstrap et surcharge Compose supprimés. Ne pas réinitialiser l'administrateur et ne jamais régénérer la clé de chiffrement au redéploiement.

Conserver ensemble, avec protection adaptée : tout le volume de données, la clé de chiffrement, les identifiants administrateur et la clé LiteLLM. La perte de la clé de chiffrement rend les secrets applicatifs chiffrés irrécupérables.

## Filtrage et fidélité

Fournisseur Traefik actif `file`, nouvelle configuration dédiée `/srv/docker-shared/traefik/dynamic/freellmapi.yml`. Aucun changement de règle globale ou d'autre application. TLS existant réutilisé (`tls: {}`), certificat vérifié sans exception.

Middleware existant `private-networks@file`, identique à Home Assistant, sur tous les chemins : `192.168.200.0/21`, `2a01:e0a:8ce:68c0::/61`, `fd72:6a3c:9e10:100::/64`. L'ACL utilise le pair socket, sans stratégie X-Forwarded-For. Observation des connexions dans Traefik : client IPv4 `::ffff:192.168.202.131` et client IPv6 `2a01:e0a:8ce:68c2::191`, dans les plages autorisées. Une origine overlay non autorisée obtient 403 même avec X-Forwarded-For privé usurpé.

Application `TRUST_PROXY=172.29.2.2/32` : seule l'IP overlay fixe de Traefik est approuvée ; à vérifier si Traefik change d'adresse. `DASHBOARD_ORIGINS=https://freellmapi.gangneux.org`. Compression désactivée, normalisation d'images désactivée, cache de réponse désactivé. Aucun ajout de mémoire partagée ou handoff ; handoff applicatif par défaut off. Les mécanismes internes natifs de compatibilité du projet ne sont pas modifiés.

Authentification `/v1` obligatoire native ; clé profil LiteLLM distincte de la session admin, sans systemPrompt. Fournisseurs à configurer manuellement via le dashboard. Ni compte externe, ni abonnement, ni cookie d'une autre application utilisé.

## Résultats du déploiement initial

- Une tâche courante sur docker-02, `healthy`, mise à jour `completed`, ancienne tâche arrêtée avant démarrage de la nouvelle.
- `/api/ping` 200 ; DNS Docker résolu depuis HomeAssistant sur docker-01 et ping inter-nœuds 200.
- Sortie Internet HTTPS du conteneur vers github.com : 200.
- HTTPS dashboard IPv4 et IPv6 : 200, vérification certificat 0, résolution forcée utilisée puisque le DNS manque.
- Administration sans session : 401 ; administration avec clé LiteLLM : 401.
- Inférence sans clé et clé incorrecte : 401 ; `/v1/models` avec clé LiteLLM : 200.
- `needsSetup=false`, tentative setup : 409, login administrateur fonctionnel après redéploiement sans bootstrap.
- Profil LiteLLM conservé après redéploiement, zéro fournisseur configuré ; pas de boucle de redémarrage observée.
- PID 1 UID/GID 1000 ; accès données en écriture vérifié sous UID 1000 ; base et WAL/SHM présents.
- Service ports `null`, ressources `{}`, seul secret de chiffrement monté ; aucune limite mémoire.
- Accès Traefik depuis l'overlay non autorisé : 403 sur `/`, `/api/ping`, `/v1/models`, même avec X-Forwarded-For usurpé.
- Home Assistant HTTPS reste 200 ; Traefik sert les deux routes sans redémarrage.
- Mémoire ponctuelle après redéploiement : **51,98 MiB** (`docker stats`, mémoire hôte affichée 15,62 GiB), aucune extrapolation.

Aucun point de test externe à Internet utilisé : les contrôles locaux, l'absence de publication et l'ACL constatée ne constituent pas une preuve de refus depuis Internet. Pas de test d'inférence ou de streaming fournisseur faute de clé autorisée.

## DNS restant

Actualisation après finalisation LiteLLM, le 21 octobre 2026 : le nom se résout désormais via le CNAME public préexistant `traefik-10.gangneux.org`, vers A `82.67.206.214` et AAAA `2a01:e0a:8ce:68c5::10` (résolveur système et 1.1.1.1). Aucune écriture DNS publique effectuée. La vue interne dédiée reste à créer. Aucun accès d'administration DNS dédié identifié ; aucun secret d'autres applications ou ACME recherché ou réutilisé.

Créer dans le DNS interne :

```text
freellmapi.gangneux.org.  A     192.168.205.10
freellmapi.gangneux.org.  AAAA  2a01:e0a:8ce:68c5::10
```

Ces enregistrements sont préparés dans `dns-internal.zone`, pour la vue interne uniquement. Ces adresses sont celles du Traefik actif observé. Le filtrage reste requis indépendamment du DNS. Contrôle immédiat en attendant (certificat toujours vérifié) :

```sh
curl --resolve freellmapi.gangneux.org:443:192.168.205.10 https://freellmapi.gangneux.org/api/ping
```

## Finalisation de l’exposition LiteLLM — 21 octobre 2026

FreeLLMAPI reste privé sur **tous** ses chemins et sans port publié. Seul le routage LiteLLM a changé : trois API précises publiques, tout le reste privé/VPN. Depuis l'overlay non autorisé, `/`, `/api/ping` et `/v1/models` FreeLLMAPI restent à 403 même avec un X-Forwarded-For privé usurpé. Aucun secret connu ni marqueur synthétique retrouvé dans ses journaux contrôlés sur 15 minutes. Aucun compte, profil, clé, fournisseur, modèle ou configuration FreeLLMAPI modifié.

Le backend LiteLLM reste `http://freellmapi_api:3001/v1`, identifiant natif `freellmapi-internal` en base LiteLLM. Résolution, connectivité et authentification du profil dédié déjà validées lors du déploiement LiteLLM, sans double /v1 ; résultats réutilisés, pas d'inférence lancée. Dernier état fournisseur constaté : zéro fournisseur configuré. Les 275 entrées du catalogue ne sont pas une autorisation ni une preuve de disponibilité. Il reste à configurer un fournisseur gratuit approuvé, puis qualifier une première inférence avant tout raccordement d'application.

Le cookie JavaScript non HttpOnly du dashboard **LiteLLM** est accepté uniquement dans son administration privée ; aucun correctif XSS ou HttpOnly revendiqué. Aucune exposition publique de l'administration FreeLLMAPI. Test depuis Internet externe NOT_RUN ; les tests overlay/LAN ne le remplacent pas. La chaîne complète reste non qualifiée.

Preuves de finalisation : `../litellm/evidence/exposure-20261021/`.

## Exploitation ciblée

Depuis le Mac :

```sh
ssh root@docker-02 'docker service ps freellmapi_api; docker service inspect freellmapi_api --format "{{json .UpdateStatus}}"'
ssh root@docker-02 'cd /srv/docker-local/compose/freellmapi && docker stack deploy -c stack.yml freellmapi'
# Forcer un remplacement contrôlé pour une vérification ciblée :
ssh root@docker-02 'docker service update --force freellmapi_api'
# Arrêt sans effacer données/secrets/routage :
ssh root@docker-02 'docker service scale freellmapi_api=0'
# Reprise :
ssh root@docker-02 'docker service scale freellmapi_api=1'
```

Les sources du répertoire sont les copies reproductibles du déploiement final. Les secrets et données restent uniquement sur le cluster. Aucun commit ou push effectué.

Sources retenues : [version v0.16.6](https://github.com/tashfeenahmed/freellmapi/releases/tag/v0.16.6), fichiers Docker, installation, variables et sécurité de ce tag ; sources serveur du même tag consultées pour bootstrap, sessions, profils clients et arrêt propre.


## Qualification FreeLLMAPI — 21 octobre 2026 (avant application validée)

### Périmètre et état final vérifié

Interventions sur l’installation existante v0.16.6 de `docker-02`, par API native authentifiée ; aucun redéploiement, changement de version ou redémarrage. Tests de génération via FreeLLMAPI `/v1/chat/completions`, sans passage par LiteLLM. TLS vérifié. Aucun secret publié.

Avant réception du rectificatif, les trois clés actives avaient été limitées aux trois modèles initiaux ; le profil `production-free` id 2 avait été créé et activé avec Groq Qwen → OpenRouter Dots → Mistral Ministral, et la stratégie passée de `balanced` à `priority`. Ces changements avaient été appliqués, pas seulement préparés.

**Après accord explicite de restauration**, état relu et vérifié :

- Profil actif `Default` id 1 ; liste des modèles identique à la capture avant intervention. Profil de mission `production-free` supprimé par l’API native, sans suppression de modèle ni de clé.
- Stratégie `balanced`, exploration désactivée ; pondérations fiabilité 0,50 / vitesse 0,25 / intelligence 0,25. Scopes des clés Mistral, Groq et OpenRouter remis à `null` (non restreints).
- Google reste désactivé ; ses anciens cooldowns sont conservés. Aucune nouvelle tentative Google.
- Corrections de quotas conservées et relues : Qwen Groq TPM 70 000 → 8 000 et TPD non renseigné → 200 000 ; GPT-OSS Safeguard RPM 30 → 3 et TPM 8 000 → 2 000. Overrides natifs persistants ; pas de modification des autres limites.
- `/readyz` : `status=ok`, `ready_upstreams=3`. Ce résultat ne qualifie pas chaque entrée du catalogue.

Aucune modification de LiteLLM, de PostgreSQL, de ses alias ou clés pendant cette mission ; aucun alias `free-default`, aucune clé LiteLLM temporaire, aucun test de bout en bout via LiteLLM. Aucun changement Codex, OpenClaw, MCP ou oMLX. Aucun changement embeddings/media ; aucun profil final créé. Les modifications d’exposition LiteLLM décrites plus haut appartiennent à l’étape historique précédente.

L’automatisme `Default` d’origine reste donc large : **ce n’est pas une liste de modèles gratuits qualifiés**. La restauration demandée ne vaut pas qualification du routage automatique existant.

### Tableau de qualification

`VERIFIED` signifie génération réellement réussie sur un petit test ; pas une mesure générale de qualité. `UNTESTED` signifie absence de test de cette capacité ou de cet alias. `BLOCKED` décrit le refus observé sur la route et à l’instant testés. Aucun nouveau `RATE_LIMITED` ou `UNSUPPORTED` démontré dans cette campagne. Toutes les fenêtres ci-dessous sont **annoncées**, sans validation de leur pleine capacité.

| Fournisseur | Modèle | Gratuit confirmé | Inférence | Outils | Contexte annoncé (tokens) | Quotas | Recommandation |
|---|---|---|---|---|---|---|---|
| Groq | `qwen/qwen3.8-27b` | Plan gratuit documenté ; compte utilisé avec succès | VERIFIED, preuve initiale réutilisée | UNTESTED | 131 072 documentation ; catalogue local 262 144 divergent | G ; RPD local prudent 250 | Rapide / repli texte ; corriger le contexte après accord |
| OpenRouter | `dots-studio/dots-3-note-preview:free` | Oui, suffixe gratuit, prix API 0/0 et réponse coût 0 | VERIFIED, réponse `OK` via FreeLLMAPI | UNTESTED ; outils annoncés | 512 000 | O | Texte long candidat ; pas de garantie de disponibilité fournisseur |
| Mistral | `ministral-8b-2512` | Oui, utilisateur : Free/Experiment, paiement à l’usage désactivé | VERIFIED, preuve initiale réutilisée | UNTESTED ; outils annoncés | 262 144 API du compte | M | Repli texte inter-fournisseur |
| Groq | `openai/gpt-oss-120b` | Plan gratuit documenté ; appel réussi | VERIFIED | VERIFIED, appel structuré correct | 131 072 | G | Raisonnement / repli développement ; petit test seulement |
| OpenRouter | `cohere/north-mini-code:free` | Oui, prix API 0/0 et réponse coût 0 | VERIFIED | VERIFIED, appel structuré correct | 256 000 | O | Développement et repli de raisonnement |
| Mistral | `codestral-2508` (`codestral-latest`) | Oui, confirmation utilisateur ci-dessus | VERIFIED sur `codestral-2508` ; alias `latest` UNTESTED en génération | VERIFIED sur version fixe | 256 000 API du compte ; fiche publique 128K divergente | M | Développement ; privilégier l’identifiant fixe testé |
| Mistral | `mistral-code-latest` | Même compte et backend gratuit confirmé | UNTESTED sous cet alias ; correspondance API à `codestral-2508` vérifiée | UNTESTED sous cet alias ; backend testé | 256 000 API du compte | M, partagé avec Codestral | Ne pas compter comme modèle ou fallback indépendant |
| OpenRouter | `nvidia/nemotron-3-super-120b-a12b:free` | Oui, prix API 0/0 ; disponibilité non acquise | BLOCKED : HTTP 404 fournisseur, un appel | UNTESTED ; outils annoncés | 262 144 API OpenRouter ; catalogue local 1 000 000 divergent | O | Exclure des propositions tant que disponibilité non résolue |
| Google | `gemini-3.7-flash`, `gemini-3.8-flash`, `gemini-flash-latest` | Non établi pour le projet refusé | BLOCKED : HTTP 403 projet | UNTESTED | Non retenu | Cooldown local 24 h ; aucun quota fournisseur prouvé | Conserver désactivé |

Présélection : cinq identifiants supplémentaires, quatre backends distincts en comptant Nemotron ; aucune sixième candidature nécessaire. Les trois générations nouvelles réussies portent sur GPT-OSS, North et Codestral. Aucun score « Intelligence » utilisé comme preuve.

### Quotas : distinguer documentation, configuration et observation

- **G — Groq** : documentation Free Plan GPT-OSS 120B / Qwen : 30 RPM, 1 000 RPD, 8 000 TPM, 200 000 TPD. Le catalogue conserve Qwen à 250 RPD, plus prudent. Réponse GPT-OSS observée à 07:49:22 UTC : en-têtes agrégés rapportés par l’application, limite requêtes 1 000 / restant 1 000 et tokens 8 000 / restant 8 000. Cela ne prouve pas une allocation indépendante pour chaque modèle ni un solde à la seconde présente. Le GET direct Groq `/models` avait retourné 403 lors du diagnostic initial : pas de répétition ni de contournement ; l’inférence par FreeLLMAPI a réussi.
- **O — OpenRouter** : clé authentifiée `is_free_tier=true`. À 07:35 UTC, compteur natif des modèles gratuits : 1 utilisé / 50 par jour, 49 restants **avant les appels suivants**. Limite locale 20 RPM / 50 RPD, partagée entre modèles gratuits ; aucun TPM fiable exposé. Ne pas multiplier 50 par modèle. Le plafond de clé à 1 dollar n’est ni un crédit de portefeuille ni une autorisation de payer. Les modèles `:free` retenus annoncent prix entrée/sortie nuls ; les deux réponses Dots/North réussies indiquent coût 0.
- **M — Mistral** : Free/Experiment et paiement à l’usage désactivé confirmés explicitement par l’utilisateur avant le test Codestral. Catalogue local : 2 RPM / 500 000 TPM ; RPD/TPD inconnus. Ce sont des valeurs de configuration, **pas des quotas réels de compte prouvés** ; pas d’en-têtes de quota exploitables observés. API du compte `/v1/models` accessible. La réponse de génération ne fournit pas de preuve de facture nulle ; `service_tier=standard` ne constitue pas un prix. Codestral, son alias Mistral Code et les autres modèles Mistral ne constituent pas des pools indépendants.

Les quotas réels non exposés restent **À valider** dans les consoles du compte. Ni valeurs statiques ni readiness ne remplacent une preuve de disponibilité ou de quota.

### Preuves des tests courts

Données synthétiques, aucun test 128K, aucune donnée métier. Pour les nouveaux candidats : calcul de 6×7 et fonction Python `add(a,b)`, transmis par l’outil `submit_result`, sortie plafonnée à 512 tokens, non streaming. Pour GPT-OSS, effort de raisonnement `low`. Les trois succès donnent 42 et une fonction d’addition correcte ; arguments JSON et AST vérifiés localement, sans exécuter le code généré ni relancer l’inférence.

| UTC le 21/10/2026 ; requête native | Cible stricte FreeLLMAPI | Résultat | Temps client total | Tokens entrée / sortie |
|---|---|---|---|---|
| 07:49:22 ; id 11 | `groq:openai/gpt-oss-120b` | 200, `finish_reason=tool_calls`, VERIFIED | 0,525 s | 163 / 77 |
| 07:49:23 ; id 12 | `openrouter:nvidia/nemotron-3-super-120b-a12b:free` | 404, BLOCKED | 0,303 s | Journal : 99 / 0 ; pas une consommation facturée établie |
| 07:49:28 ; id 13 | `openrouter:cohere/north-mini-code:free` | 200, `finish_reason=tool_calls`, VERIFIED | 4,739 s | 74 / 272 |
| 07:51:57 ; id 14 | `mistral:codestral-2508` | 200, `finish_reason=tool_calls`, VERIFIED | 0,690 s | 116 / 31 |

Chaque requête id 11–14 comporte **une seule tentative** dans le journal natif ; modèle retourné et `_routed_via` conformes pour les succès. Résolution stricte `fournisseur:modèle` vérifiée dans le code installé : aucun fallback vers un autre modèle ou fournisseur dans ces tests. Ces latences ponctuelles ne sont pas un benchmark comparatif. Le champ reasoning de North est incohérent avec ses tokens de sortie ; ne pas additionner les deux.

Nemotron : erreur source exacte `OpenRouter API error 404: Provider returned error`. FreeLLMAPI la transforme en « model not found or removed upstream ». Le catalogue OpenRouter contient pourtant encore ce modèle : la disparition globale n’est **pas démontrée**. Arrêt après ce refus unique, sans test payant alternatif ni suppression de l’entrée.

Preuves initiales réutilisées : Qwen id 9 à 07:35:02 UTC (13/4 tokens, test natif réussi) ; Ministral id 8 à 07:35:02 (4/4, test natif réussi), précédés d’inférences dashboard réussies ids 6 et 7. Dots id 10 à 07:35:06 (18/44, une tentative, réponse `OK`, coût 0). Le test direct Dots plafonné à 64 tokens avait produit un contenu nul avec `finish_reason=length` : il n’est pas compté comme succès sémantique. La réponse historique « pas de fournisseur » n’est pas attribuable avec certitude à une cause précise, faute de corps conservé.

Captures filtrées locales non versionnées : `artifacts/freellmapi-finalization/{before.json,candidates.jsonl,restored.jsonl,qualification-preflight.jsonl,semantic-checks.json}` ; contrôle AST Codestral complémentaire effectué sur la réponse conservée. Le fichier temporaire distant de préflight a été supprimé. Aucun commit/push.

### Anomalies établies et limites logicielles

1. **Google : refus de projet, pas quota prouvé.** Trois générations initiales donnent `Google API error 403: Your project has been denied access. Please contact support.` Le dashboard utilisateur confirme un projet limité, sans niveau de quota disponible ni facturation. Le statut de clé « healthy » ne prouve pas le droit d’inférer. Dans v0.16.6, `isModelAccessForbiddenError` classe largement les 403 ; `cooldownDecisionForError` applique 24 h, puis le traitement des routes épuisées peut renvoyer un 429. Cela transforme un refus d’accès en apparence de limitation. Cooldowns initiaux jusqu’au 22 octobre vers 07:24–07:27 UTC conservés ; aucune preuve de correction amont vérifiée, aucun patch déployé.
2. **Scopes incomplets hors chat.** Le routeur chat respecte `model_scope_json`, mais `reserveProviderCredential` pour embeddings/media ne l’impose pas. Une restriction de clé seule ne garantit donc pas une liste autorisée pour tous les endpoints. Aucun correctif applicatif déployé, aucune désactivation embeddings/media effectuée. Toute future politique « uniquement ces modèles » doit traiter ce point explicitement.
3. **Catalogue ≠ autorisation.** Le champ de disponibilité de la liste de modèles considère notamment la présence d’une clé active par plateforme ; certaines listes de chaînes ne filtrent pas les scopes comme le routeur. Une entrée annoncée disponible n’établit ni l’autorisation exacte ni un succès d’inférence.
4. **Métadonnées divergentes.** Qwen 262 144 local contre 131 072 documentés ; Nemotron 1 000 000 local contre 262 144 API ; Codestral 256 000 API du compte contre 128K fiche publique. Aucune capacité maximale testée, aucune correction supplémentaire de contexte appliquée avant validation.
5. **Incident Groq historique.** La mention « All models exhausted: 2 routes checked » ne peut pas être reliée à deux tentatives persistées identifiées ; ne pas inventer leurs modèles ni attribuer à un quota sans preuve. Les succès Qwen et GPT-OSS attestent seulement leur fonctionnement aux instants testés.

### Quatre chaînes proposées — NON CRÉÉES, NON APPLIQUÉES

Tous les modèles ci-dessous ont une génération VERIFIED. Seuls GPT-OSS, North et Codestral ont les outils VERIFIED. Les chaînes elles-mêmes, leurs transitions, le streaming et les grands contextes sont UNTESTED. L’ordre est une proposition d’usage, pas un classement de qualité démontré.

| Usage | Ordre proposé, fournisseur et statut | Quotas connus | Limites et fallback recommandé |
|---|---|---|---|
| Rapide | 1. Groq Qwen VERIFIED → 2. Mistral Ministral VERIFIED → 3. OpenRouter Dots VERIFIED | G (Qwen RPD local 250), M, O | Texte court ; latence non garantie. Outils UNTESTED sur ces trois modèles : ne pas présenter cette chaîne comme qualifiée pour les outils. Repli inter-fournisseur seulement pour requête compatible. |
| Développement | 1. Mistral Codestral 2508 VERIFIED/outils VERIFIED → 2. OpenRouter North Mini Code VERIFIED/outils VERIFIED → 3. Groq GPT-OSS 120B VERIFIED/outils VERIFIED | M, O, G | Modèles orientés code puis généraliste ; qualité projet non benchmarkée. Faible RPM Mistral. Ne pas ajouter Mistral Code comme fallback de Codestral : même backend/pool. |
| Raisonnement | 1. Groq GPT-OSS 120B VERIFIED/outils VERIFIED → 2. OpenRouter North Mini Code VERIFIED/outils VERIFIED → 3. Groq Qwen VERIFIED/outils UNTESTED | G, O, G ; deux étapes Groq non indépendantes | Petit calcul seulement, aucun benchmark de raisonnement complexe. Pour requête avec outils, exclure le dernier repli tant que cette capacité n’est pas testée. Un quota Groq commun exclut les deux routes Groq concernées. |
| Longs contextes | 1. OpenRouter Dots VERIFIED (512 000 annoncés) → 2. Mistral Ministral VERIFIED (262 144 annoncés) → 3. OpenRouter North VERIFIED/outils VERIFIED (256 000 annoncés) | O, M, O ; pool OpenRouter partagé | Proposition seulement : aucune grande fenêtre validée. Tester préalablement la taille réelle autorisée ; chaque repli doit accepter entrée + sortie réservée + outils. Au-delà de 262 144, aucun repli proposé compatible : erreur explicite, sans troncature. Dots/Ministral avec outils restent UNTESTED. |

Politique à faire valider : repli borné vers un modèle explicitement gratuit et compatible avec la requête ; pas de répétition immédiate sur 403, 404 ou quota connu. Un quota partagé doit retirer toutes les routes affectées. Ne pas utiliser un repli de fenêtre inférieure à la taille nécessaire, ni un modèle aux outils UNTESTED pour une tâche qui en dépend. Aucun de ces comportements de chaîne n’a été exercé dans cette campagne. Le débit Groq de 8 000 TPM limite aussi la possibilité d’exploiter une fenêtre théorique de 131K.

À exclure des futures chaînes : Google tant que le projet est refusé, Nemotron sur la route bloquée, références payantes/non qualifiées, et doublons d’alias comme faux secours. Les autres entrées du catalogue n’ont été ni supprimées ni désactivées par cette qualification.

### Point d’arrêt historique — levé par accord utilisateur

La qualification courte est terminée ; **aucune chaîne finale ni restriction définitive n’est appliquée**. Attendre une validation explicite portant sur les modèles retenus, l’ordre des quatre chaînes, les contraintes outils/contexte/quotas et la politique des endpoints non-chat. Restent également à valider les corrections de métadonnées de contexte et les quotas de compte non exposés. Ne pas créer `production-free`, ne pas changer le routage automatique et ne pas reprendre LiteLLM sans nouvelle instruction.

Sources primaires consultées : [Groq, limites](https://console.groq.com/docs/rate-limits), [Groq, modèles](https://console.groq.com/docs/models), [OpenRouter, catalogue API](https://openrouter.ai/api/v1/models), [OpenRouter, limites et clé](https://openrouter.ai/docs/api_reference/limits), [Mistral, abonnements](https://docs.mistral.ai/admin/billing-usage/subscriptions), [Codestral 25.08](https://docs.mistral.ai/models/codestral-25-08), API Mistral authentifiée `/v1/models`, et sources installées du [tag FreeLLMAPI v0.16.6](https://github.com/tashfeenahmed/freellmapi/tree/v0.16.6/server/src). Les affirmations de disponibilité ci-dessus reposent sur les réponses observées, pas sur les seules fiches.


## Application validée — 21 octobre 2026, vers 10:00 CEST

**CONFIGURED.** Le rectificatif d’application puis la confirmation utilisateur autorisent les quatre chaînes, acceptent une sélection variable selon le score global et demandent de conserver `balanced` et `Default`. Cette section remplace les propositions et points d’arrêt précédents pour l’état courant.

### Restrictions appliquées et persistance

PATCH natif des **scopes seulement**, sans remplacer, révéler, régénérer ni supprimer les clés fournisseurs :

| Fournisseur ; clé existante | Modèles autorisés au chat |
|---|---|
| Groq ; id 2 | `qwen/qwen3.8-27b` (modèle id 306), `openai/gpt-oss-120b` (id 52) |
| OpenRouter ; id 4 | `dots-studio/dots-3-note-preview:free` (id 276), `cohere/north-mini-code:free` (id 161) |
| Mistral ; id 1 | `ministral-8b-2512` (id 285), `codestral-2508` (id 281) |

Les identifiants GPT-OSS et North ont été confirmés par relecture du catalogue installé et concordent avec les générations qualifiées. Les trois fournisseurs restent actifs et sains ; Google id 3 entièrement désactivé. Nemotron, Mistral Code, les autres alias et tous les autres modèles sont exclus par absence des scopes autorisés. Aucune fiche ni clé supprimée, aucun fournisseur supplémentaire activé. Les catalogues restent visibles : visibilité ne signifie pas éligibilité.

Création idempotente par nom via `/api/profiles`, puis configuration native `/api/profiles/:id` et `/reorder`. Les quatre profils sont sans tri automatique (`auto_sort=null`) et sans ajout automatique de nouveaux modèles (`auto_include_new_models=0`). Leur ordre enregistré est celui demandé ci-dessous, **pas une priorité stricte à l’exécution**. Aucun profil `production-free` créé. Profil actif `Default` id 1 et sa liste inchangés ; stratégie globale `balanced`, exploration désactivée.

Relecture dans une **nouvelle session API** : scopes persistants, exactement six couples fournisseur/modèle éligibles avec les clés actives, exactement trois membres autorisés par chaîne, ordre et paramètres persistants. Aucun membre exclu dans les chaînes. Vérification indépendante du chemin `/v1/chat/completions` dans les sources installées : `resolveRoutingChain` fournit uniquement les membres nommés ; `routeRequest` les utilise comme chaîne préchargée ; `resolveStickyPreference` refuse une préférence de session hors chaîne ; la sélection de clé filtre `model_scope_json`. Le score `balanced` réordonne ces candidats sans ajouter un modèle extérieur. Les tentatives réelles ci-dessous sont toutes restées dans la chaîne demandée.

**Portée :** contrôle des routes automatiques de chat vérifiées, pas contrôle global de tous les endpoints. La lacune embeddings/media décrite plus haut demeure : leurs sélecteurs de credentials ne garantissent pas ces scopes. Aucune génération embeddings/media lancée ni désactivation de ces fonctions effectuée. Aucun patch de code ou contournement ajouté.

### Chaînes enregistrées et tests réels

Une seule génération courte par chaîne ; les tests d’outils précédents sont réutilisés. Chaque journal natif id 15–18 comporte **une tentative**, donc **aucun fallback observé**. Aucun dépassement volontaire de quota ni campagne de charge. Les noms s’appellent avec le préfixe `auto:`.

| Chaîne | Modèles configurés, ordre enregistré | Inférence | Fournisseur et modèle utilisés | Résultat |
|---|---|---|---|---|
| `auto:task-fast` ; profil 3 | Groq Qwen → Mistral Ministral → OpenRouter Dots | VERIFIED ; HTTP 200 | OpenRouter / Dots | Extraction `ABC42` correcte ; 3,030 s ; 44 entrée / 145 sortie |
| `auto:task-coding` ; profil 4 | Mistral Codestral → OpenRouter North → Groq GPT-OSS | VERIFIED ; HTTP 200 | OpenRouter / North | `def add(a, b): return a + b` correcte, AST contrôlé ; 2,081 s ; 25 / 92 |
| `auto:task-reasoning` ; profil 5 | Groq GPT-OSS → Groq Qwen → OpenRouter North | VERIFIED pour génération/routage ; contenu incorrect | Groq / Qwen | HTTP 200 ; répond **8** à `3×4−5`, attendu **7** ; 0,375 s ; 52 / 37 |
| `auto:task-long-context` ; profil 6 | OpenRouter Dots → OpenRouter North → Mistral Ministral | VERIFIED pour petit document seulement ; HTTP 200 | OpenRouter / Dots | Responsable `Léa` correctement extrait ; 3,099 s ; 61 / 157 |

Requêtes envoyées du 21 octobre 2026 à 10:00:44–10:00:50 CEST (08:00:44–08:00:50 UTC), corps de réponse et `_routed_via` conservés. Le journal stocke `requestedModel=null` pour ces routes auto ; l’association aux chaînes est établie par les requêtes et réponses capturées, non par ce champ. Les valeurs de latence sont les durées client totales ponctuelles. Les trois réponses OpenRouter indiquent un coût nul. Aucun appel de modèle payant observé.

Le contenu incorrect du test de raisonnement est une **limite de qualité observée**, pas un échec HTTP, un quota ou un modèle hors chaîne. Il n’a pas été masqué par une nouvelle tentative ou un remplacement. Aucune conclusion générale sur la fiabilité du raisonnement ne découle d’un HTTP 200. La correction sémantique de cette chaîne n’est pas validée par ce test.

### Contexte, outils et fallback : garanties bornées

- Filtrage natif conservé : estimation de l’entrée (heuristique notamment caractères/4), réserve de sortie plafonnée à 2 000 tokens pour le routage. Marge de 1,25 pour préférer les candidats ; le repli peut accepter un candidat qui tient dans sa fenêtre brute annoncée sans tenir la marge. Un candidat inférieur à l’estimation brute est écarté. Les métadonnées divergentes décrites dans la qualification n’ont pas été corrigées.
- La fenêtre effective n’est pas mesurée. **Aucune capacité 128K ou 256K garantie**, aucune grande fenêtre testée. Le petit document valide uniquement le chemin de routage. Au-delà de la fenêtre estimée des candidats restants, le comportement natif est l’épuisement/erreur plutôt qu’une réduction du prompt par ce filtre ; pas de mécanisme de compression ou troncature de l’entrée ajouté. Une erreur fournisseur de taille peut conduire à un autre membre compatible selon l’estimation. Cela ne garantit pas la taille réelle chez chaque fournisseur.
- Compression relue `mode=off` ; fusion non sollicitée, liste de modèles de fusion vide ; transfert de contexte non activé. Les mécanismes natifs de plafonnement de **sortie** demeurent : ils ne doivent pas être confondus avec une entrée tronquée. Pas de garantie de conservation exacte de tous les paramètres sur tous les protocoles/adaptateurs.
- Le routeur chat filtre les modèles selon leur support d’outils annoncé et préserve les contraintes de chaîne. Outils réellement VERIFIED seulement pour Codestral, North et GPT-OSS. Qwen, Dots et Ministral restent UNTESTED sur cette capacité : aucune promesse de validité des appels d’outils sur tous les membres. Pas de test supplémentaire inutile.
- Quotas, cooldowns, exclusions de tentative et budget de retry natifs conservés. Aucun fallback forcé ; comportement multi-échec et streaming UNTESTED dans cette campagne. Aucun mécanisme développé pour contourner une limite native.

### État final et actions restantes

`/readyz` relu après application et dans la session de contrôle : `status=ok`, `ready_upstreams=3`. Aucun nouveau cooldown sur Groq, OpenRouter ou Mistral ; anciens cooldowns Google conservés sans nouvel appel. Les corrections Groq Qwen et Safeguard sont relues inchangées. GPT-OSS : 30 RPM / 8K TPM / 1 000 RPD locaux ; Qwen 250 RPD local ; pool gratuit OpenRouter partagé 20 RPM / 50 RPD locaux ; quotas réels Mistral toujours inconnus. Aucun quota augmenté ni contourné.

Aucun redémarrage, changement de version, de réseau, de Traefik ou de DNS. Aucun changement LiteLLM/PostgreSQL, Codex, OpenClaw, agents ou MCP/oMLX. Seul ce README est actualisé comme livrable ; captures et scripts d’exécution dans `artifacts/freellmapi-finalization/` ignoré par Git : `applied-approved.jsonl`, `verified-approved.jsonl`. Aucun secret dans le rapport ; aucun commit/push.

Aucune action supplémentaire requise pour exposer ces quatre noms dans FreeLLMAPI. Restent comme limites connues : qualité du raisonnement non validée, quotas réels Mistral non exposés, grands contextes non qualifiés, scopes incomplets hors chat et scénarios de fallback non exercés. Aucun correctif applicatif ou raccordement client engagé. **Arrêt après application et contrôle, conformément au mandat.**
