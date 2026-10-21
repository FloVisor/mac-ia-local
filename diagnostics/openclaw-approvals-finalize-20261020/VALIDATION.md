# Finalisation des approbations OpenClaw — 2026-10-20

## État livré

Plugin `send-approval` 0.2.0 chargé par le Gateway OpenClaw 2026.10.5.
Santé réelle PASS (`health-startup-complete.json`). Le journal de démarrage
22:43:57 confirme les huit plugins dont `send-approval` et `microsoft-graph`.
Configuration et instructions des deux workspaces appliquées ; sauvegardes
privées référencées dans `preimages.json`. Aucun commit/push.

Le premier rechargement a échoué car les sept outils manquaient dans
`contracts.tools` du manifeste. Déclaration corrigée. Le Gateway s’est ensuite
arrêté proprement ; la tentative de reload suivante constatait son absence
(`deployment-manifest-fixed.json`). Relance par `open -a OpenClaw`, puis
contrôle de santé réussi. Aucun runtime OpenClaw compilé n’a été patché.

## Preuves

| Contrôle | Résultat / preuve |
|---|---|
| Politique, préimages, chemins canoniques, permissions ponctuelles et transports neutralisés | PASS, 26/26, `policy-tests-release.txt` |
| Connecteur Graph exact + composition des hooks | 13 contrôles réussis réutilisés dans `graph-tests.txt` ; dernière ancienne assertion allow-always corrigée et contrôle rejoué avec succès dans `graph-assertion-final.txt` (7 autres ignorés intentionnellement lors de ce rejeu ciblé) |
| Build Graph TypeScript/esbuild et paquet officiel npm | PASS ; `graph-package.txt`, manifeste dans `openclaw/send-approval/graph-patch/` |
| Lecture système par le vrai Gateway | PASS, `live-system-read.json` |
| Recherche Gmail neutre par le vrai Gateway | PASS, zéro résultat, aucune approbation, `live-gmail-read-40s.json` |
| Suppression des deux entrées gog générales | PASS par API CLI approvals get/set, `gog-allowlist-removal.json` |
| Outil brut exec et Gmail depuis Pro | Refusés : outils indisponibles, `live-block-*.json` |
| Graph send_draft via RPC | Refusé par restriction Gateway avant exécution ; ne constitue pas une preuve vivante du hook Graph |
| Affichage natif et décision humaine de bout en bout | NOT_RUN |
| Envoi Gmail/Outlook/SMS/iMessage réel ; suppression réelle | NOT_RUN volontairement |

La première recherche Gmail a dépassé le délai client 10 s ; le journal
indiquait une fin d’appel à 18,854 s. Une seconde lecture identique, avec un
délai client 40 s adapté à ce fait nouveau, a livré le résultat. Aucun échec
d’authentification observé. L’historique prouve que les anciennes demandes
Gmail étaient des approbations exec natives, pas celles du plugin ; la cause
exacte de chaque ancienne demande n’est pas établie.

## Couverture

- Lectures Gmail : outil dédié Perso, argv fixe gog readonly/no-send ; aucun
  shell ni permission gog globale. Téléchargements confinés au workspace.
- Gmail : payload inline exact, pièces jointes base64, création temporaire
  privée RFC822 après accord ; accord consommé une fois.
- Outlook : patch maintenable sur source amont 3.14.1, commit et SHA256 fixés.
  `send_exact` soumet le JSON approuvé directement ; `send_draft` mutable est
  bloqué. Empreinte du bundle contrôlée avant toute mutation Graph.
- SMS/iMessage : texte/destinataire/service explicites ; pièces jointes non
  qualifiées refusées. Aucun fallback SMS implicite.
- Approbations natives once/deny ; refus, expiration, transport en erreur,
  contenu modifié ou réutilisation ne donnent aucun droit. Aperçu natif borné
  à 512 caractères : contenu trop long refusé, pas de troncature silencieuse.
- Écriture via file_change : mémoire propre libre, ailleurs approbation et
  préimage ; chemins canoniques, liens physiques et autres workspaces protégés.
  Suppression de mémoire soumise à system_action et approbation.
- Système : lectures prédéfinies libres ; mutations prédéfinies approuvées.
  exec/process/code_execution/write/edit/apply_patch/message bruts désactivés.
- MCP/outils inconnus : refus par défaut ; seule découverte explicitement
  reconnue libre. BookStack : actions reconnues classifiées, import non qualifié
  refusé. Les réponses automatiques émettant message_sending sont annulées.

## Limites et suite minimale

Ce contrôle n’est pas un sandbox OS. Les accès d’un opérateur local et les
canaux/adaptateurs futurs n’émettant pas les hooks qualifiés restent hors preuve.
Les imports/MCP non qualifiés et contenus non présentables restent bloqués.
Le prochain contrôle requis est un essai humain du dialogue natif sur une
opération neutralisée, sans envoi réel. Aucun statut « tous chemins qualifiés »
n’est revendiqué. Un HTTP 202 Graph signifie acceptation, pas livraison ; aucune
preuve de livraison n’est revendiquée.

Source API Graph : https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0

Les modifications BookStack concurrentes ont été conservées. Voir
`config-verification.json` pour les chemins de configuration modifiés et les
contrôles de conservation ; aucune valeur secrète n’est publiée.
