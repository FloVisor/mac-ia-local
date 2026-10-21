# Régression MCP OpenClaw — correction 0.2.1

## Cause exacte

Le hook before_tool_call de send-approval 0.2.0 refusait :
- l'enveloppe native `tool_call`, utilisée pour tous les outils différés ;
- `orion__list_registries` ;
- tous les `orion__exec_tool`, sans distinguer accès read/write.

`orion__search_tools` était autorisé individuellement, mais son enveloppe était
bloquée avant l'appel. La dernière trajectoire Pro montre tool_search réussi,
puis trois tool_call en erreur. Le récit du modèle sur une autorisation native
manquante n'était donc pas une preuve de droits métier insuffisants.

Comparaison avec la sauvegarde précédant 0.2.0 : profil coding et alsoAllow
orion__* conservés, deny Perso orion/outline/Graph conservés. Aucune suppression
Orion du catalogue Pro : probe réel Orion, 15 outils serveur (19 surfaces natives
avec ressources/prompts), cinq registres disponibles. Les appels directs RPC
aux noms différés rendaient not_found : ce n'est pas le chemin d'exécution agent.
Le test probant utilise donc le catalogue et l'enveloppe natifs.

## Correctif appliqué

- `openclaw/send-approval/index.js` : classement de la cible tool_call,
  tool_describe libre, hook after_tool_call observant les contrats serveur.
- `lib/mcp-reads.js` : découverte Orion gratuite pour Pro ; exec_tool autorisé
  sans confirmation seulement après un vrai résultat get_contract `access: read`
  dans la même session. Cache cinq minutes, lié agent/session/registre/outil.
  Aucune confiance dans access/readOnly fourni dans les paramètres du modèle.
  Lectures Outline effectivement exposées rétablies. Mutations inconnues bloquées.
- `lib/contacts.js`, manifeste, package : outil contacts_read à argv fixe,
  lecture Contacts Apple via perso-contacts, uniquement Perso ; version 0.2.1.
- Configuration officielle : ajout contacts_read à alsoAllow et deny Pro.
  Aucun autre changement de configuration (preservation-check.json).
- Tests ciblés et README ; ajout documentaire dans integration-pitfalls.md.

Aucun shell arbitraire réouvert. Les expéditeurs dédiés restent soumis au
contrôle technique natif ; les enveloppes ne transmettent pas leurs droits.
Les autres communications, dont RCS non qualifié, restent bloquées lorsqu'aucun
chemin de confirmation exacte n'est qualifié. Les lectures n'exigent pas d'accord.

## Preuves réelles

| Test | Résultat |
|---|---|
| Pro list_registries | PASS, cinq registres, zéro approbation |
| Pro search_tools GLPI | PASS, outils read et write correctement distingués |
| Pro get_contract/search_glpi_ticket | PASS, contrat read réel |
| Pro exec_tool recherche GLPI | PASS, ticket_status=en_cours, Range=0-2, aucun filtre d'entité : trois tickets de trois entités distinctes autorisées |
| Approbations MCP pendant ces lectures | Zéro requête au broker natif instrumenté |
| Perso, filtrage natif MCP | PASS, Orion/Outline absents après application de son deny existant |
| Simulation SMS et email | PASS, deux demandes natives once/deny, broker deny, zéro exécution d'envoi |
| Tests de politique complets | PASS, 31/31, release-tests.txt |
| Perso Gmail via Gateway | PASS, recherche neutre vide |
| Perso Contacts via Gateway | PASS, accès déjà authorized, carnet iCloud ; aucune modification TCC |
| Pro Microsoft 365 via Gateway | PASS, outlook_mail_read/list_folders, limite 1 |
| Perso BookStack via Gateway | PASS, recherche pages neutre vide |
| Perso diagnostic système via Gateway | PASS, system_read/os |
| Santé Gateway après déploiement | PASS, health-after-deploy.json |

Les quatre appels MCP Pro utilisent les vrais outils matérialisés par les
factories OpenClaw installées, le vrai catalogue/tool_call, les hooks et le
transport Orion réels. Ce test isolé ne crée aucun tour LLM, aucune conversation
et ne modifie aucun historique. Source et résultats : native-live-read.mjs,
native-live-read-business-result.json. Le premier passage attestait le succès
technique ; le second, avec examen du résultat métier, confirme les trois tickets
et évite de confondre une réponse transport avec un succès GLPI.

Les autres lectures sont réellement passées par le Gateway actif ; preuves
`gateway-read-*.json`. Aucun envoi réel ni écriture métier effectué.

## Déploiement et préservation

`deploy-consented.json` : ok=true, restartRequired=false, génération 3,
entrée active du plugin pointant sur ce dépôt. Consentement de capacité par
l'option officielle --accept-capabilities, après revue du nouvel outil Contacts.
Une première tentative avait trouvé le Gateway arrêté ; le journal indique un
arrêt propre/SIGTERM, sans cause d'origine attribuable avec certitude.
Relance via OpenClaw.app, puis rechargement officiel réussi et service sain.

Sauvegarde privée avant correction :
`/Users/fngux2/.openclaw/backups-mcp-read-regression-20261020-225949/`.
Manifeste avec empreintes : preimages.json. Configuration originale sauvegardée.

Profil coding, routage, restrictions Perso et configuration Graph préservés ;
SHA256 du bundle Graph toujours qualifié. Aucun fichier du runtime Gateway ou
de ses 13 patches modifié. Aucun historique, dossier de conversation ou workspace
modifié. Aucune écriture directe de base SQLite, aucun changement SIP/TCC/macOS.
Les mutations et travaux BookStack concurrents ont été conservés. Aucun commit/push.

## Limites

Les mutations MCP non qualifiées restent bloquées : elles ne sont pas rendues
libres sous prétexte qu'exec_tool est nécessaire aux lectures. Après reload ou
expiration du cache, relire le contrat gratuitement. Les appels tool_call ambigus
sont refusés ; utiliser la forme native id/args. L'affichage du dialogue humain
n'a pas été retesté ; sa nécessité et ses décisions ont été exercées par le moteur
natif avec transports d'envoi neutralisés.
