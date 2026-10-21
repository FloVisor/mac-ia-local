# P3-B — OpenClaw, accès DIRECT et autorisations payantes

21 octobre 2026. **Résultat global : PARTIAL. Arrêt avant P3-C.**
Aucun commit/push. Aucune génération payante ou nouvelle génération Cloud gratuite.

## État effectivement livré

| Point de la mission | Statut | Preuve / limite |
|---|---|---|
| 1. Architecture déployée | IMPLEMENTED | Plugin OpenClaw → MCP stdio privé par agent → LiteLLM. DIRECT → LiteLLM indépendamment du MCP. |
| 2. Fichiers modifiés | VERIFIED | Liste ci-dessous ; comparaison sémantique de la configuration active conservée. |
| 3. Identités et clés | VERIFIED | Trois identités DIRECT nouvelles, identités DELEGATED Pro/Perso réutilisées ; huit clés distinctes relues par API native. |
| 4. Catalogue client | PARTIAL | CLI et API Gateway : 17 modèles par agent, trois catégories lisibles ; interface graphique non vérifiée. Codex : commande DIRECT préparée, aucune fusion du sélecteur graphique. |
| 5. Accès effectifs | VERIFIED | Nouvelles conversations Pro/Perso : découverte, invocation et récupération autonomes du routeur local. Perso a nécessité une reprise après expiration du premier tour. |
| 6. DIRECT / DELEGATED | IMPLEMENTED | Credentials, identités et chemins distincts. Sélection utilisateur sans confirmation par génération ; aucune clé DIRECT dans le worker. |
| 7. Autorisations ponctuelles PAID | PARTIAL / BLOCKED production | Politique du courtier fail-closed et registre persistant implémentés, recette ciblée simulée ; adaptateurs réels non qualifiés, DELEGATED PAID désactivé. Voir dernière correction. |
| 8. Budget partagé | VERIFIED | Trois clés DIRECT PAID dans `paid-openrouter-shared`, 40 USD / 1mo, dépense finale observée 0 USD ; aucun nouveau budget. |
| 9. Isolation Pro/Perso | VERIFIED | Clés/configurations/états séparés. Perso refuse status/result de la tâche Pro ; activité Perso vide. Pas une frontière OS entre processus malveillants du même compte macOS. |
| 10. Recettes | VERIFIED | Recettes conversationnelles Pro/Perso et refus status/result dans les deux sens ; détails et limites dans la reprise ciblée. Tests antérieurs conservés sans réexécution. |
| 11. Approbations existantes | VERIFIED | 31 tests PASS après changement ciblé ; configuration des plugins/connecteurs conservée. Aucun envoi réel ni modification du système de confirmation des messages. |
| 12. GPT / RTK / MCP historique | PARTIAL | Sources/binaire historique inchangés ; configuration Codex préservée sauf changement concurrent n8n-mcp. GPT natif direct reste NOT_TESTED ; RTK non modifié. |
| 13. Limites | PARTIAL | Détail ci-dessous : délai/reprise Perso, courtier, GUI, Cloud, capacités, contextes et coût opérationnel. |
| 14. Rollback | PARTIAL | Patch ciblé validé en dry-run ; rollback réel non exécuté pour conserver la livraison. Révocation/retour des credentials documentés. |
| 15. Préparation P3-C | IMPLEMENTED | Session, agent, task ID, alias, provenance limitée, tokens, durée et état disponibles ; Agent Standup non modifié. |

## Architecture et identité

`main` (Pro) utilise `~/.config/llm-router/openclaw-pro.json`,
`~/.local/state/llm-router/openclaw-pro` et sa clé DELEGATED.
`perso` utilise les chemins homologues `openclaw-perso`.
Le plugin choisit ces chemins depuis `ctx.agentId` fourni par le runtime.
`parent_session` vient de `ctx.sessionId`. Aucun champ d'identité, session,
credential, chemin de configuration, mode DIRECT ou accord payant n'est accepté
comme argument du modèle. Le sous-processus reçoit un environnement minimal,
sans credentials DIRECT hérités. Le routeur et son worker persistant sont réutilisés.
Aucune mémoire ni fichier de workspace n'est copié dans LiteLLM.

Sept outils : `llm_router_submit`, `delegate`, `status`, `result`, `cancel`,
`activity`, `catalogue` (tous avec le préfixe `llm_router_`).
Le manifeste déclare `contracts.tools`. `routerPath` absolu est fourni dans la
configuration opérateur : OpenClaw capture les plugins dans un autre répertoire,
rendant les chemins relatifs vers une source externe invalides.

**Constat initial, corrigé par la reprise ciblée en fin de rapport :** ces outils fonctionnent via `/tools/invoke` dans le
contexte des sessions authentifiées des agents. Les essais du modèle Pro via
`tool_search`, puis avec l'identifiant différé explicite
`openclaw:llm-router:llm_router_submit`, n'ont pas trouvé l'outil dans son catalogue.
Les recherches sont conservées comme échecs, pas déclarées réussies.
Le chargement du plugin et l'API native ne prouvent donc pas la délégation
autonome dans une conversation. Aucun changement global de découverte, du
runtime ou des instructions des workspaces n'a été appliqué pour la forcer.

## Identités, clés et budget

| Usage | Propriétaire LiteLLM | Clé virtuelle (alias) | Équipe |
|---|---|---|---|
| Pro DELEGATED | openclaw-pro (réutilisé) | openclaw-pro-delegated | aucune, LOCAL/FREE |
| Perso DELEGATED | openclaw-perso (réutilisé) | openclaw-perso-delegated | aucune, LOCAL/FREE |
| Pro DIRECT LOCAL/FREE | openclaw-pro-direct (créé) | openclaw-pro-direct-local-free | aucune |
| Pro DIRECT PAID | openclaw-pro-direct | openclaw-pro-direct-paid | paid-openrouter-shared |
| Perso DIRECT LOCAL/FREE | openclaw-perso-direct (créé) | openclaw-perso-direct-local-free | aucune |
| Perso DIRECT PAID | openclaw-perso-direct | openclaw-perso-direct-paid | paid-openrouter-shared |
| Codex DIRECT LOCAL/FREE | codex-direct (créé) | codex-direct-local-free | aucune |
| Codex DIRECT PAID | codex-direct | codex-direct-paid | paid-openrouter-shared |

Toutes les clés sont `llm_api`, sans wildcard. Les clés LOCAL/FREE ont exactement
les 13 alias approuvés, les payantes exactement les trois alias PAID.
Aucune MASTER_KEY sur le Mac ou dans un client. Administration par API native
sur le serveur, pas d'écriture en base interne.
Secrets locaux 0600 dans `~/.config/llm-router` (0700), jamais dans le dépôt.
Copie serveur privée sous `/srv/docker-local/compose/litellm/secrets/p3b`.
Credentials DIRECT OpenClaw importés par `models auth paste-api-key --agent …` ;
pas de secret dans `openclaw.json`.

L'import initial avec des noms génériques a révélé l'héritage natif des profils
statiques de Pro par Perso. Correction : providers `litellm-free-pro`,
`litellm-paid-pro`, `litellm-free-perso`, `litellm-paid-perso` ;
`modelPolicy.allow` explicite par agent excluant les providers de l'autre.
Les quatre profils génériques temporaires ont été retirés avec la CLI native.
Les profils statiques Pro peuvent encore être annoncés à Perso par l'héritage
natif, mais leurs providers sont exclus de sa politique de sélection.

Budget équipe relu après création : **40 USD / 1mo, spend 0 USD**. Les trois
identités DIRECT sont membres de la même équipe. Pas de plafond indépendant de
40 USD par clé/agent. Les compteurs sont asynchrones ; leur délai exact n'a pas
été mesuré, et aucune coupure au centime n'est garantie. Le plafond OpenRouter
existant n'a pas été modifié ni requalifié. Aucun test payant réel.

## Catalogue et sélection DIRECT

Chaque agent annonce 17 modèles : les deux modèles natifs existants et quinze
alias conversationnels LiteLLM (deux LOCAL, dix FREE, trois PAID).
EmbeddingGemma reste un embedding autorisé à la clé, exclu des sélecteurs de chat.
Muse-Glimmer n'est pas réactivé : la politique explicite le retire aussi de la
sélection issue de la découverte Ollama native.
Les noms portent `[LOCAL]`, `[CLOUD FREE]`, `[CLOUD PAID OpenRouter]`.
Le flag natif `local:false` des alias LiteLLM décrit le transport HTTPS ; les
labels LOCAL désignent leurs backends. Une annonce `available:true` signifie
ici présence d'un credential, pas une inférence qualifiée.

Les nouvelles déclarations utilisent une admission conservatrice 8192 tokens,
2048 de sortie ; ce n'est pas une fenêtre maximale validée. Les anciennes
configurations de contexte et les modèles par défaut restent identiques.
Les capacités tools/vision/reasoning des routes Cloud restent NOT_TESTED ; aucun
budget numérique oMLX n'est envoyé au Cloud par le nouvel adaptateur.
Le plugin oMLX existant est inchangé (Ultra → High/8192 conservé).

`catalogue.py --agent pro|perso` croise `/v1/models` authentifié et l'approbation
opérateur existante ; sortie patch + diff à examiner, sans application automatique.
Pas de suppression, promotion d'un modèle désactivé, réécriture de credentials
ou de définitions personnalisées. Toute nouvelle permission nécessite aussi une
révision explicite du `modelPolicy.allow`. Test d'idempotence et de préservation PASS.

DIRECT utilise le provider sélectionné ; aucune confirmation de paiement n'est
ajoutée à chaque réponse. Le modèle ne peut pas se donner ce droit via
`session_status(model=…)` : la politique refuse les changements demandés par
outil, sauf retour au modèle `default` existant. Les autres opérations sensibles
restent sous leurs mécanismes antérieurs.

LiteLLM : retries globaux 0, fallbacks [], retries des trois routes PAID 0.
`paid/task-advanced` pointe uniquement vers
`openrouter/deepseek/deepseek-v4.1-flash-1017` ; GLM reste indépendant.
Aucune modification de ces définitions, des pools ou des backends.

Codex : `codex/scripts/llm-router-direct.py --model ALIAS -- …` prépare une
sélection explicite avec provider Responses LiteLLM et variable privée transmise
au seul processus lancé. Aucun changement de `config.toml`, du provider GPT
par défaut, de l'authentification ChatGPT, de RTK ou du catalogue graphique.
Le binaire Codex installé accepte les surcharges et `config/read` confirme
`model_provider=litellm-direct`, URL LiteLLM, `wire_api=responses`,
`requires_openai_auth=false`, modèle GLM exact. Aucune génération Codex DIRECT
réelle, aucun affichage GUI prétendu. Le proxy GPT configuré reste inchangé ;
GPT natif direct reste NOT_TESTED comme en P3-A.

## DELEGATED payant : désactivé

Les deux clés DELEGATED refusent PAID avec **403** sur une sonde volontairement
incomplète, sans payload de génération valide. Le worker ne possède aucune clé
DIRECT. Un `paid_authorization` textuel n'ouvre aucun accès.
Les métadonnées de routage réutilisées autorisent actuellement trois candidats
MCP : Qwen oMLX, Groq/Qwen, Mistral/Ministral. Les autres modèles annoncés par
LiteLLM ne deviennent pas des candidats qualifiés par simple synchronisation.

Un test ciblé supplémentaire des primitives `Authorizations` utilise un fournisseur
simulé : refus/absence d'accord, changement d'identité/tâche/modèle/empreinte,
plafond dépassé, budget inconnu, révocation, expiration, réemploi ; huit appels
concurrents, un seul permis consommé et un seul appel simulé (0,004 USD simulé,
limite 0,01 USD). Aucun coût simulé n'est présenté comme réel.

Ces primitives ne prouvent pas un courtier privilégié opérationnel : il manque
un adaptateur de confirmation authentifié, un plafond réel par opération, une
réservation de budget globale et une exécution séparée du credential PAID.
**Aucun courtier ni outil d'émission de grants n'est exposé ; aucune escalade PAID
DELEGATED activée.** Pas de duplication des confirmations Gmail/Graph/iMessage.

## Recettes et preuves

Preuves privées filtrées sous `artifacts/llm-router-p3b/` (ignoré par Git).
Les captures de `diagnostics/` préexistantes n'ont pas été modifiées.

- **3 tests Node PASS** : identité/session imposées, falsifications d'arguments
  refusées, sept outils seulement autorisés, changement de modèle par outil refusé.
- **1 test de synchronisation PASS** : préservation des secrets, modèles par défaut,
  définitions personnalisées/désactivées, exclusions, idempotence.
- **1 test adversarial d'autorisations PASS**, avec concurrence et fournisseur simulé.
- **31 tests des protections OpenClaw PASS** après le changement final.
- Compilation Python du lanceur DIRECT et du synchroniseur ; configuration
  OpenClaw valide, plugin chargé, Gateway `ok:true`, probe iMessage `ok:true`.
- Les 41 tests historiques du routeur ne sont pas relancés.
- Une seule nouvelle inférence déléguée réelle : tâche
  `41e74897-2c1f-4c13-8944-8ca5d662d63c`, `openclaw-pro`, session
  `18fd7ecf-455e-4a2c-9bd1-42242a47120d`, état `completed`, JSON brut
  `{"value":4}`, qualité JSON PASS, 767 ms, 42/5 tokens, stop, retries/fallbacks 0/0.
  Request ID `chatcmpl-c14fdc54`, déploiement
  `17720d29-9da3-4888-aef8-f6db0cc5bd96`. Spend log : identité `openclaw-pro`,
  cible oMLX `openai/mlx-community--Qwen3.6-35B-A3B-4bit`, coût observé **0 USD**.
  Le coût dans le routeur reste `null` faute d'en-tête ; `actual_model=null`
  reste distinct de cette confirmation opérateur par journal natif.
- Perso : lecture d'état et résultat de ce task ID → `task_not_found`, activité vide.
- Les tours du modèle Pro ont utilisé le modèle local existant, sans livraison
  de message externe ; la découverte puis l'appel différé ont échoué et restent
  enregistrés (`agent-search-history.json`, `agent-submit-idempotent.json`).
- Deux échecs gratuits antérieurs conservés : divergence exacte Groq initiale
  non reconstituable ; JSON Mistral entouré de Markdown non conforme au contrôle
  JSON brut. P3-A : `OK.` au lieu de `OK`, écart de format. Aucun assouplissement,
  aucune nouvelle génération Cloud pour compenser la ponctuation.

`doctor` signale notamment un ancien device token CLI et des avertissements
préexistants de visibilité d'autres outils ; aucune réparation globale ni rotation
de credentials n'est faite. Les API natives utilisées avec l'authentification
opérateur ont répondu. Ces avertissements ne sont pas déclarés résolus.

## Fichiers et préservation

Nouveaux : `openclaw/llm-router/{index.js,schemas.json,package.json,openclaw.plugin.json,
catalogue.py,README.md,test/isolation.test.mjs,test/catalogue_test.py}`,
`mcp/llm-router/test_p3b_authorizations.py`, `codex/scripts/llm-router-direct.py`,
ce rapport. Documentation P3-B ajoutée dans PHASE3/VALIDATION et integration-pitfalls.

Modification ciblée de `openclaw/send-approval/index.js` : autoriser les sept
outils de l'adaptateur et empêcher le changement de modèle par `session_status`.
Les envois, accords natifs et politiques de fichiers/système ne sont pas modifiés.

Configuration active initiale : ajout du plugin, des sept permissions, de quatre providers
scopés et profils DIRECT, et des deux politiques explicites de modèles.
Comparaison sémantique : modèles par défaut, plugins préexistants, connecteurs
MCP et configuration des canaux inchangés. Sources et binaire `local_llm`,
catalogue Codex et plugin oMLX ont les empreintes initiales.
Une écriture concurrente concerne `.mcp_servers.n8n-mcp` dans `config.toml` ;
elle est préservée. Toutes les autres valeurs TOML sont identiques à l'avant P3-B.
Aucun commit/push, ni changement d'oMLX/Ollama/modèles chargés/RTK/Standup.

## Rollback ciblé

Préimages privées `artifacts/llm-router-p3b/before-*`, inventaire
`preservation-before.json`. Ne jamais restaurer globalement ces fichiers sur
un état ayant changé entre-temps.

1. Comparer l'état courant au patch `rollback.patch.json`. Son **dry-run PASS**
   (`rollback-scoped-dry-run.json`) enlève seulement les providers et le plugin
   ajoutés, les sept permissions, puis rétablit les politiques de modèles initiales.
   Refaire ce diff avant une application réelle ; les listes doivent préserver
   d'éventuels ajouts concurrents. Application via `openclaw config patch --file …`.
2. Retirer les quatre nouveaux profils via `models auth logout --agent AGENT
   --yes PROFILE` : `litellm-free-pro:direct`, `litellm-paid-pro:direct` pour main ;
   `litellm-free-perso:direct`, `litellm-paid-perso:direct` pour perso. Aucun accès
   direct à une base SQLite. Révoquer uniquement les huit nouvelles clés avec
   l'API native `/key/delete` côté opérateur ; ne pas toucher à la clé historique
   LOCAL/FREE. Ne pas supprimer l'équipe ni modifier son budget.
3. Restaurer les deux seuls blocs P3-B de la politique à partir de la préimage
   après comparaison des changements concurrents. Recharger `send-approval` avec
   `--accept-capabilities`. Une désactivation peut laisser les outils inaccessibles
   sans arrêter les autres plugins.
4. Les nouveaux lanceurs Codex ne modifient aucun fichier global : cesser de les
   utiliser suffit pour ce chemin. Préserver les résultats privés du routeur pour
   audit ; ne pas supprimer des tâches encore actives.
5. Revalider config, santé Gateway et probe iMessage. En cas de schéma de plugin
   périmé en mémoire, relancer l'application après fermeture effective ; ne pas
   réécrire la registry ou une base interne.

## Blocages et suite minimale

**BLOCKER — délégation autonome OpenClaw :** outils disponibles via API native,
absents du catalogue différé du modèle. Tentatives : manifeste/chemin externe
corrigés, nouvelle session après relance, recherche native observée dans
`chat.history`, appel par identifiant explicite. Aucune nouvelle hypothèse
suffisamment étayée pour poursuivre cette boucle. Prochaine action : diagnostic
ciblé du catalogue d'outils du runtime installé, sans nouvelle inférence ni
élargissement de permissions. Le chemin natif LOCAL/FREE sûr reste déployé ;
l'accès autonome conversationnel n'est pas déclaré livré.

**BLOCKER — DELEGATED PAID :** pas de preuve de plafond opérationnel et de courtier
privilégié raccordé à une confirmation authentifiée. Prochaine action : qualifier
ce contrat serveur sur fournisseur simulé avant toute activation. Reste désactivé.

P3-C non commencé. Les événements privés permettent d'exposer ultérieurement
agent/session/tâche/alias, état/durée, tokens, coût connu ou null, erreurs/refus.
Les pools FREE n'ont pas été exécutés ; leur alias n'est jamais présenté comme
preuve de leur membre réel. Aucun prompt complet dans des journaux partagés.

Sources d'interface confrontées à l'installation : [configuration Codex](https://learn.chatgpt.com/docs/config-file/config-reference),
[clés virtuelles LiteLLM](https://docs.litellm.ai/docs/proxy/virtual_keys),
[budgets d'équipe LiteLLM](https://docs.litellm.ai/docs/proxy/team_budgets),
documentation OpenClaw installée (`tools/mcp`, `providers/litellm`,
`concepts/models`, `concepts/model-failover`, `gateway/tools-invoke-http-api`).


## Reprise ciblée — découverte et frontière payante (21 octobre 2026)

Aucun redéploiement, aucune nouvelle clé, aucun commit/push. Les 31 tests
antérieurs ne sont pas relancés. Preuves nouvelles privées :
`artifacts/llm-router-p3b/discovery-followup/`.

### Diagnostic de la découverte

- **VERIFIED** : manifeste `contracts.tools`, chargement du plugin et registre
  d'inspection (`tools.catalog`) contiennent les sept outils.
- **VERIFIED** : `tools.effective`, sur les sessions de recette, localise la
  différence : Pro exclut les sept outils au filtre du profil `coding`, avec
  `alsoAllowPath=agents.entries.main.tools.alsoAllow`. Sa liste propre
  `[message]` remplace le complément global. Perso hérite du complément global
  et annonce les sept outils `available`.
- **VERIFIED** : correction par `openclaw config patch`, après dry-run schéma /
  résolvabilité PASS : ajout des sept noms exacts à la seule liste Pro.
  `message`, les deny et agentToAgent sont conservés. Pas de wildcard,
  changement de profil ou ouverture globale. Après correction, les sept outils
  Pro sont `available` dans `tools.effective`. Gateway health relu.
- Le filtre localModelLean n'inclut pas ces noms dans ses exclusions. La
  compaction construit le catalogue depuis les outils survivant aux politiques ;
  `tool_search`, `tool_describe`, `tool_call` sont bien transmis à Qwen.
  Le refus Pro avait donc lieu avant cette construction ; l'API HTTP native
  n'exerçait pas ce même parcours. Aucun patch du runtime ni du moteur.
- **VERIFIED** : nouvelle conversation Perso, demande de calcul délégué sans
  nom d'outil : découverte puis invocation du routeur et création de
  `b075d3bc-ed47-4c10-aca4-7f3a5db21370`, session
  `7774414c-25ca-4575-8bd1-188c2cea46d5`, identité `openclaw-perso`.
  Résultat local `323`, état completed, durée routeur 66134 ms, 44/1064 tokens,
  retries/fallbacks 0/0. Coût routeur null, pas assimilé à un coût mesuré nul.
  **PARTIAL pour un tour unique** : premier tour expiré après 120 s pendant
  l'attente ; reprise dans la même conversation sans nouvelle tâche :
  `llm_router_result` via `tool_call`, résultat `323`, zéro échec.
  Pro refuse status/result de ce task ID : `task_not_found`.
- Le premier tour Pro avant correction a sélectionné `sessions_spawn`, refusé
  par la protection existante. Refus conservé ; aucune permission ajoutée à cet
  outil. Le tour après correction utilise une nouvelle conversation.

### Courtier : diagnostic et options avant nouvelle frontière

**BLOCKED en production, DELEGATED PAID reste désactivé.** Le worker refuse
explicitement un candidat PAID (`paid_broker_not_connected`) et ne détient pas
le credential DIRECT. Les huit clés et le budget partagé 40 USD/mois restent
inchangés. Aucun appel OpenRouter facturable n'est effectué.

La primitive `issue(decision="approved", identity=...)` accepte des chaînes
fournies par son appelant : elle ne prouve ni une identité cliente attestée ni
une décision native. Son `budget_remaining` est également une donnée appelante.
Elle n'est pas exposée ; la rendre accessible au modèle serait une faille.
Les tests simulés antérieurs ne prouvent donc pas un courtier complet.

Option A proposée, soumise à décision avant implémentation : courtier isolé et
recette exclusivement simulée, sans activation PAID. L'adaptateur natif lie une
résolution `allow-once` attestée à l'identité runtime Pro/Perso, à la session,
au task ID, au modèle exact, à l'empreinte canonique du payload, au plafond USD
et à l'expiration. Aucun de ces attributs d'autorité ne vient d'un argument du
modèle. Révocation possible avant consommation ; consommation et réservation
atomiques, un seul appel concurrent, aucun rejeu ni reprise automatique après
résultat incertain. L'exécuteur séparé doit vérifier côté serveur l'appartenance
à `paid-openrouter-shared`, sans nouvelle clé ni budget indépendant. Les accords
Gmail/Outlook/SMS/iMessage/fichiers/commandes existants restent distincts.

La réservation locale ne suffit pas à garantir le budget partagé avec les
appels DIRECT concurrents. Un solde déclaré ou des compteurs asynchrones ne
constituent pas une réservation globale. Il faut un contrôle serveur commun
aux chemins DIRECT et DELEGATED, ou refuser DELEGATED si ce contrôle manque.
De même, estimation tokens × prix, `max_tokens`, annulation de flux ou contrôle
a posteriori ne garantissent pas un plafond facturable par opération. Le
contrat fournisseur doit imposer ce plafond avant génération ; capacité absente,
inconnue ou non attestée => refus serveur, zéro appel fournisseur.

Recette proposée : fournisseur simulé comptant ses appels ; attestations
absentes/falsifiées, changement d'identité/session/tâche/modèle/payload/plafond,
expiration, révocation, rejeu, concurrence, budget inconnu/insuffisant, mauvaise
équipe, absence de garantie de plafond et coût simulé au plafond. Un appel
simulé seulement pour un permis valide ; zéro dans chaque refus.

Option B : conserver le blocage documenté sans ajouter cette frontière.
**NOT_TESTED** : adaptateur natif de paiement, courtier serveur privilégié,
réservation commune avec DIRECT et garantie effective de plafond fournisseur.
Ces capacités ne sont pas déclarées implémentées ou vérifiées. La question de
périmètre a été présentée avant toute application de cette nouvelle frontière,
conformément à la consigne de reprise. Arrêt avant P3-C.


### Résultat final de la recette Pro après correction

**VERIFIED** : conversation neuve `agent:main:p3b-autonomous-fixed-20261021`,
session `ebb8c52d-38a4-4c2f-b323-99e8552725fd`, demande sans nom d'outil.
Qwen découvre le routeur, l'invoque et récupère le résultat de
`03f28a06-7323-4291-a798-6f567ddd9512` : `{"result":323}`.
Identité `openclaw-pro`, backend local, 2125 ms de génération déléguée,
55/8 tokens, reasoning demandé off, retries/fallbacks 0/0.
Le résumé du tour conserve 13 appels et 3 échecs : notamment un alias oMLX
natif inconnu du routeur, puis consultation du catalogue et choix de l'alias
`local-omlx/...` correct. Ce n'est pas une recette sans erreur intermédiaire.
Perso refuse status/result de cette tâche : `task_not_found`.
Les deux historiques complets, réponses finales et refus croisés sont conservés.
Gateway `health.ok=true`. Aucun élargissement de l'autorisation des lectures.

Bilan des deux blocages : découverte **VERIFIED** (reprise Perso explicitée),
courtier de production **BLOCKED**, mission **PARTIAL**. Nouvelle implémentation
et nouveaux tests simulés du courtier **NOT_TESTED**, en attente de décision sur
la frontière proposée ; les tests simulés antérieurs restent acquis.

Retour arrière de la seule correction de cette reprise : supprimer uniquement
les sept noms `llm_router_*` ajoutés à
`agents.entries.main.tools.alsoAllow`, avec comparaison de l'état courant et
préservation des ajouts concurrents. Préimage ciblée `pro-policy-before.json`.
Le rollback initial ne couvre pas automatiquement ce complément par agent.


## Autorisation de tests en production — suite du 21 octobre 2026

L'utilisateur autorise ensuite les tests directement en production. Cette
réponse lève l'attente d'autorisation précédente ; elle ne supprime pas les
exigences de plafond par opération, d'accord ponctuel DELEGATED et de refus si
le contrôle est impossible. Aucun accord permanent de paiement n'est créé.

### Contrôles réellement exécutés

Preuves nouvelles : `artifacts/llm-router-p3b/broker-production/`.

| Contrôle | Statut | Résultat et portée |
|---|---|---|
| Version et mécanisme de réservation | VERIFIED | LiteLLM 1.104.5 actif contient `reserve_budget_for_request`, appelé après les contrôles communs. Le diagnostic initial ne doit pas être interprété comme une absence de réservation native. |
| Configuration de réservation | VERIFIED | `/etc/litellm/config.yaml` : `disable_budget_reservation` et `fail_closed_budget_enforcement` non définis. Réservation non désactivée ; mode de refus strict non activé par cette configuration. Aucune modification appliquée. |
| Prix inconnu, mode strict demandé | VERIFIED, limite reproduite | Dans un processus du conteneur actif, appels IO de budget remplacés par mocks : estimation `None` avec `fail_closed_budget_enforcement=True` → retour `None`, zéro écriture de compteur, aucune exception. Cela signifie absence de réservation, pas refus d'inférence. |
| Plafond USD par opération | BLOCKED | L'estimateur retourne 0,004 USD pour un payload synthétique avec ou sans `max_cost_usd=0,0001`. Cette fonction ne fait pas respecter ce champ ; la signature de la réservation ne possède pas de plafond USD d'opération. Cela ne démontre pas à lui seul le comportement de toutes les autres API LiteLLM. Aucune garantie exploitable démontrée dans le chemin actuel. |
| Faux accord soumis au Gateway actif | VERIFIED pour l'échec de l'appel | Pro et Perso : `llm_router_submit` avec `paid_authorization="approved"` → HTTP 500, `ok:false`, `tool_error`, message générique `tool execution failed`. Ce résultat ne prouve pas à lui seul l'origine interne du refus. Perso : activité identique avant/après. Pour Pro, contrôle après échec du premier script non collecté ; aucune assertion d'activité inchangée. |
| Identités et huit clés | VERIFIED | API native serveur : cinq identités concernées, huit clés existantes ; les trois DIRECT PAID rattachées à `paid-openrouter-shared`, les DELEGATED toujours LOCAL/FREE sans équipe PAID. Aucun nouvel identifiant ou credential. |
| Budget et santé après tests | VERIFIED | Équipe 40 USD / 1mo, spend 0 USD ; LiteLLM readiness healthy, DB connected, liveliness répond ; santé Gateway relue. |
| Génération payante réelle et décompte | NOT_TESTED | Aucune génération OpenRouter ni preuve de coupure facturable par opération. |
| Courtier complet / approbation native payante | BLOCKED | Aucun courtier privilégié activé. Identité attestée d'approbation et réservation commune stricte ne sont pas déclarées livrées par ces tests. |

Le cas de prix inconnu est injecté dans le processus de qualification : il ne
prouve pas que les trois routes PAID actuelles ont des prix manquants. Les
fonctions installées sont exercées avec mocks dans le conteneur de production ;
ce n'est pas une génération payante bout en bout, ni une modification de la DB
ou du processus serveur. Script reproductible :
`mcp/llm-router/qualify_litellm_budget.py`, sans credential ni inférence.

Source installée : `litellm/proxy/spend_tracking/budget_reservation.py`,
248–377 (retour anticipé 300–304), 1190–1209, 1310–1370, 1507–1563 ;
`proxy/auth/user_api_key_auth.py`, 3077–3114. La [documentation native des budgets](https://docs.litellm.ai/docs/proxy/users)
décrit la réservation ; elle ne remplace pas la qualification du plafond exact
par opération lié à l'accord utilisateur dans cette installation.

Deux erreurs de diagnostic conservées : chemin supposé `/app/config.yaml`
inexistant (chemin déclaré retrouvé dans la stack : `/etc/litellm/config.yaml`) ;
assertion initiale du test Gateway attendant un détail d'erreur que l'API masque.
Le test Pro n'a pas été rejoué à l'identique ; le test Perso utilise le contrat
HTTP effectivement observé. Aucun contournement ni essai d'authentification
alternatif. Revue locale consultée mais son assimilation de `None` à un rejet
est écartée : le code et l'exécution montrent uniquement l'absence de réservation.

**Décision : DELEGATED payant reste désactivé**, conformément au repli demandé
si le plafond ne peut pas être correctement garanti. Les modèles payants restent
accessibles administrativement et par le chemin DIRECT existant. Aucun budget,
catalogue, modèle par défaut, clé ou confirmation existante modifié. Aucun des
31 tests antérieurs relancé ; pas de nouveau déploiement, commit/push ou P3-C.
P3-B reste **PARTIAL**, sans attente d'une nouvelle permission pour les tests.
La prochaine condition technique est une garantie serveur démontrable de coût
par opération et son intégration à une approbation native attestée ; augmenter
un budget ou autoriser globalement les outils ne résout pas cette limite.


## Correction du courtier DELEGATED — politique fail-closed

Nouvelle consigne : implémenter le contrôle minimal dans le courtier, tests
**uniquement sur fournisseur simulé**, aucun appel OpenRouter facturable.
Cette section décrit le dernier état et remplace l'attente d'implémentation
mentionnée plus haut. Résultat global **PARTIAL**, activation **BLOCKED**.

### Changements appliqués

Ajout de `mcp/llm-router/paid_broker.py`, noyau de politique séparé des primitives
historiques `authorization.py` ; contrat détaillé dans `PAID-BROKER.md`.
`router.py` conserve son refus `paid_broker_not_connected`. Aucun nouveau point
d'entrée MCP ni adaptateur fournisseur réel ; aucune activation ou déploiement.
Les interfaces de confiance sont refusées par défaut si elles ne sont pas
fournies : attestation cliente, reçu natif ponctuel, tarif/borne fournisseur,
coordination transactionnelle de l'équipe partagée et facture finale attestée.
Un nom de contrat, un booléen ou un solde fourni par le modèle ne constituent
pas ces preuves. Les fixtures du test n'ont aucune valeur d'attestation réelle.

- Tarif USD exact versionné, applicable et épinglé à un modèle/fournisseur et à
  l'empreinte du payload. Validité vérifiée avant réservation et juste avant
  lancement. Tarif inconnu, changé, expiré, non attesté ou coût non borné : refus.
- Coût maximal en entiers nano-USD : borne des tokens facturables d'entrée,
  tokens de sortie limités, tarif sortie couvrant le raisonnement et frais fixes.
  Toute autre source de facturation doit être couverte par le contrat réel ou
  refusée. Texte seul ; `max_output_tokens` explicite 1–4096, `n=1`, aucun outil,
  recherche, image/audio, multiplicateur ou paramètre facturable arbitraire.
- Accord `allow-once` attesté, lié à identité/session, tâche, modèle, payload,
  tarif, plafond et expiration. Reçu unique et offre immuable ; refus d'un accord
  permanent, d'un simple texte, d'une autre identité/session/tâche ou d'un rejeu.
- Registre propre au composant, privé, transaction `BEGIN IMMEDIATE`, commit
  `synchronous=FULL` avant lancement. Consommation de l'accord et réservation
  intégrale de la borne dans le même commit. Somme dépenses confirmées + toutes
  réservations + nouvelle borne <= enveloppe autorisée, sinon aucun appel.
  Registre verrouillé/inaccessible ou échec de commit : refus sans génération.
- Une opération ne peut être lancée qu'une fois, y compris entre instances et
  après crash. Aucun fallback ni retry (`allow_fallback=False`, `num_retries=0`).
- Timeout, erreur, réponse sans facture définitive ou mort du processus : borne
  intégralement conservée. Expiration et révocation ne libèrent pas une dette
  déjà engagée ; aucune libération automatique sur TTL ou changement de mois.
- Facture finale vérifiée : conversion atomique de la réserve en dépense,
  différence libérée et répétition idempotente. Facture tardive acceptée après
  expiration ; une facture provisoire ou un coût supposé nul ne libère rien.
  Dépassement du contrat fournisseur ou facture finale contradictoire : dette
  connue conservée, compte gelé. Ce gel ne peut pas annuler un coût externe.

### Garanties testées et limites

**VERIFIED sur simulateur uniquement** : **21 tests PASS** en 2,367 s, recette nouvelle
`test_paid_broker.py`, sans client HTTP, credential réel ni accès au serveur de
production. SQLite temporaire propre à chaque test, supprimée à la fin.
Cas couverts : tarif absent/inapplicable, borne non garantie, paramètres
facturables supplémentaires, accord absent/falsifié, mauvaise identité/session,
offre modifiée, expiration, révocation, plafond d'opération, refus budgétaire,
coordination absente, registre verrouillé, échec du commit durable,
réservations visibles par une connexion indépendante avant appel,
huit appels concurrents pour le même accord (un seul lancement), huit opérations
concurrentes avec une seule borne disponible (aucun dépassement), timeout,
réouverture du registre, arrêt brutal réel du processus après commit,
facture provisoire/falsifiée/tardive/zéro, réconciliation répétée,
révocation pendant l'appel, rupture du tarif ou de la facture définitive.
Commande et résultat final conservés sous
`artifacts/llm-router-p3b/broker-fail-closed/tests-final.txt`.
Les 31 tests OpenClaw et autres tests historiques ne sont pas relancés.

**VERIFIED préservation** : empreintes avant/après identiques des sept fichiers
suivis : routeur, primitives historiques, plugin routeur OpenClaw, protections
send-approval, rapport P3-A, configuration OpenClaw et configuration Codex.
Aucune modification des clés, identités, modèles, catalogues, budget LiteLLM,
DIRECT, RTK, Standup, proxies ou services de modèles. Aucun commit/push.

**BLOCKED production** : aucun adaptateur réel ne prouve actuellement le
plafond fournisseur, le reçu d'approbation native et la coordination persistante
avec **tous les consommateurs DIRECT** de `paid-openrouter-shared`. Le hook
`shared_coverage` doit attester une coordination sur la même transaction ; un
relevé de dépenses asynchrone ne satisfait pas le contrat. Le registre de
qualification représente l'enveloppe partagée simulée de 40 USD, sans créer un
deuxième budget de 40 USD en production. DIRECT et son fonctionnement restent
inchangés. Initialisation/rotation mensuelle du registre partagé réel non
intégrées ; aucun reset automatique pouvant effacer une dette incertaine.

**NOT_TESTED** : génération PAID réelle, intégration native OpenClaw du nouvel
accord, réservation commune réelle avec DIRECT et garantie fournisseur de coût
facturable. Un fournisseur mensonger ne peut pas être rendu sûr par une simple
estimation locale. L'activation est donc interdite, même si les tests du noyau
passent. **DELEGATED payant reste désactivé ; budget 40 USD/mois et huit clés
existantes conservés.** Pas de nouvelle demande d'autorisation : le blocage
restant est technique. Arrêt avant P3-C.


Revue complémentaire locale : **NOT_COMPLETED**. Le MCP `local_llm/delegate`
a retourné `timed out awaiting tools/call after 300s` ; aucune proposition de
revue disponible, aucun nouvel essai. Ce résultat n'est pas présenté comme une
validation. Relecture directe des transactions/états et tests ciblés exécutés ;
`git diff --check` PASS. Les contrôles de production restent NOT_TESTED dans
cette correction, conformément à la consigne de fournisseur simulé uniquement.


## Incident Perso signalé après P3-B — diagnostic du 21 octobre 2026

**PARTIAL : services vérifiés ; incident graphique non reproduit, cause non établie.**
Les autres travaux P3-B restent suspendus. Aucun correctif de configuration appliqué.

- **VERIFIED** : Gateway saine ; plugins chargés, dont BookStack Perso, sans erreur de chargement.
- **VERIFIED** : modèle par défaut Pro et Perso strictement identique à `before-0`
  (oMLX / Qwen 3.6 35B natif, même profil). La session Perso mémorisée par
  l’application existe toujours et utilise ce modèle ; son dossier existe dans
  le catalogue explicitement limité à Perso. Dossiers Pro/Perso distincts par API.
- **VERIFIED** : deux conversations techniques nouvelles, sans livraison externe,
  répondent `PERSO_OK` (2 227 ms) et `PRO_OK` (1 981 ms), provider `omlx`,
  modèle `mlx-community--Qwen3.6-35B-A3B-4bit`. Cela valide le chemin Gateway
  vers Qwen, sans constituer une preuve du chemin graphique signalé.
- **VERIFIED** : BookStack HTTPS HTTP 200 (page de connexion) ; recherche native
  `bookstack_search` sous identité Perso, `scope=global`, `corpus=pages`,
  requête technique sans document attendu : HTTP 200, `ok=true`, zéro résultat.
  Aucun document chargé ou modifié.
- **VERIFIED / diagnostic source** : le libellé exact correspond à
  `newSession.catalogUnavailable` dans le bundle installé. Les conditions
  comprennent un dossier non résolu ou une cible de terminal indisponible ;
  le libellé seul ne permet pas de conclure à une panne du fournisseur.
  Aucun journal serveur correspondant à ce libellé n’a été trouvé dans la
  fenêtre inspectée. Le correctif antérieur de portée agent des dossiers est
  présent ; cela ne démontre pas son bon comportement dans l’écran fautif.
- **BLOCKED** : reproduction de l’écran exact. Aucune surface native ni navigateur
  n’est disponible dans l’inventaire de l’outil d’interface. L’état persistant
  indique une ancienne conversation Perso, mais ne révèle pas le formulaire
  ou le brouillon réellement bloqué. Clarification demandée : ouverture d’une
  ancienne conversation ou création depuis un dossier.
- **NOT_TESTED** : nouveau tour dans l’ancienne conversation personnelle,
  fonctionnement du formulaire graphique et correction de celui-ci. Aucun
  historique réinitialisé, supprimé ou recréé ; aucun budget, clé, permission,
  défaut ou configuration modifié. Aucun appel OpenRouter.

Preuves privées : `artifacts/openclaw-perso-incident-20261021/`
(`diagnostic-summary.json`, `perso-qwen.json`, `main-qwen.json`).
Les réponses brutes des deux conversations techniques restent privées.
Prochaine étape minimale : identifier l’action exacte et la cible de l’écran
bloqué, puis reproduire le chemin de résolution du dossier/cible avant de
proposer un éventuel correctif ciblé et réversible. Ne pas attribuer l’incident
à P3-B sur la seule chronologie.


### Précision utilisateur : blocage dans les deux dossiers Perso

L’utilisateur confirme que le message apparaît dans les dossiers Appartement VARS
et Jardin (nom API : Projet Jardin 2026).

**VERIFIED — défaut de résolution reproduit hors interface :** extraction sans
modification du chargeur `Jm` du bundle installé, puis exécution avec les vrais
catalogues retournés par `sessions.groups.list` pour Pro et Perso. Pour une route
explicitement `agent=perso`, les deux dossiers sont `missing` si le store partagé
est sur Pro, et `resolved` si ce store est sur Perso (quatre assertions PASS).
Le chargeur appelle `groupsLoad()` sans transmettre l’agent de la route ; le
correctif antérieur du store utilise la sélection globale. C’est un défaut
reproductible de portée entre route et store, compatible avec le symptôme.
**PARTIAL :** la sélection globale réellement active dans l’écran fautif n’est
pas observable ; ce lien causal précis n’est donc pas encore confirmé en GUI.

**VERIFIED :** variantes brute, gzip et Brotli du bundle, ainsi que les trois
variantes servies par HTTP local, identiques après décompression. Hypothèse d’une
variante précompressée non mise à jour écartée.

Preuves : `artifacts/openclaw-perso-incident-20261021/group-route-repro.mjs`
et `group-route-repro.json`. Aucun nouveau tour LLM ni appel BookStack nécessaire
pour cette précision ; les validations fonctionnelles précédentes restent valides.

**Correction non appliquée :** aucune configuration modèle fautive démontrée.
Une correction durable doit rendre la résolution des dossiers explicitement liée
à l’agent de la route et maintenir cette portée dans les contrôles ultérieurs,
sans fusionner les catalogues ni rendre les dossiers visibles aux deux agents.
Cela implique une modification du correctif Control UI existant, au-delà du seul
changement de configuration demandé. Présenter cette option avant application.
Vérification utilisateur minimale : sélectionner explicitement Perso dans le
sélecteur global d’agent, puis rouvrir le formulaire depuis chacun des dossiers ;
ce contrôle n’exige ni envoi de message ni modification de données.


### Correction autorisée du formulaire de dossiers — 21 octobre 2026

Après accord explicite utilisateur (« oui »), correction **APPLIED / VERIFIED
techniquement**, validation de la fenêtre macOS **NOT_TESTED / attendue**.

**Cause reproduite :** la route du formulaire portait Perso, mais chargeait et
vérifiait les dossiers depuis la sélection globale, éventuellement Pro. Ce défaut
concerne le correctif antérieur d'isolation des dossiers dans l'interface ; aucun
lien causal avec les modèles, clés ou budgets P3-B n'est démontré.

**Correction minimale du chemin UI :** complément versionné
`openclaw/migrations/patch-app-control-ui-group-route.py`, intégré au script
`patch-app-control-ui-agent-scope.sh`. Le chargeur existant est réutilisé dans un
store à identité d'agent de route immuable. Chargement, contrôles avant création
et retries relisent le même store ; la sidebar globale reste séparée. Changer
l'agent du formulaire après résolution d'un dossier de l'autre agent bloque la
soumission. Seules les réponses `ready` sont mises en cache ; retry et changement
d'epoch Gateway forcent un rechargement.

**Déploiement VERIFIED :** deux bundles (core et new-session), dans les assets
embarqués de l'app macOS et dans ceux du runtime Gateway ; variantes gzip/Brotli
régénérées et vérifiées. Ancres strictes et idempotence, contrôle syntaxique des
deux modules et du script shell. Sauvegardes de chaque fichier avant écriture,
suffixe `.bak-group-route-v1`, conservant le correctif sidebar antérieur.

La Gateway conservait en mémoire les anciens octets du core déjà servi.
`gateway.restart.preflight` a confirmé zéro travail actif et aucun bloqueur ;
`openclaw gateway restart --safe --json` a été accepté. Après ce redémarrage natif,
Gateway saine et six variantes HTTP (deux modules × identité/gzip/br) strictement
identiques aux fichiers corrigés ; variantes compressées de l'app vérifiées aussi.
Aucune réinitialisation, suppression, recréation ou migration de session.

**Recettes ciblées VERIFIED :** dix scénarios sur le code installé avec fournisseur
Gateway simulé (deux dossiers Perso avec sélection Pro, contrôles pré-soumission,
isolation Pro, changement de sélection, invalidation/retry, indisponibilité sans
fallback, reprise, concurrence/réponse tardive, identité absente, refus du
changement d'identité à la soumission, changement d'epoch ; scénarios regroupés).
Le chargeur et le contrôle de route installés sont également exécutés avec les
RPC natifs réels `sessions.groups.list/defaults` : les deux dossiers sont résolus
par Perso malgré la sélection globale Pro ; refus de ces dossiers sous Pro.
Cette preuve du code UI avec Gateway réelle ne vaut pas preuve du rendu macOS.

Après redémarrage, la conversation technique Perso existante répond `PERSO_OK`
via `omlx` / `mlx-community--Qwen3.6-35B-A3B-4bit` en 2 002 ms. Recherche native
BookStack sous Perso : HTTP 200, `ok=true`, zéro résultat sur une chaîne technique.
Aucune lecture de document ni écriture BookStack. Treize fichiers surveillés
(configuration OpenClaw/Codex, fichiers de clés existants et sources de protections)
ont les mêmes empreintes avant et après. Aucun modèle, budget, clé, identité,
MCP historique, RTK ou Standup modifié. Aucun appel OpenRouter ; pas de reprise
des autres travaux P3-B ; aucun commit/push.

**Limite / prochaine étape :** recharger la fenêtre OpenClaw après conservation
des brouillons, puis vérifier les deux dossiers. Aucun outil d'interface native
n'est disponible dans cette session ; confirmation utilisateur demandée.
Un ancien module déjà importé ou mis en cache par la fenêtre ne constitue pas
une preuve d'échec du code corrigé. Ne pas annoncer l'incident GUI résolu avant
cette confirmation.

Retour arrière limité : restaurer les fichiers `.js`, `.js.gz`, `.js.br` des deux
bundles depuis leurs voisins `.bak-group-route-v1`, dans les assets app et
Gateway, puis redémarrage natif sûr si nécessaire et rechargement de la fenêtre.
Ce rollback a été préparé par sauvegardes ; restauration réelle **NOT_TESTED**.
Preuve partageable : `diagnostics/openclaw-perso-group-route-20261021/RESULTS.json`.
Preuves privées complémentaires : `artifacts/openclaw-perso-incident-20261021/`.


### Régression Pro introduite par le premier correctif — correction v2

L’utilisateur confirme que Perso n’affiche plus le message, mais que Pro est
maintenant affecté alors qu’il fonctionnait avant notre intervention.
**La régression Pro vient du premier correctif Codex ; elle ne doit pas être
attribuée rétroactivement à P3-B ou à LiteLLM.**

**Cause VERIFIED par test rouge sur les bundles v1 installés :** une route sans
paramètre `agent` désigne l’agent par défaut du formulaire, `main` (Pro). Le
premier correctif choisissait à tort `state.selectedId`, susceptible de valoir
`perso`. Le test échoue explicitement : attendu `main`, obtenu `perso`. Les dix
tests précédents utilisaient des routes explicitement identifiées et ne
couvraient pas ce cas ; leur succès n’avait donc pas démontré le parcours Pro.

**Correction v2 APPLIED :** seul le module `new-session` évolue, dans l’app et
le runtime Gateway. La résolution réutilise `Mo`, le helper natif du formulaire,
avec la même liste d’agents et le même défaut. Si la liste est encore froide,
le chargeur attend son hydratation avant de résoudre un dossier. Aucun fallback
vers la sélection globale. Identité absente sans défaut disponible : dossier
indisponible, pas de portée ouverte. Le store séparé et les refus croisés sont
conservés. Sauvegardes supplémentaires `.bak-group-default-v2` (version v1 avant
ce complément), sans écraser les sauvegardes initiales `.bak-group-route-v1`.
Script de réapplication et test durable mis à jour.

**Validation VERIFIED :** treize scénarios sur le code installé, dont les trois
nouveaux cas Pro implicite après sélection Perso, refus des dossiers Perso sous
Pro implicite et hydratation à froid. La recette du chargeur installé avec RPC
Gateway réels résout les deux dossiers Pro en route implicite malgré sélection
globale Perso, et les deux dossiers Perso explicites malgré sélection globale
Pro ; les refus croisés restent effectifs. Syntaxe/idempotence vérifiées.

Préflight natif : zéro travail actif. Redémarrage Gateway `--safe` accepté ;
Gateway saine, six variantes HTTP des bundles strictement conformes au disque,
variantes compressées app vérifiées. Pro répond `PRO_OK` avec Qwen natif en
2 488 ms dans la conversation technique existante. Treize fichiers surveillés
(configurations, clés, protections) inchangés depuis avant le premier correctif.
BookStack n’a pas été modifié ; son contrôle natif réussi précédent est conservé
sans nouvelle requête inutile. Aucun historique réinitialisé, aucun modèle ou
budget changé, aucun appel facturable, aucun commit/push.

**PARTIAL :** Perso confirmé dans l’app par l’utilisateur après v1 ; validation
visuelle de Pro après v2 attendue, après rechargement de la fenêtre. Ne pas
confondre recette du chargeur avec recette visuelle. Les autres travaux P3-B
restent suspendus jusqu’à clôture de l’incident.
Preuves : `diagnostics/openclaw-pro-group-default-v2-20261021/RESULTS.json`
et `artifacts/openclaw-perso-incident-20261021/` (`*-default-v2*`).


### Abandon du masquage des dossiers à la demande utilisateur

Le symptôme persiste dans Commercial après v2. Les tests isolés ne démontraient
pas le fonctionnement réel de la fenêtre ; ne pas considérer l’incident clos.
L’utilisateur demande de retirer le masquage plutôt que poursuivre les patches,
et précise de conserver les modifications du routeur LLM de ce matin.

**APPLIED / VERIFIED sur disque :** core UI d’origine restauré depuis la
sauvegarde du 20 octobre, module new-session restauré depuis sa préimage avant
nos compléments, dans app et runtime Gateway, avec variantes gzip/Brotli.
Handlers de lecture `sessions.groups.list/defaults` remis au code natif sans
filtrage par propriétaire ; handlers de mutation et leurs protections inchangés.
Treize fichiers restaurés/régénérés, empreintes finales vérifiées. Aucune base,
conversation, catégorie, identité, clé, modèle ou permission d’outil modifiée.
Les dossiers peuvent redevenir visibles dans les deux vues ; le masquage est
abandonné. Les scripts de masquage et compléments documentés plus haut sont
retirés du déploiement actif et ne doivent pas être réappliqués.

**Routeur LLM préservé VERIFIED :** configuration OpenClaw inchangée par empreinte,
entrée plugin llm-router présente et activée, aucun fichier llm-router dans le
manifeste de rollback ; treize fichiers protégés (configurations, clés, sources
de protections) inchangés. Aucun retour arrière P3-B ni reprise de son courtier.

**PARTIAL / BLOCKED vérification en ligne :** la Gateway est arrêtée avant le
préflight demandé pour recharger les assets. Health : ECONNREFUSED sur loopback.
Journal : arrêt propre et SIGTERM pendant arrêt, sans redémarrage. Ne pas
interpréter le rollback sur disque comme une validation du rendu. Prochaine
étape : rouvrir OpenClaw pour relancer sa Gateway puis vérifier les dossiers.
Aucun démarrage d’une Gateway parallèle, aucune suppression de session.
Preuves privées : `artifacts/openclaw-perso-incident-20261021/unmask-rollback/`
(manifeste, préimages du rollback et result.json). Aucun commit/push.


Après réouverture par l’utilisateur : **VERIFIED** Gateway saine, plugins chargés
sans erreur dont llm-router, BookStack Perso et send-approval. Les six variantes
HTTP des deux bundles restaurés correspondent au disque. Les catalogues natifs
list/defaults renvoient désormais les quatre dossiers pour Pro et Perso, conforme
à l’abandon du masquage. Entrée llm-router toujours activée ; treize empreintes
protégées inchangées. **PARTIAL** : le formulaire Commercial reste à confirmer
visuellement par l’utilisateur, sans nouvelle modification ni test LLM.
