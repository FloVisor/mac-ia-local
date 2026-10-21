# Reprise DeepSeek — 20 octobre 2026

## État retrouvé

Journal fourni : `~/Downloads/Texte collé(20261020-201358).txt` (831 lignes).
Exploration des approbations natives, hooks, limites d’affichage, allowlists et
connecteur Graph. Aucune création de plugin ni configuration activée dans le
journal ou sur disque. Configuration initiale égale à celle sauvegardée.
Sauvegarde retrouvée : `~/.openclaw/backups-send-approval-20261020-220331`.
JSON lisibles, SQLite vérifié en lecture seule immutable : `integrity_check=ok`.
Aucune restauration ni écriture SQL. Inventaire/empreintes : `backup-check.json`.

## Récupération et modifications

Réutilisation des choix établis : plugin maintenable, hook natif
`before_tool_call.requireApproval`, décisions `allow-once`/`deny`, conservation
OpenClaw.app, runtime et règles exec. Nouveau code : `openclaw/send-approval/`.
Installation via CLI officielle `plugins install --link ... --force`.
Seul le sous-arbre `plugins` de la configuration est modifié par l’installateur ;
les entrées préexistantes, agents, restrictions, routage, profil coding,
alsoAllow et modèles sont identiques à la sauvegarde (`preservation.json`).
Les deux AGENTS.md des workspaces reçoivent un paragraphe de fonctionnement
natif ; préimages ciblées : `workspace-preimages.json`.
Travaux BookStack concurrents préservés. Aucune modification du runtime compilé.

## Tests

`node --test openclaw/send-approval/test/*.test.mjs` : **18/18 PASS**,
sortie `tests.txt`. Sept décisions dans le moteur installé : accord ponctuel,
refus, timeout, annulation, absence de décision, allow-always interdit, décision
inconnue. Erreur de transport, veto et exception de hook : blocage. Paramètres
figés malgré modification pendant l’attente ; nouvelle action = nouvelle demande.
Contrôle d’alias/scripts, fichiers, signatures distantes, doublons de paramètres,
apercus longs et séparation Gmail Perso. Les décisions acceptées sont uniquement
simulées, avec exécution neutralisée (compteur). Aucun broker de production
n’est remplacé. Restrictions de configuration Pro/Perso vérifiées inchangées ;
pas de campagne conversationnelle réelle entre les deux agents.

Test réel Gateway `plugin.approval.request` : demande factice sans outil,
ID `plugin:fd713411-fb85-47b3-aafa-4de6df3cd03c`, statut `accepted`,
`deliveryRoute=approval-client`, timeout 1000 ms. Aucun accord envoyé par Codex.
Liste ultérieure des approbations : `[]` (demande expirée, aucun reliquat).
Aucune commande gog/imsg d’envoi exécutée, aucun mail/SMS/iMessage envoyé.

## Déploiement

Rechargement officiel via `plugins reload send-approval --json` : voir
`deployment.json` pour génération et empreinte du code actif. Le retour vient de
la Gateway, pas seulement d’une inspection locale. `health.json` confirme le
plugin chargé, aucune erreur de plugin, hot reload actif et iMessage connecté.
`openclaw config validate` : PASS. Aucun redémarrage de service.

## Limites et blocages

**Mission fonctionnelle partielle.** Les contenus inline courts de Gmail et des
messages passent par l’approbation native. Outlook send_draft, fichiers, pièces
jointes, messages dépassant l’aperçu natif et chemins CLI OpenClaw/AppleScript
sont bloqués. Les brouillons restent disponibles. Pas d’autorisation permanente.

BLOCKER Outlook : Graph 3.14.1 n’affiche pas le contenu du brouillon et ne lie
pas son état distant à l’accord. Preuve dans son `dist/index.js` :
`mutationApprovalText` décrit des destinataires indisponibles ; `mailWrite`
POSTe `/me/messages/{id}/send` avec un corps vide sans snapshot du contenu.
Le magasin `NativeApprovalSnapshotStore` lie agent/session/outil/arguments,
pas les destinataires ou le corps distants. Le plugin local interdit donc cet
appel avant le hook Graph existant, sans contourner l’autorisation native.
NEXT REQUIRED ACTION : correction maintenable du connecteur Graph garantissant
l’envoi du contenu exactement approuvé, puis recette neutralisée avant déblocage.
Aucun mail de signalement envoyé, car la mission interdit tout envoi réel.

NOT_RUN : affichage visuel du dialogue, décision humaine de bout en bout,
envoi réel, couverture universelle des autres outils/canaux. Le hook n’est pas
un sandbox et les réponses automatiques de canal ne sont pas couvertes.
