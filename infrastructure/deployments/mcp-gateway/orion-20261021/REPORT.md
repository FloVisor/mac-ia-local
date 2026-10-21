# Orion derrière Docker MCP Gateway — 2026-10-21

État : **BLOCKED avant ajout et bascule — refus OAuth DCR confirmé à la reprise**. Aucune configuration active modifiée ; aucun redémarrage, aucun consentement ni échange de jeton effectué, aucun secret copié. Une unique tentative DCR de compatibilité a été refusée (voir reprise ci-dessous). Ancienne connexion Pro conservée. Perso, moteurs et politiques inchangés. Aucun commit/push ou appel de génération payant supplémentaire.

Qualification finale des options exposées par la CLI : [QUALIFICATION.md](QUALIFICATION.md). La connexion directe Pro est conservée.


## Reprise : preuve OAuth complémentaire (21 octobre 2026)

**BLOCKER : HTTP 400 `invalid_redirect_uri` lors de l'unique tentative DCR.**

La découverte publique standard a fourni :

- Ressource : `https://owu.mix3cloud.net/.well-known/oauth-protected-resource/mcp-front/mcp`.
- Métadonnées AS : `https://owu.mix3cloud.net/.well-known/oauth-authorization-server/mcp-front`.
- Issuer : `https://owu.mix3cloud.net/mcp-front` ; endpoints `/authorize`, `/token`, `/register`, `/revoke` sous cet issuer.
- PKCE S256, authorization_code et refresh_token annoncés.
- Authentification token annoncée : `client_secret_post`, `client_secret_basic` ; `none` non annoncé. Cela reste un écart à qualifier et **ne constitue pas un refus prouvé de la méthode none** : le refus observé porte sur la redirection.

Le GET sans jeton de la ressource a fourni le challenge 401 indiquant ces métadonnées ; il s'agit de la découverte standard, pas d'un jeton existant refusé. Aucun secret de la connexion OpenClaw n'a été consulté.

Le binaire déployé a été copié temporairement pour extraire ses informations Go, sans modification distante. Il embarque `github.com/docker/mcp-gateway-oauth-helpers v0.0.3`. L'analyse par `go tool objdump` a échoué : `no symbol section` ; aucun résultat de désassemblage n'est revendiqué. Le module officiel v0.0.3 définit `DefaultRedirectURI = https://mcp.docker.com/oauth/callback`. Le code Gateway upstream actuel PerformDCR utilise cette valeur lorsque son paramètre est vide et enregistre un client public (`token_endpoint_auth_method=none`) ; le flux CE actuel lance l'enregistrement avant de créer son callback local. La correspondance du code complet avec la build HEAD installée n'est pas établie : le test ci-dessous est une preuve HTTP de compatibilité du candidat DCR, pas une exécution du client Gateway.

Un seul POST de compatibilité a été effectué sur l'endpoint DCR annoncé, avec l'URI par défaut ci-dessus, PKCE prévu par le flux, type public `none` et portées de lecture seulement. **Résultat réel à 2026-10-21T16:13:30Z : HTTP 400**, erreur `invalid_redirect_uri`, description :

> Redirection refusée. Admises : http://127.0.0.1|localhost:<port>/… ou une URI HTTPS déclarée par l'instance. Refusées : https://mcp.docker.com/oauth/callback

Preuve complète expurgée : [dcr-compatibility.json](dcr-compatibility.json). Aucun client_id, client_secret ou jeton retourné, aucun objet OAuth de test créé. Aucune seconde tentative avec une autre redirection ou méthode d'authentification ; aucun contournement.

### Statuts de la reprise

| Contrôle | État | Limite |
|---|---|---|
| Découverte des métadonnées OAuth publiques Orion | PASS | Endpoints et mécanismes annoncés établis |
| Compatibilité DCR du candidat avec redirection Gateway par défaut | FAIL | HTTP 400 invalid_redirect_uri |
| Flux natif Gateway complet | NOT_RUN | Prérequis DCR et helper non satisfaits |
| Deux identités effectives | NOT_RUN | Deux consentements et deux magasins à qualifier |
| Ajout et appels Orion réels depuis Codex / Pro via Gateway | NOT_RUN | Aucun profil actif modifié |
| Skill commun et send-approval sur ce transport | NOT_RUN | Alias et contrats réels pas encore disponibles |
| Bascule Pro | NOT_RUN | Connexion directe préservée |

### NEXT REQUIRED ACTION

Faire qualifier une combinaison officiellement supportée entre Gateway et Orion : soit un flux Gateway utilisant une redirection loopback autorisée et accessible depuis le navigateur, soit une URI HTTPS préalablement approuvée et déclarée par l'administrateur Orion. Vérifier ensuite la prise en charge des clients publics `none` ou des secrets clients, avant de provisionner le helper et les magasins distincts. Ces décisions ne sont ni remplacées par une réutilisation du token OpenClaw, ni par une modification improvisée de la requête refusée.

Une procédure de consentement interactive exécutable ne peut pas être présentée comme fonctionnelle sur cette installation : la requête préalable est refusée. Après correction approuvée, exécuter authorize séparément dans les états codex/pro, ouvrir l'URL produite, choisir l'identité de chaque profil et vérifier le callback réellement routé vers le processus d'autorisation ; reprendre ensuite les étapes de recette déjà décrites. Aucune invitation de consentement n'a été générée pendant cette reprise.

Rollback de cette reprise : aucune configuration active à restaurer, aucun client OAuth à supprimer. Les seuls nouveaux fichiers sont les preuves et le rapport ; le binaire temporaire a été retiré. Les résultats de la revue locale antérieure n'ont pas été réutilisés comme preuve de sécurité.

Sources supplémentaires : code officiel Gateway `pkg/oauthdiscovery/discovery.go` et `cmd/docker-mcp/oauth/auth.go` ; module officiel `github.com/docker/mcp-gateway-oauth-helpers@v0.0.3` distribué via proxy.golang.org. Les informations Go du binaire installé sont conservées dans [gateway-build-info.txt](gateway-build-info.txt).

## Preuves du diagnostic exécuté

- SSH publickey vers docker-02 opérationnel. Services actifs : codex `8752839dcb3b`, pro `7a2a8d35815b`, perso `27d9527d422d` (identifiants éphémères).
- Le CLI hôte répond `docker: unknown command: docker mcp`. CLI réellement installé : `/docker-mcp` dans les conteneurs ; `version` répond `HEAD`. Image épinglée : `docker/mcp-gateway@sha256:f5a679a05fc39022a046167bef92aeeb01bcd59485ad27843ae5227db7950688`.
- `/docker-mcp oauth --help` expose authorize/ls/revoke ; authorize accepte `--scopes` et `--open-browser`.
- `/docker-mcp oauth ls` répond exactement : `Get "http://localhost/apps": dial unix /root/.docker/desktop/tools.sock: connect: no such file or directory`. Cela prouve l'absence du service Desktop attendu par cette commande, pas l'absence du mode OAuth CE.
- `/docker-mcp feature ls` : mcp-oauth-dcr activé ; oauth-interceptor, dynamic-tools, tool-name-prefix, use-embeddings désactivés.
- Inspection statique du binaire installé : chaînes `DOCKER_MCP_USE_CE`, `MCP_GATEWAY_OAUTH_PORT`, `No credential helper found`, `Starting OAuth authorization` présentes. Le code upstream actuel décrit un mode CE autonome ; correspondance exacte du commit installé non établie (version HEAD, labels image null).
- Recherche des exécutables `docker-credential-*` dans tous les répertoires PATH du conteneur Codex : **aucun résultat**. Les commandes ciblées pour pass/secretservice/desktop ne trouvent rien. `config.json` existe, son contenu secret n'a pas été lu. Aucun stockage sécurisé utilisable par le flux CE n'est démontré.
- Inspection ciblée des montages : volumes distincts `mcp_gateway_codex` et `mcp_gateway_pro` vers `/root/.docker`, socket Docker partagé. Aucun helper OAuth n'est monté. L'indépendance des états est prouvée ; l'indépendance future des identités OAuth n'est pas encore prouvée.
- Configuration OpenClaw Pro examinée avec sortie filtrée aux seuls champs non secrets : transport `streamable-http`, auth `oauth`, URL Orion ci-dessous, portées `kb:read tags:read tags:write registry:read registry:write`. Aucun jeton lu ou transféré.
- Essai de métadonnées publiques à la racine `/.well-known/oauth-authorization-server` : réponse non JSON. Ce chemin n'est pas une métadonnée OAuth validée ; aucun endpoint d'autorisation, token ou DCR Orion n'est déduit de cet essai. Pas d'essais d'authentification alternatifs.

## Compatibilité et identités

Orion actuel : `https://owu.mix3cloud.net/mcp-front/mcp`, Streamable HTTP + OAuth côté OpenClaw. Le skill partagé ne fournit pas cette connexion.

Le transport HTTP distant de Gateway est déjà utilisé par Context7. L'aide installée propose OAuth/DCR ; la compatibilité OAuth **de bout en bout avec Orion reste NOT_RUN** faute de stockage sécurisé prêt et de validation de la découverte/DCR. Ne pas assimiler une capacité générale à une recette Orion.

Docker documente que les identifiants OAuth sont partagés entre profils d'un même état. Les deux processus actuels ont des états séparés : deux consentements et identités sont envisageables **si** les helpers utilisent eux aussi des magasins ou namespaces séparés. Deux volumes seuls ne le garantissent pas. Le socket partagé n'établit pas une fusion des identités HTTP et n'est pas une frontière de sécurité système.

## Préparation et suite exacte

`orion.candidate.yaml` est un candidat non importé, sans secret ; son schéma est fondé sur la spécification actuelle des entrées distantes. Ne l'importer qu'après qualification du binaire épinglé et du stockage OAuth.

1. Fournir un credential helper supporté, disponible aux processus d'autorisation **et** aux Gateway persistantes, avec magasins isolés Codex/Pro. Aucun stockage en clair ou copie du token OpenClaw ne remplace ce prérequis. Vérifier également accès au callback navigateur et persistance des refresh tokens. Cette préparation système n'est pas effectuée.
2. Exporter les profils avec `/docker-mcp profile export codex <fichier>` et équivalent pro ; conserver les exports privés, la définition du déploiement et les préimages de tout fichier effectivement modifié.
3. Placer le candidat approuvé sous le répertoire catalogues autorisé, puis importer uniquement dans chacun de ses états : `/docker-mcp profile server add codex --server file://<chemin-relatif-catalogues>/orion.yaml`, puis équivalent pro. L'import n'est pas exécuté.
4. Dans chaque état, commande d'authentification fournie par le CLI installé : `DOCKER_MCP_USE_CE=true /docker-mcp oauth authorize orion --scopes "kb:read tags:read tags:write registry:read registry:write"`. Exécuter séparément, choisir l'identité voulue et contrôler les scopes consentis ; les portées peuvent être réduites suivant le besoin validé. Ne pas exposer l'URL de consentement dans des logs publics. Aucun refus ne doit être contourné.
5. Le code upstream prévoit un callback sur `127.0.0.1:54321`, configurable par `MCP_GATEWAY_OAUTH_PORT`. Dans le déploiement actuel ce loopback est celui du **conteneur** : un simple tunnel SSH vers le loopback de l'hôte ne suffit pas. Le chemin navigateur exact dépend du helper/runner retenu et reste à qualifier avant de lancer authorize. Aucune procédure interactive de bout en bout n'est prétendue validée à ce stade.
6. Après OAuth qualifié, recharger uniquement codex/pro (watch=false), préserver Perso. Vérifier noms/schémas réels, absence de collisions avec Context7/time et identité effective de chaque connexion.
7. Codex : nouvelle session app-server native, inventaire MCP puis appels réels, sans génération payante. Pro : session main isolée, modèle déjà opérationnel et outils natifs tool_search/tool_call ; pas de --deliver. Conserver appels, arguments expurgés, réponses et identifiant de session. Charger le SKILL.md canonique dans chaque client.
8. Recette lecture : list_registries → search_tools → get_contract → exec_tool pour un contrat réel access=read, sans objet de test mutable. Tester les protections par unit tests/simulation du hook, jamais une mutation réelle. Retirer la connexion directe Pro uniquement après succès complet.

## send-approval : incompatibilité de noms à traiter avant bascule

La politique actuelle qualifie `orion__*`, dont exec_tool uniquement après un résultat réel get_contract de la même session, avec accès read et cache borné. Les noms `docker_gateway_pro__*` qualifiés aujourd'hui sont Context7/time. Elle n'a pas été modifiée. Les alias Orion derrière Gateway ne sont pas encore découverts ; leur qualification et l'observation des contrats doivent être adaptées uniquement aux noms vérifiés, sans élargir aux outils inconnus. Préserver refus Perso, contrats write, exec_tool non qualifié, session distincte et enveloppes ambiguës. **La politique existante ne constitue pas une preuve de lectures Orion sans confirmation via Gateway.**

## Matrice de recette de cette mission

| Parcours | État | Preuve / limite |
|---|---|---|
| Configuration Orion Pro actuelle examinée | PASS | Champs non secrets filtrés ; aucune copie de jeton |
| États Gateway Codex/Pro distincts | PASS | Montages inspectés |
| OAuth Orion compatible Gateway installée | NOT_RUN | Helper absent ; découverte/DCR/refresh non qualifiés |
| Deux identités OAuth distinctes | NOT_RUN | Stockages OAuth et consentements à qualifier |
| Ajout Orion codex/pro | NOT_RUN | Précondition OAuth non remplie |
| Découverte + quatre appels réels Codex via Gateway | NOT_RUN | Orion non ajouté |
| Découverte + quatre appels réels Pro via Gateway | NOT_RUN | Orion non ajouté |
| Skill partagé exécuté avec ce transport dans les deux clients | NOT_RUN | Pas de duplication ; transport non prêt |
| Lectures sans confirmation et mutations protégées via Gateway | NOT_RUN | Adaptation exacte des alias à qualifier |
| Bascule Pro / retrait connexion directe | NOT_RUN | Dépend de toute la recette |

Les validations antérieures du transport direct Pro et des skills ne sont pas relancées et ne sont pas réétiquetées comme preuves Gateway. Aucun problème de modèle local n'est utilisé comme motif de blocage.

## Rollback

État actuel : rien à annuler, car aucun raccordement actif n'a changé. Après futur ajout, retirer uniquement orion avec `/docker-mcp profile server remove codex orion` et équivalent pro, puis recharger les deux services ; restaurer préimages des seules politiques/instructions modifiées. Si Pro a été basculé, rétablir sa définition directe OAuth sauvegardée et vérifier le chemin natif. Ne pas révoquer l'autorisation directe existante, ne pas toucher aux autres serveurs ou à Perso. Une révocation des nouveaux tokens Gateway exige de vérifier qu'ils sont indépendants avant toute action.

## Sources et contrôle critique

- Docker profils : https://docs.docker.com/ai/mcp-catalog-and-toolkit/profiles/ (partage des identifiants au sein d'un état).
- Spécification entrée : https://github.com/docker/mcp-gateway/blob/main/docs/server-entry-spec.md
- Flux autonome et helper : https://github.com/docker/mcp-gateway/blob/main/cmd/docker-mcp/oauth/auth.go ; https://github.com/docker/mcp-gateway/blob/main/pkg/oauth/credhelper.go ; https://github.com/docker/mcp-gateway/blob/main/pkg/oauth/callback_server.go
- Revue locale llm-router `771d652d-4a08-404e-9747-9b26a1a8e532` reçue, non retenue pour les hypothèses non étayées de fusion des credentials par socket et commandes invalides. Aucun secret transmis.
