# Approbations natives — 0.2.1

Plugin local OpenClaw 2026.10.5. Politique fermée par défaut, approbation native
`allow-once` / `deny`, sans autorisation persistante. Les paramètres et le plan
sont figés ; le droit est lié à l’agent, la session et l’appel, puis consommé une fois.

| Voie | Politique |
|---|---|
| `gmail_read` | Perso ; commandes gog de lecture à arguments contrôlés, sans shell |
| `contacts_read` | Perso ; Contacts Apple iCloud, status/containers/search/get sans shell |
| `gmail_send` | Perso ; destinataires, objet, corps et pièces jointes inline approuvés |
| Graph lecture | Pro ; libre |
| Graph `send_exact` | Pro ; payload exact, pièces jointes inline, approbation native du connecteur patché |
| Graph `send_draft` | Refusé : brouillon distant mutable |
| `imessage_read` | Lecture contrôlée |
| `imessage_send` | Texte et destinataire explicites ; sans pièces jointes ni bascule SMS implicite |
| `system_read` | Commandes de lecture prédéfinies |
| `system_action` | Actions prédéfinies, approbation et préimage vérifiée ; suppression mémoire comprise |
| `file_change` | Écriture/édition ; mémoire propre libre, autres fichiers approuvés avec préimage |
| Outils bruts `exec/process/code_execution/write/edit/apply_patch/message` | Désactivés par configuration |
| BookStack | Lectures reconnues libres ; mutations reconnues approuvées ; import non qualifié refusé |
| Orion | Découverte libre pour Pro ; exec_tool libre uniquement après un vrai contrat `access: read` dans la même session |
| Outline | Lectures reconnues libres pour Pro ; mutations bloquées |
| Outils inconnus | Refus conservateur |

Les chemins sont canoniques ; liens vers un autre workspace, liens physiques et
fichiers de contrôle sont protégés. L’exception mémoire couvre uniquement
`USER.md`, `MEMORY.md` et `memory/` de l’agent. Les envois automatiques passant
par `message_sending` sont annulés. La taille native de l’aperçu est bornée à
512 caractères : un contenu non présentable est refusé, jamais tronqué.

`tool_describe` est libre. `tool_call` classe la cible et ses arguments, puis le
catalogue natif réapplique les hooks à la cible. Aucun accès n’est accordé à
l’enveloppe sans contrôler son contenu. Les accords d’envoi ne sont pas relayés
par une enveloppe : utiliser le sender dédié directement ; sinon l’action reste
bloquée. Les contrats Orion proviennent exclusivement des résultats réels de
`get_contract`, jamais des arguments du modèle ; cache de cinq minutes lié à
l’agent, la session, le registre et l’outil. Après expiration/reload, relire le
contrat gratuitement. Les mutations MCP non qualifiées restent bloquées.

## Graph maintenable

`graph-patch/manifest.json` fixe la version amont, le commit et le SHA256 du
bundle qualifié. `apply-source-patch.py` prépare le patch sur la source exacte ;
construire et installer l’archive avec le CLI officiel. Aucune modification du
runtime compilé OpenClaw. Une divergence du bundle bloque les mutations Graph
jusqu’à requalification. Les pièces jointes sont limitées à 10 et 3 MiB au total.

## Recette et limites

```sh
node --test openclaw/send-approval/test/*.test.mjs
openclaw plugins reload send-approval microsoft-graph --json
openclaw gateway call health --json
```

Les tests neutralisent les transports et le broker natif. Aucun message réel
n’est envoyé, aucune suppression réelle n’est utilisée pour la recette.
L’affichage du dialogue dans le client macOS et une décision humaine de bout en
bout restent à valider. Ce plugin ne constitue pas une isolation du système
contre un opérateur local ; une nouvelle voie d’outil ou de canal doit être
qualifiée avant activation. Voir le rapport de validation du 2026-10-20.


### Consultations Context7 via Docker Gateway Pro

Exception fermée pour `docker_gateway_pro__resolve-library-id` (`libraryName`, `query`) et `docker_gateway_pro__query-docs` (`libraryId`, `query`, `language` facultatif), agent `main` uniquement. Champs inconnus et chaînes vides refusés ; dispatch direct/différé contrôlé. Les contrats officiels réellement découverts portent `readOnlyHint=true`, `destructiveHint=false`. Les autres outils, agents et protections conservent leur politique. Test : `test/context7.test.mjs`.
