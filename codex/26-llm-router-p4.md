# P4 — centralisation Codex et audit de retrait

21 octobre 2026. **Migration et retrait de local_llm : VERIFIED pour la configuration
active et le choix autonome. Exécution complète de la revue : FAILED par troncature.**
Voir la clôture contrôlée en fin de rapport ; les étapes précédentes conservent leurs
preuves et décisions historiques, remplacées par cette dernière décision.
Aucun commit/push. Aucun changement OpenClaw, LiteLLM, moteurs, modèles serveur,
budgets, clés, catalogue DIRECT, extension Standup ou mécanisme d’approbation.

## Changements appliqués

- `~/.codex/AGENTS.md` : seule section de délégation remplacée par politique
  `llm-router`, découverte dynamique, local prioritaire, gratuit sous confidentialité,
  asynchrone, contexte ciblé, vérification par GPT et erreurs conservées.
- DIRECT distingué de DELEGATED ; payant délégué toujours désactivé. Plafond 40 USD/mois.
  Budgets oMLX Off/Minimal désactivé, Low 512, Medium 2048, High 8192, Max 16384
  conservés comme politique, sans requalification ni écriture serveur.
  Contextes oMLX 128K et Ollama Qwen3 4B 8K préservés.
- `~/.codex/config.toml` : seul `model` passe de Qwen à `gpt-6.1-sol`, conformément
  à P4. Aucun autre changement sémantique ; les trois déclarations MCP sont identiques.
  Ceci ne bascule pas rétroactivement les sessions existantes.
- `codex/global-instructions.md` : même section de délégation, en conservant le
  reste de sa préimage ; copie documentaire, pas une seconde source chargée.
- `AGENTS.md` et `codex/AGENTS.md` : description du domaine MCP neutralisée.
- `infrastructure/AGENTS.md` : règle générique local_llm retirée ; restriction
  de secrets et spécificité Docker Swarm conservées.

RTK et Graphify globaux conservés octet pour octet hors section remplacée.
Les modifications préexistantes du dépôt et son index sont laissés en place.

## MCP avant / après

| Serveur | Avant | Après | Décision |
| --- | --- | --- | --- |
| local_llm | lanceur ~/.codex/bin/local-llm-mcp | identique | conserver, préconditions de retrait non remplies |
| llm-router | Python 3.14, mcp/llm-router/router.py, ~/.config/llm-router/codex.json | identique | privilégier globalement |
| node_repl | binaire cua_node de ChatGPT.app | identique | conserver |

Identité routeur `codex`, stockage privé `~/.local/state/llm-router/codex`,
clé dédiée référencée par `key_file` sans lecture du secret dans cette mission.
Catalogue réel lu via MCP : un modèle local, deux gratuits individuellement
qualifiés avec réserves de qualité historiques, aucun payant.
Les droits serveur LOCAL/FREE et refus PAID sont réutilisés de P3, non retestés.
CLI Homebrew 0.160.0 ; Desktop 0.163.0-alpha.10.2.

## Test autonome et trajet réel

Test sans outil imposé : sous-agent `01a15ea0-cddf-7a02-96cf-23af393ef85d`,
checklist courte de migration. Il a lu les instructions et traité directement,
avec zéro génération secondaire. Choix cohérent pour une tâche triviale mais
**PARTIAL : préférence autonome llm-router non démontrée**. Aucun nouvel essai
pour obtenir artificiellement le résultat attendu.

Revue P4 distincte choisie par l’orchestrateur, soumise sans modèle imposé :
`tâche b8dcf88c-41b3-4e93-9d0c-77e6042c0531`, parent réel
`01a15e9a-41d4-7d60-a285-4d97ec190dc2`.

- `submit` immédiat queued, puis `status` completed et `result` récupéré : VERIFIED.
- Sélection `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit`, motif
  `first_compatible_local_free_paid`, backend local ; modèle demandé null.
- 11 744 ms ; 230 entrée + 440 sortie = 670 tokens ; une tentative routeur.
- Request ID `chatcmpl-45bb21ce` ; headers retries 0 / fallbacks 0.
- Raisonnement off transmis, application fournisseur non confirmée.
- `actual_model=null`, provenance `alias_only_unconfirmed` : aucun modèle
  fournisseur confirmé indépendamment pour cet appel. Coût inconnu null.
- Une seule nouvelle inférence locale ; aucun Cloud gratuit ni payant.
- Évaluation critique : contenu rejeté pour affirmations non étayées (panne totale,
  corruption de cache, dette critique, vulnérabilité supposée). Seul le constat
  de retrait prématuré est cohérent avec les preuves. `completed` ne signifie
  pas qualité validée ; contrôle automatique `quality=not_checked`.

Quotas, breakers, erreurs, récupération après fermeture du client et profils :
preuves des 41 tests historiques et P3 réutilisées ; pas de répétition de campagne.
L’erreur historique objective_quality_failed reste visible dans activity.

## Supervision

Collecteur P3-C exécuté en lecture seule sur la tâche réelle : VERIFIED.
Tâche distincte mcp_delegation, état completed, parent exact, 670 tokens,
11 744 ms, request_id et provenance inconnue conservés ; erreurs collecteur [].
Preuve `artifacts/p4-migration/collector-task.json`.
Affichage de cette nouvelle tâche dans le webview Live Call : NOT_TESTED.
Aucune réinstallation, modification ou relance globale de VS Code.

## Inventaire local et GitHub

Cinq dépôts, six racines en incluant le worktree :

| Dépôt | Remote | État initial |
| --- | --- | --- |
| mac-ia-local | FloVisor/mac-ia-local | nombreuses modifications concurrentes et index préexistant |
| XITHI-Infrastructure-Ops | FloVisor/XITHI-Infrastructure-Ops | AGENTS et travaux étrangers modifiés |
| .codex-worktrees/XITHI-xansible-decisions-0.5.16 | même remote | propre |
| Plateforme-SD-WAN-XITHI | FloVisor/Plateforme-SD-WAN-XITHI | propre, branche chore/altiwan-branding |
| Plateforme-CaaS-XITHI | FloVisor/Plateforme-CaaS-XITHI | propre |
| m3-si-xithi | rldet9/m3-si-xithi | propre |

Découverte par marqueur .git fichier ou dossier, sans plafond de profondeur,
avec contrôle git worktree list. Dépendances, caches, artefacts et diagnostics
exclus de l’analyse d’instructions ; aucun historique Git complet parcouru.
Inventaire technique : `artifacts/p4-migration/local-inventory.json` (40 fichiers).
Les fichiers liés actifs sont aussi examinés, notamment LOCAL_LLM.md SD-WAN.
Aucun skill global contrôlé sous ~/.agents/skills et ~/.codex/skills n’impose
local_llm ou llm-router. Les plugins embarqués ne sont pas nettoyés.

GitHub `fngux2` : BLOCKED, réponse exacte :
`the owner handle "fngux2" was not recognized as either a GitHub user or an organization`.
Aucune tentative de contourner l’accès. Remotes observés : FloVisor.
Liste FloVisor accessible : sept dépôts (quatre clones ci-dessus, plus
post-activation-validation, super-agent, nodectra).
`post-activation-validation` est vide (branche par défaut vide).
`super-agent` et `nodectra` : arbres HEAD récursifs non tronqués lus via gh API ;
13 AGENTS au total lus en lecture seule. Nodectra : PROJECT/SECURITY,
aucune politique de délégation identifiée. Super-agent : CONFLICT/PROJECT/SECURITY,
CODEX_HOME isolé ~/.codex-super-agent et modèle Ollama volontairement spécifique.
Ne pas écraser cette exception ; sa configuration isolée n’a pas été modifiée.
Ces dépôts ne sont pas sous Workspaces ; aucune écriture distante.
Le compte fngux2 inaccessible et les configurations isolées empêchent d’annoncer
une couverture universelle de tous les environnements.

## Classification des instructions locales découvertes

PROJECT = conserver ; SECURITY = restrictions à préserver.
GLOBAL/OBSOLETE/CONFLICT identifient une règle de délégation à centraliser ou arbitrer.
Les rapports historiques et les sources du MCP ancien ne sont pas des instructions
actives et ne sont pas réécrits.

| Fichier | Classification |
| --- | --- |
| `mac-ia-local/AGENTS.md` | PROJECT |
| `mac-ia-local/ollama-v0.35.0/AGENTS.md` | PROJECT |
| `mac-ia-local/openclaw/AGENTS.md` | PROJECT |
| `mac-ia-local/openclaw/perso-famille-contacts/workspace-perso/skills/famille-contacts/SKILL.md` | PROJECT |
| `mac-ia-local/codex/AGENTS.md` | PROJECT |
| `mac-ia-local/infrastructure/AGENTS.md` | PROJECT, SECURITY |
| `mac-ia-local/perf/AGENTS.md` | PROJECT |
| `m3-si-xithi/.mcp.json` | PROJECT |
| `m3-si-xithi/SKILL.md` | PROJECT, SECURITY |
| `m3-si-xithi/AGENTS.md` | PROJECT, SECURITY |
| `m3-si-xithi/.codex/hooks.json` | PROJECT |
| `m3-si-xithi/.codex/config.toml` | PROJECT |
| `m3-si-xithi/.vscode/mcp.json` | PROJECT |
| `Plateforme-SD-WAN-XITHI/AGENTS.md` | PROJECT, SECURITY |
| `Plateforme-SD-WAN-XITHI/tools/AGENTS.md` | PROJECT, SECURITY |
| `Plateforme-SD-WAN-XITHI/appliance/AGENTS.md` | PROJECT |
| `Plateforme-SD-WAN-XITHI/experiments/AGENTS.md` | PROJECT |
| `Plateforme-SD-WAN-XITHI/contracts/AGENTS.md` | PROJECT, SECURITY |
| `Plateforme-SD-WAN-XITHI/lab/AGENTS.md` | PROJECT |
| `Plateforme-SD-WAN-XITHI/tests/AGENTS.md` | PROJECT |
| `Plateforme-SD-WAN-XITHI/docs/AGENTS.md` | PROJECT |
| `Plateforme-SD-WAN-XITHI/product/AGENTS.md` | PROJECT |
| `Plateforme-SD-WAN-XITHI/acceptance/AGENTS.md` | PROJECT |
| `Plateforme-CaaS-XITHI/AGENTS.md` | PROJECT, SECURITY |
| `XITHI-Infrastructure-Ops/AGENTS.md` | PROJECT, SECURITY, GLOBAL, OBSOLETE, CONFLICT |
| `XITHI-Infrastructure-Ops/tools/AGENTS.md` | PROJECT, SECURITY |
| `XITHI-Infrastructure-Ops/projets/AGENTS.md` | PROJECT, SECURITY |
| `XITHI-Infrastructure-Ops/projets/_modele/AGENTS.md` | PROJECT |
| `XITHI-Infrastructure-Ops/projets/mixtrio/mixtrio-partner-api/AGENTS.md` | PROJECT |
| `XITHI-Infrastructure-Ops/projets/ecole_nationale_superieure_de_l_electronique_et_de_ses_applications/modernisation-du-si/AGENTS.md` | PROJECT |
| `XITHI-Infrastructure-Ops/tests/ansible/AGENTS.md` | PROJECT |
| `XITHI-Infrastructure-Ops/ansible/AGENTS.md` | PROJECT, SECURITY |
| `XITHI-Infrastructure-Ops/deployment/software/AGENTS.md` | PROJECT, SECURITY |
| `XITHI-Infrastructure-Ops/deployment/log-collection/AGENTS.md` | PROJECT |
| `XITHI-Infrastructure-Ops/supervision/AGENTS.md` | PROJECT |
| `.codex-worktrees/XITHI-xansible-decisions-0.5.16/AGENTS.md` | PROJECT, SECURITY |
| `.codex-worktrees/XITHI-xansible-decisions-0.5.16/tools/AGENTS.md` | PROJECT, SECURITY |
| `.codex-worktrees/XITHI-xansible-decisions-0.5.16/tests/ansible/AGENTS.md` | PROJECT |
| `.codex-worktrees/XITHI-xansible-decisions-0.5.16/ansible/AGENTS.md` | PROJECT, SECURITY |
| `.codex-worktrees/XITHI-xansible-decisions-0.5.16/supervision/AGENTS.md` | PROJECT |

Compléments de classification :

| Source | Classification | Action |
| --- | --- | --- |
| ~/.codex/AGENTS.md ancienne section | GLOBAL, OBSOLETE | remplacée |
| infrastructure/AGENTS.md ancienne préférence | GLOBAL, OBSOLETE ; restriction SECURITY | préférence retirée, sécurité conservée |
| SD-WAN/docs/project/LOCAL_LLM.md | GLOBAL, OBSOLETE, CONFLICT, PROJECT, SECURITY | laissé pour arbitrage ciblé |
| super-agent/AGENTS.md distant | PROJECT, SECURITY, CONFLICT avec universalité | CODEX_HOME isolé préservé |
| 13 AGENTS distants super-agent/nodectra | PROJECT, SECURITY, exception ci-dessus | lecture seule |
| codex/15, 16, 17, rapports P3, anciens README | historique / description | conservés |

## Dépendances et blocages du retrait

1. Infrastructure-Ops/AGENTS.md impose encore local_llm, Qwen et 32K ; règle
   GLOBAL/OBSOLETE/CONFLICT. `git fetch origin` effectué selon sa procédure ;
   divergence observée **3 / 3** par rapport à l’amont. Sa procédure impose un
   arbitrage avant poursuite : aucune modification de ce checkout ni worktree.
2. SD-WAN/AGENTS.md charge docs/project/LOCAL_LLM.md : préférence local_llm,
   128K, consignes de mission et autorisation de secrets uniquement au local.
   Mélange volontaire de règles projet/sécurité et routage : laissé pour décision,
   aucune transformation de l’autorisation locale en autorisation Cloud.
3. Plusieurs processus historiques local-llm-mcp sont attachés à des clients
   Codex vivants. Cela prouve leur chargement, pas une génération en cours ;
   aucun processus arrêté, aucune session réinitialisée.
4. Aucune référence trouvée dans les deux AGENTS OpenClaw Pro/Perso contrôlés,
   ni dans openclaw.json contrôlé. Pas de modification OpenClaw.
5. Scripts historiques smoke_local.py et recettes documentaires restent des
   consommateurs explicites de qualification/rollback, pas une dépendance de
   production démontrée. Sources et lanceur conservés.
6. Choix autonome routeur non démontré par le test borné ; revue locale rejetée
   pour qualité. Ne pas prétendre la substitution qualifiée pour tous les usages.

**NEXT REQUIRED ACTION** : arbitrer le checkout Infrastructure-Ops divergé et
l’exception SD-WAN, puis qualifier une tâche autonome réellement représentative
avant retrait. Aucun retrait ni désactivation de local_llm pendant ce lot.

## Audit node_repl

Origine vérifiée : MCP déclaré globalement, commande Mach-O arm64 embarquée dans
`/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node_repl`.
Distinct du feature natif `js_repl=false` et de llm-router.

Runtime Node/JavaScript persistant : marqueur créé dans un appel et relu dans
un second ; top-level await/import dynamique et lecture fs disponibles. L’objet
nodeRepl expose cwd et métadonnées de requête. Pas de borne de permissions déduite
abusivement des chemins trusted : l’import fs disponible ne qualifie pas une
isolation de sécurité complète. Processus du compte macOS, ressources CPU/mémoire,
accès fichiers et navigateur selon les API et contrôles clients.

Consommateur actif : configuration du plugin unified-computer-use pointe
CUA_REPL_NODE_REPL_PATH vers ce même binaire ; le navigateur utilise les services
trusted. Plusieurs processus actifs observés. La déclaration globale et le runtime
partagé sont distincts ; on ne prétend pas que supprimer la seule déclaration
arrêterait tous les consommateurs. Son indépendance sans régression n’est pas
qualifiée. **Décision : conserver déclaration, fichiers et dépendances.**
Apport : état interactif conservé, imports Node et automatisation navigateur ;
le shell ne remplace pas à lui seul les objets persistants de ces sessions.

## Validation et limites

| Contrôle | Statut |
| --- | --- |
| Nouvelle instruction globale chargée dans cette conversation | VERIFIED, actualisation AGENTS fournie par le client |
| Config/read Desktop depuis mac-ia-local, CaaS, m3-si-xithi | VERIFIED, GPT-6.1-Sol et mêmes trois MCP |
| Chargement effectif de toutes instructions dans ces trois nouvelles générations | NOT_TESTED, aucune génération par dépôt |
| Délégation locale asynchrone, récupération et corrélation | VERIFIED |
| Qualité revue locale | PARTIAL, contenu rejeté |
| Préférence autonome routeur | PARTIAL, traitement direct pour tâche triviale |
| Collecteur P3-C | VERIFIED ; webview nouvelle tâche NOT_TESTED |
| Retrait ancien MCP | BLOCKED, conservé |
| Autres MCP inchangés | VERIFIED, comparaison TOML avant/après |
| GPT et DIRECT LiteLLM après changement | PARTIAL, configuration préservée ; nouvelle inférence NOT_TESTED |
| RTK | VERIFIED 1.0.1, section identique ; hooks globaux absents avant et après |
| node_repl | VERIFIED runtime persistant ; conservé |
| git diff --check | VERIFIED |

config/read ne prouve pas l’injection de toutes instructions ni la connexion de
chaque MCP projet ; les capacités de modèles tiers restent celles de P3.
Aucun benchmark, aucun test serveur modifié donc aucune nouvelle campagne moteur.

Référence officielle confrontée au client :
[chargement global et hiérarchique AGENTS](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
Les restrictions de projet et CODEX_HOME isolés continuent de primer dans leur périmètre.

## Rollback ciblé

Préimages privées avant chaque écriture dans `artifacts/p4-migration/`, manifeste
`changes.json`, empreintes avant/après et diffs. Ne pas restaurer config.toml entier :
remettre seulement la valeur model antérieure si elle correspond encore à notre
valeur après P4. Restaurer uniquement la section délégation de l’AGENTS global et
celle de sa copie à partir de leurs préimages respectives ; conserver RTK,
Graphify et toute écriture concurrente. Pour les trois AGENTS de ce dépôt, annuler
seulement les lignes du diff P4. Aucun rollback moteur/clé/budget requis.
Avant application, comparer état actuel et after_sha256 ; si divergence, fusion
manuelle ciblée obligatoire. Les empreintes et préimages sont présentes ; rollback
préparé, pas exécuté sur la configuration active.

Sources historiques conservées ; aucun commit/push. Arrêt après P4 avec les
blocages et limites ci-dessus, aucune mission suivante lancée.


## Finalisation après arbitrage explicite — 21 octobre 2026

### Nettoyage réellement appliqué

L’utilisateur autorise les modifications ciblées malgré la divergence, sans merge,
rebase, commit ou push. Les anciennes préférences ne sont plus un blocage.

- Infrastructure-Ops/AGENTS.md : bloc local_llm/Qwen/32K supprimé. Interdiction de
  secrets délégués préservée dans « Confidentialité des sous-tâches ». Toute autre
  ligne de la préimage reste identique, notamment accès, RBAC, procédures et rapports.
- SD-WAN/docs/project/LOCAL_LLM.md : préférence local_llm/Qwen et prescription
  SOL/Medium retirées. Autorisation de secrets conservée pour exécution exclusivement
  locale ; interdiction explicite du Cloud. Critères de validation réseau, preuves,
  responsabilités et limites de concurrence conservés. Historique de délais étiqueté
  comme historique, sans nouvelle prescription. Correction d’une autorisation de reprise
  obsolète : le checkpoint courant prime (STATE.md:1748 déclare une pause).
- SD-WAN/AGENTS.md:89 : lien conservé sous « contraintes des sous-tâches du projet ».
- Aucune nouvelle préférence llm-router ajoutée dans ces dépôts.

La recherche des instructions actives dans les six racines locales inventoriées
ne retrouve plus de prescription local_llm. Restent les rapports historiques et
les sources de rollback, volontairement conservés. Exclusions techniques identiques
à l’inventaire initial ; ne pas annoncer de couverture des comptes inaccessibles.
Préimages, empreintes et diffs : artifacts/p4-finalization/changes.json et *.diff.

### Origine exacte de la divergence Infrastructure-Ops

Local : e527351 (historique menu Exécutions), e3f8498 (choix du bastion),
87e1d89 (preuve de livraison 0.9.5). Distant : 5a88736 (audit SMTP FBA10),
6d6f460 (diagnostic CPU FBA-CFM), d2f9c0a (diagnostic BAM-CENTRAL-01).
Les trois commits distants touchent des missions documentaires ; les trois locaux
portent xansible, ses tests et preuves. Aucun ne modifie AGENTS.md.
La consigne historique était un ajout non committé distinct, confirmé par git diff.
Aucune synchronisation de branches appliquée ; autres travaux et index préservés.

### Chargement global et test autonome

Config/read strict du binaire Desktop depuis Infrastructure-Ops et SD-WAN :
GPT-6.1-Sol, mêmes trois déclarations MCP, couches de configuration présentes.
La politique globale existe, aucune surcharge AGENTS.override identifiée à l’audit.
La revue indépendante a effectivement lu ~/.codex/AGENTS.md:311, les AGENTS projet,
STATE et la passation. Les règles globales sont également injectées dans son contexte.
Cela prouve le chargement pour cette revue ; config/read seul ne prouve pas une
nouvelle génération dans chacun des deux dépôts.

Prompt de revue documentaire autonome : aucun MCP ni modèle imposé. Le sous-agent
Curie, 01a15ea6-ff32-76f2-a27e-6d62252052fd, choisit spontanément llm-router,
consulte son catalogue puis exécute une seule soumission. **Choix autonome VERIFIED.**

Tâche 9cd001b5-4fd6-4c64-b788-7d1237e62a10 : backend local, alias Qwen3.6,
1098 tokens (398 entrée, 700 sortie), 24 107 ms, une tentative, retries/fallbacks 0.
Le sous-agent a explicitement sélectionné l’alias après consultation du catalogue.
actual_model=null : provenance fournisseur non confirmée. Parent_session omis
par le sous-agent : la nouvelle tâche n’est pas rattachée au parent dans le collecteur.
Aucune correction artificielle du stockage pour reconstruire ce lien.

**Résultat fonctionnel non validé** : failed / truncated_or_invalid_completion,
finish_reason=length, texte vide. Point de refus : mcp/llm-router/router.py:475.
Le plafond 700 tokens a été atteint ; aucun diagnostic plus précis du contenu
interne n’est démontré. status/result récupèrent cet échec sans nouvelle génération.
L’orchestrateur rejette le résultat et vérifie directement le diff ; il ne transforme
pas l’erreur en succès. Aucun retry, autre modèle ou appel Cloud.

Collecteur P3-C en lecture seule : tâche retrouvée, failed, 1098 tokens, 24 107 ms,
parent null, aucune erreur collecteur. Preuve collector-task.json. L’affichage
webview Live Call de cette tâche reste NOT_TESTED ; Agent Standup inchangé.

### Dépendances et décision de retrait

Aucune dépendance fonctionnelle restante identifiée dans les instructions actives,
les configurations OpenClaw contrôlées et les configurations de services ciblées.
La seule déclaration active retrouvée est ~/.codex/config.toml:70-72.
Douze traces récentes contrôlées (queues bornées 1 Mio) : aucun appel historique
non terminé identifié ; cette recherche bornée ne prouve pas une absence universelle.
Les processus anciens chargés dans les sessions ne sont ni arrêtés ni réinitialisés.

**local_llm conservé uniquement parce que le test autonome complet n’a pas fourni
un résultat utilisable**, conformément à la condition explicite utilisateur.
Aucune ancienne consigne ni divergence Git ne bloque désormais son retrait.
Risque concret d’un retrait déclaré validé maintenant : prétendre qualifier une
substitution sur une revue ayant échoué, sans résultat local exploitable.
Action minimale restante : une recette autonome bornée produisant un résultat
utilisable avec un plafond de sortie adapté, à autoriser/reprendre sans répétition
automatique de cet échec. Ensuite supprimer uniquement le bloc MCP ancien.
Aucun changement moteur ou niveau de raisonnement nécessaire pour préparer cette recette.

### GitHub : identité et limite établies

Authentification existante utilisée en lecture seule : gh api user confirme
FloVisor, id 321680055. Aucun token affiché. Aucun GH_TOKEN/GITHUB_TOKEN fourni
par l’environnement contrôlé. gh api users/fngux2 retourne HTTP 404 Not Found.
Il ne s’agit pas d’un refus 401/403 de l’identité existante. L’API ne permet pas
ici de distinguer compte absent, renommé ou non visible ; ne pas inventer la cause.
Aucun autre credential essayé. FloVisor n’est pas assimilé à fngux2.
**Tous les dépôts éventuellement associés à fngux2 restent non audités, liste
impossible à établir avec cette réponse.** Pas de centralisation distante exhaustive.

### Préservation et rollback de cette finalisation

Configuration active Codex non modifiée pendant cette reprise ; ancien MCP toujours
présent. Copie privée config.before-removal.toml préparée et conservée ; code source
historique et lanceur intacts. Pour annuler les corrections documentaires, utiliser
les préimages de changes.json après comparaison des empreintes ; appliquer seulement
les blocs des diffs, jamais une restauration globale du dépôt ou de config.toml.

Contrôles : git diff --check dans les deux dépôts PASS ; contrôle de la portée du
bloc Infrastructure PASS ; revue directe du diff SD-WAN effectuée. Aucune campagne
P3 rejouée. RTK, proxy, adaptateur, catalogue, raisonnement, Agent Standup, OpenClaw,
modèles serveur, clés, budgets et node_repl inchangés. Aucun commit/push.

Arrêt après cette finalisation ; blocage technique conservé, aucune relance automatique.


## Clôture contrôlée — plafond identifié et retrait effectué

### Origine exacte du plafond : VERIFIED

La consigne de recette donnée par l’orchestrateur au sous-agent Curie imposait
une sortie de 700 tokens. Le sous-agent l’a répercutée dans sa soumission MCP :
`max_output_tokens:700`, et dans le texte « Maximum700 tokens ».
Le journal de session `01a15ea6-ff32-76f2-a27e-6d62252052fd` conserve cet appel
custom_tool_call ; la requête persistée de la tâche confirme la même valeur.
Lecture de la requête par SQLite en mode ro/query_only uniquement, aucune écriture.

- router.py:23-29 : le profil review fournit une instruction textuelle, pas un plafond.
- router.py:438 : le routeur transmet `max_tokens=args.get('max_output_tokens',2048)`.
- L’appel transmet donc 700 à LiteLLM ; ce n’est pas une limite imposée par le profil.
- Retour : completion_tokens=700, finish_reason=length ; refus explicite router.py:475.
- Aucun élément ne démontre une limite indépendante 700 côté LiteLLM ou backend.
  Le résultat suffit à établir le plafond client atteint, pas le détail interne
  du contenu ni l’application effective du raisonnement off.

Cette limite s’est révélée insuffisante pour cette revue. Pour une prochaine revue
structurée de cette portée, proposition ciblée : omettre max_output_tokens pour
utiliser le défaut existant 2048, ou l’expliciter à 2048 sur cette seule requête,
avec format attendu concis. Cela ne garantit pas la qualité ou la terminaison.
Aucun défaut global, profil, réglage LiteLLM, backend ou budget modifié.
**Aucune nouvelle génération effectuée**, ni relance pour obtenir un PASS.

### Validation et décision

| Point | Statut final |
| --- | --- |
| Découverte autonome | VERIFIED |
| Sélection spontanée de llm-router | VERIFIED |
| Soumission et récupération asynchrones | VERIFIED, preuves précédentes conservées |
| Exécution complète de la revue | FAILED, plafond client 700 atteint ; aucun résultat utilisable |
| Qualification générale de qualité du modèle | Non revendiquée |
| Supervision collecteur P3-C | VERIFIED, failed visible ; parent absent conservé |
| Webview quotidien de cette tâche | NOT_TESTED |
| Migration de la préférence globale | VERIFIED |
| Retrait déclaration local_llm | VERIFIED |

L’arbitrage utilisateur retient le choix spontané comme critère principal. La
troncature bornée par la requête n’est pas un défaut de découverte ni une dépendance
fonctionnelle nécessitant de conserver le MCP historique. Son échec est conservé.

### Dépendances et retrait

Nouvelle recherche ciblée dans les instructions et configurations des six racines
locales, instructions globales, OpenClaw Pro/Perso et configuration contrôlée :
seules références restantes dans les instructions : description du code historique
(mac-ia-local/AGENTS.md:21) et index de rapports (codex/AGENTS.md:10).
Ce sont des descriptions, pas des prescriptions de délégation.
Les vérifications précédentes des services ciblés et traces récentes sont réutilisées.
Aucun consommateur fonctionnel dépendant identifié dans ce périmètre ; ne pas
assimiler cette conclusion à une preuve universelle hors des chemins audités.

Suppression du seul bloc `[mcp_servers.local_llm]` de ~/.codex/config.toml.
Comparaison TOML stricte : toutes les autres valeurs sont identiques, y compris
node_repl, llm-router, modèle courant, plugins, contextes et niveaux de raisonnement.
Le catalogue llm-router répond après retrait, sans inférence.
Les sessions déjà ouvertes peuvent conserver les outils découverts au démarrage ;
aucune session ni processus existant n’a été forcé à redémarrer. La disparition
s’applique aux nouveaux chargements de configuration.

### Préservation et rollback immédiat

Preuves privées : `artifacts/p4-closeout/` :

- config.before.toml (permissions 0600), local_llm.toml et config.diff ;
- dependency-audit.json ; fresh-codex.json ;
- preservation.before.json et preservation.after.json ;
- rollback.py, syntaxe compilée et reconstruction TOML exacte vérifiée en mémoire.

Rollback supporté par fichier de configuration documenté :

```sh
python3 artifacts/p4-closeout/rollback.py
```

Le script refuse si local_llm existe déjà ; sinon ajoute uniquement la déclaration
sauvegardée, contrôle sa valeur et conserve toutes les autres configurations,
y compris les modifications concurrentes. Ouvrir ensuite une nouvelle session Codex.
Le rollback n’a pas été exécuté sur le fichier actif pour ne pas annuler la migration.
Le code source `mcp/local-llm-mcp/local-llm-mcp.py` et le lanceur historique gardent
leurs empreintes. Instructions globales, configuration routeur et catalogue gardent
également leurs empreintes de début de clôture. Les contrôles documentaires précédents
restent valides, aucune nouvelle campagne rejouée.

RTK, Agent Standup, OpenClaw, LiteLLM, modèles, clés, budgets, raisonnement,
contextes et node_repl préservés. Aucun appel payant, aucun commit/push.
La limite GitHub fngux2 HTTP404 reste indépendante : inventaire non exhaustif de
ce compte, jamais assimilé à FloVisor. Arrêt après P4.
