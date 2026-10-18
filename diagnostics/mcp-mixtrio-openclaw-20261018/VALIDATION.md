# Intégration MCP MIXTRIO (orion + outline) dans OpenClaw — 2026-10-18

## Périmètre

Ajout des MCP `orion` (frontal plateforme MIXTRIO) et `outline` (wiki) à l'installation OpenClaw existante, sans toucher Codex, oMLX, Ollama, Microsoft 365, Gmail, ni les autres MCP. Aucun nouvel agent, aucune réinstallation.

## Installation modifiée

- OpenClaw **2026.10.4 (383c124)**, binaire `~/.openclaw/bin/openclaw` (runtime bundled OpenClaw.app), Gateway local `127.0.0.1:18789`, config `~/.openclaw/openclaw.json`, agent `main` (modèle inchangé : `omlx/mlx-community--Qwen3.6-35B-A3B-4bit`).

## Changements

| Fichier | Changement |
|---|---|
| `~/.openclaw/openclaw.json` | `mcp.servers.orion` : `https://owu.mix3cloud.net/mcp-front/mcp`, transport `streamable-http`, `auth: oauth` ; `mcp.servers.outline` : `https://outline.mix3cloud.net/mcp`, idem. `tools.allow` : ajout `orion__*`, `outline__*` (préexistants `exec`, `microsoft-graph` conservés). `models.providers.omlx.models[0].contextWindow` : 32768 → **131072** (alignement sur le cap serveur oMLX validé dans `qwen36-cap-128k-20261017`). |
| `~/.openclaw/workspace/AGENTS.md` | Section « Outils métier MIXTRIO — MCP orion et outline » ajoutée (parcours list_registries → search_tools → get_contract → exec_tool, KB ciblées, confirmation avant écriture, anti-injection, pas de fabrication de références). Aucun remplacement du contenu existant. |

- Aucune restriction d'URL ajoutée (`?access=read` / `?domains=glpi` non posés) : droits effectifs = consentement OAuth + politique serveur.
- Jetons stockés par OpenClaw (`openclaw mcp login`), renouvellement natif ; aucun secret en config littérale, en conversation ni en Git.

## Sauvegarde et retour arrière

- Sauvegarde horodatée protégée : `~/.openclaw/backups-mcp-mixtrio-20261018-101751/` (openclaw.json, AGENTS.md, USER.md ; chmod 700).
- Retour arrière : restaurer les deux fichiers depuis la sauvegarde, puis `openclaw mcp logout orion` et `openclaw mcp logout outline`, puis `openclaw mcp reload`. (Restaure aussi `contextWindow: 32768` ; pour conserver le 128K, ne restaurer que `mcp` et `tools.allow`.)

## Authentifications

- **orion** : OAuth navigateur, compte OWUI **ordinaire** (admin refusé par le serveur), redirection locale `http://127.0.0.1:8989/oauth/callback` acceptée par le frontal, PKCE S256, cases d'écriture **non cochées** → lecture seule (portées `kb:read`, `tags:read`, `registry:read`).
- **outline** : parcours OAuth propre (`outline.mix3cloud.net/oauth/authorize`), indépendant d'Orion, de Microsoft et de Google.
- Incident sans effet : une URL d'autorisation orion rejouée après consentement a produit une erreur navigateur « client OAuth non chargé » ; le jeton avait déjà été échangé et stocké (`oauth: authorized` confirmé).

## Résultats de la recette (lecture seule, ~20 appels distants)

| Test | Résultat |
|---|---|
| A. Config OpenClaw validée | ✅ `openclaw config validate` : valid |
| B. Connexion réelle + catalogue | ✅ orion : 11 outils ; outline : 19 outils (`mcp probe`) |
| C. Registres + KB orion | ✅ 5 registres (tool_glpi_wrapper, tools_glpi_cmdb, tools_ldap, tools_redmine, tools_oyat_redmine — tous lecture, `registry:write` non accordé) ; 59 KB listées |
| D. Outil GLPI lecture | ✅ `search_glpi_ticket` trouvé via `search_tools`, contrat lu via `get_contract`, lecture limitée réalisée (3 tickets ouverts, entité #117) |
| E. Recherche documentaire ciblée | ✅ `search_knowledge` sur la seule KB CORPORATE (« procédure incident », passages + file_id réels) |
| F. Outline | ✅ 10 collections, document « Règlement Intérieur » (`25813084-50a8-4318-b64e-37b4fbfc59e5`) lu et résumé |
| G. Sélection autonome par « main » | ✅ demande naturelle « 3 tickets GLPI ouverts » : outils choisis par le modèle, identifiants réels cités (#21217, #20407, #20318), aucune écriture |
| Persistance | ✅ après `openclaw mcp reload` et dans sessions neuves (`agent:main:mcp-mixtrio-recette-*`) |

## Droits obtenus et limites d'approbation

- orion : lecture KB + étiquettes + outils métier **en lecture** ; écriture fermée (portée non accordée au consentement). Les ~145 contrats métier restent à découvrir à la demande.
- outline : scope `read+write` demandé par son serveur OAuth ; aucune écriture effectuée pendant la recette.
- La consigne de confirmation dans AGENTS.md n'est **pas** un contrôle d'accès technique. `exec_tool` sert à la lecture comme à l'écriture ; OpenClaw 2026.10.4 n'offre pas d'approbation par-outil MCP granulaire pour le runtime embarqué (les `codex.defaultToolsApprovalMode` ne visent que les threads Codex app-server). Aucune approbation permanente globale n'a été accordée. Le contrôle effectif d'écriture côté orion est la portée OAuth (écriture actuellement interdite).

## Incidents et corrections

- **Rejet de contexte (préexistant, corrigé)** : OpenClaw déclarait `contextWindow: 32768` pour Qwen3.6-35B alors que le cap serveur oMLX est 131072 (validé `qwen36-cap-128k-20261017`) ; un tour de recette a été rejeté localement (« estimated input 33531 leaves only 0 output tokens »). Corrigé à 131072 ; compactage embarqué OpenClaw actif (mode `safeguard`, défaut). Aucun réglage Codex touché.
- **Doctor préexistant non traité** (hors périmètre) : « Held agent main database » (journal de suppression reconstruit) — voir `openclaw doctor --fix`.

## Non testé

- Renouvellement OAuth réel (seul le stockage des jetons a été vérifié) ; à observer au-delà d'1 h de jeton d'accès.

## Actions restantes éventuelles (utilisateur / Raph)

- Cocher les cases d'écriture au prochain consentement orion si l'écriture GLPI/Redmine est voulue (`openclaw mcp logout orion` puis `openclaw mcp login orion`).
- Enrôler les clés métier manquantes dans OWUI (jamais dans OpenClaw) le cas échéant.
