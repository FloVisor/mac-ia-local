# Recette orion 0.3.0 (skills servis) — 2026-10-19

## Périmètre

Rejouer les limites relevées le 2026-10-18 ([mcp-mixtrio-openclaw-20261018](../mcp-mixtrio-openclaw-20261018/VALIDATION.md)) contre le frontal **orion 0.3.0** (m3-mcp-front 1.30.0, SDK MCP Python), en production sur mixtrio depuis le matin du 2026-10-19. Lecture seule (portées `kb:read tags:read registry:read`, jeton OpenClaw existant). Aucune écriture, aucun changement de config OpenClaw hors installation du skill orion.

## Limites du 18/10 → verdicts 0.3.0

| # | Limite du 18/10 | Verdict 0.3.0 | Preuve |
|---|---|---|---|
| L1 | Aucun skill servi à l'agent ; mode d'emploi absent | ✅ corrigée | `list_skills` rend 5 skills (orion, tool-glpi-wrapper, tools-ldap, tools-redmine, redmine-oyat-operations) ; instructions serveur et `get_contract`/`list_registries` orientent vers `get_skill("orion")` |
| L2 | « Mes tickets » exigeait ~20 appels `search_glpi_ticket` (une entité à la fois) | ✅ corrigée | skill GLPI v2.5.0 : `assigned_to:"me"` **sans entité**, filtres optionnels combinés en ET ; `exec_tool` rend les tickets réels en **1 appel / ~6,5 s** (#21457 ECOFAC, #21253 SMIDEN, #21220, #21209, #20991, #20902) |
| L3 | Outil métier appelé par son nom = échec sec (`Unknown tool id`) + hallucinations | ✅ corrigée | appel direct `search_glpi_ticket` → refus **orienté** : « lire get_contract(tool_name=…), puis exec_tool(…) ; règles du registre : get_skill("tool-glpi-wrapper") » ; outil inconnu → message générique (pas de divulgation), orienté `list_registries`/`search_tools` |
| L4 | Skill > 20 000 chars illisible en entier | ✅ corrigée | `get_skill("tool-glpi-wrapper")` (30 360 chars) → aperçu 4 932 chars + `toc` (titres + offsets) + `next_offset` + `how` ; `get_skill(offset=20000)` → bloc final 10 360 chars, `complete: true` ; `search_skill` trouve les passages avec offsets |
| L5 | Catalogue : 11 outils | ✅ conforme doc | `tools/list` : **14 outils** (dont `list_skills`, `get_skill`, `search_skill`) ; `mcp probe` OpenClaw : 14 |

## Détail des tests (client MCP direct, jeton lecture seule)

- **T1** `list_skills` : 5 skills, `chunked: true` pour tool-glpi-wrapper (30 360 chars), `registries` renseignés. ✅
- **T2** `get_skill("orion")` : rendu entier (8 418 chars), `complete` implicite. ✅
- **T3** `get_skill("tool-glpi-wrapper")` : aperçu 4 932 chars (≈5 000), `complete: false`, `next_offset: 4932`, sommaire (titres, niveaux, offsets), consigne `how` (blocs de 20 000 / `search_skill`). ✅
- **T4** `get_skill(offset=20000)` : bloc final 10 360 chars, `complete: true`. ✅
- **T5** `search_skill("tool-glpi-wrapper","mes tickets")` : 4 matches avec offsets + headings, `truncated: false` — le filtre « mes tickets » est documenté dans le skill servi. ✅
- **T6** appel direct `search_glpi_ticket` : refus orienté (appel exact + skill à lire), pas d'échec sec. ✅
- **T7** outil inconnu `search_glpi_ticket_inexistant` : message générique orienté, pas de divulgation d'outils masqués. ✅
- **T8-T10** `search_tools` (query `ticket`, `search_glpi_ticket`) : outil trouvé, `registry_skills` signale le skill du registre ; `get_contract` rend les paramètres avec les exemples « mes tickets » intégrés. ✅
- **T11** `exec_tool(search_glpi_ticket, {assigned_to:"me"})` : tickets réels en 1 appel, 6,5 s. ✅
- **T12** filtre combiné `{assigned_to:"me", ticket_status:"en_cours"}` : 5 tickets réels (ECOFAC, SMIDEN, ENS Électronique, EJ, XITHI). ✅
- **T13** `list_registries` : `write_available: true`, `write_open: false`, `write_closed_because` explicite (reconnexion en cochant la case). ✅
- **T14** `search_knowledge("procédure incident")` : 30 KB interrogées, 88 passages, `empty_documents: 1` compté, aucune KB en échec. ✅
- **T15** prompt MCP `orion` : servi via `prompts/get` (8 418 chars, même contenu que le SKILL.md) ; `prompts/list` : 1 prompt. ✅
- **Skill local** : `https://owu.mix3cloud.net/mcp-front/skills/orion.md` servi **sans authentification** (200, 8 663 octets, `text/markdown`) ; installé dans `~/.agents/skills/orion/SKILL.md` et `~/.claude/skills/orion/SKILL.md` ; `openclaw skills check --agent main` : orion `Ready`, visible modèle + commande.

## Bout en bout (agent main, Qwen3.6-35B via passerelle)

Demande naturelle « Affiche mes tickets en cours GLPI » (session `agent:main:mcp-mixtrio-recette-030`) :

- Parcours correct : `list_registries` → `search_tools` → `get_contract` → `exec_tool` (11 appels d'outils au total).
- Réponse : ticket réel **#21457** (ECOFAC, en cours, ouvert le 19/10 10:15) avec nuance honnête sur les autres statuts. **Aucune énumération d'entités**, aucune hallucination d'ID.
- 1 échec `tool_search` au premier essai : `limit` placé au niveau batch au lieu de par-query — **bug de formatage du modèle local Qwen 35B, déjà connu (18/10), pas du frontal** ; l'agent s'est corrigé au second appel et a abouti.

## Test complémentaire (2026-10-19, 11h) : « tickets de lundi » — cause racine trouvée ✅

Reprise du point « tickets de lundi » (évoqué le 18/10, non rejoué dans la première passe) :

- **T16** `get_contract(search_glpi_ticket)` : `date_from`/`date_to` (YYYY-MM-DD, date d'ouverture / de clôture selon statut) sont **documentés** dans le contrat et le skill. ✅ côté doc
- **T17–T19** `exec_tool` avec `args={...}` : filtres apparemment ignorés — 50 tickets toutes dates, aucune erreur. ❌
- **Confirmation en conditions réelles (11:25, session agent « Liste les tickets assignés du jour »)** : requête correcte (`assigned_to=me`, `date_from=2026-10-19`, `ouverts`) passée avec `args` → 29 tickets des 16/10 et 19/10 mélangés, dont **#21455 qui n'est pas assigné à Florian** (technicien `null`, groupe « DC EXPANSION Techniciens », Florian non membre).
- **T20 — cause racine (11:35)** : la passerelle attend **`params`**, pas `args`. Le skill orion documente bien `exec_tool(tool_name, params)`, mais le frontal **accepte `args` sans erreur et l'ignore silencieusement** (la validation pydantic ne porte que sur `tool_name`). Rejoué avec `params` :
  - `assigned_to=me` → **31 tickets, #21455 absent** ✅
  - `assigned_to=me` + `date_from/to=2026-10-19` → **1 ticket : #21457** ✅ (le filtre date fonctionne parfaitement)

**Diagnostic final** : ce n'est ni le filtre date ni `assigned_to` — c'est le nom du paramètre de `exec_tool`. Avec `args`, tous les filtres sont perdus et l'agent rend « tous les tickets ouverts » en croyant répondre à la demande. **Bug frontal à signaler à Raphaël** : `exec_tool` devrait rejeter `args` avec un message orienté (comme il le fait pour un outil métier appelé directement), ou l'accepter comme alias de `params`. Parade immédiate côté agent : AGENTS.md des 3 workspaces mis à jour (« `params`, jamais `args` »).

## Reste ouvert / à signaler à Raphaël

1. **`exec_tool` accepte `args` et l'ignore silencieusement** (T20 ci-dessus) : filtres perdus, résultats faux sans erreur — c'est ce qui a fait remonter #21455 (non assigné) dans « mes tickets du jour ». À rejeter avec message orienté ou aliaser à `params`. Prioritaire.
2. **Bug de formatage `tool_search` du Qwen 35B toujours présent** (côté modèle, pas frontal) : le premier appel place `limit` au niveau du batch. La parade du 18/10 (section « Format des appels d'outils » dans le AGENTS.md du workspace OpenClaw) reste nécessaire ; le skill orion servi ne couvre pas ce point (il documente le frontal, pas le format tool_search d'OpenClaw).
2. **ART non testé depuis ce poste** : `owui.autorite-transports.fr` ne résout pas (DNS) depuis le Mac ; la 0.3.0 n'y est pas vérifiée ici.
3. **`agent exec` isolé** ne voit pas les jetons OAuth des MCP (`openclaw mcp login orion` requis dans ce contexte) — artefact du mode exec, pas de la 0.3.0.
4. Renouvellement OAuth réel toujours non observé (jeton 1 h) — inchangé depuis le 18/10.

## Conclusion

Les limites L1-L5 relevées le 18/10 sont **corrigées et validées** sur mixtrio en 0.3.0, en lecture seule. Le point « tickets de lundi / du jour » s'est avéré être un **piège de nommage `args` vs `params`** sur `exec_tool` (T20) : avec `params`, tous les filtres — date inclus — fonctionnent parfaitement. Le skill orion est installé localement (`~/.agents/skills/orion`, `~/.claude/skills/orion`) et visible du modèle. Restent : le rejet/alias de `args` côté frontal (prioritaire), le point modèle (tool_search) et l'instance ART à jouer depuis un poste qui la résout.