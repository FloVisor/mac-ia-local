# P3-C — dérivé Agent Standup livré en environnement isolé

Statut : **PASS dans le périmètre isolé**. Aucune bascule quotidienne effectuée.

## Résultat fonctionnel

Dérivé MIT Agent Standup 1.40.0, commit amont
`04c6f42c3030396f48ea16c0581bb1824c963798`, identité
`local-xithi.agent-standup-p3c`, version `1.40.0-p3c.1`.
Sources et procédure : [agent-standup-local/README.md](agent-standup-local/README.md).
Le VSIX est construit et installé uniquement dans le profil de revue sous
`artifacts/agent-standup-p3c/`. Le lanceur isolé a été exécuté.

Live Call conserve sa scène, ses personnages SVG animés, ses sessions, son arbre,
son replay et ses détails. Le collecteur partagé d’agent-observer fournit les
participants supplémentaires ; aucune troisième interface n’est créée.

Sur des traces existantes, la recette retrouve Lovelace, Confucius et Harvey sous
leur session Codex parente, avec nom, chemin de tâche, modèle déclaré et état
completed. La tâche llm-router est distincte, avec état failed, six transitions,
37 tokens et erreur structurée. Son parent absent des traces disponibles est
explicitement marqué « Session référencée · trace absente ». Aucun processus actif
ni succès n’est inventé. Les modèles Codex sont déclarés ; l’alias demandé au
routeur n’est jamais présenté comme preuve du modèle exécuté.

## Validation exécutée

| Contrôle | Résultat |
| --- | --- |
| Construction VSIX et syntaxe modules/script navigateur | PASS |
| Collecteur, suite finale | 8 PASS |
| Intégration agent-observer, résultat précédent conservé | 3 PASS |
| Pont Standup : hiérarchie, états, provenance et redémarrage | 3 PASS |
| Suite amont initiale | 43 PASS, 4 FAIL, 1 SKIP |
| Reprise ciblée des quatre échecs après correction | 4 PASS, 0 FAIL |
| Non-régression navigateur Live Call | 10 PASS, 0 FAIL, 0 SKIP |
| Extension Host VS Code isolé : activation et ouverture réelle | PASS |
| Rendu Live Call du serveur de cette instance : natifs/MCP/arbre/rechargement | PASS |
| Mise à jour candidate sur la même base, sans promotion | PASS |

La suite amont complète n’a pas été répétée après correction : les 43 succès
antérieurs sont conservés et les quatre échecs repris ciblément. Le test amont
ignoré ne devient pas artificiellement PASS. Les dix tests Live Call séparés
couvrent notamment ordres, reprise, absence de doublons et comportements animés.

La validation visuelle associe une véritable ouverture du webview par l’Extension
Host isolé et des captures Chrome automatisées du même serveur Live Call. Les
captures ont été inspectées : noms et modèles lisibles, personnages présents,
arbre parent/enfants et détail MCP distinct. Ce n’est pas une capture native de
la fenêtre VS Code. Aucun appel réel de traduction, voix ou génération distante
n’a été testé ; le lanceur de revue les bloque avec P3C_OFFLINE_TEST=1.

Preuves locales privées sous `artifacts/agent-standup-p3c/` :
`vscode-result.json`, `visual-done.json`, `live-call-native.png`,
`live-call-hierarchy.png`, `live-call-mcp.png`, `upstream-tests.txt`,
`upstream-targeted.txt`, `live-regression.txt`, `installation-check.json`,
`update-candidate/comparison.json` et `local-changes.patch`.

VSIX SHA-256 :
`9a1f3dc06e30a51346f8f3335072452ef41b705cf5d579fadda1df734dd3d811`.
Les fichiers runtime installés correspondent à ceux validés en mode développement.
VS Code ajoute ses métadonnées au manifeste lors de l’installation.

## Préservation, limites et risques

L’extension officielle Agent Standup 1.40.0 reste installée : ses quatre fichiers
principaux ont été contrôlés inchangés. Aucun dérivé n’est installé dans le
répertoire d’extensions quotidien. Aucune modification de l’extension officielle
Codex, des hooks/RTK, config.toml, P3-A/P3-B, MCP, OpenClaw, moteurs, catalogues,
clés ou budgets ; aucune inférence payante, aucun commit/push.

La collecte utilise les événements structurés d’origine, jamais une sortie RTK.
Elle est bornée : lecture au plus toutes les 5 s, découverte 30 s, fenêtre
14 jours/200 fichiers, 200 tâches, 20 transitions MCP et 64 transitions natives.
Pas de nouvelle journalisation de prompts, réponses ou secrets ; cache mémoire.
Les messages originaux de la session parente restent traités par le chemin amont.

Les formats de traces Codex et la base routeur restent des dépendances de lecture
susceptibles d’évoluer. L’association MCP au parent est déclarative. Sans preuve
fournisseur, actual_model reste inconnu. Un état silencieux trop ancien devient
unknown, pas completed. La recette exploite des traces existantes et des tests
synthétiques ; elle ne lance aucune nouvelle délégation réelle.

Le mécanisme de mise à jour compare les points d’intégration et produit un build
candidat séparé avec patch local. Il refuse une dérive de contexte et ne promeut
rien. Une version future reste à qualifier ; le téléchargement d’une nouvelle
version n’a pas été testé dans cette recette hors inférence.

## Lancement et rollback

```sh
bash codex/agent-standup-local/launch-isolated.sh
```

Rollback immédiat : fermer cette fenêtre isolée. L’environnement quotidien ne
nécessite aucune restauration. La désinstallation facultative du seul dérivé
isolé est documentée dans le README ; conserver agent-observer et les preuves.

**Point d’arrêt respecté :** dérivé fonctionnel présenté pour revue ; remplacement
ou bascule de l’extension quotidienne uniquement après accord utilisateur distinct.

## Déploiement quotidien autorisé — 2026-10-21

**Statut quotidien : PARTIAL — installé, rechargement et confirmation visuelle requis.**
Cette section complète la qualification isolée ; elle ne transforme pas ses captures
en validation graphique quotidienne.

### Cible, préparation et installation

Profil **Default**, confirmé par les associations de projets du VS Code actif,
sans profil nommé supplémentaire :
`~/Library/Application Support/Code/User`, extensions `~/.vscode/extensions`.
Version initiale : `doublegeste.agent-standup` **1.40.0**.

Le VSIX préalablement qualifié a été installé sans reconstruction, SHA-256
`9a1f3dc06e30a51346f8f3335072452ef41b705cf5d579fadda1df734dd3d811`.
Le contenu installé est identique au paquet ; seul `__metadata` ajouté par VS Code
est exclu de la comparaison du manifeste.

Sauvegarde locale privée : `artifacts/agent-standup-p3c/daily-deployment/` :

- `official-extension/` : copie complète de l’extension officielle.
- `agent-standup-official-1.40.0.vsix` : paquet de restauration issu des fichiers installés.
- `official-preferences/` : préférences/personnages/sélections Live Call existants.
- `settings.json`, `storage.json`, `extensions.json` et sauvegarde SQLite cohérente
  `state-backup.vscdb` : état antérieur pour audit/récupération ciblée.
- `preflight.json` : empreintes et métadonnées de préparation.

La restauration du paquet officiel a été effectivement testée via la CLI dans un
répertoire temporaire, puis sa version et son serveur comparés. Ces répertoires
temporaires ont été retirés ; le profil isolé de qualification est conservé.
Aucune écriture directe dans les bases internes VS Code n’a été faite. Ne pas
restaurer toute la base utilisateur par-dessus un profil actif.

Aucun changement concurrent des fichiers officiels n’a été détecté entre leur
sauvegarde et la bascule (contrôle des mtimes). Un verrou local de déploiement a
encadré la préparation ; ce contrôle ne constitue pas une exclusion universelle
des autres programmes.

Installation via CLI officielle : désinstallation de `doublegeste.agent-standup`,
puis installation du VSIX `local-xithi.agent-standup-p3c` **1.40.0-p3c.1**.
Une seule identité Agent Standup reste enregistrée. Le paquet qualifié conserve
son identité distincte et ses commandes `p3cStandup.*` ; aucun besoin de modifier
son identifiant pour les préférences, copiées octet pour octet vers
`~/.config/agent-standup-p3c/` depuis `~/.config/agent-standup/`.
Aucun réglage explicite `agentStandup.*` utilisateur ou du projet courant n’était
à migrer ; les paramètres utilisateur n’ont pas été modifiés. L’état interne de
webview de l’ancienne identité n’est pas transposé ; un onglet et son point de
replay peuvent devoir être rouverts. Les journaux de sessions sont intacts.

### Vérifications quotidiennes et limites

| Contrôle après installation | Résultat réel |
| --- | --- |
| Registre : dérivé 1.40.0-p3c.1 seul Agent Standup installé | PASS |
| Contenu installé conforme au VSIX qualifié | PASS |
| Paramètres utilisateur et préférences officielles inchangés | PASS |
| Copie des préférences du dérivé identique | PASS |
| Autres extensions préservées | PASS, normalisation de sérialisation URI seulement pour agent-observer |
| Lecture des sessions par le serveur du code installé | PASS, contrôle non génératif séparé |
| Trois sous-agents sous main : Lovelace, Confucius, Harvey | PASS, événements existants |
| Tâche llm-router distincte, état failed, profil testing | PASS |
| Modèles déclarés/demandés, exécution inconnue sans preuve | PASS |
| Durées issues des traces | PASS : ~147220, 500061, 346399 ms ; MCP 10796 ms |
| Actualisation après 5,2 s, sans doublons ni erreur collecteur | PASS sur le serveur de contrôle |
| Lecture directe des événements, sans compression RTK | PASS ; hooks inchangés |
| Ouverture Live Call dans le webview quotidien après rechargement | NOT_TESTED |
| Personnages animés, arbre, navigation et fonctions historiques quotidiens | NOT_TESTED |
| Mesure prolongée de charge quotidienne | NOT_TESTED ; limites de collecte déjà qualifiées conservées |

Le premier contrôle HTTP a reçu 404 pour une session avant initialisation du
collecteur ; après attente bornée de disponibilité, le contrôle réussit. Aucun
journal ni session n’a été modifié pour le faire passer. Le serveur de contrôle,
lancé depuis les fichiers installés avec P3C_OFFLINE_TEST=1, a été arrêté. Il ne
prouve pas l’activation du dérivé dans les Extension Hosts quotidiens déjà ouverts.
Aucune batterie de qualification n’a été relancée, aucune inférence déclenchée.

Les anciennes fenêtres peuvent conserver le code officiel chargé jusqu’au
rechargement. Aucun redémarrage complet ni arrêt forcé de VS Code n’a été effectué.
**Action utilisateur restante :** dans chaque fenêtre quotidienne utilisant Agent
Standup, exécuter **Développeur : Recharger la fenêtre**, puis **Agent Standup: Open**.
Confirmer visuellement personnages/présentation habituels, sessions Codex, sous-agents
sous leur parent et catégorie distincte llm-router. Sans cette confirmation,
le critère graphique quotidien reste NOT_TESTED et le statut global PARTIAL.

### Rollback opérationnel et maintenance

```sh
bash artifacts/agent-standup-p3c/daily-deployment/rollback-official.sh
```

Désinstalle uniquement le dérivé et réinstalle le paquet officiel local 1.40.0.
Recharger ensuite les fenêtres. Les préférences officielles originales sont
restées en place ; aucune restauration n’est normalement nécessaire. Si elles
ont été modifiées ultérieurement et qu’un retour exact est voulu, fermer d’abord
les vues Live Call et copier `daily-deployment/official-preferences/prefs.json`
vers `~/.config/agent-standup/prefs.json` après sauvegarde du fichier courant.
Les paramètres VS Code étant inchangés, ne pas remplacer settings.json en bloc.

Réinstallation ultérieure du dérivé validé :

```sh
bash artifacts/agent-standup-p3c/daily-deployment/reinstall-p3c.sh
```

Ce script vérifie l’empreinte avant installation et conserve les préférences du
dérivé. Ne pas exécuter ces scripts simultanément ; recharger les fenêtres après.

Le registre VS Code indique **source=vsix, pinned=true** pour le dérivé. Son identité
locale distincte empêche une version officielle de remplacer ce même identifiant.
Aucun réglage global de mise à jour ni réglage d’une autre extension n’a changé.
Pour les mises à jour officielles futures, utiliser le mécanisme candidat décrit
plus haut, comparer les changements, qualifier séparément puis décider explicitement
la promotion. Ne pas réinstaller l’officiel parallèlement au dérivé.

Preuves supplémentaires : `deployment-result.json`, `installed-registry.json`,
`installed-runtime-check.json` sous `daily-deployment/`.
Aucun commit/push, aucun changement des composants protégés. Mission arrêtée après
installation et contrôles accessibles ; confirmation graphique quotidienne attendue.

## Correctif quotidien — compteurs participants, 2026-10-21

À la demande utilisateur, installation directe en profil Default de
**1.40.0-p3c.2**. La pastille native `.tk` affiche maintenant les tokens du
collecteur pour les sous-agents et tâches MCP, avec le même format ⚡ que le
parent. Total fourni prioritaire ; sinon entrée + sortie si les deux sont connus.
Aucune valeur inventée pour les données absentes, aucun ajout au cumul parent.
Les rafraîchissements natifs et les mises à jour des métadonnées restaurent le
compteur. Survol : total exact et ventilation entrée/sortie disponible.

Construction/syntaxe PASS ; contrôles ciblés PASS : MCP 68+3=71, natif 20+5=25,
zéro, absence, préservation du parent, restauration après effacement et changement
de valeur. Installation CLI PASS, fichiers installés comparés au VSIX PASS,
pinned=true. Aucune nouvelle inférence ni batterie complète. Profil isolé non utilisé.

VSIX SHA-256 : `89ec62f38f32bbbdce6c9d8ef7c686d0d5dabe08b5894f52270bb6f6198cbc52`.
Ancien VSIX qualifié conservé sous
`daily-deployment/agent-standup-p3c-1.40.0-p3c.1.vsix` ; le script
`reinstall-p3c.sh` pointe désormais explicitement vers ce paquet de retour.
Le rollback vers l’officiel reste disponible sans changement. Préférences,
sources de collecte et composants protégés inchangés.

Les captures utilisateur précédentes confirment l’affichage quotidien des
participants natifs et MCP et les 71 tokens dans les détails. L’affichage du
nouveau badge après ce correctif reste **NOT_TESTED graphiquement** : recharger
la fenêtre et confirmer ⚡71 sur la vignette llm-router.

## Incident de sélection historique — 2026-10-21

Correctif quotidien **1.40.0-p3c.3** installé ; statut **PARTIAL**, rechargement
et vérification graphique requis. Collecteur fonctionnel : les trois historiques
sont toujours présents dans la timeline du serveur quotidien. Limites amont des
sélecteurs (30 sessions / tableau 12 h) corrigées dans le pont et le sélecteur
Live Call. Préférence de retrait des agents terminés conservée. Rapport, preuves
et rollback : [27-agent-standup-p3c-incident.md](27-agent-standup-p3c-incident.md).
