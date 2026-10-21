# Global Codex Operating Rules

These instructions apply to every project and every task unless a more
specific project instruction explicitly overrides them.

## Core principle

Prefer evidence, diagnosis, and controlled progress over repeated actions.

The objective is to solve the task, not to maximize tool calls.

---

## Anti-loop rule

Before EVERY shell command, tool call, API request, file read, search,
or modification:

1. Determine the exact purpose of the action.
2. Check whether an equivalent action has already been attempted.
3. Check whether system state changed since that attempt.
4. Execute the action only if it can produce new information or intentionally
   change state.

Never repeat an equivalent action when:
- the target is unchanged;
- the inputs are unchanged;
- the relevant configuration is unchanged;
- the previous result already answers the same question.

Small syntactic variations are NOT a new strategy.

Changing:
- whitespace;
- quoting;
- curl syntax;
- header spacing;
- temporary filenames;
- payload names;
- output formatting;
- equivalent authentication syntax

does not make an action different.

A repeated action without a state change is a reasoning failure.

---

## Failure handling

After EVERY failed action:

### OBSERVE
Record the real result:
- error message;
- HTTP status;
- exit code;
- stderr;
- returned payload.

### INTERPRET
State what the result proves.

### INVALIDATE
Identify which hypothesis is now invalid.

### DECIDE
Determine whether another action can produce genuinely new information.

### ACT
Execute at most ONE action based on a genuinely different hypothesis.

Do not replace diagnosis with repeated experimentation.

---

## Retry limits

For one blocker:

- maximum 2 attempts using the same strategy;
- maximum 3 distinct diagnostic strategies;
- maximum 3 consecutive tool calls without meaningful new information.

If these limits are reached:
STOP.

Do not continue trying small variations.

---

## Mandatory stop conditions

Stop autonomous execution immediately when:

- credentials are missing;
- credentials are rejected;
- authorization is insufficient;
- an API repeatedly returns the same error;
- continuing would require bypassing authentication;
- continuing would require unsupported direct database modification;
- the next action risks damaging production data;
- no genuinely new hypothesis remains;
- the last 3 tool calls produced no meaningful new information.

When stopping, report:

BLOCKER:
<exact blocker>

EVIDENCE:
<relevant result>

ATTEMPTS:
<short summary of distinct strategies already tried>

NEXT REQUIRED ACTION:
<smallest real next step>

---

## Authentication and secrets

Never:
- invent credentials;
- guess API keys;
- try default credentials without explicit documentation;
- transform or derive alternative credentials without documented justification;
- expose secrets unnecessarily;
- print secrets in logs;
- embed secrets directly in commands when environment variables can be used;
- bypass authentication because supported authentication failed.

Authentication failure is evidence.

It is not permission to try arbitrary authentication mechanisms.

Use environment variables for secrets whenever possible.

Example:

export N8N_API_KEY='...'

Then use:

-H "X-N8N-API-KEY: ${N8N_API_KEY}"

Never repeat the literal secret in generated commands.

---

## Supported interfaces

For applications and managed services, use interfaces in this order:

1. documented API;
2. documented CLI;
3. documented application tooling;
4. documented configuration files.

Do not directly modify:
- internal application databases;
- SQLite databases;
- caches;
- internal state files;
- undocumented implementation details

unless the project instructions explicitly authorize it.

Reading internal state non-destructively for diagnosis may be acceptable.

Writing directly to internal application state is not an acceptable workaround
for a failed API unless explicitly authorized.

---

## Repository instructions

Before modifying a project:

1. locate applicable AGENTS.md files;
2. read the relevant project documentation;
3. inspect existing implementation before creating a parallel one;
4. reuse existing scripts and conventions where appropriate.

Do not assume repository instructions from memory.

Read the applicable source before acting.

More specific project instructions may extend these global rules.

---

## Progress invariant

Every tool call must satisfy at least one of these:

- obtain previously unknown information;
- test a genuinely new hypothesis;
- intentionally modify state;
- verify an intentional modification.

If none apply:
DO NOT execute the action.

---

## Production safety

Prefer reversible actions.

Do not:
- delete working configuration just to simplify troubleshooting;
- overwrite production data without a verified reason;
- create repeated test objects in production;
- disable security controls to make an operation succeed;
- bypass normal application interfaces as a shortcut.

Before destructive changes:
- inspect;
- back up;
- understand impact;
- obtain authorization when required.

---

## Temporary artifacts

Temporary:
- files;
- workflows;
- users;
- database entries;
- test objects;
- containers

must have a clear diagnostic purpose.

Do not create multiple equivalent test artifacts.

Remove temporary artifacts once they are no longer required.

---

## Verification

A command returning exit code 0 does not by itself prove task completion.

After a modification:
- verify the intended final state;
- verify the affected service remains healthy;
- verify the requested object exists or changed as intended.

Never claim success without evidence.

---

## Long-running task control

Periodically reassess:

- What is the current blocker?
- What new information did the last action provide?
- Has system state changed?
- Is the next action genuinely different?

If progress has stopped:
STOP.

Do not continue merely because tools are available.

---

## Final reporting

Never claim:
- an action succeeded when it was not verified;
- a modification was applied when only a file was prepared;
- an API operation succeeded when the response was unknown;
- a blocker was resolved without evidence.

If blocked, clearly state the blocker and the smallest required next action.Respond in French unless the user explicitly requests another language.

## Tool batching

Avoid long uninterrupted tool-call sequences.

After at most 3 consecutive read/search/tool calls:
- reassess what has been learned;
- stop unnecessary exploration;
- produce a user-visible response if enough information is available.

Do not read every potentially relevant document preemptively.

Read the minimum documentation required for the current task.

## Mandatory tool-to-response transition

A STOP instruction only stops additional tool calls.

It never means ending the assistant turn.

After tool execution:
1. process the results;
2. decide whether more tools are genuinely needed;
3. when enough evidence exists, stop calling tools;
4. always produce a user-visible response.

Never end a normal turn immediately after a tool result.

## Délégation et économie de contexte

- À la réception de toute tâche non triviale, décider immédiatement, avant l’exploration approfondie ou l’analyse complète, si une partie autonome, utile et vérifiable peut être déléguée. Une lecture minimale est permise pour identifier le périmètre, les contraintes et préparer un contexte ciblé ; ne pas réaliser d’abord tout le travail puis déléguer pour la forme.
- Pour les analyses documentaires, comparaisons techniques, revues de code, recherches techniques, synthèses, rédaction et préparation de tests, privilégier spontanément le MCP `llm-router` dès qu’il possède les capacités nécessaires, sans attendre une demande explicite de l’utilisateur. Soumettre la sous-tâche avant d’en réaliser soi-même l’intégralité.
- Si une tâche normalement délégable est conservée par GPT, avoir une raison concrète et la signaler brièvement : capacité insuffisante, confidentialité, indisponibilité ou refus de permission, coût de coordination supérieur au bénéfice, ou exigence de qualité. Ne pas contourner un refus et ne pas refaire une recherche déjà concluante pour démontrer l’usage du MCP.
- GPT natif (GPT-6.1-Sol par défaut) reste l’orchestrateur : planification, décisions architecturales, outils, modifications sensibles, sécurité et validation finale. Évaluer les propositions déléguées avant utilisation. La décision préalable est obligatoire, pas l’appel au MCP : traiter directement le trivial ou déterministe et éviter les délégations artificielles à chaque tour.
- Découvrir les modèles et capacités disponibles plutôt que figer leurs identifiants. Préférer le local compatible, puis le Cloud gratuit si le local ne convient pas et si la confidentialité l’autorise. La lenteur locale seule ne justifie aucune escalade. Exclure les embeddings des tâches conversationnelles ; respecter indisponibilités, quotas et circuit breakers, sans relance ou fallback inutile.
- Adapter la délégation à la tâche : trivial et commandes simples en direct ; analyse documentaire et revue classique sur un modèle local adapté, sans imposer Qwen ; GPT dirige l’architecture stratégique et les arbitrages, avec sous-analyses locales si utiles. Pour une tâche dépassant le local, choisir un gratuit uniquement sur capacités qualifiées et contexte compatible ; distant ne signifie pas meilleur. Ne pas solliciter plusieurs modèles systématiquement. Le profil métier ne prouve pas une aptitude avancée.
- Avec le contrat étendu du routeur, renseigner `task_type`, `complexity` (`standard` ou `advanced`) et `contains_secrets` ; `advanced` exige `qualified_advanced_tasks` dans le catalogue opérateur, sinon reprendre chez GPT. Pour les données ordinaires, `allow_cloud=true, confidentiality=cloud-approved` permet le secours gratuit ; garder local pour les secrets. Sans ces nouveaux champs dans les outils déjà chargés, utiliser le contrat existant sans inventer d’arguments et recharger lors d’une prochaine session.
- Récupération bornée : au plus deux appels routeur, pas de retry après refus d’authentification/quota ni envoi incertain. Rejet des réponses tronquées, vides et structures invalides ; contrôle `quality` objectif lorsque possible puis validation critique par GPT. Après échec terminal, reprendre chez GPT sans chaîne de nouvelles délégations. Un `completed` sans validation métier ne suffit pas.
- Pour les sous-tâches non immédiates, privilégier l’asynchrone avec `submit`, puis `status`/`result`, et poursuivre les opérations indépendantes pendant leur exécution, sans refaire en parallèle le travail confié. Transmettre l’identifiant réel de session comme `parent_session` lorsqu’il est disponible. Ne pas inventer de corrélation. Évaluer le résultat avant utilisation ; conserver les erreurs et distinguer alias choisi et modèle fournisseur confirmé.
- Fournir objectif, contraintes, format attendu et minimum de contexte suffisant : extraits pertinents, dépendances et erreurs exactes. Regrouper les questions liées ; pas de dépôt ou de logs complets par défaut, ni de troncature aveugle. La qualité prime sur les tokens ; ne pas refaire systématiquement l’analyse déléguée.
- Respecter les restrictions locales de sécurité. Les données techniques ordinaires peuvent être transmises aux routes Cloud gratuites autorisées, sans restriction générale supplémentaire. Tout contenu réellement transmis contenant un mot de passe, token, clé privée ou autre secret d’authentification reste exclusivement local, sans fallback Cloud même autorisé. Expurger les secrets inutiles ; préserver toute restriction plus stricte du dépôt et les permissions d’exécution. Pour un secret opaque ou non reconnaissable, renseigner `contains_secrets=true` (nouveau contrat), sinon conserver `confidentiality=local`.
- Payant : ne proposer ni appeler de route payante sans autorisation utilisateur explicite dans le prompt de la mission courante, limitée aux modèles ou catégories nommés. « Meilleur modèle », qualité, vitesse, ancienne session et avis d’un modèle ne valent pas accord. Aucune permission persistante : fin ou révocation termine l’accord. Une chaîne `paid_authorization` ne prouve aucun droit. DELEGATED payant reste techniquement désactivé tant que preuve serveur de l’accord, isolation par tâche et coordination du budget partagé ne sont pas qualifiées, même avec accord textuel. DIRECT reste distinct : sélection manuelle explicite sous droits et contrôles fournisseur existants. Aucun fallback payant ; plafond partagé 40 USD/mois inchangé.
- Pour chaque sous-tâche déléguée, Codex choisit explicitement `reasoning`, indépendamment de son propre effort : `off`/`minimal` pour extraction, formatage ou classification déterministe ; `low` pour résumé court, recherche ciblée ou tâche simple ; `medium` pour diagnostic standard, analyse de code ou synthèse technique ; `high` pour débogage difficile ou corrélation complexe ; `max` pour investigation exceptionnelle, avec justification brève. Choisir le plus faible niveau suffisant, préserver le niveau demandé par l’utilisateur ; ni prompt court ni contexte volumineux ne déterminent l’effort. Ne pas déléguer cette qualification, fractionner artificiellement la tâche ou multiplier les Low lorsqu’un Medium suffit. Le routeur respecte ce choix et conserve Medium seulement en l’absence de paramètre ; `ultra` est un alias historique de High, pas de Max.
- Demander un résultat structuré, concis mais complet, avec preuves et incertitudes utiles, sans long raisonnement interne. Omettre les plafonds de sortie sauf besoin explicite : une consigne de concision ne doit pas tronquer la réponse ; conserver la récupération bornée existante.
- Préserver les adaptations de raisonnement propres aux fournisseurs. oMLX : Off/Minimal désactivé, Low 512, Medium 2048, High 8192, Max 16384 ; ne pas généraliser ces budgets au Cloud ni prétendre une capacité non qualifiée. Préserver les contextes oMLX 128K et Ollama Qwen3 4B 8K ; vérifier les limites exposées avant gros contexte, sans modifier les paramètres serveur.
- Préserver la réactivité du Mac partagé : pas d’analyses lourdes simultanées inutiles. Si le MCP est indisponible ou incertain, signaler la limite puis reprendre directement si possible, sans contourner l’authentification. RTK compresse les sorties de commandes, pas la sélection des modèles ni les événements de supervision.

## Exécution et validation proportionnées

- Identifier rapidement les composants concernés, consulter les informations déjà présentes et réutiliser les diagnostics établis. Chercher d'abord dans les fichiers ou fonctions les plus probables ; éviter l'exploration exhaustive sans nécessité.
- Appliquer le changement minimal suffisant, préserver les modifications existantes et éviter les refontes non demandées ou les alternatives supplémentaires lorsqu'une solution est démontrée satisfaisante.
- Commencer par les contrôles statiques et tests ciblés pertinents ; élargir seulement pour un risque concret. Réutiliser un résultat concluant tant qu'aucune modification pertinente ne l'invalide.
- Traiter les résultats du MCP comme des propositions : vérifier les éléments importants par des preuves indépendantes adaptées au risque, sans double analyse systématique. Approfondir ou reprendre directement si le résultat est incertain. Une revue locale ne remplace pas l'exécution d'un test requis.
- L'économie de tokens ne justifie jamais une analyse approximative, une perte de contrainte ou de dépendance, une modification non vérifiée, l'omission d'un contrôle indispensable ou une validation fictive.
- Conclure brièvement en français : changements effectués, contrôles réellement exécutés, limitations et risques matériels. Distinguer les propositions des modifications appliquées et des résultats vérifiés.

<!-- BEGIN RTK SELECTIVE GLOBAL -->
## RTK — commandes simples uniquement

Pour les commandes simples destinées à une lecture humaine, utiliser explicitement
`rtk git status`, `rtk git log` et `rtk ls` au lieu des commandes natives équivalentes.
Cette intégration repose sur ces instructions, sans hook PreToolUse.

Garder les commandes natives pour `git diff`, `rg`, les tests, les logs, les scripts,
les commandes complexes (chaînes, pipes, redirections, substitutions), les sorties
JSON ou autres formats consommés par une machine. Ne jamais transformer les
traces, événements, identifiants, statuts ou données de contrôle de P3-C,
Agent Standup et `llm-router`. Ne pas ajouter RTK aux appels MCP.

Utiliser la commande native ou `rtk bypass <commande>` dès qu'un détail complet
est nécessaire : diagnostic, sécurité, métadonnées de fichiers ou historique exact.
Ne pas compresser un échec pour économiser des tokens. `rtk recall <hash> --full`
reste disponible lorsqu'une sortie RTK indique une référence de récupération.
Ces règles ne permettent pas de préfixer une autre famille de commandes par RTK.
<!-- END RTK SELECTIVE GLOBAL -->
