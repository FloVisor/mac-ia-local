# Incident P3-C — diagnostic quotidien du 2026-10-21

Statut : **PARTIAL**, confirmation graphique quotidienne requise.

## Installation réellement observée

Serveur PID 30188, port 60772, lancé par Extension Host quotidien depuis
`~/.vscode/extensions/local-xithi.agent-standup-p3c-1.40.0-p3c.2/server.js`.
Identité unique enregistrée : `local-xithi.agent-standup-p3c`, VSIX épinglé.
Les fichiers p3c.2 correspondaient intégralement au VSIX qualifié (hors métadonnées
VS Code). Aucun remplacement officiel démontré. Une instance isolée distincte
reste ouverte, PID serveur 20203 ; son port 58507 n'est pas celui diagnostiqué.
Des fenêtres quotidiennes anciennes ont activé l'officiel avant la bascule ;
leur dernier journal d'activation ne suffit pas à certifier leur code courant.

## Cause démontrée et limites

Le parent historique `01a13a9b-ac78-7b00-86eb-a1a8ca464d78` est au rang 89
par mtime dans les traces disponibles. Le collecteur le découvre et l'API du
serveur quotidien renvoie Lovelace, Confucius et Harvey sous `main`, completed,
modèle gpt-6-astra déclaré, sans erreur collecteur ni doublon.
Le sélecteur replay demande seulement 30 sessions Codex. Le sélecteur Live Call
utilise /api/board, qui limite les sessions à 12 heures. Les historiques deviennent
donc inaccessibles dans ces listes malgré une timeline toujours disponible.
La préférence quotidienne vanish=true retire aussi normalement les participants
terminés après deux minutes ; elle est conservée. Son effet graphique sur la vue
ouverte n'a pas été constaté et ne doit pas être présenté comme cause exclusive.

L'API quotidienne expose aussi Curie et James terminés, gpt-6.1-sol déclaré,
et une délégation llm-router review completed, alias local oMLX demandé,
modèle exécuté inconnu. La délégation historique testing failed reste disponible
sous sa session référencée. Aucun de ces états ne prouve un sous-agent actif.
Pas de rupture de format/localisation démontrée ; le chemin de lecture du
collecteur fonctionne avec les traces et tâches actuelles, sans compression RTK.
Aucun lien causal démontré avec P3-A, P4 ou RTK.

## Correction appliquée

p3c.3 conserve dans les sessions sélectionnables les parents déjà connus du
collecteur, sans étendre ses scans ni changer sa logique. Le sélecteur Live Call
fusionne ses sessions récentes avec les sessions historiques, marquées historique
et idle au niveau de la liste ; les états d'exécution restent issus des traces.
Déduplication par projet/id. Aucun changement des préférences, personnages,
animations, sessions, moteurs, modèles, budgets, permissions ou composants protégés.

Installé par CLI dans le profil Default. 235 fichiers comparés au VSIX : PASS.
SHA-256 : `92fea3f8c104e68c9c2914a36ecc78e32afd6df74d01acafc3604007fb282043`.
Construction et syntaxe : PASS. Tests ciblés du pont et sélecteur : 5 PASS.
Serveur candidat hors génération : parent historique sélectionnable et trois
participants hiérarchisés, modèles et états corrects, sessions sans doublons : PASS.
L'ancien serveur quotidien p3c.2 reste chargé jusqu'au rechargement de fenêtre.
Aucune confirmation graphique p3c.3, ni validation des animations après correction.
Aucune inférence déclenchée, aucun commit/push.

## Vérification utilisateur manquante

Développeur : Recharger la fenêtre, puis Agent Standup: Open dans le profil quotidien.
Dans le sélecteur Live Call, rechercher le titre du parent historique (ou utiliser
le replay pour le retrouver), ouvrir la session et vérifier les trois noms sous
main, modèles déclarés et états completed. Vérifier une session récente contenant
llm-router, la distinction MCP, les détails/tokens, l'arbre et les animations.
Si nécessaire, désactiver temporairement via l'interface « Retirer les agents
terminés (2 min) », puis rétablir la préférence après contrôle. Envoyer des captures
Live Call et arbre. Aucun PASS global avant cette vérification.

## Retour arrière

`bash artifacts/agent-standup-p3c/incident-20261021/rollback-p3c2.sh`

Vérifie le hash et réinstalle le VSIX p3c.2 sauvegardé, puis recharger la fenêtre.
Script préparé, non exécuté. Retour officiel préexistant toujours disponible via
`artifacts/agent-standup-p3c/daily-deployment/rollback-official.sh`.
Ne pas restaurer les bases internes VS Code. Sources précédentes p3c.js/BASE.json
conservées dans le dossier incident ; le retour runtime n'annule pas ces sources.
Preuves : candidate-check.json et installed-check.json dans ce même dossier.
