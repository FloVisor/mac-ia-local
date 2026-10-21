# Orion direct Codex / OpenClaw Pro — livraison du 21 octobre 2026

**Décision appliquée : abandon de la migration Orion vers Gateway.** Une seule entrée globale `[mcp_servers.orion]` a été ajoutée dans `~/.codex/config.toml` avec `url = "https://owu.mix3cloud.net/mcp-front/mcp"`. Pas de secret dans cette déclaration. La connexion Gateway existante est préservée. OpenClaw Pro n'a pas été modifié : sa connexion directe fonctionne. Aucune modification de Perso, du skill partagé, des politiques send-approval, des Bearer, moteurs ou autres stacks. Aucun commit, push ou appel de génération payant supplémentaire.

## Configuration et OAuth réellement appliqués

Commande officielle installée exécutée : `codex mcp add orion --url https://owu.mix3cloud.net/mcp-front/mcp`. Elle a détecté OAuth, lancé le consentement natif et terminé par **Successfully logged in**. Callback local observé `http://127.0.0.1:54321/callback/<nonce>` ; aucun identifiant ou jeton OpenClaw copié. L'URL de consentement complète n'est pas conservée dans ce rapport. Le stockage est géré par Codex avec son réglage natif par défaut ; le backend précis de stockage n'a pas été inspecté.

Contrôle TOML : une seule clé orion, endpoint exact, aucun doublon. Après retrait logique de cette nouvelle entrée, la configuration correspond à la préimage, à l'omission de `mcp_servers.node_repl.args = []` près. Ce champ vide et son absence sont équivalents ; le changement annexe ne constitue pas une preuve de modification concurrente. Aucun autre paramètre préexistant ne diffère.

Préimage privée : `~/.codex/orion-direct-rollback-20261021/config.toml.before` (0600, répertoire 0700). Elle peut contenir des paramètres privés existants : ne pas l'ajouter au dépôt.

## Recette réelle

| Composant | Connexion | Skill | Appel réel | Statut |
|---|---|---|---|---|
| Codex CLI Orion | OAuth natif réussi, serveur connected | Découvert au chemin canonique et lu par fs/readFile | list_registries, search_tools, get_contract, exec_tool read | PASS client natif ; aucun tour modèle ajouté |
| Codex Desktop Orion | Client embarqué connecté avec la configuration globale | Découvert et lu par ce client | Même séquence, session GLPI effectivement retournée | PASS backend embarqué ; interface graphique NOT_RUN |
| OpenClaw Pro Orion | Connexion directe existante, découverte native réussie | Présent dans le prompt et lecture read du SKILL.md observée | Quatre outils Orion via tool_search/tool_call, aucune erreur | PASS |
| OpenClaw Perso — exclusion | deny orion__* et Gateway Pro conservés | Orion et Context7 absents de l'allowlist de skills | Preuve runtime antérieure réutilisée ; pas de nouveau tour Perso | PASS configuration et validation antérieure conservée ; nouveau test runtime NOT_RUN |
| Docker MCP Gateway | Profils codex/pro/perso conservés, accès Codex et Pro opérationnel | Context7 conservé Codex/Pro, absent Perso | Time + resolve-library-id + query-docs Codex frais ; Pro preuves antérieures + découverte fraîche | PASS sur ce périmètre, détails ci-dessous |

Les tests Codex utilisent de nouvelles instances natives app-server, sans turn/start et sans génération de modèle. Appels au transport MCP via mcpServer/tool/call ; la lecture métier n'est pas un texte produit par un modèle. Le contrat get_session_glpi retournait access=read, sans paramètres requis. exec_tool a utilisé params={} et registry=tool_glpi_wrapper. Le résultat contenait un objet session ; aucune mutation métier.

CLI testée : `/opt/homebrew/bin/codex`. Client embarqué Desktop testé : `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`. Les réussites de ce binaire ne sont pas présentées comme un test de l'interface graphique. Skill canonique : `/Users/fngux2/AI/skills/shared/orion/SKILL.md`, 9713 octets, SHA256 `8935561c4c23b1389af84af1aae8cbfd89efef7200ae5355d90c20048ccec47c`. Découverte native scope=user/enabled=true, symlink Codex vers le dossier partagé. Aucun skill dupliqué. Lecture technique dans le client natif confirmée ; pas de nouvelle conversation modèle Codex pour prouver une injection à un modèle payant.

Session Pro : `agent:main:orion-direct-final-20261021`, ID `89586ccf-5612-4609-9e0e-9b289493e02b`. Modèle local omlx Qwen configuré opérationnel, aucun fallback. Trajectoire native : skill lu puis appels réels orion__list_registries, orion__search_tools, orion__get_contract, orion__exec_tool. toolSummary indique zéro échec. Le résultat métier est expurgé par l'exporteur ; ne pas confondre le résumé modèle avec la preuve d'appel. Les événements imbriqués identifient le serveur orion et exec_tool, et le reçu technique confirme la réussite. Aucun changement de send-approval nécessaire : les alias directs restent ceux déjà qualifiés.

Perso : configuration actuelle vérifiée (`orion__*` et `docker_gateway_pro__*` refusés, orion/context7 absents des skills) ; recette d'exclusion déjà réalisée lors de la centralisation réutilisée puisque ces règles n'ont pas changé. Son résultat antérieur se trouve dans `artifacts/skills-centralization/perso-live.json` et le rapport de centralisation `/Users/fngux2/AI/skills/config/validation.json`. Aucun parcours Perso nouveau n'est revendiqué.

## Gateway : nettoyage ciblé

Inventaire natif actuel : codex = time/context7 ; pro = time/context7 ; perso = time. Aucune déclaration Orion dans ces trois profils. Recherche de chemins nommés Orion dans le déploiement et les catalogues des trois états : aucun résultat. Aucun conteneur (y compris arrêté) ni secret Swarm nommé Orion. Les précédents essais n'avaient ajouté aucun raccordement, routage, helper ou jeton ; le seul POST DCR avait été refusé avant création de client. Aucun élément expérimental actif identifié avec certitude, donc **aucune suppression**. Pas de prune, suppression de volume ou changement Traefik.

Time Codex et les deux outils Context7 ont été appelés réellement pendant cette recette. La Gateway Pro a été reconnectée avec son client natif OpenClaw et expose exactement time/Context7, sans diagnostic d'erreur. Ses appels Time/Context7 déjà validés ne sont pas répétés : preuves conservées dans [pro-tool-receipts.json](../context7-20261021/pro-tool-receipts.json). Perso ne déclare que time. Aucune rotation des trois Bearer ni modification d'isolation ; les accès Codex et Pro authentifiés fonctionnent toujours. Aucun nouveau test de refus croisé des tokens : validation antérieure conservée.

Rapports, preuve DCR et candidat documentaire orion.candidate.yaml conservés comme historique de la migration abandonnée. Ce candidat n'est pas déployé et ne doit pas être importé. Aucune recherche de compatibilité OAuth Gateway poursuivie.

## Test manuel Desktop restant

L'interface native Desktop n'est pas pilotable avec les outils disponibles dans cette session. Ouvrir une **nouvelle conversation Codex Desktop** pour recharger la configuration ; vérifier Orion connecté dans les paramètres MCP. Puis demander : « Utilise le skill partagé orion ; appelle list_registries, recherche get_session_glpi, lis son contrat et effectue cette lecture via exec_tool. Aucune écriture. » Vérifier les traces d'outils réelles et la lecture du SKILL.md canonique. Si l'application demande un consentement distinct, utiliser son flux habituel ; ne pas copier les jetons. Ce test UI reste NOT_RUN. Ne pas provoquer d'appel de modèle payant pour cette seule validation sans autorisation.

## Preuves et rollback

Synthèse expurgée : [direct-validation.json](direct-validation.json). Traces MCP et scripts natifs dans `artifacts/orion-direct/` (non versionnés) ; trajectoire Pro expurgée sous `~/.codex/orion-direct-rollback-20261021/.openclaw/trajectory-exports/pro-complete`. Données métier complètes non reproduites dans le rapport ; traces locales en mode 0600. Les sorties de diagnostic ne contiennent pas de jeton OAuth copié.

Rollback ciblé : `codex mcp logout orion`, puis `codex mcp remove orion` si le retour arrière est décidé. Ne pas restaurer aveuglément l'intégralité de config.toml si d'autres travaux ont eu lieu ; comparer la préimage et retirer uniquement l'entrée ajoutée. Aucun rollback OpenClaw/Gateway nécessaire car non modifiés. Ne pas révoquer l'autorisation OpenClaw Pro. La normalisation args=[] n'a pas d'effet à annuler.

Documentation officielle consultée : https://developers.openai.com/codex/extend/mcp (configuration MCP partagée, connexion HTTP et login OAuth). Les aides de la version installée ont fourni les commandes réellement exécutées.
