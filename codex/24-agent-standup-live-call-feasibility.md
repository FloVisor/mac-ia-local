# Rectificatif P3-C — intégration dans Agent Standup: Live Call

21 octobre 2026. **Étude de faisabilité uniquement.**

**Conclusion : intégration techniquement faisable dans le Live Call existant,
mais nécessitant des modifications du code d’Agent Standup 1.40.0. Aucun point
d’injection externe supporté trouvé dans cette version.** Une contribution
acceptée en amont éviterait un fork local ; une version locale modifiée, même
légèrement, serait un dérivé à maintenir et nécessite l’accord explicite demandé.
Aucun fork, patch, remplacement ou essai d’injection réalisé.

La vue Explorateur livrée précédemment ne satisfait pas la cible Live Call.
`agent-observer/`, ses sources et son installation restent conservés, sans
modification pendant cette étude. Aucune troisième interface créée.

## 1. Identification et preuves

- Extension active : **doublegeste.agent-standup@1.40.0**, registre local
  `~/.vscode/extensions/extensions.json` relu. Dossier installé :
  `~/.vscode/extensions/doublegeste.agent-standup-1.40.0/`.
- Dépôt du manifeste : [Atoll92/agent-standup](https://github.com/Atoll92/agent-standup).
- Licence **MIT**, texte installé `LICENSE.txt`, copyright Arthur 2026.
  Modification et redistribution autorisées sous conservation des mentions de
  licence ; l’autorisation juridique ne remplace pas l’accord de déploiement.
- Commit amont consulté :
  [`04c6f42c3030396f48ea16c0581bb1824c963798`](https://github.com/Atoll92/agent-standup/commit/04c6f42c3030396f48ea16c0581bb1824c963798).
  **codex.js, server.js et public/index.html installés sont identiques octet pour
  octet à ce commit.** Cela identifie précisément ces trois composants, sans
  prétendre connaître le commit de construction de tout le VSIX.

Empreintes de la copie installée examinée :

| Fichier | SHA-256 |
|---|---|
| codex.js | e0428bc73d24f5b5ab19439f5e149c28b32de8d5790b4e75bcb3592f1b22a46f |
| server.js | 78ee743673d9fb9cd53027b01230faa9ef646f98a19e3fa820eb2b512854e0c7 |
| public/index.html | 310fbcaadeab1a6b1f8bad42edaed74a5d5aae7fed3b0975b486e59f4ff8a900 |
| extension.js | 7fcd813b2aea70c5b970864b751d0f850e18c2b5a71ccfc61cb0ec5aa23152a7 |

## 2. Chemin réel des données vers les personnages

1. **extension.js** ouvre le panneau et la sidebar VS Code. Il lance server.js
   dans un processus Node distinct par fenêtre, avec repli dans l’Extension Host.
   La webview intègre le site local dans une iframe. Les messages échangés servent
   à la navigation, aux actions et à l’épinglage de session ; aucune inscription
   de participant externe n’est exposée.
2. **server.js:9–11** charge codex.js et vibe.js dans `SOURCES=[codex,vibe]`.
   Ce registre est interne et statique. `recordOf()` sélectionne aussi les parsers
   dans le code. Aucun chargement de plugin arbitraire documenté ou configuré.
3. **codex.js** découvre les rollout JSONL de CODEX_HOME/sessions, lit session_meta,
   les noms de session, turn_context et les événements. `head()` détecte les
   enfants ; `sessions()` les exclut explicitement. `boardRow()` fixe subActive
   et subTotal à zéro. Son parser convertit les tours, outils et tokens en
   événements communs, sans créer de relation de sous-agent Codex.
4. **server.js:169–182, 887–944** construit une chronologie commune :
   `agents[]` et `events[]`. `subFilesOf()` sait utiliser une méthode interne
   `source.subFiles`, comme le fait Vibe ; `x.st` permet un état déjà projeté.
   Les événements `order`, `report`, `finish`, `tools` et `usage` alimentent le
   même appel animé. La relation parent/enfant Claude repose notamment sur
   toolUseId ; elle ne se transpose pas automatiquement aux IDs Codex.
5. **GET /api/session** fournit cette chronologie complète ou un flux incrémental
   avec clés d’événements, epoch et séquence. Ce n’est pas une route d’écriture
   ou une API d’enregistrement d’agents. `stamp()` et `timelineEntry()` gèrent
   l’invalidation et le cache ; les mises à jour externes doivent y participer.
6. **public/index.html** charge `data.agents`, construit les personnages via
   persona/addTile/buildStage, puis applique les événements aux états et
   animations. Le polling ajoute les nouveaux participants. Les noms propres
   passent par `a.own` et la préférence ownNames ; sans cette information,
   l’interface attribue des prénoms de présentation.

Repères supplémentaires vérifiés : addTile:1277, transitions order:1341,
modèle déduit des événements usage:1450, agentState:1483, loadSession:2687,
polling incrémental vers la fin du fichier. La scène existante est donc
réutilisable : aucune réécriture du moteur d’animation ne paraît nécessaire.
Cette appréciation est fondée sur la lecture du code, pas sur un prototype.

## 3. Décision entre les voies envisagées

| Voie | Faisabilité dans la version examinée | Décision |
|---|---|---|
| API officielle / plugin externe | Aucun point trouvé dans manifeste, exports, messages webview, registre et routes | Non disponible dans la surface examinée |
| Une autre extension injecte des participants dans le Live Call installé | Pas de contrat pour alimenter cette scène ; nécessiterait interception réseau, injection JS ou monkey-patch | Écartée : fragile et intrusive |
| Extension légère du code **en amont** | Adaptateurs internes et scène déjà structurés pour plusieurs agents | Option recommandée si acceptée par le mainteneur ; délai externe inconnu |
| Dérivé local à patch limité | Faisable sous MIT ; mêmes panneaux et personnages | Accord explicite requis avant fork ou déploiement |
| Nouvelle vue ou remplacement de scène | Ne répond pas à la cible | Exclu |

Un petit diff local reste une modification d’un logiciel tiers à maintenir ;
il ne devient pas une intégration non invasive parce qu’il est court. Un proxy
qui réécrirait les réponses /api/session serait également une interception non
supportée. Fabriquer de faux journaux Claude pour tromper la découverte est exclu.

## 4. Modifications proposées, non appliquées

### Collecte et corrélation réutilisées

Réutiliser **Collector.session/router/snapshot**, les filtres de confidentialité,
les bornes et tests de `agent-observer/collector.py`. Ne pas démarrer sa TreeView
comme interface de cette intégration. Le processus Python peut fournir une
projection en mémoire au serveur Standup, par son protocole local existant,
sans service HTTP supplémentaire ni journal parallèle.

Évolutions nécessaires après décision :

- Conserver dans la projection le nom technique `agent_nickname` et le rôle/chemin
  d’agent de session_meta. Le collecteur actuel les filtre volontairement ou ne
  les restitue pas ; il doit donc être étendu pour ce besoin précis.
- Garder l’identité, le type de participant, le parent et les événements séparés.
  Prévoir des IDs DOM sûrs et préfixés distinctement pour Codex et MCP, ainsi que
  des clés de transition stables. Ne pas se baser sur l’ordre des fichiers.
- Exposer les transitions natives et routeur, pas seulement un instantané final.
  Les états de task MCP et les tours Codex n’ont pas les mêmes cycles de vie.
- Conserver la lecture SQLite du seul espace **codex**, mode=ro/query_only,
  fermeture explicite ; aucun Engine ni worker, aucun request/output sélectionné.
  Dépendance au schéma interne signalée, échec visible si incompatible.

### Adaptateur Codex et serveur Standup

- **codex.js** : indexer les vrais liens parent_thread_id/thread_spawn, exposer
  les descendants via les conventions internes subFiles/subCount/watch ou une
  projection équivalente, alimenter le résumé de session sans compteurs fictifs.
  Ne pas présenter les enfants comme des sessions principales indépendantes.
- **server.js** : enrichir buildTimeline avec les participants projetés, préserver
  leur parent réel, y compris pour les descendants d’un sous-agent. Générer les
  événements communs utiles aux animations à partir de faits structurés.
- Ajouter des métadonnées explicites : catégorie native/MCP, état source,
  tâche courte connue, modèle déclaré/demandé/exécuté, provenance, durée, usage,
  coût nullable. Ce sont des **champs proposés**, pas une API déjà disponible.
- Étendre l’invalidation du cache aux changements des sous-agents et aux
  révisions de la projection routeur. Surveiller seulement tasks.sqlite ne suffit
  pas en cas de WAL ; préférer une révision calculée depuis la projection lue,
  ou prendre correctement en compte les fichiers associés, sans les modifier.
- Ne pas appliquer la règle actuelle « transcript silencieux 4 min = finished »
  aux états explicites Codex/MCP. Silence ≠ completed. unknown doit rester visible.
- Une tâche MCP terminée avec échec ne doit pas produire une remise de résultat
  présentée comme un succès. Ne pas injecter le texte privé du résultat.

### Live Call existant

- **public/index.html** : réutiliser les personnages, leur arrivée/départ, les
  bulles de tâche, la scène, les détails et les sélecteurs de session existants.
- Afficher une distinction persistante **Sous-agent Codex** / **Tâche MCP ·
  llm-router** sur les mêmes tuiles ; un personnage MCP reste une représentation
  graphique de tâche, jamais un sous-agent natif prétendu.
- Afficher nom technique, tâche courte disponible, état source et modèle avec
  son niveau de preuve. Le modèle ne doit pas attendre le premier événement de
  tokens ; aucun faux événement usage ne doit être créé pour le faire apparaître.
- Faire évoluer agentState/classes/badges pour queued/running/completed/failed/
  cancelled/unknown, en conservant les états historiques des autres sources.
- Mettre à jour les métadonnées d’un personnage déjà présent. Le polling actuel
  retourne tôt si `d.events` est vide et ne fait qu’ajouter les nouveaux agents :
  un simple changement de modèle/nom/état pourrait donc rester invisible.
- Garder les fonctions existantes et leurs préférences. Ne pas déclencher
  traduction, plaisanterie ou voix distante pour des événements techniques ajoutés.
  Le README installé précise que certaines fonctions linguistiques peuvent appeler
  Claude ; une validation future devra les neutraliser **dans le profil isolé**,
  sans changer les préférences normales de l’utilisateur.

Le noyau des adaptations concernerait donc codex.js, server.js, public/index.html
et la projection du collecteur. Ajouter un point officiel de plugin nécessiterait
également un contrat de chargement/configuration. Aucun chiffrage en jours ou
nombre exact de lignes n’est qualifié sans prototype autorisé.

## 5. Données réelles disponibles et limites

Trois enfants natifs ont été relus dans session_meta :

| Nom runtime | Identifiant réel | Chemin technique |
|---|---|---|
| Lovelace | 01a13a9c-fae5-7b72-8f2e-e867f83f49af | /root/map |
| Confucius | 01a13a9c-d5ca-7332-a1f1-cb2d34bccd92 | /root/frontend |
| Harvey | 01a13a9c-ab14-7142-8b88-bfab2b8e2b7c | /root/backend |

Le parent explicite commun est `01a13a9b-ac78-7b00-86eb-a1a8ca464d78`.
Ces noms viennent du runtime ; les prénoms aléatoires du rendu ne sont pas une
preuve d’identité. `agent_role` est null dans ces trois métadonnées. Les chemins
techniques sont connus ; une description métier courte de la tâche ne l’est pas
par ces seuls champs. Ne pas inventer un résumé. Réutiliser un libellé court
structuré lorsqu’il existe ; sinon afficher le chemin/profil et « tâche détaillée
non exposée », sans recopier le prompt complet.

La recette précédente a observé gpt-6-astra dans turn_context des trois enfants.
C’est un **modèle déclaré**, pas une attestation fournisseur d’exécution. Cette
étude ne relance aucune génération et ne requalifie pas le trajet réseau.

Pour llm-router, les champs déjà projetés fournissent profil, parent déclaré,
alias, états, transitions, request_id, durée, tokens et coût nullable. Le modèle
réel ne doit être présenté confirmé qu’avec une provenance démontrée ; l’alias
local-omlx ou un response_model ne suffit pas. Le parent de la tâche P3-A est une
référence déclarative sans journal disponible dans la fenêtre du collecteur.
**La route actuelle /api/session refuse une session sans fichier source** :
son apparition dans Live Call nécessiterait un support explicite des références
orphelines, ou resterait une limitation visible. Aucun faux fichier ne doit être
créé pour contourner cette validation.

local_llm doit garder un identifiant de source distinct. Un appel observé sans
état persistant ne permet pas d’inventer une tâche active ou un résultat récupérable.
OpenClaw Pro/Perso reste entièrement hors collecte.

## 6. Risques et contrôles à prévoir

| Risque | Contrôle requis pour une implémentation autorisée |
|---|---|
| Mise à jour Standup écrasant les changements | Patch versionné sur base précise, rebase contrôlé, aucun patch manuel de copie installée |
| Double apparition d’un agent, tokens hérités d’un fork | Identifiants et événements stables, tests de reprise/fork ; ne pas sommer aveuglément les cumuls |
| Mauvais parent ou mélange de sessions simultanées | Relation structurée explicite, tests intersessions et descendants, orphelins signalés |
| Faux completed après silence | État source prioritaire, unknown en cas d’absence de preuve |
| Modèle ou fournisseur trompeur | Déclaré/demandé/confirmé séparés, inconnus explicites |
| Fuite de prompts/résultats via bulles, logs ou traduction | Projection minimale, échappement des noms/descriptions, erreurs filtrées, aucun contenu privé ajouté |
| Interface figée par lecture ou processus en défaut | Processus isolé borné, cache, une seule collecte partagée par serveur, erreurs visibles sans retry infini |
| Préférences/historique cassés par retour de version | Pas de migration destructive, aucun changement du format des préférences existantes |
| Frontend non synchronisé ou doublons après redémarrage | Clés/epoch/seq cohérents, modifications de métadonnées sans événements testées |

## 7. Recette future nécessaire — NOT_TESTED ici

D’abord fixtures et traces existantes : trois noms natifs et parents corrects,
participants MCP distincts, six états et transitions, modèle inconnu, coûts null,
multisessions, enfant d’enfant, redémarrage, cache/WAL, parent absent, confidentialité.
Puis **vrai Live Call dans un profil VS Code isolé** : personnages visibles,
arrivée/activité/fin cohérentes, modèle et tâche lisibles, erreurs et catégorie
visibles, sélection/épinglage/historique/replay/animations préservés.
Aucune génération nécessaire pour ce périmètre de recette.

Les huit tests du collecteur de la livraison précédente sont une base réutilisable,
pas une preuve d’intégration Live Call. Aucun test d’affichage modifié ou nouveau
prototype n’a été exécuté dans cette étude.

## 8. Activation et rollback proposés — non exécutés

Si changement amont : utiliser ensuite une version officielle contenant le
support, avec validation préalable dans un profil isolé. Aucun envoi au mainteneur
ou publication n’a été effectué.

Si dérivé local approuvé :

1. Conserver le VSIX officiel **1.40.0** récupéré par interface supportée et son
   empreinte, la version active et une sauvegarde privée ciblée des préférences
   Standup. Ne pas sauvegarder de secrets inutiles.
2. Construire le dérivé dans un checkout séparé sur la base qualifiée, conserver
   MIT, documenter précisément les écarts et le packaging. Pas de modification
   dans ~/.vscode/extensions. Choisir explicitement l’identité et le traitement
   des mises à jour pour éviter deux serveurs et deux panneaux concurrents.
3. Installer et tester dans un profil VS Code isolé avec ses propres préférences,
   en réutilisant les vraies traces en lecture seule ; conserver la version normale.
4. Seulement après validation distincte du déploiement : installation via VSIX
   supportée, configuration ciblée et vérification du Live Call normal.
5. Rollback : fermer l’hôte modifié, désinstaller le dérivé par VS Code, réinstaller
   le VSIX officiel conservé si remplacement ; restaurer seulement les préférences
   Standup effectivement modifiées. Vérifier version, sessions, scène et absence
   du processus de collecte ajouté. Ne pas toucher aux données Codex/routeur.

Un profil isolé permet d’abandonner le candidat sans altérer la version normale.
Le rollback réel d’un dérivé reste NOT_TESTED puisqu’aucun dérivé n’existe.
L’installation actuelle de agent-observer n’est ni supprimée ni désactivée par
cette étude ; sa désactivation éventuelle est une décision séparée.

## 9. Statuts et point d’arrêt

- **VERIFIED** : extension active, licence, architecture installée, identité des
  trois fichiers avec le commit amont, mécanismes de scène/flux, liens/noms natifs.
- **PARTIAL** : faisabilité déduite du code ; tâches détaillées et provenance
  fournisseur non disponibles par les seuls champs existants.
- **IMPLEMENTED** : ce diagnostic uniquement. Aucun support Live Call ajouté.
- **BLOCKED pour l’implémentation locale** : accord explicite requis pour un
  dérivé modifiant Agent Standup, conformément au rectificatif utilisateur.
- **NOT_TESTED** : prototype, animations enrichies, régression globale et rollback
  d’une version modifiée.

**Prochaine décision minimale : choisir une évolution amont ou autoriser un
prototype dérivé isolé à patch limité.** Aucun remplacement de l’extension normale
ne découle d’un simple accord pour un prototype.

Aucune modification P3-A/P3-B, moteur, proxy, adaptateur, hooks RTK, routeur MCP,
catalogue, modèle, clé, budget ou permission. Aucun commit/push, aucune inférence.
Arrêt après l’étude demandée.
