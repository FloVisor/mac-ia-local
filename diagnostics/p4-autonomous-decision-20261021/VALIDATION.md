# P4 — décision de délégation en amont

Date : 21 octobre 2026. Aucun commit/push, aucun appel à un modèle LiteLLM payant.

## Modification appliquée

Seule la section « Délégation et économie de contexte » de
`/Users/fngux2/.codex/AGENTS.md` est modifiée. Elle impose une décision préalable
pour les tâches non triviales, une préférence spontanée pour les sous-tâches
adaptées au routeur et une justification concrète des exceptions. Les tâches
asynchrones permettent de poursuivre le travail indépendant. La décision est
obligatoire ; l'appel au MCP reste conditionnel. Les restrictions de
confidentialité, le local prioritaire et les responsabilités GPT sont conservés.

Aucune consigne copiée dans un dépôt. `codex/global-instructions.md` est inchangé.
Comparaison avant/après : préfixe et suffixe de la section identiques. Le fichier
global fait 16 220 octets ; aucun `~/.codex/AGENTS.override.md` présent.

## Deux essais neutres, sessions fraîches

Deux threads éphémères créés avec le binaire réellement embarqué dans Desktop :
`/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`,
version `0.163.0-alpha.10.2`. Aucun override de modèle, permission, configuration,
instructions de base ou développeur. Défaut natif GPT-6.1-Sol conservé.
Les réponses `thread/start` donnent comme unique `instructionSources` :
`/Users/fngux2/.codex/AGENTS.md`. La nouvelle section a également été réinjectée
dans la conversation Desktop principale après écriture.

| Essai | Observation | Résultat |
|---|---|---|
| Comparaison documentaire | Lecture de trois notes fictives, puis initiative d'appeler le catalogue de llm-router, avant toute synthèse finale | Choix autonome observé ; exécution BLOCKED_PERMISSION |
| Traduction d'une phrase | Réponse « The server is available. », sans commande ni appel MCP | PASS direct |

Thread documentaire : `01a15eb9-9ef2-7a81-b4b1-a0da0ca1eee7`.
Thread trivial : `01a15eba-69fa-7f11-bac2-2eb2f8f75596`.

Prompts exacts, sans mention du MCP ni directive sur la délégation :

> Compare les trois notes du dossier courant. Identifie les contradictions et les risques, distingue les exigences validées des propositions, puis propose les corrections prioritaires et les critères de recette manquants. Réponds en français, en 300 mots environ. Ne modifie aucun fichier.

> Traduis en anglais : « Le serveur est disponible. »

Le premier essai émet `mcpServer/elicitation/request`, serveur `llm-router`,
`codex_approval_kind=mcp_tool_call`, outil `catalogue`, paramètres `{}` :
`Allow the llm-router MCP server to run tool "catalogue"?`
Le client de test n'accorde aucune approbation et arrête cette branche. Aucun
nouvel essai avec des flags d'approbation, aucune préférence cachée modifiée.
Le second essai est indépendant et n'exige aucune approbation.

Un contrôle automatique trop strict attendait une traduction sans guillemets
alors que le résultat était entouré de guillemets typographiques : assertion
échouée, sans nouvelle génération. Le texte et l'absence d'appels d'outils sont
directement vérifiables dans la trace conservée.

## CLI, Desktop et portée des preuves

Le CLI installé est `0.160.0` ; sa configuration effective filtrée est identique
à celle du moteur Desktop pour le modèle, le fournisseur, les permissions et
les déclarations MCP contrôlées. Un nouveau processus est utilisé pour chaque
essai Desktop. Cela vérifie le moteur et le chargement global, pas une nouvelle
fenêtre manipulée dans l'interface graphique. Aucune capture UI n'est annoncée.
Le thread principal existant n'est ni redémarré ni réinitialisé.

Sept empreintes protégées restent identiques après les essais : configuration
Codex (donc déclarations MCP/permissions), configuration routeur, catalogue des
modèles, miroir historique des instructions, source Standup contrôlée, script
RTK contrôlé et source du routeur. Aucun budget, modèle, MCP ou droit modifié.
Les fixtures temporaires sont supprimées ; leur contenu synthétique et les
traces nécessaires à l'audit restent dans le répertoire privé de preuves.

## Limite et action restante

Politique globale appliquée et chargée ; discrimination documentaire/trivial
observée. La délégation exécutée de bout en bout dans le moteur Desktop n'est
pas validée : autorisation ponctuelle du catalogue requise. Pour la compléter,
faire approuver les appels nécessaires à un seul essai documentaire, sans
autorisation permanente ni changement de configuration. Aucun contournement.

Preuves locales privées : `artifacts/p4-autonomous-decision-20261021/` :
`AGENTS.before.md`, `global.diff`, `fixtures.json`, `validate.py`, `summary.json`,
`documentary.json`, `trivial.json`, `cli-config.json`,
`preservation.before.json`, `preservation.after.json`.

## P4 — audit et exception des lectures MCP

Correction ciblée du 21 octobre 2026. **PARTIAL : status/result autorisés dans la
configuration effective ; essai autonome arrêté sur catalogue ; aucune preuve
d'exécution/récupération de délégation dans cet essai.**

### Origine de la confirmation

La requête vient du moteur Codex Desktop avant l'exécution du MCP :
`mcpServer/elicitation/request`, `codex_approval_kind=mcp_tool_call`.
La configuration initiale ne contient aucun override par outil ni serveur.
`router.py:tools_list` ne déclare aucune annotation MCP, notamment aucun
`readOnlyHint`. `serve` n'émet pas de demande d'approbation : la confirmation
observée relève donc de la politique cliente Codex appliquée à l'outil non
annoté, pas d'une autorisation DELEGATED du routeur. La trace ne démontre pas
qu'une annotation seule supprimerait cette confirmation ; elle n'a pas été
modifiée pour le prétendre.

La documentation officielle décrit le réglage persistant par outil :
https://learn.chatgpt.com/docs/config-file/config-reference
et https://learn.chatgpt.com/docs/extend/mcp?surface=app .
Aucun réglage global de confiance ou de politique shell n'est nécessaire.

### Audit et droits réellement appliqués

| Outil | Effets du traitement | Permission appliquée |
|---|---|---|
| status | SELECT de tâche filtré par identité ; lecture des métadonnées | approval_mode = approve |
| result | Même SELECT ; pagination validée ; aucun effacement ni acquittement | approval_mode = approve |
| catalogue | GET /models authentifié ; écrit le cache, ou un circuit breaker sur 401/403 ; refresh force la consultation | Aucune exception : confirmation conservée |
| submit / delegate | Enregistrement, purge de rétention, événements, lancement d'un worker et génération possible | Aucune exception |
| cancel | Modification de l'état et événements ; arrêt éventuellement trop tardif | Aucune exception |
| activity | Non concerné par la demande d'exception | Inchangé |

Les méthodes status/result elles-mêmes n'ont aucun effet d'écriture ni requête
fournisseur. Le démarrage commun du serveur initialise son stockage et ses
permissions ; cela ne constitue pas un effet de ces deux lectures. Le code
catalogue ne peut être déclaré strictement sans effets secondaires. Aucune
modification de ce code ou du catalogue n'a été effectuée.

Seuls les deux blocs suivants sont ajoutés à `~/.codex/config.toml` :

```toml
[mcp_servers.llm-router.tools.status]
approval_mode = "approve"

[mcp_servers.llm-router.tools.result]
approval_mode = "approve"
```

L'approbation MCP ne remplace aucun contrôle serveur. La sélection Cloud exige
conjointement l'autorisation serveur, allow_cloud de la tâche et confidentialité
cloud-approved ; les données restent locales par défaut. Ces drapeaux de tâche
sont des déclarations de l'orchestrateur, pas une attestation indépendante de
consentement humain : c'est une raison supplémentaire de ne pas auto-autoriser
submit dans son ensemble. Son schéma ne permet pas au réglage Codex par outil
de séparer les arguments locaux, Cloud gratuits et Cloud sensibles. L'identité
vient de la configuration serveur et filtre les lectures. Les candidats payants
échouent avant inférence avec paid_broker_not_connected et approval_required ;
aucun droit DIRECT ou DELEGATED payant n'a été ajouté. Les mécanismes de budget,
clé et identité restent inchangés. Aucun appel payant effectué.

### Un seul essai documentaire frais

Binaire embarqué Desktop identique à l'essai précédent ; nouveau processus et
thread `01a15ec2-4f93-7e53-8d45-7af59a61ac76`. Aucun override de permission,
modèle ou instruction dans thread/start. config/read confirme les deux overrides
persistants. Prompt neutre identique à la comparaison Atlas reproduite plus haut,
sans nom MCP ni directive de délégation. Fixtures synthétiques temporaires
supprimées après essai.

Résultat : choix spontané de catalogue, paramètres `{}`, puis confirmation
`Allow the llm-router MCP server to run tool "catalogue"?`. Arrêt au premier
obstacle sans l'approuver ni relancer. Exécution et récupération : NOT_RUN.
Absence de confirmation sur status/result : NON EXERCÉE dans cet essai, donc
pas de VERIFIED sur leur comportement à l'exécution. Chargement de leurs droits :
PASS. Il s'agit du moteur Desktop, pas d'une manipulation de sa fenêtre graphique.

Contrôles : lors de l’écriture, comparaison TOML démontrant exactement deux
overrides. Le contrôle final échoue sur l’égalité complète : changement concurrent
de model_reasoning_effort détecté, conservé sans intervention. Le diff final
contient ce champ et les deux overrides ; six empreintes protégées inchangées. Tests témoins : NOT_RUN, pytest absent du
Python système puis du venv existant ; deux échecs exacts « No module named
pytest », aucune installation ni troisième tentative.

### Limite et alternatives

Le réglage par nom d'outil est suffisamment ciblé pour status/result. Il ne
peut exprimer une condition sur refresh ou les arguments de submit. Pour lever
le blocage catalogue tout en respectant l'audit, il faut décider explicitement
si ses effets opérationnels de cache/circuit breaker sont acceptables pour une
exception dédiée à catalogue ; cela dépasse le critère strict « sans effets
secondaires » de cette demande. Autre option : une interface de consultation
strictement pure, à concevoir seulement dans un périmètre autorisant sa modification.
Aucune autorisation générale du MCP n'est recommandée ou appliquée.

### Preuves et rollback

Preuves privées : `artifacts/p4-read-approvals-20261021/` : configuration avant
(mode 600), protected.json, preservation.json, validate.py, summary.json,
documentary.json et stderr. Elles contiennent les résultats effectifs ; le
fichier global de configuration sauvegardé ne doit pas être publié.

Rollback ciblé, sans écraser d'autres modifications :
`python3 artifacts/p4-read-approvals-20261021/rollback.py`.
Le script supprime uniquement le bloc exact ajouté et refuse si celui-ci a changé.
Ouvrir une nouvelle session Desktop pour recharger les droits. Aucun rollback
exécuté. RTK, proxy, catalogue, sélecteur, OpenClaw, Standup, modèles et budgets
non modifiés. Aucun commit/push.

## Finalisation ciblée — catalogue autorisé et message capacity

Autorisation utilisateur reçue : exception permanente dédiée à catalogue, y
compris ses seuls effets techniques de découverte/cache/circuit breaker.
Ajout unique à ~/.codex/config.toml :

```toml
[mcp_servers.llm-router.tools.catalogue]
approval_mode = "approve"
```

status/result restent approve ; aucun défaut serveur/global changé. L'audit
précédent établit que catalogue appelle GET /models sans contenu de tâche et
n'effectue aucune inférence ni mutation métier. Les réponses sont filtrées par
les modèles autorisés. Le cache et les circuits techniques restent actifs.

submit/delegate : aucun override permanent ajouté. Le contrôle Codex par outil
ne distingue pas les arguments locaux des arguments Cloud. Le serveur bloque
l'inférence payante (paid_broker_not_connected) mais sa condition Cloud accepte
les déclarations allow_cloud/confidentiality de l'orchestrateur ; elle ne fournit
pas une attestation indépendante du consentement pour des données sensibles.
Une exception générale n'est donc pas justifiée. Les délégations locales
peuvent encore demander une approbation ponctuelle. Une séparation serveur de
l'outil local serait une évolution distincte, non appliquée dans cette mission.

### Vérification fraîche et unique essai

Thread moteur Desktop : 01a15ec8-8c4e-7251-8df9-3c33fd02e373.
config/read confirme catalogue/status/result = approve ; aucun override de
submit/delegate. Prompt documentaire Atlas neutre inchangé. Aucun override de
modèle ou fournisseur introduit. Le défaut chargé dans cet essai est désormais
local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit (modelProvider openai), pas le
GPT de la précédente validation. Ce changement existait au chargement ; aucun
modèle ni budget n'a été modifié par cette correction.

L'essai ne produit que le message utilisateur, sans réponse ni appel MCP.
Stderr : à 14:06:04 UTC / 16:06:04 Paris, connexion WebSocket à
ws://127.0.0.1:11434/api/codex/v1/responses refusée HTTP 426 Upgrade Required,
puis « falling back to HTTP ». Aucune erreur capacity observée dans cet essai.
Arrêt explicite du client de test sans relance (KeyboardInterrupt, code 130),
traces sauvegardées par finally et app-server de test terminé. Aucun submit,
delegate, génération déléguée ou résultat MCP ; aucune approbation ponctuelle
accordée. L'arrêt du client ne prouve pas l'arrêt immédiat d'une éventuelle
inférence déjà reçue par le serveur local.

Chargement des permissions : PASS. Sélection autonome, absence de confirmation
sur appels réels, exécution et récupération : NON VALIDÉES dans cet essai.
Aucune nouvelle session de test lancée. Validation du moteur Desktop, pas une
preuve graphique. Les résultats antérieurs de sélection autonome sont conservés.

### Origine du message historique

Trace source : ~/.codex/sessions/2026/10/21/
rollout-2026-10-21T15-38-49-01a15eaf-9a76-7351-b6c3-a7b90e3a509c.jsonl,
ligne 449, événement task_complete du tour
01a15ec0-c676-7bd2-96f0-9c5ffbf9440a, à 14:01:40.020 UTC / 16:01:40 Paris :

```json
{"message":"Selected model is at capacity. Please try a different model.","codex_error_info":"server_overloaded"}
```

Le turn_context indique gpt-6.1-sol, effort low. Il s'agit d'une erreur de
terminaison du tour principal Codex, enregistrée par le moteur, pas d'un résultat
d'outil llm-router. Aucune preuve disponible d'une origine LiteLLM ou fournisseur
local pour cet événement. Le texte n'existe ni dans router.py ni dans adapter.py.
La trace ne contient pas la réponse fournisseur brute permettant d'attribuer
avec certitude le composant distant qui a émis la saturation, ni sa cause.
Le 426 du nouvel essai est un événement différent et ne démontre pas l'origine
de la saturation historique. Aucun retry de reproduction effectué.

### Préservation et rollback

Preuves privées : artifacts/p4-final-permissions-20261021/ : config.before.toml
(mode 600), summary.json, documentary.json, documentary.stderr, capacity.json,
preservation.json, validate.py, rollback.py et rollback-block.txt.
Comparaison TOML à l'application : seul catalogue est ajouté aux deux exceptions
existantes. Le contrôle des empreintes historiques trouve la source Standup
différente de l'ancienne référence ; cette correction ne l'a ni écrite ni
restaurée. Les cinq autres références contrôlées sont identiques. Cette
comparaison historique ne permet pas de dater le changement Standup.
Aucun fichier P3-A, RTK, OpenClaw, modèle ou budget modifié par cette intervention.
Aucun appel payant ni commit/push.

Rollback de cette seule finalisation :
`python3 artifacts/p4-final-permissions-20261021/rollback.py`.
Il enlève uniquement le bloc catalogue exact, conserve status/result et refuse
si le bloc a changé. Nouvelle session nécessaire pour recharger la configuration.
Rollback préparé, non exécuté. Les essais témoins pytest précédemment impossibles
n'ont pas été relancés ; aucun environnement installé.
