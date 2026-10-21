# llm-router — phase MCP indépendante

## Politique active — 21 octobre 2026

### Réserve de sortie locale — correction de la revue audio

Par défaut, **omettre `max_output_tokens`** : le worker dimensionne la réserve
Qwen selon `task_type` (sinon `profile`). Réserve réponse : analyse/revue,
diagnostic, comparaison, synthèse, architecture et documentation 3072 ; code
4096 ; tests 2048. Une entrée d'au moins 12000 octets UTF-8 porte le minimum à
6144. Ce seuil est une heuristique de dimensionnement, pas un tokenizer ni une
garantie de qualité ; l'admission conserve sa borne UTF-8 et le contexte 131072.

Contrat rétrocompatible : un `max_output_tokens` fourni sans autre précision
reste un plafond de réponse **hard**, même si c'est Codex qui a généré ce chiffre.
Il ne prouve jamais une exigence humaine. `output_budget_mode=hard` exige ce
nombre. `output_budget_mode=auto` autorise explicitement à traiter ce nombre
comme un indice ajustable, soumis au plancher et au plafond automatique 8192.
Ne pas inventer un petit plafond pour économiser des tokens sur une revue.
Les routes Cloud conservent leur réserve existante (défaut 2048) et leurs contrôles.

Pour Qwen seulement : enveloppe envoyée = réserve de réponse + budget de pensée
inchangé + un token de frontière lorsque la pensée est active (mesure oMLX :
2049 pour Medium2048, 513 pour Low512). Medium/High/Max restent 2048/8192/16384.
Le schéma et `generation_limits` exposent mode, source, réserve demandée/effective,
pensée, frontière et enveloppe ; la sélection admet cette même enveloppe.

Une réponse `length` reste rejetée (`completion_truncated`), jamais promue en
réussite. La récupération existante vers une autre route gratuite autorisée est
conservée. À défaut, Qwen en mode automatique peut refaire la même tâche locale
avec une réserve doublée, au plus 8192, après nouvelle admission contexte.
Maximum **deux appels au total** : pas de continuation du texte partiel, troisième
appel ou changement de pensée. Modèle explicitement imposé, hard cap, échéance,
annulation, auth/quota, envoi incertain ou contexte insuffisant interdisent cette
reprise de taille. Le refus de hard cap explicite le contrat et la prochaine action.
Les arguments initiaux et l'idempotence ne sont pas réécrits dans le stockage.

Les workers nouvellement lancés chargent ce code. Un client stdio déjà ouvert
peut conserver l'ancien schéma : les anciens arguments restent compatibles et
l'omission du plafond fonctionne avec le nouveau worker ; le champ additionnel
requiert le rechargement naturel du client. Aucun redémarrage Desktop forcé.


Le code déployé pour Codex applique désormais une sélection local-first par
capacités, contexte et type/complexité de tâche. Voir le rapport
[politique et recette](../../codex/29-delegation-policy.md). Les états historiques
de raccordement et de qualification ci-dessous ne décrivent pas ce déploiement.

- Contrat étendu : `task_type` (profil ou diagnosis/comparison/synthesis/architecture),
  `complexity` (trivial/standard/advanced/strategic), `contains_secrets` booléen.
  Les anciens appels restent compatibles, `standard` et local par défaut.
- Trivial/strategic : `orchestrator_required`, sans génération. Advanced :
  `qualified_advanced_tasks` doit contenir le type demandé pour chaque modèle
  et chaque membre d'un pool. Aucune aptitude avancée n'est inventée : les routes
  de production actuelles n'ont pas cette qualification, donc retour GPT.
- Secrets : indicateur par tâche + détection conservatrice de formes courantes,
  contrôle répété avant dispatch ; aucune route Cloud, même explicitement demandée.
  Un secret opaque ne peut pas être détecté exhaustivement : l'appelant doit
  le signaler ou conserver `confidentiality=local`. Expurger les secrets inutiles.
- Deux appels maximum : récupération sur réponse invalide ou 502/503/504,
  vers une autre route compatible non payante. À défaut, un seul retry local
  sur ces erreurs HTTP transitoires, ou une reprise Qwen automatique de taille
  après troncature selon le contrat ci-dessus. Un modèle explicitement imposé ne change
  pas de route et n'est pas relancé. Pas de reprise sur auth/quota/envoi incertain.
  Échec terminal : `return_to_gpt=true`. Les tentatives et usages restent tracés
  sans leur contenu ; le coût inconnu reste null. Pas de troisième appel.
- Pour Groq seulement, `quality.kind=json` envoie `response_format=json_object`,
  documenté pour ses modèles ; validation locale toujours stricte, sans retrait
  de balises. Aucune garantie JSON Schema ajoutée.
- Aucune proposition payante automatique. Une route payante explicite reste
  refusée par `paid_broker_not_connected`, même avec accord textuel courant.
  DIRECT, clés et plafond partagé 40 USD/mois inchangés.
- Les processus stdio déjà ouverts peuvent garder l'ancien schéma ; les nouveaux
  chargements et workers utilisent les sources déployées. Aucun client concurrent
  n'est interrompu. Utiliser l'ancien contrat dans une session déjà chargée.



Nouveau serveur MCP stdio, Python 3 standard, identifiant **llm-router 0.1.0**.
Aucune installation dans Codex/OpenClaw, aucun remplacement de `local-llm-mcp`.
Ce répertoire est autonome ; aucune dépendance ni import du MCP historique.

**État : accès LOCAL/FREE et chemin LiteLLM réel VERIFIED ; conformité des deux
réponses gratuites PARTIAL.** Une clé dédiée est installée hors dépôt, aucun
client raccordé. Voir [VALIDATION.md](VALIDATION.md). Aucun appel payant, aucune
modification des budgets, modèles ou pools.

## Exécution isolée

```sh
python3 -m unittest discover -s mcp/llm-router -q
python3 mcp/llm-router/smoke_local.py
python3 mcp/llm-router/router.py --config /chemin/prive/config.json
```

Copier `config.example.json` dans un emplacement privé et adapter `state_dir`.
Ne jamais y placer de clé : `key_file` désigne un fichier privé appartenant à
l'utilisateur (0600, liens symboliques refusés). S'il est configuré, il prévaut
sur `key_env` et ne retombe jamais sur une autre identité. Sans `key_file`,
`key_env` désigne une variable d'environnement, comme auparavant.
La recette réelle utilise `~/.config/llm-router/config.json` et
`~/.config/llm-router/litellm-local-free.key`, dossier 0700/fichiers 0600.
Le processus doit recevoir une clé LiteLLM **LOCAL/FREE seulement**, identité
serveur dédiée, permissions explicites. Ne pas utiliser MASTER_KEY. La configuration
n'est pas l'identité déclarée par le modèle : elle appartient à l'opérateur.
Une identité et un répertoire distincts pour Codex, OpenClaw Pro et Perso.
Le marqueur d'identité interdit la réutilisation accidentelle d'un même stockage.
Le contrôle suppose des utilisateurs locaux et fichiers de configuration de confiance ;
il n'isole pas deux processus malveillants exécutés sous le même compte macOS.

Le smoke test réutilise en mémoire la source de clé oMLX de l'ancien MCP,
crée sa configuration et son état dans un dossier temporaire, puis les supprime.
Il ne change ni oMLX ni ses proxies. Ce mode `isolated_local_only=true` est une
recette explicite, **pas un fallback de production** ni une preuve LiteLLM.

## Contrats MCP

- `delegate(profile, task, ...)` : cinq profils conservés (`analysis`, `coding`,
  `review`, `testing`, `documentation`), texte de réponse JSON contenant résultat
  et métadonnées. Compatibilité fonctionnelle ; le préfixe texte historique n'est
  pas reproduit à l'identique. Pour une sortie >16 000 caractères, `next_offset`
  permet de continuer avec `result`.
- `submit(profile, task, ...)` : écrit puis retourne `task_id` immédiatement.
- `status(task_id)` : état et métadonnées observées, jamais le prompt/résultat.
- `result(task_id, offset=0, limit=4000)` : récupération paginée, maximum 16 000
  caractères par lecture, sans nouvelle inférence.
- `cancel(task_id)` : une tâche encore en file devient `cancelled` atomiquement ;
  une tâche en cours devient `cancel_requested`. Aucun arrêt fournisseur inventé.
  Si la réponse arrive, elle est conservée en `completed` avec
  `cancellation=too_late_completion_received`.
- `catalogue(refresh=false)` : catalogue visible par la clé, enrichi par les
  métadonnées approuvées dans la configuration opérateur.
- `activity(after=0, limit=100)` : événements ordonnés, curseur, indicateur de
  rétention et instantané des tâches actives/incertaines ; limite maximale 200.

Paramètres additionnels de `submit/delegate` : `model`, `allow_cloud`,
`confidentiality` (`local` par défaut ou `cloud-approved`), `reasoning`,
`required_capabilities`, `context_tokens`, `max_output_tokens`, `deadline`
(timestamp Unix), `parent_session`, `idempotency_key`, `quality`,
`paid_authorization` (référence réservée, **ne débloque aucun paiement**).
L'identité et le mode DIRECT ne peuvent pas être fournis dans les arguments MCP.

Exemple non facturant avec configuration locale isolée :

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"submit","arguments":{"profile":"testing","task":"Reply exactly OK.","reasoning":"off","parent_session":"session-reference","quality":{"kind":"exact","expected":"OK"}}}}
```

`quality` : `json` vérifie un objet et ses propriétés `required`, `python` vérifie
la syntaxe AST sans exécuter le code, `exact` compare à `expected` fourni par
l'orchestrateur. Pas de score de confiance LLM. Pas de tests de code généré ni de
calcul à partir d'une expression arbitraire. Une comparaison à une valeur connue
peut détecter un calcul faux. Le JSON Schema complet reste à implémenter.
Les exigences tools/vision sont refusées explicitement faute de transport
structuré de ces entrées. Les cinq profils délèguent du texte.

## Worker, durées et récupération

`submit` lance un worker détaché (`start_new_session`), un seul détenteur du
verrou `flock` par stockage. Les autres workers sortent sans exécuter de tâche.
Le worker se termine après 60 s sans travail ; un prochain `submit` le relance.
Un worker peut aussi être lancé explicitement avec `--worker`, ou `--worker --once`.
Après interruption, `running/cancel_requested` deviennent `unknown` au prochain
démarrage du worker, sans relance automatique. Avant ce démarrage, `status`
peut encore montrer le dernier état connu : vérifier `updated/last_activity_at`.
Le worker ne survit pas à un arrêt du Mac ; les tâches en file sont conservées.
Aucun LaunchAgent n'est installé pendant cette phase.

L'idempotence implicite dépend du contenu complet, de l'identité et de la
politique. Une clé explicite réutilisée avec d'autres données/politique est
refusée. Une tâche déjà exécutée n'est pas relancée durant sa rétention.
Après purge, la déduplication historique n'est plus garantie. La politique
changée entre soumission et exécution provoque un refus avant inférence.

Le chemin génération utilise SSE : `connect_timeout` (défaut 20 s),
`inactivity_timeout` (défaut `null`, pas de limite), aucun plafond artificiel de
durée totale. Les événements d'activité ne contiennent pas les deltas.
Une interruption réseau après envoi produit `unknown`, jamais un retry caché.
L'échéance utilisateur est vérifiée avant l'appel ; si elle expire pendant
l'appel, le résultat est conservé avec `deadline_exceeded=true`. **Pas encore
d'interruption active à l'échéance.** Le délai MCP du client reste indépendant :
utiliser `submit/status/result` pour les tâches longues. Les timeouts upstream
LiteLLM déjà configurés restent inchangés (300 s non-stream / 3600 s stream dans
le rapport existant) ; SSE ne démontre pas la suppression de ces limites upstream.

## Catalogue et décision

GET `/v1/models` avec la clé dédiée, aucun catalogue administratif utilisé pour
accorder une permission. L'API LiteLLM conserve la décision finale d'accès.
Intersection avec `models` configuré par l'opérateur : backend `local/free/paid`,
`kind=chat/pool`, fenêtre d'admission `context`, capacités vérifiées/annoncées,
état `enabled`, membres des pools, fournisseur optionnel. Une entrée inconnue,
un contexte inconnu, des membres non documentés ou une capacité non vérifiée
ferment la route. Le fichier exemple qualifie uniquement Qwen local ; ce n'est
pas une copie de l'ensemble du catalogue. Ajouter des métadonnées ne crée aucun
modèle dans LiteLLM. Les autres modèles/pools existants n'ont pas été recréés.

Priorité explicable local → gratuit → candidat payant ; pas d'appel en cascade.
Le cloud exige **les deux** : politique serveur `allow_cloud=true` et consentement
par tâche `allow_cloud=true, confidentiality=cloud-approved`.
Un pool exige tous ses membres visibles, compatibles et non bloqués. Un modèle
individuel est préféré à un pool au même niveau. Le modèle retourné par l'API est conservé dans `response_model`, distinct des
modèles demandé/sélectionné. Lorsque ce champ est un alias connu, `actual_model`
reste `null` et `provider_model_confirmation=alias_only_unconfirmed`. Les
`request_id`, `x-litellm-call-id` et `x-litellm-model-id` permettent une corrélation
opérateur avec les journaux natifs, sans donner une clé administrative au worker.
Les journaux LiteLLM sont recherchés par l'identifiant de complétion `request_id`,
pas par le `x-litellm-call-id`. Le fournisseur interne des pools n'est pas garanti
par le seul champ `model` upstream.
Muse-Glimmer est toujours refusé ; les embeddings ne passent pas par cette API.

Le contexte utilise une borne conservatrice UTF-8 de l'entrée et des instructions,
une marge de 256 et la sortie réservée (2048 par défaut), et tient compte d'un
`context_tokens` supérieur fourni par l'appelant. Ce n'est pas un comptage exact
via tokenizer ni une qualification de fenêtre maximale. Pas de troncature d'entrée.

Cache configurable, TTL **0 par défaut** : nouvelle découverte avant chaque
décision. Avec TTL positif, seules les routes LiteLLM sont utilisées ; ses
permissions restent applicables à l'inférence. Aucun catalogue périmé en secours.
**Secours direct oMLX de production non activé** : la disponibilité d'un ancien
instantané ne prouve pas l'absence de révocation. Une autorisation locale fraîche
et vérifiable reste à définir ; le mode de recette explicite reste disponible.

## Quotas, erreurs et raisonnement

Au plus deux appels par tâche selon la politique active ci-dessus. Les essais internes
FreeLLMAPI ne sont pas supposés connus (`upstream_attempts=null`).
Les 401/403 suspendent l'identité persistante ; 404 et 5xx bloquent la route.
429 conserve `Retry-After` numérique/date. Sans expiration connue, pas de délai
inventé. Comme sa portée fournisseur peut être inconnue, 429 suspend aussi
l'identité conservativement ; le pool ne sert pas de contournement.
Les événements `cooldown` conservent cause, portée, début, expiration éventuelle,
dernier échec et dernière réussite disponible. Le corps des erreurs HTTP n'est
jamais journalisé. Aucun changement dans LiteLLM/FreeLLMAPI.

Après diagnostic uniquement, l'opérateur peut rouvrir explicitement une portée :

```sh
python3 mcp/llm-router/router.py --config /chemin/prive/config.json --reset-scope credential:isolated-test
```

Ce contrôle n'est pas un outil exposé au modèle. La réouverture est tracée dans
les mêmes événements. Un 401/403 n'est pas contourné par une autre authentification.

Mapping oMLX : off/minimal désactivés, low 512, medium 2048, high 8192,
max 16384, ultra → high/8192. `thinking_budget` est envoyé au niveau supérieur,
`enable_thinking` dans `chat_template_kwargs`. Valeur envoyée ≠ valeur appliquée :
`confirmed=null` tant que non observable. Sur les autres routes, pas de budget
numérique inventé ; adaptation `unsupported_not_sent`.
Pour cet alias Qwen uniquement, `max_output_tokens` réserve la réponse : le
`max_tokens` transmis est cette réserve plus le budget de pensée demandé
(1200 + 2048 = 3248 en Medium). oMLX compte les deux dans sa génération totale.
Cette réserve totale est aussi vérifiée à l'admission dans les 131072 tokens de
contexte, sans tronquer l'entrée ni changer la configuration des modèles.
`reasoning_effort` n'est pas envoyé sur cette route : les paramètres explicites
ci-dessus portent l'adaptation. `generation_limits` et, si fourni par upstream,
`usage.completion_tokens_details.reasoning_tokens` rendent ces valeurs observables.
`finish_reason!=stop`, réponse vide ou structure invalide sont des échecs.
Les erreurs distinguent `completion_truncated` (`length`), `empty_completion`,
`unexpected_finish_reason` et `objective_quality_failed` (contenu non conforme).
Les contrôles objectifs échoués conservent provenance/usage et, désormais,
le contenu rejeté dans le résultat privé récupérable ; aucun contenu n'est ajouté
aux événements. L'état reste `failed`, sans nouvel appel ni assouplissement du contrôle.

## Confidentialité, supervision et rétention

Un **seul stockage applicatif** `tasks.sqlite` contient tâches, résultats,
événements, cache et circuit breakers. Répertoire 0700, fichier 0600 ; umask 077
pour le serveur et les workers. Les prompts et résultats nécessaires à la reprise
sont uniquement dans les tâches privées, jamais dans le journal d'activité.
Pas de serveur réseau ni d'export vers Agent Standup.

Événement : `seq/task_id/identity/at/state/meta`. Métadonnées : session parente
si fournie, profil, modèles demandé/sélectionné/effectif, backend, état, durée,
activité, usage, coût observé ou `null`, erreurs codifiées, cooldown, référence
et état de l'autorisation payante. Pas de prompt, résultat ou corps d'erreur.
Les identifiants/session doivent rester des références opaques, sans secrets.
Le coût local peut rester `null` si non exposé : ce n'est pas une dépense inventée.

Historique événements borné (1000), tâches terminales bornées (100, 24 h), purge
lors des nouvelles soumissions. Les tâches `unknown` ne sont pas supprimées
silencieusement ; plafond de 100 tâches non purgées en attente/incertaines avant
refus. Les limites sont configurables. La rétention est logique ; la taille
physique SQLite peut conserver son maximum historique. Pas de chiffrement
applicatif ; protection disque/macOS à la charge de l'environnement.

## Payant et phase 3

Voir [PHASE3.md](PHASE3.md). Aucun outil MCP ne sait émettre une autorisation.
`authorization.py` fournit des primitives testées d'accord ponctuel, consommation
atomique, révocation et validation du contrat DIRECT ; ces primitives **ne sont
pas un courtier déployé ni un système d'authentification**. Les grants futurs
utiliseront une table de la même base applicative, pas un second suivi des tâches.
Le processus ordinaire n'a aucune clé payante ; son chemin payant est fermé.
Une référence de grant ou le mot « DIRECT » dans un prompt ne change rien.

## Retour arrière et point d'arrêt

Aucun client n'a été raccordé : le rollback consiste à arrêter uniquement le
processus worker de cette recette (PID établi au lancement), puis conserver ou
supprimer son dossier temporaire après arrêt. Aucun restart de service existant,
aucun changement `~/.codex/config.toml`, OpenClaw, oMLX ou ancien MCP nécessaire.
La prochaine phase exige une décision utilisateur ; la qualification partielle
présente ne vaut ni validation cloud réelle ni autorisation de raccordement.
