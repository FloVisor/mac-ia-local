# Intégration iMessage OpenClaw — Retour d'expérience (2026-10-18)

Ce document capitalise les pièges rencontrés lors de l'intégration du canal
iMessage dans OpenClaw, pour éviter de les reproduire sur les prochains
outils/canaux à intégrer.

## Environnement de référence

- OpenClaw 2026.10.4 (CLI + app `/Applications/OpenClaw.app`)
- macOS 27.0.1, Apple Silicon, SIP activé
- Modèle unique : `omlx/mlx-community--Qwen3.6-35B-A3B-4bit` (32k ctx)
- Config : `~/.openclaw/openclaw.json`

## Pièges rencontrés et résolutions

### 1. TCC / Full Disk Access — l'attribution suit le processus responsable

**Symptôme** : `imsg rpc not ready (Database unavailable: code=-32002)` —
accès refusé à `~/Library/Messages/chat.db`.

**Cause** : macOS attribue l'autorisation TCC au *processus responsable*
(responsible process), pas au binaire enfant. Le Gateway est un enfant de
`OpenClaw.app` ; c'est donc **OpenClaw.app** qui doit avoir l'Accès complet au
disque, pas nécessairement `imsg` ou `bun`.

**Règle** : identifier le processus responsable avec
`ps -o ppid= -p <pid_gateway>` en remontant la chaîne, et accorder FDA à
l'app parent. Un Gateway lancé depuis un terminal hérite de l'autorité du
terminal (VS Code), pas d'OpenClaw.app — d'où des comportements différents
selon le mode de lancement.

**Non-documenté mais important** : `/opt/homebrew/bin/imsg` est un symlink ;
le sélecteur de fichiers macOS ne le suit pas. Utiliser le chemin réel dans
`Cellar/`.

### 2. `tools.allow` restrictif — l'outil `message` n'était pas autorisé

**Symptôme** : l'agent répond « aucun outil de messagerie iMessage n'est
disponible » alors que le canal est `connected, works`.

**Cause** : `tools.allow` global était une allowlist restrictive
(`["exec", "microsoft-graph", "orion__*", "outline__*"]`) sans `message`.
Le canal fonctionne (envoi CLI OK) mais l'**agent** n'a pas l'outil.

**Règle** : à chaque intégration d'un canal (iMessage, Telegram, etc.),
vérifier **les deux niveaux** :
1. Le canal : `openclaw channels status --probe` → `connected, works`
2. L'outil agent : `openclaw doctor` → ne doit PAS contenir
   « message tool is unavailable for that agent »

Le doctor est le vérificateur systématique après toute modification.

### 3. Politique Microsoft Graph — refus locaux vs OAuth

**Symptôme** : `outlook_calendar_read` échoue avec `access_denied` en
1-2 ms (durée ≈ 0 = refus de politique **locale**, pas un problème OAuth).

**Cause** : le modèle passe parfois des paramètres inventés (ex.
`calendarId: "default"`) non présents dans
`plugins.entries.microsoft-graph.config.policy.services.calendar.agents.main.resources`.

**Règle** : un refus < 5 ms = politique locale. Un refus lent/401 = OAuth.
Ajouter les valeurs que le modèle utilise naturellement aux `resources`
autorisées, ou instruire l'agent (prompt) de ne pas préciser le paramètre.

### 4. Saturation de session — le modèle ne répond plus

**Symptôme** : `Context window exceeded: estimated input 49121 leaves only
0 output tokens within the 32768-token context`. L'agent ne répond plus,
les tours restent bloqués 10+ min, et le rechargement de config est différé
(`reload deferred while active work finishes`).

**Cause** : la session `agent:main:main` accumule l'historique au-delà de la
fenêtre de contexte du modèle local (32k).

**Règles** :
- Compacter par troncature (pas LLM — le modèle saturé ne peut pas se
  résumer lui-même) :
  `openclaw sessions compact agent:main:main --agent main --max-lines 40`
- Surveiller : `openclaw sessions --agent main --active 120` (colonne
  Tokens ctx %)
- Un reload différé persistant signale souvent un tour d'agent bloqué.

### 5. Utility model / titres de session — fallback crustacé

**Symptôme** : titres de session aléatoires (`salty-lobster`) au lieu de
résumés ; log `dashboard session title generation exhausted`.

**Cause** : la génération de titre passe par le modèle utilitaire = modèle
principal par défaut. Sur un modèle local 35B en 32k, ces micro-requêtes
échouent souvent (timeout/abort).

**Attention** : ne PAS ajouter un provider supplémentaire (ex. Ollama) sans
mesurer l'impact — un second modèle 30B chargé en VRAM sature un Mac 48 Go
avec le modèle principal. Si un utility model léger est voulu, vérifier
l'empreinte mémoire cumulée et décharger après test
(`curl /api/generate -d '{"model":"X","keep_alive":0}'`).

### 6. `dmPolicy` — sens exact

- `pairing` : les expéditeurs inconnus reçoivent un code d'appairage ;
  une fois approuvés (`openclaw pairing approve imessage <code>`), ils
  peuvent **discuter avec l'agent** (réponses automatiques).
- `disabled` : les DM entrants sont ignorés — **l'envoi sortant fonctionne
  toujours**. C'est le bon choix si on ne veut que du sortant.

## Checklist d'intégration d'un nouvel outil/canal

1. **Audit** : `openclaw plugins list`, `openclaw agents list`,
   `openclaw channels status --probe`, sauvegarde config
   (`cp ~/.openclaw/openclaw.json ~/.openclaw/backups-<date>/`).
2. **Permissions macOS** : identifier le processus responsable du Gateway
   (`ps -o ppid=`), accorder FDA au parent, pas aux enfants.
3. **Config ciblée** : modifier uniquement les clés nécessaires (jamais de
   remplacement complet du fichier). Valider : `openclaw config validate`.
4. **Vérifier l'outil agent** : `openclaw doctor` — l'outil doit être
   disponible pour l'agent routé (allowlist `tools.allow`).
5. **Redémarrer** : `openclaw gateway restart`, puis re-probe.
6. **Diagnostic des échecs** : durée de l'erreur (ms = politique locale,
   lente = réseau/OAuth), `openclaw sessions tail --agent main`,
   `/tmp/openclaw/openclaw-gateway.log`.
7. **Surveiller la saturation** : tokens de session vs fenêtre de contexte
   du modèle local.

## État final (2026-10-18)

- Canal iMessage : `connected, works`, envoi sortant validé par test réel
- `dmPolicy=disabled` (pas de réponses automatiques entrantes)
- `tools.allow` inclut `message`
- Calendrier Graph : `default` ajouté aux ressources autorisées
- Modèle principal : Qwen omlx 65k déclaré (cap serveur 128k), utility model `ollama/qwen3:0.6b-titre` (0,79 Go, keep_alive 5 min)
- Skill `tool-ids` : IDs exacts + format tool_search correct, visible du modèle
- `commands.ownerAllowFrom` vidé : les réponses dashboard ne fuient plus
  vers iMessage (effet de bord de l'approbation d'appairage à surveiller)
- `tools.exec.safeBinProfiles.osascript` : permet la résolution de contacts
  via AppleScript sans approbation manuelle

## 7. Timeout titres 15 s codé en dur (constat structurel, 2026-10-18)

**Symptôme** : `dashboard session title generation exhausted; using a
crustacean fallback name` (9 occurrences le 2026-10-18 avant correction).

**Cause racine** : le timeout de génération de titre est codé en dur à
15 s (`const TIMEOUT_MS = 15e3`) dans
`~/.openclaw/runtime/current/lib/node_modules/openclaw/dist/conversation-label-generator-CtZqoFhF.mjs`.
Aucune clé de config ne l'expose. Le Qwen 35B local met >15 s par requête
→ échec systématique → slug crustacé.

**Ne pas patcher le dist** (écrasé au prochain upgrade).

**Solution retenue** : mini-modèle Ollama dédié au titrage.

### Déploiement validé (2026-10-18)

- Modèle : `qwen3:0.6b-titre` — variante **créée localement** de `qwen3:0.6b`
  avec `PARAMETER num_ctx 2048` (Modelfile). Justification ctx réduit : le
  modèle de base alloue un KV-cache pour 40 960 tokens par défaut → **5,64 Go
  de VRAM** pour 522 Mo de poids. Avec ctx 2048 : **0,79 Go**. Le titrage
  n'a jamais besoin de plus de quelques centaines de tokens.
- Config : `models.providers.ollama` (baseUrl 127.0.0.1:11434) +
  `agents.defaults.utilityModel = "ollama/qwen3:0.6b-titre"`.
- `OLLAMA_KEEP_ALIVE=5m` (LaunchAgent `org.gangneux.ollama-serve` **et**
  `org.gangneux.ollama-env` — les deux définissent la variable, il faut
  patcher les deux plists).
- Latence mesurée : **~1,2 s** moyenne (0,9-1,3 s), très loin du timeout
  de 15 s.
- Déchargement confirmé : `/api/ps` vide après 5 min d'inactivité.

### Piège : le titrage n'est déclenché que par le chemin `chat.send`

Le CLI `openclaw agent` ne déclenche PAS la génération de titre (sessions
`direct` non candidates). Seules les clés `dashboard:`, `ios-`, `node-`
sont auto-titrées (`isAutoTitleSessionKey` dans
`dashboard-session-title-DGVVxyGL.mjs`). Pour tester sans Control UI :
`openclaw gateway call sessions.title.prepare --json --params
'{"agentId":"main","message":"..."}'`.

### Piège : RAM tendue + mini-modèle chargé = rejet prefill du modèle principal

Le garde-fou mémoire d'oMLX rejette les prompts quand le pic de prefill
dépasse le plafond dynamique (~22,8 Go sur 48 Go de machine avec ~20 Go déjà
utilisés par le modèle 35B). Le mini-modèle Ollama chargé (0,79 Go) peut
faire basculer la garde → `prefill_memory_exceeded` sur le modèle
**principal**. Symptômes : `400 oMLX prefill memory guard rejected this
prompt`. Parade : keep_alive court (5 min) pour que le mini-modèle ne reste
pas chargé inutilement.

**Correction structurelle (2026-10-18 soir)** : `~/.omlx/settings.json` →
`memory.memory_guard_tier = "custom"` +
`memory.memory_guard_custom_ceiling_gb = 24.5` (plafond fixe au lieu du
dynamique qui se resserre quand la RAM baisse). `final_ceiling` effectif
passé de 26,0 Go à 39,3 Go. Compromis assumé : en RAM très tendue, macOS
swappe au lieu de rejeter. Ollama également bridé :
`OLLAMA_CONTEXT_LENGTH` 131072 → 4096 (le titrage n'a jamais besoin de plus).

## 9. Paramètres inventés sur les outils Graph (2026-10-18 soir)

**Symptôme** : `outlook_mail_read` → `invalid_read_parameter` (0 ms) ;
`outlook_calendar_read` → `access_denied` (2 ms). Refus de validation
**locale** stricte : le plugin n'accepte que des champs exacts par action
(`READ_ACTION_FIELDS` dans `~/.openclaw/extensions/microsoft-graph/dist/index.js`).

**Cause** : le modèle devine des paramètres plausibles mais interdits
(`sender`, `from`, `query`, `calendarId` inventé).

**Parade** : consigne compacte dans AGENTS.md (section Tools) listant les
signatures exactes des actions courantes + « calendarId = "me" ou "default",
jamais un nom inventé ». Validation : 3 appels mail consécutifs, 0 erreur
(avant : 1 erreur par conversation en moyenne).

## 10. Sessions longues = re-prefill complet (2026-10-18 soir)

**Symptôme** : première réponse lente (2-6 min), runs qui s'enchaînent sans
requête utilisateur.

**Cause** : sessions accumulant des dizaines d'appels d'outils (ex :
énumération GLPI multi-entités) → prompt 33k+ tokens. Le prompt-cache est
**droppé à 6 144 tokens** à chaque tour (`historyRewrite`) → re-prefill
complet à chaque requête. Un tour avorté (timeout livraison) est **rejoué
automatiquement** par l'auto-reply, chaque essai refaisant un appel d'outil.

**Règles** :
- Compacter les sessions gonflées : `openclaw sessions compact <key> --agent main --max-lines 40`
- Surveiller : `openclaw sessions --agent main --active 120` (colonne Tokens ctx %)
- Une demande « toutes entités » GLPI = énumération interminable : restreindre à une entité connue

## 8. Bug format tool_search du Qwen 35B (2026-10-18)

**Symptôme** : `tool_search failed: set limit on each batch query, not on
the batch request` (échecs à 11:10, 11:19, 12:01, 12:07, 12:42) puis
`tool_call failed: Unknown tool id` (ex. `list_registres` sans préfixe) et
hallucinations (tickets GLPI inventés).

**Cause** : le Qwen 35B formate mal tool_search — il place `limit` au niveau
du batch (`{"limit":5,"queries":[{"query":"..."}]}`) au lieu de le mettre
dans chaque query (`{"queries":[{"query":"...","limit":5}]}`), et appelle
des IDs sans préfixe MCP.

**Parade** : la skill seule ne suffit PAS — le modèle ne la consulte qu'à la demande.
La correction efficace est dans **`~/.openclaw/workspace/AGENTS.md`** (injecté en
permanence dans le system prompt) : section "Format des appels d'outils
(CRITIQUE)" en tête de la section Tools (préfixes obligatoires + format
par-query + exemple), et parcours orion rewritten avec les IDs préfixés
(`orion__list_registries`, etc.). Vérifier aussi
`openclaw skills list --json` → `modelVisible: true` pour la skill
`tool-ids` (renfort).

**Piège racine** : le AGENTS.md d'origine documentait le parcours orion avec
des noms SANS préfixe (`list_registries`, `search_tools`...) — le modèle
suivait ces instructions et ignorait la skill. Toujours vérifier la cohérence
AGENTS.md ↔ IDs réels (`openclaw mcp probe <server> --json`).

**Validation post-correction (2026-10-18 13:23-13:40)** : requête "Affiche mes
tickets en cours GLPI" → l'agent a interrogé ~20 entités via
`search_glpi_ticket`, trouvé 5 tickets réels (entité 31 ED-TRANS, IDs
21424/21354/21198/21195/20132), 0 `tool_search failed`, 0 `Unknown tool id`
sur 3 runs consécutifs.

**Statut 2026-10-19 (recette orion 0.3.0)** : le bug modèle **persiste** —
premier appel `tool_search` de la session avec `limit` au niveau batch (échec
10:58:15), puis **auto-correction au retry** (format par-query, succès) ; le
run aboutit. La parade AGENTS.md reste nécessaire et suffisante en pratique :
elle réduit à ~1 échec par session, immédiatement récupéré. La règle est
présente dans les **trois** workspaces (main, perso, technique — même modèle
Qwen 35B). Côté frontal orion 0.3.0, rien à corriger : les 4 appels orion du
run ont tous réussi.

**Session réelle 11:25 « Liste les tickets assignés du jour »** : 5 échecs
avant succès — 3× `tool_search` batch-limit (11:25:36/38/40, corrigé à la 4ᵉ
tentative), puis 2 omissions d'arguments obligatoires côté modèle :
`orion__search_tools` sans `query` (11:25:51) et `orion__exec_tool` sans
`tool_name` (11:26:14). Tous auto-corrigés au retry ; parcours orion final
correct. **MAIS la réponse rendue était fausse** : 29 tickets des 16/10 et
19/10 mélangés, dont #21455 non assigné à Florian.

**Cause racine trouvée (11:35) — `args` vs `params` sur `exec_tool`** : la
passerelle attend `params` ; le frontal **accepte `args` sans erreur et
l'ignore silencieusement** (validation pydantic sur `tool_name` seul). Avec
`args`, tous les filtres (`assigned_to`, `date_from`…) sont perdus →
l'agent rend « tous les tickets ouverts » en croyant répondre à la demande.
Avec `params` : `assigned_to=me` → 31 tickets (sans #21455) ;
+ `date_from/to=2026-10-19` → 1 ticket (#21457). **Le filtre date fonctionne
parfaitement** — le diagnostic initial « filtre date ignoré » était faux.
Parade : AGENTS.md des 3 workspaces (« `params`, jamais `args` ») ; à faire
rejeter ou aliaser côté frontal orion (signalé à Raphaël).

## Benches de validation (2026-10-18)

### BENCH #1 — Titres (7 requêtes sessions.title.prepare)

- 6/7 titres réels (1 `null`), latence moyenne ~1,2 s
- 0 `title generation exhausted` après déploiement (dernier : 12:43,
  avant le changement à 12:49)
- Exemples : "Fonctionnement des containers Docker",
  "Calculer le budget mensuel pour les courses alimentaires"

### BENCH #2 — Tooling (10 requêtes agent main)

- `tool_search failed` : **0/10** (vs 6 échecs entre 12:01 et 12:42 avant
  la skill)
- `tool_call failed (Unknown tool id)` : **0/10**
- Hallucinations détectées : **0** (données orion/outline croisées avec
  `mcp probe`, exec osascript vérifié, Graph calendrier cohérent)
- 2 échecs `prefill_memory_exceeded` (13:03, 13:05) sans lien tooling :
  mini-modèle Ollama chargé pendant RAM tendue → résolus par déchargement
  (keep_alive 5 min)

### BENCH #3 — Mémoire

- Avant : 0,4 Go libres (mini-modèle non chargé, baseline)
- Pendant : 0,2 Go libres, mini-modèle 0,79 Go VRAM
- Après (5 min) : 2,0 Go libres, `/api/ps` vide → **déchargement confirmé**

### Non-régression

- iMessage : `connected, works` (probe OK)
- Graph : lecture calendrier OK (0 événement le 18/10, réponse cohérente)
- Doctor : 4 warnings pré-existants (skill_workshop, memory search, bind
  loopback, secrets en clair) — aucun nouveau
- Modèle principal : `omlx/mlx-community--Qwen3.6-35B-A3B-4bit` toujours
  `default,configured` ; contextWindow relevé 32768 → 65536 (décision
  utilisateur 2026-10-18, cap serveur oMLX 131072 inchangé)

## Limite connue : comportement du modèle local

Le modèle Qwen 35B (32k contexte, 55 outils catalogués) est **inconstant**
sur les enchaînements d'outils autonomes : il peut exécuter correctement
osascript un tour, puis affirmer « exec non configuré » au tour suivant sans
même essayer. Ce n'est pas un problème de configuration — la chaîne complète
(résolution contact → envoi iMessage) est prouvée fonctionnelle en CLI.

**Parade** : relancer la demande en cas d'échec de l'agent. Ne pas « corriger »
la config sur la base des affirmations du modèle — vérifier les logs
(`grep -E "exec|tool" /tmp/openclaw/openclaw-gateway.log`) pour distinguer
un vrai refus d'une hallucination du modèle.

## Lecteur documentaire commun (PDF / OCR) — 2026-10-19

Recette complète : [diagnostics/openclaw-document-reader-20261019](../diagnostics/openclaw-document-reader-20261019/VALIDATION.md).

### Pièges rencontrés

1. **`--agent "*"` n'est pas hérité par les agents nommés.** Une entrée
   d'allowlist ajoutée avec `--agent "*"` ne s'applique pas à `main`, `perso`,
   `technique` : il faut une entrée par agent. Symptôme :
   `SYSTEM_RUN_DENIED: approval cannot safely bind this command` sur un agent
   alors qu'un autre passe.
2. **Les commandes composées ne sont pas liables par l'approbation.** `cmd1 && cmd2`,
   pipes et redirections échouent en `ask` comme en `allowlist`. Utiliser des
   appels simples, ou allowlister le binaire et laisser l'agent enchaîner les
   appels.
3. **`tools.exec.mode: "ask"` génère des popups à chaque miss.** Pour un usage
   documentaire fluide : passer en `allowlist` et n'ajouter que les binaires
   nécessaires, par agent. Vérifier ensuite qu'une commande non listée reste
   refusée (`curl` → `exec denied: allowlist miss`).
4. **Le store `media://inbound` est partagé entre agents.** Une pièce jointe
   Outlook téléchargée par Pro est lisible par tous. Le convertisseur copie
   l'original dans `<workspace-agent>/.documents/<agent>/<conversation>/originals/`
   avant conversion.
5. **Ne jamais déduire l'agent d'une valeur par défaut.** Un `--agent` par
   défaut à `main` ferait écrire les artefacts de Perso dans le workspace de
   Pro. Déduire du répertoire de travail réel, et échouer explicitement
   (`agent_not_determined`) hors workspace.
6. **Frontmatter de skill** : une virgule finale dans le bloc JSON `metadata`
   rend le YAML invalide et le skill disparaît silencieusement de la liste.
   Valider avec `python3 -c "import yaml; yaml.safe_load(...)"` après édition.
7. **Wrapper appelé par symlink** : `dirname "$0"` pointe vers `~/.local/bin`.
   Résoudre les liens (`readlink` en boucle) avant de localiser le script.

### Checklist appliquée

- [x] Identifiants réels des agents (`openclaw agents list`), pas les noms affichés
- [x] Emplacement partagé des skills vérifié (`<state-dir>/skills`)
- [x] Copies locales masquantes contrôlées (workspace, `.agents`, workshop)
- [x] Skill visible modèle pour les 3 agents (`skills list --json`)
- [x] Allowlist de skills préservée (seul ajout : `document-reader` pour Technique)
- [x] Convertisseur exécuté depuis chaque agent (pas seulement le terminal)
- [x] OCR réellement exécuté sur un scan depuis chaque agent
- [x] Pièce jointe récupérée avec les connecteurs propres à chaque agent
- [x] Isolation des artefacts vérifiée (3 dossiers distincts)
- [x] `tools.deny` et MCP inchangés (Perso : Graph/orion/outline toujours refusés)

## Import PDF/OCR BookStack et `invalid connect params` — 2026-10-20

Recette complète : [diagnostics/openclaw-bookstack-import-20261020](../diagnostics/openclaw-bookstack-import-20261020/VALIDATION.md).

### Pièges rencontrés

1. **`document-extract` désactivé = plus aucune pièce jointe lisible.**
   C'est le seul fournisseur du contrat `documentExtractors`. Sans lui :
   `PDF extraction disabled or unavailable` → `read-failure` →
   `[Attachment could not be read]`. Vérifier
   `plugins.entries.document-extract.enabled` avant tout diagnostic d'import.
2. **`hydrationSuppressed` sur les pièces jointes non-image.** Le gateway
   offloade le fichier vers `media://inbound/<id>` sans exposer ni chemin ni
   texte : le modèle n'a aucun `filePath`. Les outils doivent accepter
   `media://inbound/<id>` et le résoudre eux-mêmes (rejeter la traversée).
3. **Troncature de slug qui mange l'extension.** Un `slug()` coupé à 80 car.
   sur un nom de 103 car. supprimait `.pdf` → `Format non pris en charge : `.
   Toujours préserver l'extension après troncature.
4. **`openclaw gateway restart` ne redémarre pas le processus** (même PID), et
   `openclaw plugins disable` ne décharge pas le plugin du gateway en cours.
   Seul `openclaw gateway stop --force` garantit un état propre. Symptôme d'un
   état corrompu : accumulation de `Plugin replacement applied` dans le log.
5. **`invalid connect params: at /client/id`** = un client WebSocket envoie un
   `client.id` hors de `GATEWAY_CLIENT_IDS` (17 valeurs canoniques). Le client
   synthétique légitime du SDK envoie `gateway-client` / `internal` ; une
   identité qui reprend `manifest.id` + `manifest.version` du plugin est
   fautive. `tcpdump -A` ne la voit pas (masquage XOR WebSocket) : capturer en
   binaire (`-w`) puis démasquer.
6. **`tool_search` : `limit` au niveau batch est rejeté.** Le validateur exige
   `limit` dans chaque query. Consigne permanente dans les trois `AGENTS.md`.
