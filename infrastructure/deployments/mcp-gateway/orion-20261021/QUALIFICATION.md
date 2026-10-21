# Qualification des solutions OAuth Orion / Gateway

Date : 21 octobre 2026. Résultat : **BLOCKED — conservation d'Orion en direct dans OpenClaw Pro**. Aucun profil, Bearer, skill, moteur, politique ou serveur modifié. Aucun commit/push ni appel LLM payant. Pas de nouvelle tentative DCR pendant cette qualification.

## Conclusion et cause exacte

Le refus observé est `HTTP 400 invalid_redirect_uri` sur le candidat DCR utilisant `https://mcp.docker.com/oauth/callback`. Il n'est pas causé par le modèle, par le skill, ni par une ancienne configuration Codex manquante. La requête préalable était un POST HTTP de compatibilité, **pas une exécution du flux natif Gateway**. Elle prouve le refus de cette URI, pas l'échec des étapes suivantes.

Le CLI actuellement déployé ne permet pas de lui substituer une autre URI via les options OAuth examinées. Son aide n'expose que scopes/open-browser ; deux contrôles du parseur, sans requête OAuth, répondent :

```
/docker-mcp oauth authorize orion --redirect-uri http://127.0.0.1:54321/callback
unknown flag: --redirect-uri

/docker-mcp oauth authorize orion --client-id diagnostic-no-secret
unknown flag: --client-id
```

Le second argument est une chaîne de diagnostic, pas un identifiant OAuth utilisé pour une connexion : le parseur rejette l'option avant exécution. Le shell regroupant ces contrôles et les lectures d'aide se termine à 0 ; cela ne transforme pas ces rejets en succès.

L'aide complète de `gateway run` ne propose ni callback, ni client-id/client-secret, ni import d'identité OAuth. `profile config` expose des paramètres de configuration de serveur, sans mécanisme documenté d'injection dans le gestionnaire OAuth. `secret set` stocke des secrets ; ce n'est pas une commande d'import de client DCR. Aucun enregistrement interne sérialisé n'a été fabriqué ou injecté dans le helper ou la base.

## Version et niveau de preuve

Image déployée connue : `docker/mcp-gateway@sha256:f5a679a05fc39022a046167bef92aeeb01bcd59485ad27843ae5227db7950688`. CLI `HEAD`, protocole serveur précédemment observé 2.0.1 ; ne pas confondre les deux versions. Informations Go du binaire déjà conservées : Go1.25.12, module Gateway `(devel)`, oauth-helpers v0.0.3. Le commit de build n'est pas fourni. Les aides CLI examinées pendant cette qualification proviennent du conteneur installé ; les explications de code ci-dessous proviennent de la branche officielle main, **pas d'un source identifié exactement pour la build HEAD**. Le binaire temporaire précédemment collecté a été retiré ; le désassemblage avait échoué, aucune nouvelle tentative équivalente.

## Stratégies examinées dans l'ordre demandé

| Stratégie | Conclusion | Preuve / limite |
|---|---|---|
| Callback personnalisé officiellement exposé | Non disponible dans les interfaces examinées | Option redirect-uri rejetée ; aucun paramètre équivalent dans l'aide ou la configuration OAuth documentée |
| Client OAuth préenregistré | Aucun import pris en charge identifié | Option client-id rejetée ; commande OAuth sans import/configuration de client ; la bibliothèque manipule des clients DCR mais cela n'est pas une interface CLI |
| Authentification alternative supportée des deux côtés | Non établie | Gateway accepte des en-têtes distants, mais aucune API key/PAT Orion documentée et disponible ; aucun jeton OpenClaw copié ni utilisé comme Bearer statique |
| Maintien du raccordement direct | Retenu | Configuration active Pro inchangée ; la validation antérieure directe ne vaut pas validation Gateway |

Le code officiel CE crée un Manager avec la redirection HTTPS Docker par défaut et enregistre le client DCR avant de démarrer son récepteur local. `SetRedirectURI` est une méthode Go ; la commande n'en expose pas l'appel. De plus, la méthode modifie le champ du Manager, tandis que le gestionnaire DCR a été construit avec sa propre redirection : elle ne constitue pas, à elle seule, un paramétrage complet du parcours. Aucun patch de code ou proxy OAuth personnalisé n'est introduit.

`MCP_GATEWAY_OAUTH_PORT` règle le port de `http://127.0.0.1:<port>/callback` dans le code du récepteur ; il ne remplace pas la redirection enregistrée en CE. Le flux CE utilise le proxy OAuth Docker et encode le port local dans state. Le flux Community décrit dans main utilise un callback loopback mais dépend du mode Docker Desktop/docker pass ; l'existence de ce code ne qualifie pas sa disponibilité sur ce Swarm Linux. Aucun mode Desktop simulé ni socket fictif.

## Qualification Orion et administration

Les métadonnées publiques déjà établies annoncent issuer `https://owu.mix3cloud.net/mcp-front`, endpoints authorize/token/register/revoke, PKCE S256, authorization_code/refresh_token, et token auth `client_secret_post`/`client_secret_basic`. Elles n'annoncent pas `none`. Le code DCR Gateway consulté demande un client public `none` et le provider n'utilise pas de client_secret. Cette différence est **à qualifier**, car la requête antérieure a été rejetée sur redirect_uri avant qu'une éventuelle acceptation/rejection de none soit prouvée.

Le refus Orion indique que les URI HTTP loopback avec port sont admises, ainsi que les URI HTTPS déclarées par l'instance. Il ne fournit pas la liste de ces URI HTTPS. `http://127.0.0.1:54321/callback` est donc **annoncée comme admissible par cette règle**, mais ni enregistrée ni validée dans un flux Gateway. **Aucune URI utilisable de bout en bout n'est confirmée.**

Aucun accès à une configuration administrative Orion, ni API administrative documentée avec droits appropriés, n'est fourni par les éléments disponibles. La capacité d'un administrateur à déclarer une URI HTTPS est indiquée par le message serveur ; la procédure, les droits et la possibilité de préenregistrer deux clients indépendants restent à confirmer par l'administrateur. Aucun accès au serveur distant ou à ses secrets n'est tenté. Aucun nouvel objet de test OAuth n'est créé pour vérifier une possibilité que le CLI ne permet pas d'utiliser.

## Identifiants, callback et renouvellement en CE/Swarm

Le code officiel CE lit et écrit clients DCR et jetons par un credential helper sélectionné dans la configuration Docker. Aucun exécutable docker-credential-* n'a été trouvé dans le PATH du conteneur Codex au diagnostic antérieur ; aucun stockage sûr prêt n'est démontré. Les volumes `/root/.docker` sont séparés entre Codex et Pro, mais le magasin du helper doit aussi être séparé : les clés OAuth dépendent du serveur/provider, pas du nom du profil. Un magasin partagé pour le même serveur orion peut donc partager une identité malgré les volumes distincts.

Le renouvellement CE est implémenté dans le code officiel via refresh_token et réécriture dans le helper, suivi du rechargement du serveur. **NOT_RUN en réel** : aucun jeton Gateway n'existe. Ni un code lu, ni un mécanisme Go existant ne prouve son fonctionnement sur cette instance.

Le callback écouterait le loopback du conteneur. Le loopback du navigateur sur le Mac et celui de l'hôte Swarm sont différents ; un simple ssh -L vers le loopback de l'hôte ne raccorde pas le récepteur du conteneur. Aucun écouteur public, routage OAuth ou tunnel non qualifié n'est ajouté. Pas de procédure interactive prétendue fonctionnelle tant que redirection, méthode de client et stockage ne sont pas compatibles.

## Validation et restrictions

| Test | Statut | Résultat |
|---|---|---|
| Métadonnées publiques Orion | PASS antérieur réutilisé | Aucun changement connu nécessitant répétition |
| Compatibilité DCR URI Docker | FAIL antérieur réutilisé | HTTP400 invalid_redirect_uri ; aucune répétition |
| CLI : callback personnalisable par redirect-uri | FAIL | unknown flag, avant réseau |
| CLI : client préenregistré par client-id | FAIL | unknown flag, avant réseau |
| Configuration documentée alternative callback/client | NOT_AVAILABLE | Aucun mécanisme supporté identifié dans les interfaces examinées |
| Enregistrement d'une autre URI | NOT_RUN | Pas de parcours CLI qualifié qui puisse l'utiliser |
| Autorisation/callback/échange natifs Gateway | NOT_RUN | Bloqués avant consentement |
| Stockage sécurisé de jetons Gateway | NOT_RUN | Helper et magasin à fournir |
| Renouvellement réel | NOT_RUN | Pas de jeton Gateway |
| Deux clients et identités OAuth indépendants | NOT_RUN | Deux autorisations et magasins indépendants à qualifier |
| Découverte et quatre appels Orion Codex/Pro via Gateway | NOT_RUN | Orion non ajouté |
| Absence Orion sur Perso | Configuration antérieure conservée | Aucun ajout ni changement de Perso ; pas de nouvelle recette runtime |
| Conservation send-approval | Configuration conservée | Aucune modification ; comportement via Gateway non qualifié |
| Bascule | NOT_RUN | Aucune connexion Gateway validée |

La politique actuelle utilise les alias directs orion__* et qualifie exec_tool grâce à un vrai get_contract read dans la même session. Les alias Gateway ne sont pas établis et cette mission interdit de modifier la politique : même une réussite OAuth ne suffirait pas à autoriser une bascule Pro si les alias ne sont pas déjà reconnus. Il faudrait alors une mission distincte ou une configuration supportée démontrant la conservation exacte des alias. Aucun élargissement silencieux.

## BLOCKER / EVIDENCE / ATTEMPTS / NEXT REQUIRED ACTION

**BLOCKER :** pas de combinaison OAuth supportée établie sur la Gateway installée : redirection CE refusée, absence d'option CLI callback/client, helper non disponible ; compatibilité des clients publics non prouvée.

**EVIDENCE :** preuve HTTP conservée dans dcr-compatibility.json ; rejets du parseur reproduits ci-dessus ; aides natives ; sources officielles listées ci-dessous. Pas de nouvel essai d'authentification.

**ATTEMPTS :** (1) vérification des interfaces installées, dont deux paramètres distincts rejetés localement ; (2) vérification des capacités de configuration, stockage et renouvellement dans les interfaces documentées et le code officiel ; (3) confrontation avec les métadonnées et le refus Orion déjà collectés. Aucune variante réseau de la requête rejetée.

**NEXT REQUIRED ACTION :** demander à l'administrateur Orion de confirmer la procédure autorisée pour une redirection HTTPS dédiée et le support de clients publics DCR avec PKCE/none, ainsi que deux autorisations indépendantes. En parallèle, obtenir côté Docker une version/interface officiellement supportée qui expose le callback voulu ou l'import d'un client OAuth complet en CE. Le simple ajout de l'URI Docker dans une allowlist n'est pas présenté comme une correction suffisante : le proxy callback, le type de client, le helper et l'isolation devront ensuite être qualifiés. Aucun mail envoyé.

Si aucune de ces capacités n'est disponible, la solution retenue demeure Orion direct dans Pro. La migration Gateway reste non réalisée ; l'absence d'Orion dans Codex ne disparaît pas avec cette décision.

## Rollback

Aucune configuration active modifiée pendant cette qualification : rien à restaurer, aucun nouveau client ou jeton à supprimer. Les fichiers documentaires constituent la livraison. Le rollback de la future migration reste décrit dans REPORT.md ; il ne faut ni supprimer l'accès direct Pro, ni révoquer son autorisation tant que le chemin Gateway complet n'est pas validé.

## Sources primaires

- CLI OAuth : https://github.com/docker/mcp-gateway/blob/main/cmd/docker-mcp/commands/oauth.go
- Flux CE et Community : https://github.com/docker/mcp-gateway/blob/main/cmd/docker-mcp/oauth/auth.go
- Manager et SetRedirectURI : https://github.com/docker/mcp-gateway/blob/main/pkg/oauth/manager.go
- Callback local : https://github.com/docker/mcp-gateway/blob/main/pkg/oauth/callback_server.go
- Provider et refresh CE : https://github.com/docker/mcp-gateway/blob/main/pkg/oauth/provider.go
- Client DCR et stockage : https://github.com/docker/mcp-gateway/blob/main/pkg/oauth/dcr/credentials.go ; https://github.com/docker/mcp-gateway/blob/main/pkg/oauth/token_store.go
- Schéma public des entrées : https://github.com/docker/mcp-gateway/blob/main/docs/server-entry-spec.md
- Éléments locaux : gateway-build-info.txt ; dcr-compatibility.json ; REPORT.md.
