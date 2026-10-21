# P3-A — intégration Codex de llm-router, 21 octobre 2026

**État courant après activation de l'option B : PARTIAL.** Adaptateur DIRECT
et synchroniseur installés ; quinze alias LiteLLM dans le catalogue accepté par
le binaire Desktop. Trajets Qwen (six efforts + outil) et Mistral gratuit vérifiés.
Ollama : contexte 8192 imposé et appliqué ; incident multi-tour corrigé. Un tour
Desktop avec outil et résultat est completed, deux requêtes, aucune relance.
Voir la dernière section pour la cause, les preuves et les limites.
Rollback réel et réactivation vérifiés. GPT et authentification préservés, sans
nouvelle inférence GPT ni PAID. Voir la dernière section pour les preuves actuelles.
Les sections antérieures conservent les résultats de leurs étapes respectives.

**Recette MCP initiale, conservée :** enregistrement, autorisation ciblée,
appel depuis Codex et récupération asynchrone VERIFIED. Qualité exacte échouée :
`OK.` reçu au lieu de `OK`, tâche conservée `failed/objective_quality_failed`.
Aucune nouvelle génération pour faire passer ce contrôle.

## Changements effectivement appliqués

- Nouveau MCP global `llm-router`, Python 3.14 et source du dépôt, configuration
  privée `~/.config/llm-router/codex.json`, identité `codex`, stockage distinct
  `~/.local/state/llm-router/codex`. Clé LOCAL/FREE existante lue par `key_file`.
- `local_llm` conservé intégralement. Le CLI `mcp add` avait supprimé le champ vide
  `node_repl.args` : champ rétabli. Comparaison TOML finale : seul ajout du nouveau MCP.
- Catalogue déclaré `~/.codex/ollama-launch-models.json` : entrée Muse-Glimmer
  retirée, visibilité de `gpt-6-sol` passée à `hide`, priorité Qwen passée de -2
  à 50 pour conserver GPT-6.1-Sol en tête. Modèle configuré `gpt-6.1-sol` inchangé.
- Copies sans secret dans `llm-router-mcp.toml` et `llm-router-models.json`.
- Aucun changement permanent de sécurité, backend, contexte, budget ou service.
  Aucun changement OpenClaw/Agent Standup, aucun commit/push.

Diff sémantique de `config.toml` : uniquement la section reproduite dans
[llm-router-mcp.toml](llm-router-mcp.toml). Les autres sections parsées sont identiques
à la sauvegarde antérieure à P3-A, y compris `local_llm`, providers et environnement.

## Origine et levée ponctuelle du refus — VERIFIED

Codex CLI/app-server **0.160.0**. La chaîne exacte
`MCP tool call requires approval, but approval policy is never` est présente
 dans le binaire Codex installé, pas dans le serveur Python du routeur.
L'appel initial a échoué côté client, avant toute tâche. Le `tools/list` du
routeur n'annonce aucune annotation (`readOnlyHint` absent) et sa déclaration
n'est assortie d'aucune politique d'approbation cliente explicite. Le chemin
conservateur par défaut de Codex demande alors une approbation ; `never` refuse
cette demande. Ce n'est ni une authentification LiteLLM rejetée, ni le mécanisme
`approval_required` du routeur réservé aux propositions payantes.

Le parsing strict et `config/read` du binaire installé reconnaissent :

```toml
# Overrides de processus uniquement, jamais écrits dans config.toml
approval_policy = "never"
[mcp_servers.llm-router]
enabled_tools = ["submit"]
required = true
[mcp_servers.llm-router.tools.submit]
approval_mode = "approve"
```

Surcharge fournie par `-c` au seul app-server de recette. `required=true` et
`mcp_optional_startup_grace_ms=0` assurent la découverte avant la génération.
Aucun mode bypass, auto-review global ou changement d'approbation des autres
outils. Le processus est terminé : la surcharge n'est plus active. Elle autorise
l'outil pendant cette session, pas un jeton consommable à usage unique ; une seule
soumission a effectivement eu lieu. Les contrôles LOCAL/FREE du routeur restent actifs.

Premier essai isolé : zéro appel, le modèle n'a pas découvert l'outil différé.
Second essai : catalogue contrôlé (`connected`, uniquement `submit`), découverte
permise, un seul appel effectué. Les autres outils MCP conservent leur politique.
Leur récupération a été faite par un client stdio de recette distinct, via
l'interface MCP documentée, sans toucher aux règles Codex ni au stockage interne.

Sources : [configuration OpenAI](https://developers.openai.com/codex/config-reference/),
clés `mcp_servers.<id>.tools.<tool>.approval_mode` et `enabled_tools`, confrontées
à `--strict-config`, `config/read` et à l'appel réel du binaire installé.

## Recette réelle bornée — VERIFIED pour le transport, PARTIAL pour la qualité

- Session Codex réelle : `01a15de3-b087-75d2-bc09-b064732582a0`, retournée par
  `thread/start`, transmise explicitement par le client de recette à `parent_session`.
  Pas de propagation automatique prétendue, aucun identifiant inventé.
- Tâche : `1e595a8e-9e9d-4553-8d18-7d38fee4949f`, identité `codex`.
- `submit` retourne `queued` en 7 ms. Processus Codex fermé ; une autre connexion
  MCP récupère `status`, `result` et les six événements `activity`.
- État final `failed`, réponse privée `OK.`, erreur `objective_quality_failed`.
  Inférence terminée avec `finish_reason=stop`, 35/2/37 tokens, durée routeur 10 796 ms.
- Alias sélectionné/réponse : `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit`.
  `actual_model=null`, `provider_model_confirmation=alias_only_unconfirmed`.
- Request ID `chatcmpl-cc3f2439`, déploiement LiteLLM
  `17720d29-9da3-4888-aef8-f6db0cc5bd96`, retries/fallbacks exposés **0/0**.
- Journal natif oMLX à **11:56:26,565 Europe/Paris** : modèle effectif
  `mlx-community--Qwen3.6-35B-A3B-4bit`, prompt 35, sortie 2, plafond 64,
  durée 10,45 s. Corrélation temporelle/usage cohérente ; ce journal ne contient
  pas le request ID LiteLLM, donc pas de jointure native univoque par identifiant.
- Raisonnement off : `enable_thinking=false` envoyé ; application `confirmed=null`.
  Aucun autre niveau ni paramètre global modifié ou requalifié.
- Coût routeur `null`, jamais transformé en zéro. Aucun alias cloud ou payant appelé.
- `activity` conserve la session et les métadonnées sans texte de tâche/réponse.
  Il s'agit d'une tâche MCP, pas d'un sous-agent natif Codex.

**MCP historique VERIFIED** : client stdio séparé, serveur `local-llm-mcp 1.1.0`,
outil `delegate`, un appel `testing`, réponse `OK`, modèle Qwen3.6, request ID
`chatcmpl-7dc3c8fc`, 287 ms, un token de sortie. Source et binaire SHA-256 identiques
à l'avant P3-A ; instructions globales identiques également.
Deux inférences locales au total : une via le nouveau MCP et une via l'historique.
Les 41 tests de phase 2 n'ont pas été relancés. Deux tests témoins PASS lors de
l'enregistrement initial ; aucun changement ultérieur de configuration de moteur.

## Sélecteur, GPT, RTK et permissions

- App-server `model/list` initial : GPT-6.1-Sol et Qwen visibles ensemble,
  Muse-Glimmer absent après modification, GPT-6-Sol caché. L'affichage commun
  n'est pas une preuve de sélection correcte des providers ; aucune fusion
  automatique du catalogue natif ne doit être supposée. Catalogue personnalisé
  statique, sujet à vieillissement. Priorité finale GPT/Qwen 0/50 vérifiée dans le fichier.
- Routes locales/gratuites LiteLLM accessibles via MCP selon métadonnées qualifiées ;
  leur présence dans LiteLLM ne les rend pas sélectionnables dans Codex.
- DIRECT LiteLLM : **NOT_TESTED/non raccordé**. Proposition supportée à qualifier :
  profils séparés avec provider/credential DIRECT dédié et catalogue propre,
  modèles distants explicitement étiquetés gratuits/payants. Aucun profil activé.
  `paid-openrouter/deepseek-v4.1-flash-1017`, `paid-openrouter/glm-5.3` et
  `paid/task-advanced` non ajoutés au sélecteur ni testés.
- DELEGATED payant : **BLOCKED**, courtier non raccordé, clé ordinaire LOCAL/FREE.
  Refus serveur PAID déjà qualifié en phase 2, non retesté. Aucun credential payant,
  MASTER_KEY ou changement du budget partagé 40 USD/mois.
- Authentification ChatGPT reconnue par `account/read` et `codex login status`.
  **GPT natif direct NOT_TESTED** : `openai_base_url` reste explicitement
  `http://127.0.0.1:11434/api/codex/v1`. L'essai antérieur a observé cette URL
  pour Responses et un repli websocket vers HTTP. Les tours GPT terminés ne
  prouvent donc pas un trajet direct ChatGPT. Proxy ni paramètres auth modifiés.
- **RTK inchangé/non activé** : rapports 18/19 réutilisés, `hooks.json` et `RTK.md`
  absents, instructions globales préservées, aucune nouvelle batterie RTK.
- P3-B/P3-C non commencés. Pour P3-C : session, task ID, alias, provenance limitée,
  états/durée, tokens, coût null et erreurs disponibles dans les événements.

## Preuves et rollback

Preuves privées sous `artifacts/llm-router-p3a/` (ignoré par Git) :
`isolated-discovery-attempt.json`, `isolated-session.json`, `recovered-task.json`,
`legacy-smoke.json`, `omlx-completions.txt`, `final-preservation.json`, preuves
initiales et sauvegardes privées. Ne pas publier les captures complètes sans filtrage.
Scripts de recette dans `scripts/p3a-session.py` et `scripts/p3a-recover.py` ;
gardes contre une nouvelle génération après conservation des résultats.

1. Désactivation réversible : ajouter `enabled=false` dans la seule section
   `[mcp_servers.llm-router]`, puis ouvrir une nouvelle session Codex.
2. Désenregistrement : `codex mcp remove llm-router`. Vérifier le diff ciblé ; le
   CLI peut normaliser des champs vides. Ne jamais restaurer aveuglément tout
   `config.before.toml` sur un fichier ayant reçu des écritures concurrentes.
3. Catalogue : restaurer seulement l'entrée/visibilité/priorité concernées à partir
   de `catalogue.before.json`, après comparaison de l'état actuel. Restaurer
   Muse-Glimmer est une possibilité de rollback, pas une recommandation d'activation.
4. Conserver les résultats privés pour audit. Ne pas supprimer le répertoire de
   qualification de phase 2 ni la clé partagée LOCAL/FREE. Aucun rollback RTK,
   OpenClaw, budget ou MCP historique nécessaire.

**Arrêt après cette recette.** Aucune prétention de conformité exacte ni de
qualification générale de modèles, de tous les niveaux de raisonnement ou de GPT natif.

## Complément — catalogue Desktop LiteLLM (21 octobre 2026)

**P3-A reste PARTIAL.** Le raccordement MCP ne constitue pas l'achèvement
fonctionnel du catalogue. Aucune nouvelle route ni entrée active ajoutée pendant
ce complément. Aucun changement structurant appliqué ; décision d'architecture
requise avant la suite. Aucune inférence, même gratuite, ni reprise des tests MCP.

### Diagnostic réellement vérifié

- Desktop ChatGPT **26.1013.40934 / 20770**, binaire embarqué
  `CodexCLI.app/Contents/MacOS/codex` **0.163.0-alpha.10.2**. Le CLI Homebrew
  **0.160.0** des recettes précédentes n'est pas ce binaire.
- `config/read` et `model/list` du binaire Desktop confirment le catalogue
  `~/.codex/ollama-launch-models.json`. Il contient les GPT existants et un seul
  modèle tiers, `qwen36-omlx`. GPT-6.1-Sol est désormais `isDefault=true`,
  GPT-6-Sol `hidden=true`, Qwen visible/non prioritaire. Compte `chatgpt` reconnu.
- La liste est un fichier statique chargé au démarrage, pas une découverte de
  LiteLLM. Aucun provider LiteLLM dans la configuration. Le MCP n'alimente pas
  automatiquement le sélecteur et `qwen36-omlx` n'est pas un alias LiteLLM.
- Routage privé installé `~/.codex/ollama-launch-codex-routing.json` :
  `qwen36-omlx` → upstream `http://127.0.0.1:8000/v1`, modèle
  `mlx-community--Qwen3.6-35B-A3B-4bit`. Donc **Desktop → proxy Ollama :11434
  → oMLX :8000**, sans LiteLLM. Traces natives existantes du 20 octobre à
  22:41:25, 22:41:40 et 22:42:00 : `route=upstream`, réponses HTTP 200.
- Le proxy garde une référence Muse-Glimmer dans son allow-list ET dans
  `auto_review_fallback_model`, malgré son retrait du sélecteur. C'est une
  référence obsolète encore potentiellement utilisable par le proxy, pas une
  preuve d'exécution récente. **L'exclusion complète n'est donc pas achevée.**
  Ne pas simplement supprimer l'entrée : le chargeur exige que le fallback
  déclaré appartienne à l'allow-list. Il faudra modifier les deux de façon
  cohérente lors de la livraison retenue, sans réactiver Muse-Glimmer.
- Journaux existants du 21 octobre à 12:03:27 et 12:03:37 :
  `route=chatgpt model="gpt-6.1-sol"`, HTTP 200, client annulé. Les sources du proxy
  distinguent ChatGPT via `ChatGPT-Account-ID` et visent
  `https://chatgpt.com/backend-api/codex`. Preuve de forwarding ChatGPT existant,
  pas de nouvelle recette d'inférence ni preuve d'un trajet sans proxy.

### Découverte native : limite qualifiée sur le binaire Desktop

Schémas générés par **le binaire embarqué** : `model/list` accepte seulement
`cursor/includeHidden/limit`. Les modèles retournés n'ont pas de champ provider,
endpoint ni catégorie. `thread/start` accepte un `modelProvider` pour le fil.
Déclarer plusieurs providers dans TOML ne crée donc pas une association
provider/entrée dans le sélecteur. Les catégories peuvent être identifiées par
les libellés `[LOCAL]`, `[CLOUD FREE]`, `[CLOUD PAID]` ; des sections UI natives
séparées ne sont pas établies par ce contrat.

Expérience sans inférence : un seul serveur HTTP simulé loopback, un provider
`audit` Responses dans un `CODEX_HOME` temporaire sans catalogue personnalisé,
endpoint `/v1/models` exposant `local-audit/model`. Après `model/list`,
**zéro requête HTTP**, modèle simulé absent, 11 entrées du catalogue client
retournées. Le serveur refusait tout POST ; aucune génération possible par ce
simulateur. Processus, socket et dossier temporaire supprimés. Cette preuve
porte sur cette version et cette configuration ; elle ne démontre pas une
impossibilité universelle de futurs providers ou clients.

**Conclusion : aucune fusion native dynamique multi-provider qualifiée.**
Une simple liste d'alias ajoutée au JSON donnerait des entrées sans routage
approprié et ne satisferait pas la demande. En particulier, le proxy route les
modèles non inscrits dans son allow-list vers OpenAI/ChatGPT : il ne faut pas y
laisser tomber par défaut des alias LiteLLM.

Référence : [configuration officielle OpenAI](https://developers.openai.com/codex/config-reference/),
`model_catalog_json` chargé au démarrage, `model_provider`, profils et providers.
La documentation ne promet pas de fusion ; l'expérience Desktop et les schémas
ci-dessus bornent la conclusion.

### Catalogue approuvé attendu, identifiants exacts

GET authentifié `/v1/models` avec la clé existante **LOCAL/FREE** : 13 alias,
dont EmbeddingGemma. Lecture seule, sans inférence. Après exclusion de l'embedding,
les **12 alias de chat LOCAL/FREE** attendus sont tous présents :

| Catégorie | Identifiant de routage exact |
|---|---|
| LOCAL — oMLX | `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit` |
| LOCAL — Ollama | `local-ollama/qwen3:4b-instruct` |
| CLOUD FREE — Groq | `free-groq/qwen3.8-27b` |
| CLOUD FREE — Groq | `free-groq/gpt-oss-120b` |
| CLOUD FREE — OpenRouter | `free-openrouter/dots-3-note-preview:free` |
| CLOUD FREE — OpenRouter | `free-openrouter/north-mini-code:free` |
| CLOUD FREE — Mistral | `free-mistral/ministral-8b-2512` |
| CLOUD FREE — Mistral | `free-mistral/codestral-2508` |
| CLOUD FREE — pool | `free/task-fast` |
| CLOUD FREE — pool | `free/task-coding` |
| CLOUD FREE — pool | `free/task-reasoning` |
| CLOUD FREE — pool | `free/task-long-context` |
| CLOUD PAID — référence demandée | `paid-openrouter/deepseek-v4.1-flash-1017` |
| CLOUD PAID — référence demandée | `paid-openrouter/glm-5.3` |
| CLOUD PAID — pool demandé | `paid/task-advanced` |

Les trois alias PAID ne sont **pas** visibles avec cette clé, conformément à ses
permissions. Leur existence administrative et le budget 40 USD/mois restent
les preuves de phase 2, non relues avec un credential administratif pendant ce
complément. Aucun credential DIRECT PAID n'est installé dans ce raccordement.
La clé DELEGATED LOCAL/FREE ne sera ni élargie ni réutilisée pour le payant.

Le synchroniseur devra utiliser le catalogue réellement visible par chaque
identité DIRECT, filtré par la politique de chat approuvée ; une présence dans
un catalogue administratif n'est jamais un droit. Les libellés simplifiés sont
indépendants du `slug` exact. Pas de réécriture d'alias ni de remplacement d'un
pool explicite par un modèle individuel dans le client.

### Possibilités techniques et choix avant modification structurante

Le proxy existant sait déjà router chaque entrée de son allow-list vers un
upstream distinct. Son code recrée les headers des requêtes tierces, ne transmet
pas les credentials Codex/ChatGPT et injecte seulement la clé upstream prévue.
Il relit la configuration de routage à la requête. C'est une base réutilisable,
sans remplacer le provider GPT ni l'authentification ChatGPT.

**Limite empêchant un simple ajout de routes :** `prepareUpstreamRequest`
normalise tous les upstreams comme oMLX, transforme l'input, et injecte
`chat_template_kwargs.enable_thinking` et les budgets 512/2048/8192/16384 selon
l'effort. Ce contrat ne qualifie ni LiteLLM Responses, ni les providers cloud.
Il ne faut pas supposer que LiteLLM ou chaque modèle supprimera ces paramètres.
La compatibilité Responses/SSE, outils et reprise multi-tour doit être qualifiée
sur le chemin livré ; une réussite MCP Chat Completions ne la démontre pas.

| Option | Avantages | Limites et impacts |
|---|---|---|
| **A — Étendre le proxy existant** | Un seul point de routage, conservation de ChatGPT et du port actuel ; alias LiteLLM exacts ; pas de service complémentaire | Adaptateur distinct LiteLLM/Cloud, secrets par fichier privé plutôt que clé en clair dans JSON, puis reconstruction et remplacement contrôlé du binaire Ollama. **Non autorisé/appliqué ici** ; régression possible sur le frontal existant. |
| **B — Ajouter un adaptateur LiteLLM local derrière le proxy existant — recommandé** | Aucun remplacement du proxy ou de l'authentification ; GPT garde son chemin ; l'allow-list existante envoie seulement les 15 alias approuvés vers l'adaptateur. Credentials DIRECT et adaptation Responses isolés du MCP | Nouveau petit service loopback supervisé et synchroniseur. L'adaptateur neutralise explicitement les paramètres oMLX sur cloud et traduit/préserve les contrôles locaux qualifiés. Transport Responses/SSE et outils à tester sans PAID. Configurations de routage/catalogue à mettre à jour après validation. |
| **C — Profils GPT et LiteLLM séparés** | Séparation explicite des credentials/providers ; rollback simple ; moins d'intermédiation | Ne réalise pas le sélecteur unique demandé. Changement de profil/client/session nécessaire ; prise en charge effective des profils dans l'UI Desktop à qualifier. Repli possible uniquement après choix utilisateur. |

B est une **proposition**, pas un adaptateur déjà installé. Le choix entre A et B
porte sur le lieu d'adaptation, pas sur la création d'une nouvelle authentification
GPT. Un provider LiteLLM global remplaçant le provider ChatGPT est écarté.

### Livraison proposée pour A ou B, non exécutée

1. Synchroniseur dédié en lecture : catalogue GPT natif obtenu dans un processus
   isolé sans `model_catalog_json` personnalisé (pattern déjà présent dans
   `defaultCodexAppNativeModelCatalog`), plus `/v1/models` des identités DIRECT.
   Préserver intégralement les métadonnées GPT, GPT-6.1-Sol prioritaire et
   GPT-6-Sol masqué. Ne pas maintenir à la main une copie figée du catalogue GPT.
2. Intersection permissions/politique chat, exclusion systématique EmbeddingGemma
   et Muse-Glimmer, noms préfixés par catégorie, slugs LiteLLM inchangés. Métadonnées
   de capacités/contexte documentées ; ne pas recopier les capacités GPT ou les
   budgets oMLX sur des modèles cloud.
3. Générer catalogue Desktop et routage à partir de la **même révision** validée.
   Publication atomique de chaque fichier sous verrou ; pas d'activation d'une
   entrée avant sa route. Révocation/refus serveur toujours appliqués à l'appel.
   Une erreur de découverte n'élargit jamais les droits ni ne crée de secours payant.
4. Synchronisation au lancement puis périodique : mécanisme nouveau à approuver.
   Le catalogue Desktop est chargé au démarrage ; la mise à jour du fichier seul
   ne prouve pas un rafraîchissement immédiat de l'UI. Redémarrage explicite de
   Desktop si nécessaire, sans redémarrer arbitrairement une session utilisateur.
5. DIRECT PAID : credential client distinct, propriétaire autorisé et équipe
   `paid-openrouter-shared` contrôlés côté LiteLLM, plafond existant **40 USD/mois
   inchangé**. Aucun MASTER_KEY au Mac, aucune réutilisation du credential MCP.
   Ne publier de routes PAID utilisables qu'après relecture effective des droits
   et du rattachement budgétaire. Aucun consentement par génération après ce
   contrôle et la sélection DIRECT explicite ; DELEGATED PAID reste fermé.
6. Qualification ciblée du chemin Desktop : sélection exacte, Responses/SSE,
   un aller-retour outil et une reprise multi-tour sur LOCAL, puis FREE si
   nécessaire/autorisé. Vérifier les headers sans exposer de secrets et le trajet
   ChatGPT préservé. PAID : contrôles de droits/budget sans inférence facturable ;
   aucune qualification réelle de génération payante ne sera prétendue.
7. Retirer aussi la référence Muse-Glimmer et son fallback cohérent du routage
   actif lors de cette livraison. Ne pas laisser une route obsolète dissimulée
   uniquement par le sélecteur. RTK, OpenClaw, Agent Standup et local_llm inchangés.

### Preuves, état et retour arrière de ce complément

`artifacts/llm-router-p3a/catalogue-audit/` : `desktop-actual.json`,
`desktop-discovery.json`, `litellm-visible.json`, schémas générés par Desktop,
script de lecture/expérience sans inférence. Le répertoire est ignoré par Git.

**VERIFIED** : origine de la liste, modèle GPT par défaut, visibilité, routage
Qwen hors LiteLLM, forwarding ChatGPT historique, 12 alias chat LOCAL/FREE visibles,
absence de découverte automatique dans l'expérience provider isolée.
**PARTIAL** : catalogue complet réellement utilisable dans Desktop, exclusion de
Muse-Glimmer du routage, fusion dynamique et adaptation Responses non livrées.
**BLOCKED pour activation PAID** : identité/credential DIRECT avec rattachement
budgétaire non raccordés à Desktop. Pas de tentative avec une autre identité.
**NOT_TESTED** : inférence Desktop des alias LiteLLM, facturation/coupure PAID,
rafraîchissement UI à chaud, compatibilité universelle outils/contexte/raisonnement.

Rollback de ce complément : aucune configuration active modifiée, seuls rapport
et preuves préparés. Pour une future option B : sauvegardes ciblées avant écriture,
restauration des seules entrées/catalogue appartenant au lot, puis arrêt du service
complémentaire via son gestionnaire documenté ; conserver le proxy actuel et
ChatGPT. Pour A : conserver le binaire qualifié actuel et sa configuration avant
tout remplacement. Les étapes de rollback antérieures restent valables pour MCP.

**Décision attendue : A, B ou repli C. Arrêt avant implémentation/déploiement
structurant. P3-A n'est pas déclaré achevé.**

Contrôle de préservation du complément : les instructions globales, la source et
le binaire `local_llm` gardent leurs empreintes antérieures ; le catalogue actif
correspond encore à sa copie versionnée. La comparaison avec la sauvegarde de
P3-A relève toutefois la disparition de la section `mcp_servers.n8n-mcp`, en plus
de l'ajout attendu `llm-router`. Cette différence indépendante est observée,
sans attribution ni restauration ; aucune action de ce complément n'a écrit dans
`config.toml`. Ne pas réutiliser la sauvegarde globale pour écraser cet état.
Preuve : `catalogue-audit/preservation.json` (`config_still_only_adds_llm_router=false`).

## Qualification des niveaux de raisonnement — complément du 21 octobre

**P3-A demeure PARTIAL.** La qualification ci-dessous distingue les capacités
annoncées par le catalogue, le transport observé et l'application dans un moteur.
Aucune inférence supplémentaire, gratuite ou payante, n'a été exécutée pour ce
complément. Aucun réglage global oMLX, aucune configuration active ni OpenClaw
n'ont été modifiés. Les recettes MCP déjà acquises n'ont pas été relancées.

### Desktop réellement installé, distinct du CLI

Le binaire embarqué **0.163.0-alpha.10.2** a fourni les niveaux ci-dessous via
`model/list`. Ce sont les choix annoncés au sélecteur par l'app-server : le rendu
graphique et les clics dans l'UI ne sont pas vérifiés. `none` désigne Off ; les
valeurs supplémentaires `xhigh` et `ultra` sont conservées telles quelles,
sans les assimiler à Max. Aucun niveau GPT n'a été uniformisé ou supprimé.

| Modèle Desktop | Visibilité | Niveaux annoncés au sélecteur | Niveau demandé et paramètre transmis pendant cette recette | Appliqué au moteur | Preuve |
|---|---|---|---|---|---|
| gpt-6.1-sol | Visible, défaut prioritaire | Low, Medium, High, xhigh, Max, ultra | Aucun nouvel appel | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| gpt-6-astra | Visible | Low, Medium, High, xhigh, Max, ultra | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| gpt-6-sol | Masqué | Low, Medium, High, xhigh, Max, ultra | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| gpt-6-luna | Visible | Low, Medium, High, xhigh, Max | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| gpt-reserve | Masqué | Low, Medium, High, xhigh, Max | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| gpt-5.6-sol | Visible | Low, Medium, High, xhigh, Max, ultra | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| gpt-5.6-terra | Visible | Low, Medium, High, xhigh, Max, ultra | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| gpt-5.6-luna | Visible | Low, Medium, High, xhigh, Max | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| gpt-5.5 | Visible | Low, Medium, High, xhigh | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| codex-auto-review | Masqué | Low, Medium, High, xhigh, Max | Aucun | Non observé | VERIFIED catalogue ; NOT_TESTED raisonnement |
| qwen36-omlx | Visible | Off, Low, Medium, High, Max ; **Minimal absent** | Six efforts testés contre un mock loopback, voir ci-dessous | Aucun moteur appelé | PARTIAL |

Test nouveau, sans inférence : un app-server Desktop avec `CODEX_HOME`
temporaire, provider mock local et catalogue existant en lecture seule a reçu
six `turn/start` avec `effort=none/minimal/low/medium/high/max`. Les six corps
HTTP `/v1/responses` contiennent exactement `reasoning.effort` demandé.
Le mock retourne volontairement HTTP 400 « capture only », sans retries ;
ce statut n'est ni un rejet d'authentification ni un test de génération.
Minimal est accepté par l'API app-server même s'il n'est pas proposé dans
le catalogue Qwen courant. Cela ne prouve pas son accessibilité graphique.
Le champ `effort` s'applique au tour et aux tours suivants selon le schéma
Desktop ; aucune session active de l'utilisateur n'a été changée.

### Qwen3.6 oMLX : budget distinct de la génération totale

| Niveau demandé | Desktop annoncé | Paramètre cible par requête oMLX | Application observable | Preuve |
|---|---|---|---|---|
| Off (`none`) | Oui | `chat_template_kwargs.enable_thinking=false`, aucun budget | Ancienne recette MCP a envoyé false ; confirmation moteur absente | PARTIAL |
| Minimal | Non | `chat_template_kwargs.enable_thinking=false`, aucun budget | Mapping du proxy lu ; pas de génération ni de chemin LiteLLM Desktop | PARTIAL ; sélecteur actuel UNSUPPORTED |
| Low | Oui | `enable_thinking=true`, `thinking_budget=512` | Fermeture forcée de pensée au seuil sur tokens synthétiques | VERIFIED composant ; PARTIAL chaîne |
| Medium | Oui | `enable_thinking=true`, `thinking_budget=2048` | Même vérification au seuil 2048 | VERIFIED composant ; PARTIAL chaîne |
| High | Oui | `enable_thinking=true`, `thinking_budget=8192` | Même vérification au seuil 8192 | VERIFIED composant ; PARTIAL chaîne |
| Max | Oui | `enable_thinking=true`, `thinking_budget=16384` | Même vérification au seuil 16384 | VERIFIED composant ; PARTIAL chaîne |

Le proxy existant traduit les quatre niveaux avec ces budgets et désactive
Off/none/minimal. Cela concerne aujourd'hui **Desktop → ancien proxy → oMLX**,
pas Desktop → LiteLLM. Le mapping ne couvre pas xhigh/ultra : ces valeurs
peuvent activer thinking sans budget explicite ; ne pas les annoncer pour Qwen.

Test du code **oMLX réellement installé** : `_resolve_thinking_budget` conserve
les quatre budgets explicites par requête ; `ThinkingBudgetProcessor`, exécuté
avec MLX sur des tokens synthétiques, force le token de fin de pensée aux
seuils 512/2048/8192/16384. Aucun modèle chargé pour ce test. Le mécanisme cesse
ensuite de forcer les tokens : il ne limite pas la réponse entière.
Ce budget est indépendant de `max_tokens` et de la fenêtre de contexte.
Il reste une limite de pensée, pas une garantie de consommation exacte : le
modèle peut finir plus tôt et des tokens de fermeture peuvent être nécessaires.

Test du mapping LiteLLM installé : avec `thinking_budget=512`, thinking activé
et `max_tokens=64`, les champs thinking restent dans `extra_body`, tandis que
`max_tokens` reste 64. Cela prouve la séparation des paramètres à cette étape,
pas leur arrivée effective à oMLX. Un plafond total inférieur peut naturellement
couper la génération avant l'épuisement du budget de pensée.
**La chaîne complète via LiteLLM demeure NOT_TESTED.**

### Conversions des services installés, sans requête fournisseur

Les fonctions de transformation de **LiteLLM 1.104.5** et **FreeLLMAPI 0.16.6**
ont été exécutées dans leurs conteneurs installés, sans credentials transmis,
sans inférence, sans écriture distante et sans import du module base de données
FreeLLMAPI. Les tests FreeLLMAPI extraient les fonctions pures du fichier installé.

LiteLLM `get_optional_params` conserve les six valeurs sur les chemins
`openai` utilisés par les modèles gratuits et pools ; il ne garantit pas leur
support chez le fournisseur. Pour les deux modèles `openrouter` payants,
`max` devient **xhigh**, y compris dans le corps produit par `transform_request`.
Les cinq autres valeurs sont conservées dans `reasoning_effort`. Ce corps
n'a jamais été envoyé à OpenRouter : acceptation distante **NOT_TESTED**.

FreeLLMAPI lit bien `reasoning.effort` sur Responses et le convertit en champ
plat. Le commentaire du fichier Responses disant que reasoning est ignoré
est **obsolète** : le schéma incorpore `samplingParamSchemaFields` et le chemin
utilise `pickSamplingParams`. La lecture de ce chemin prévaut sur le commentaire.

| Demande | LiteLLM vers FreeLLMAPI | FreeLLMAPI → Groq | FreeLLMAPI → Mistral | FreeLLMAPI → OpenRouter |
|---|---|---|---|---|
| Off / none | none | **low** | Paramètre supprimé | none |
| Minimal | minimal | **low** | Paramètre supprimé | minimal |
| Low | low | low | Paramètre supprimé | low |
| Medium | medium | medium | Paramètre supprimé | medium |
| High | high | high | Paramètre supprimé | high |
| Max | max | **high** | Paramètre supprimé | **high** |

Ce tableau décrit le corps construit par les adaptateurs, **pas** le raisonnement
appliqué par les modèles. Les efforts inconnus deviennent absents dans
FreeLLMAPI ; les défauts du fournisseur reprennent alors la main. Il n'existe
pas ici de rejet systématique d'un niveau indisponible : clamp et suppression
peuvent être silencieux. Ne pas présenter Off sur Groq, ni Max distinct de High
sur ces routes, comme des capacités qualifiées. Ne pas traduire ces niveaux
en budgets numériques oMLX.

### Matrice par alias LiteLLM approuvé

Dans **toutes les lignes**, l'alias exact est absent du catalogue Desktop actif,
donc aucun niveau n'y est sélectionnable aujourd'hui. O/M/L/D/H/X désignent
Off, Minimal, Low, Medium, High, Max ; les demandes ci-dessous sont les vecteurs
des tests de composants, pas des appels aux modèles. « Non observé » interdit
toute conclusion de fonctionnement de bout en bout.

| Alias exact | Niveaux Desktop | Demande examinée | Paramètre transmis / transformation établie | Effectivement appliqué | Preuve |
|---|---|---|---|---|---|
| `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit` | Absent ; ancien alias Qwen : O/L/D/H/X | O/M/L/D/H/X | Cible false/false/512/2048/8192/16384 ; tests de composants ci-dessus | Budgets vérifiés sur tokens synthétiques seulement | PARTIAL |
| `local-ollama/qwen3:4b-instruct` | Absent | O/M/L/D/H/X | Aucun mapping spécifique Ollama qualifié | Non observé ; ni budget oMLX ni support thinking déduits du nom | NOT_TESTED |
| `free-groq/qwen3.8-27b` | Absent | O/M/L/D/H/X | `reasoning_effort=low/low/low/medium/high/high` | Non observé | PARTIAL conversions ; Off et Max distinct UNSUPPORTED par cette route |
| `free-groq/gpt-oss-120b` | Absent | O/M/L/D/H/X | Même conversion Groq | Non observé | PARTIAL conversions ; Off et Max distinct UNSUPPORTED par cette route |
| `free-openrouter/dots-3-note-preview:free` | Absent | O/M/L/D/H/X | `reasoning_effort=none/minimal/low/medium/high/high` | Non observé | PARTIAL conversions ; Max distinct UNSUPPORTED par FreeLLMAPI |
| `free-openrouter/north-mini-code:free` | Absent | O/M/L/D/H/X | Même conversion OpenRouter gratuit | Non observé | PARTIAL conversions ; Max distinct UNSUPPORTED par FreeLLMAPI |
| `free-mistral/ministral-8b-2512` | Absent | O/M/L/D/H/X | `reasoning_effort` supprimé pour les six valeurs | Non observé ; défaut fournisseur | UNSUPPORTED pour pilotage d'effort sur cette route |
| `free-mistral/codestral-2508` | Absent | O/M/L/D/H/X | Même suppression Mistral | Non observé ; défaut fournisseur | UNSUPPORTED pour pilotage d'effort sur cette route |
| `free/task-fast` | Absent | O/M/L/D/H/X | Groq Qwen / Mistral Ministral / OpenRouter Dots : conversion dépend du membre | Non observé | PARTIAL ; aucun niveau commun garanti |
| `free/task-coding` | Absent | O/M/L/D/H/X | Mistral Codestral / OpenRouter North / Groq GPT-OSS : dépend du membre | Non observé | PARTIAL ; aucun niveau commun garanti |
| `free/task-reasoning` | Absent | O/M/L/D/H/X | Groq GPT-OSS / Groq Qwen / OpenRouter North : dépend du membre | Non observé | PARTIAL ; support réel de chaque membre NOT_TESTED |
| `free/task-long-context` | Absent | O/M/L/D/H/X | OpenRouter Dots / OpenRouter North / Mistral Ministral : dépend du membre | Non observé | PARTIAL ; aucun niveau commun garanti |
| `paid-openrouter/deepseek-v4.1-flash-1017` | Absent | O/M/L/D/H/X, fonctions seules | `reasoning_effort=none/minimal/low/medium/high/xhigh` | Non observé, aucun appel payant | PARTIAL transformation ; génération NOT_TESTED |
| `paid-openrouter/glm-5.3` | Absent | O/M/L/D/H/X, fonctions seules | Même conversion LiteLLM OpenRouter | Non observé, aucun appel payant | PARTIAL transformation ; génération NOT_TESTED |
| `paid/task-advanced` | Absent | O/M/L/D/H/X, analyse de route | Alias du chemin DeepSeek ; conversion attendue ci-dessus, pool lui-même non exécuté | Non observé | PARTIAL documentaire ; génération NOT_TESTED |

Membres des pools : reprise des preuves du déploiement FreeLLMAPI existant,
sans actualisation par inférence. Un changement de membres exige de recalculer
les capacités communes avant publication au sélecteur. Un nom de pool
« reasoning » ne garantit ni niveau, ni exactitude du résultat.

Métadonnées historiques OpenRouter dans `paid-models.pending.json` : DeepSeek
annonce none/low/high/max et raisonnement facultatif ; GLM annonce low/high/max,
raisonnement obligatoire. Minimal et Medium ne sont pas documentés dans ces
instantanés ; Off ne doit pas être proposé pour GLM sur cette seule base.
Ces métadonnées ne sont pas une preuve actuelle d'acceptation. La conversion
LiteLLM Max→xhigh doit être résolue/qualifiée avant d'annoncer Max sur ces routes.

EmbeddingGemma demeure exclu du sélecteur conversationnel. Muse-Glimmer n'est
pas qualifié/activé par ce travail. OpenClaw reste intact : son mapping existant
**Ultra → High / 8192** est distinct du mapping Codex et n'a pas été modifié.

### Preuves, limites et prochaine décision

Preuves nouvelles ignorées par Git dans `artifacts/llm-router-p3a/reasoning-audit/` :
`desktop_mock.py`, `desktop-mock.json`, `omlx-component.json`,
`parameter-components.json` (synthèse des sorties de tests de fonctions),
`litellm-transform.json` (sortie directe de la construction des corps).
La liste Desktop est celle déjà acquise dans `catalogue-audit/desktop-actual.json`.

VERIFIED s'applique uniquement aux observations et composants explicitement
désignés. Pas de preuve graphique, pas de chaîne Desktop/LiteLLM/oMLX livrée,
pas de raisonnement cloud effectivement appliqué. Les essais mock retournent
une erreur intentionnelle et ne comptent pas comme une génération réussie.
Les budgets numériques locaux ne sont jamais transposés aux clouds.

La future option A ou B doit publier seulement les niveaux réellement supportés,
préserver les capacités GPT et refuser explicitement un effort indisponible
plutôt que promettre un niveau supprimé ou converti silencieusement. Pour un
pool, prendre l'intersection des capacités qualifiées de tous ses membres, ou
afficher une limite explicite sans garantie de niveau. Qualifier ensuite un
minimum de générations LOCAL et, si utile, FREE sur le chemin livré. PAID reste
sans inférence avant autorisation spécifique, même si l'identité DIRECT est
ultérieurement raccordée au budget existant.

**BLOCKER :** aucune fusion native dynamique multi-provider n'est qualifiée dans
Desktop installé ; le proxy existant adapte tous les upstreams comme oMLX.
**EVIDENCE :** expérience de découverte sans appel HTTP, schémas Desktop,
lecture du proxy, captures mock et conversions de composants ci-dessus.
**ATTEMPTS :** catalogue/config Desktop, découverte provider isolée, inspection
et tests hors réseau des transformations et du moteur installé.
**NEXT REQUIRED ACTION :** choix explicite de l'option A ou B déjà décrite avant
toute nouvelle architecture ; B demeure la recommandation réversible.

Rollback du complément raisonnement : aucune configuration active à restaurer ;
les processus mock sont arrêtés et leurs homes temporaires supprimés. Conserver
les preuves, ou retirer uniquement les artefacts de cette recette. Ne restaurer
aucune sauvegarde globale, ne toucher ni OpenClaw ni aux paramètres oMLX.

## Option B autorisée, implémentée et activée — 21 octobre 2026

La décision utilisateur lève l'attente architecturale des sections précédentes.
**L'option B est déployée ; P3-A reste PARTIAL, pas achevé fonctionnellement
pour l'ensemble du catalogue.** Aucun travail P3-C, aucun commit/push.

### Architecture effectivement livrée

```text
Codex Desktop / binaire embarqué 0.163.0-alpha.10.2
  → proxy existant 127.0.0.1:11434/api/codex/v1, binaire inchangé
      ├─ GPT : chemin, provider, authentification ChatGPT et catalogue inchangés
      └─ alias LiteLLM exact → adaptateur 127.0.0.1:11439/v1
          → LiteLLM HTTPS, identité codex-direct, clé DIRECT de la catégorie
              ├─ local-omlx → relais Tailscale existant → oMLX loopback:8000
              ├─ local-ollama → chemin existant LiteLLM/Ollama (recette en échec)
              ├─ free-* et free/task-* → FreeLLMAPI
              └─ paid-* / paid/task-advanced → OpenRouter, sans recette payante
```

Sources : [adaptateur et gestionnaire](litellm-adapter/README.md).
Deux nouveaux LaunchAgents : `org.gangneux.codex-litellm-adapter` (KeepAlive)
et `org.gangneux.codex-litellm-adapter-sync` (StartInterval 300 secondes).
Le second est normalement au repos entre deux cycles ; son enregistrement ne
signifie pas qu'une synchronisation tourne continuellement.

État privé 0700 dans `~/.local/state/codex-litellm-adapter/`, configuration et
secret d'entrée privés dans `~/.config/codex-litellm-adapter/`. Aucun secret
dans le dépôt. Seuls les fichiers de configuration documentés du sélecteur et
du routage ont été activés ; aucune écriture dans une base/cache interne Codex.

Le proxy existant retire déjà les headers ChatGPT sur ses routes tierces.
L'adaptateur exige son propre secret loopback, ne traite aucun modèle GPT et
lit les deux credentials DIRECT existants, jamais celui du MCP. Il reconstruit
Chat Completions avec les seuls paramètres pris en charge. Il retire les
contrôles oMLX pour les clouds et les reconstruit pour Qwen depuis l'effort.
Il n'exécute aucun outil : les appels reviennent à Codex, qui garde son contrôle.

Les réponses sont **tamponnées**, puis traduites en événements SSE Responses.
Il ne s'agit pas d'un streaming token par token. L'annulation ferme la connexion
amont ; le moment où chaque fournisseur cesse de calculer/facturer n'est pas
qualifié. Deux requêtes au plus, refus 429 au-delà ; pas de retry/fallback ajouté.
Texte, historique de fonctions et namespaces qualifiés ; images et autres items
non pris en charge refusés. L'outil OpenAI hébergé `web_search`, envoyé par
Desktop malgré la capacité de recherche désactivée, est exclu **uniquement**
sur les routes de l'adaptateur. Le comportement des outils GPT est inchangé.

### Synchronisation réelle et catalogue Desktop

Découverte authentifiée `/v1/models` pour chaque credential DIRECT, intersection
de la politique chat déjà approuvée : deux LOCAL, six gratuits individuels,
quatre pools FREE, trois PAID. Les identifiants de routage restent exactement
les alias LiteLLM. Libellés préfixés `[LOCAL]`, `[CLOUD FREE]`, `[CLOUD PAID]`.
EmbeddingGemma et Muse-Glimmer absents du catalogue conversationnel final.
Ancien alias `qwen36-omlx` conservé **masqué**, routé vers le même adaptateur
et le véritable alias LiteLLM, pour les sessions existantes.

Le synchroniseur conserve chaque entrée GPT existante **à l'identique**,
priorités, visibilité et efforts compris. GPT-6.1-Sol reste configuré et défaut ;
GPT-6-Sol reste masqué. Le catalogue embarqué Desktop est consulté à chaque cycle
sans auth ni inférence pour diagnostic : `gpt-reserve`, absent de ce catalogue
embarqué mais déjà autorisé localement, est préservé. Les modèles GPT nouveaux
du binaire ne sont pas ajoutés automatiquement à vos autorisations.

La liste LiteLLM est découverte, pas recopiée manuellement dans le script.
La politique d'approbation existante reste une allow-list ; une nouvelle route
serveur ne vaut pas automatiquement approbation du chat. Les capacités sont des
surcouches explicites, pas déduites de la seule présence dans `/models`.

Verrou du gestionnaire, remplacement atomique par fichier, routes avant catalogue,
santé de l'adaptateur exigée avant publication. Ce n'est pas une transaction
atomique entre les deux fichiers. Une entrée possédée modifiée concurremment
bloque l'écriture. Une route révoquée reste une route de refus vers l'adaptateur
afin qu'une session ancienne ne tombe pas sur le backend GPT. Un cycle manuel
de synchronisation après réactivation est passé sans nouvelle inférence.

`model/list` du **binaire Desktop**, relancé après activation finale, accepte
quinze alias exacts et expose les six efforts Qwen, Minimal compris. Cela prouve
le catalogue chargé par le processus Desktop ; **le rafraîchissement graphique
à chaud de la fenêtre déjà ouverte n'est pas vérifié**. L'app-server charge le
fichier au démarrage. Aucun redémarrage forcé de l'application hébergeant la
session en cours ; recharge au prochain démarrage approprié.

### Identité DIRECT PAID et budget — VERIFIED administrativement

P3-B a fourni entre-temps `codex-direct-local-free.key` et
`codex-direct-paid.key` ; aucune clé n'a été émise dans cette livraison P3-A.
Relecture API native sur le serveur, avec le mécanisme opérateur existant,
sans transfert de MASTER_KEY au Mac :

- propriétaire des clés : **codex-direct**, clés privées 0600, droits explicites ;
- clé LOCAL/FREE : treize alias, embedding exclu du sélecteur ;
- clé PAID : les trois alias demandés, équipe **paid-openrouter-shared**,
  non bloquée, **40 USD / 1mo**, sans nouveau budget par client/modèle ;
- découverte avec chaque clé cliente : 13 et 3 alias exactement ;
- après recette : équipe toujours 40 USD / 1mo, spend **0 USD** ;
- journal de l'adaptateur : **zéro requête de modèle PAID**, pas seulement zéro
  réponse payante réussie. Aucun appel payant de validation.

Les trois routes payantes sont raccordées aux credentials habilités et au contrôle
financier existant ; elles ne sont pas déclarées qualifiées par inférence.
Une sélection DIRECT manuelle ne demande aucune confirmation supplémentaire.
Le refus local est testé lorsque l'attestation d'identité/budget manque ; les
révocations et budgets restent appliqués côté LiteLLM, sans clé de secours.
La granularité de coupure du budget n'a pas été requalifiée.

### Qwen : chaîne complète et niveaux effectivement observés

Le sélecteur actuel annonce Off, Minimal, Low, Medium, High, Max pour
`local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit`. Des `turn/start` réels avec le
binaire Desktop passent par **le proxy actif, l'adaptateur, LiteLLM et oMLX**.
Les six efforts aboutissent à un tour `completed`, réponse `OK` ou `OK.`.
Le contrôle MCP historique exigeant exactement `OK` n'a pas été rejoué ni effacé.

| Visible / demandé | Adaptateur → LiteLLM | HTTP LiteLLM → oMLX observé | Raisonnement mesuré | Requête LiteLLM | Preuve |
|---|---|---|---|---|---|
| Off / none | `enable_thinking=false`, pas de budget | Même contrôle, pas de `thinking_budget` | 0 token | `chatcmpl-388b81e1` ; premier trajet global `chatcmpl-4ea90c96` | VERIFIED transport + désactivation observée |
| Minimal | `enable_thinking=false`, pas de budget | Même contrôle | 0 token | `chatcmpl-aead1b33` | VERIFIED transport + désactivation observée |
| Low | `enable_thinking=true`, budget 512 | **512**, pas de `max_tokens` imposé par le test | 12 tokens | `chatcmpl-9761a617` | VERIFIED paramètre transmis, pensée active ; saturation PARTIAL |
| Medium | true, budget 2048 | **2048**, limite de génération distincte | 11 tokens | `chatcmpl-9b72dcb9` | VERIFIED paramètre transmis, pensée active ; saturation PARTIAL |
| High | true, budget 8192 | **8192**, limite de génération distincte | 86 tokens | `chatcmpl-6b41d57f` | VERIFIED paramètre transmis, pensée active ; saturation PARTIAL |
| Max | true, budget 16384 | **16384**, limite de génération distincte | 12 tokens | `chatcmpl-ae046beb` | VERIFIED paramètre transmis, pensée active ; saturation PARTIAL |

La capture ciblée est faite dans l'espace réseau du conteneur LiteLLM installé,
sur son trafic HTTP sortant vers le port oMLX 8000. Elle ne conserve que modèle,
thinking_budget, enable_thinking, max_tokens et reasoning_effort : aucun header,
prompt, credential ou pcap écrit. Le corps contient le modèle moteur exact
`mlx-community--Qwen3.6-35B-A3B-4bit`, pas seulement l'alias de routage.
Les statistiques renvoyées et les journaux natifs oMLX corroborent génération et
comptes de tokens. Les journaux natifs LiteLLM attribuent les dix appels réussis
collectés avant l'essai Ollama corrigé à **codex-direct**, destinations oMLX ou
FreeLLMAPI. Les IDs de threads et tours sont dans les fichiers de recette.

L'application du plafond lors d'une pensée qui l'atteint reste une preuve de
**composant**, acquise précédemment sur le code oMLX installé avec tokens
synthétiques. Aucune génération longue n'a été lancée pour épuiser 16K tokens.
La pensée peut finir avant son plafond ; le compte Max n'a pas à dépasser High.
Budget de pensée, limite totale de génération et contexte restent distincts.
Aucun paramètre global oMLX changé.

La première session réelle a chargé 84 792 tokens avec l'environnement global,
et répondu OK en environ 102 s ; une isolation initiale encore trop chargée
contenait 73 507 tokens. Minimal a alors atteint le délai de recette 180 s :
connexion fermée et état 499 conservés. Les essais restants ont été suspendus,
puis une capture mock a vérifié l'allègement **avant** les nouvelles inférences.
Les modèles LiteLLM n'injectent plus les instructions d'usage apps/plugins/skills ;
les processus de recette désactivent aussi découverte hôte/apps et documents
projet, sans modifier la configuration globale. Les tours budgétaires utilisent
ensuite environ 5 200 tokens, environ 4–7 s après préremplissage initial.
Ces temps décrivent la recette, pas un benchmark ni une garantie de performance.

### Matrice finale par modèle/pool

Les GPT gardent exactement les niveaux du tableau Desktop précédent : aucune
uniformisation, aucun nouvel appel GPT. Pour les autres clouds, aucune liste
d'efforts non qualifiée n'est annoncée au sélecteur. Si un effort est néanmoins
envoyé par l'API ou hérité d'un tour, il est préservé à l'entrée cloud et les
conversions sont tracées. Les champs `applied_effort` restent inconnus sans preuve.

| Alias exact | Niveaux visibles Desktop | Niveau demandé / transmis dans la recette | Effectivement observé | Preuve finale |
|---|---|---|---|---|
| `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit` | Off, Minimal, Low, Medium, High, Max | Six niveaux, paramètres et IDs ci-dessus | Pensée off/on et trafic oMLX ; outil réel + reprise | VERIFIED pour trajet/contrôles ; saturation des budgets PARTIAL |
| `local-ollama/qwen3:4b-instruct` | Aucun effort qualifié annoncé | Effort absent ; `parallel_tool_calls` d'abord envoyé, ensuite retiré seulement pour Ollama | Deux HTTP 400, aucun succès Desktop | PARTIAL ; arrêt, pas de troisième inférence |
| `free-groq/qwen3.8-27b` | Aucun effort qualifié annoncé | Pas d'inférence nouvelle ; mapping composant O/M→Low, Max→High | Aucun niveau appliqué observé | PARTIAL conversion ; trajet Desktop NOT_TESTED |
| `free-groq/gpt-oss-120b` | Idem | Même conversion Groq | Non observé | PARTIAL conversion ; trajet Desktop NOT_TESTED |
| `free-openrouter/dots-3-note-preview:free` | Idem | Composant conserve none/minimal/low/medium/high ; Max→High | Non observé | PARTIAL conversion ; trajet Desktop NOT_TESTED |
| `free-openrouter/north-mini-code:free` | Idem | Même conversion FreeLLMAPI/OpenRouter | Non observé | PARTIAL conversion ; trajet Desktop NOT_TESTED |
| `free-mistral/ministral-8b-2512` | Aucun effort qualifié annoncé | Effort absent dans le tour réel, aucune valeur/budget oMLX envoyée | Réponse `OK.`, tour completed, request `4f893daa0b184b4883bcc2879d9a0fab` | VERIFIED génération Desktop ; contrôle d'effort UNSUPPORTED par l'adaptateur FreeLLMAPI actuel |
| `free-mistral/codestral-2508` | Aucun effort qualifié annoncé | Pas de nouvelle inférence ; effort supprimé par FreeLLMAPI selon test de composant | Non observé | UNSUPPORTED pilotage d'effort ; trajet Desktop NOT_TESTED |
| `free/task-fast` | Aucun niveau commun garanti annoncé | Pas de nouvelle inférence ; conversion dépend du membre | Non observé | PARTIAL composants ; trajet Desktop NOT_TESTED |
| `free/task-coding` | Idem | Dépend du membre | Non observé | PARTIAL composants ; trajet Desktop NOT_TESTED |
| `free/task-reasoning` | Idem | Dépend du membre ; nom reasoning sans garantie | Non observé | PARTIAL composants ; trajet Desktop NOT_TESTED |
| `free/task-long-context` | Idem | Dépend du membre | Non observé | PARTIAL composants ; trajet Desktop NOT_TESTED |
| `paid-openrouter/deepseek-v4.1-flash-1017` | Aucun effort qualifié annoncé | Aucun appel ; mapping hors réseau conserve la demande sauf Max→xhigh dans LiteLLM | Identité, droits, budget et route seulement | VERIFIED administratif ; inférence/effort NOT_TESTED |
| `paid-openrouter/glm-5.3` | Idem | Aucun appel ; même conversion Max→xhigh ; Off non revendiqué | Idem | VERIFIED administratif ; inférence/effort NOT_TESTED |
| `paid/task-advanced` | Idem | Aucun appel ; alias DeepSeek, pas de modèle de secours | Idem | VERIFIED administratif ; inférence/effort NOT_TESTED |

Le catalogue affiche quinze routes raccordées, **pas quinze générations
qualifiées**. Une entrée visible n'est pas une preuve d'utilisation réussie.
Les tables de conversions précédentes restent valables : Max n'est jamais
présenté comme effectivement appliqué lorsque High/xhigh arrive au fournisseur
ou lorsque le paramètre est ignoré. Aucun budget numérique Qwen transposé.

### Tests, échecs conservés et arrêt ciblé

- **9 tests nouveaux d'adaptateur PASS** : contrôles locaux/cloud séparés,
  protocoles fonctions/namespaces/custom, historique parallèle, état incomplete,
  annulation fermant l'amont, refus PAID sans attestation, option Ollama isolée.
- **2 tests nouveaux de rollback PASS** : préservation de modifications étrangères,
  refus d'un conflit sur les entrées possédées avant écriture.
- **2 tests témoins légers witness-a PASS**, requis par AGENTS pour la modification
  de configuration. Pas de relance des batteries MCP historiques.
- Outil réel : thread `01a15e15-f045-7232-88c3-2b28c189f836`, exécution
  `/bin/bash -lc 'printf P3A_TOOL_OK'`, sortie `P3A_TOOL_OK`, code **0**, puis
  reprise du modèle et réponse finale identique. Deux requêtes LiteLLM
  `chatcmpl-66a03f43` et `chatcmpl-2a5d50cf`.
- Deux premiers tours ont échoué **avant inférence**, respectivement sur
  `unsupported_tool_type:namespace` puis `unsupported_tool_type:web_search`.
  Inventaire complet ensuite capturé contre un mock, traduction qualifiée hors
  inférence, puis essai réel réussi. Erreurs non effacées.
- Ollama : `/api/show` confirme modèle présent, outils/thinking/completion.
  Test hors réseau de LiteLLM installé : `UnsupportedParamsError`,
  `ollama_chat does not support parameters: ['parallel_tool_calls']`.
  Ce paramètre est retiré uniquement de cette route, pas de `drop_params=true`
  global. L'essai corrigé reçoit encore **HTTP 400**. L'erreur restante n'est
  pas expliquée par cette seule correction ; pas de troisième essai.
  Aucun téléchargement de modèle ni changement de configuration moteur.

La délégation locale de revue a utilisé le MCP historique avec succès
(`chatcmpl-6ebc5410`), sans en changer source/configuration/binaire. Ce travail
de revue n'est pas une relance du scénario MCP de validation initial.

### Préservation GPT et composants hors périmètre

Empreintes avant/après identiques pour `~/.codex/config.toml`, `auth.json`,
instructions globales, binaire `local_llm`, LaunchAgents Ollama et oMLX,
et source du mapping OpenClaw. Toutes les entrées GPT sont identiques au
snapshot d'activation ; politique d'auto-review inchangée.
`openai_base_url` est toujours **http://127.0.0.1:11434/api/codex/v1**,
`model=gpt-6.1-sol`. Aucun remplacement du proxy ni modification de sa source.
RTK demeure non activé ; OpenClaw et Agent Standup non modifiés par ce lot.

**Cela prouve la préservation de configuration, pas une nouvelle validation de
génération GPT native.** Le chemin ChatGPT historique documenté plus haut reste
la preuve disponible ; aucun nouveau tour GPT n'a été lancé pour la renouveler.

La référence historique `muse-glimmer:30b-mlx` reste dans le routage/fallback
d'auto-review existant. Elle n'est ni publiée par l'adaptateur, ni ajoutée au
sélecteur, ni appelée dans la recette. Un blocage global de Muse-Glimmer n'est
donc pas démontré. La supprimer avec son fallback changerait cette politique
existante pouvant concerner GPT : **non exécuté conformément à la condition
d'arrêt utilisateur**. Ce point demande une décision distincte, pas une
modification silencieuse du comportement GPT.

### Rollback exécuté et réactivation vérifiée

Le rollback a été exercé sur la configuration active après les recettes :
modèles/catalogue et routes restitués **à l'identique par slug**, deux services
arrêtés et leurs LaunchAgents retirés. L'ordre JSON peut différer, pas les valeurs
des entrées. Les tests de conflit vérifient qu'une modification étrangère n'est
pas écrasée. Puis `start`, `activate`, `schedule` et un cycle `sync` ont réussi.
L'état final conserve donc **l'option B active**, pas l'état de rollback.

```sh
python3 codex/litellm-adapter/manage.py rollback
```

La commande arrête d'abord le synchroniseur pour empêcher une réactivation
automatique, restaure seulement les entrées possédées, puis arrête l'adaptateur.
Elle conserve snapshots et clés DIRECT existantes, ne révoque rien de P3-B et
ne restaure jamais un ancien `config.toml` global. En cas de conflit : arrêt
et réconciliation manuelle, pas d'écrasement. Fermer les sessions LiteLLM avant
rollback/recharger Desktop ensuite : les anciens sélecteurs restent chargés
dans leurs processus jusqu'au redémarrage. Ne pas forcer le redémarrage d'une
application hébergeant une session en cours.

### Preuves et suite minimale

`artifacts/llm-router-p3a/option-b/` (ignoré par Git) :
`identity-budget.json`, `direct-catalogues.json`, `desktop-final-models.json`,
`desktop-lightweight-*.json`, `desktop-tool-roundtrip.json`, `desktop-free-mistral.json`,
deux échecs `desktop-ollama*.json`, `omlx-wire.jsonl`, `omlx-budget-wire.jsonl`,
`spend-native.json`, `adapter-activity.json`, `adapter-tests.txt`,
`rollback-tests.txt`, `rollback-live.json`, `preservation-before.json`,
`preservation-after.json`, `ollama-capabilities.json`,
`ollama-parameter-diagnostic.json`, captures mock et scripts de recette.
La copie versionnable `llm-router-models.json` correspond au catalogue final,
sans les credentials de routage qui restent seulement dans les fichiers privés.

**BLOCKER :** Ollama encore HTTP 400 après correction ciblée, et qualification
graphique à chaud/efforts cloud non établie.
**EVIDENCE :** deux tours Desktop Ollama `failed`, deux HTTP 400 de l'adaptateur ;
le second ne contient plus parallel_tool_calls. Autres preuves ci-dessus.
**ATTEMPTS :** recette réelle initiale ; présence/capacités lues sans inférence ;
reproduction de l'incompatibilité de paramètre par fonction LiteLLM hors réseau ;
correction locale puis un seul nouvel essai réel. Arrêt de cette branche.
**NEXT REQUIRED ACTION :** récupérer l'erreur structurée restante de LiteLLM/Ollama
sans nouvelle génération, puis décider du correctif ciblé sur preuve. Redémarrage
Desktop à un moment choisi pour contrôle graphique. Aucun test payant sans nouvel
accord spécifique ; pas de P3-C. **P3-A reste PARTIAL.**


## Diagnostic final Ollama — lecture seule, sans troisième inférence

**Cause démontrée : dépassement du contexte effectif du moteur Ollama.**
Le second refus n'est pas une répétition de l'incompatibilité
`parallel_tool_calls` du premier essai. Aucun nouveau POST d'inférence n'a été
émis pour ce diagnostic ; seules les preuves locales et l'API native de lecture
`GET /spend/logs` de LiteLLM ont été consultées.

### Corps structuré retrouvé et corrélation

L'enregistrement LiteLLM `e1b6e801-ab2d-40ce-b2ec-b4cd9ac716b1`, modèle
`ollama_chat/qwen3:4b-instruct`, est `failure`, du **21 octobre 2026
10:55:27.728 à 10:55:30.380 UTC** (12:55:27–30 Europe/Paris).
`error_information` contient `error_code=400`, `error_class=BadRequestError`,
`llm_provider=ollama_chat` et `normalized_error=400_INVALID_REQUEST`.
Dans `error_message`, `Ollama_chatException` conserve le corps fournisseur
imbriqué suivant, présenté ici après décodage des chaînes JSON :

```json
{"error":{"code":400,"message":"request (4489 tokens) exceeds the available context size (4096 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":4489,"n_ctx":4096}}
```

Ce n'est pas une capture HTTP brute : le corps est conservé dans l'exception
structurée de LiteLLM. Son traceback est tronqué par le stockage LiteLLM,
mais les champs d'erreur et le message ci-dessus sont présents.
Preuve filtrée : `artifacts/llm-router-p3a/option-b/ollama-second-error.json`.

Corrélation : adaptateur `request_id=6a0fa8877df6c6f9c54c1f51`,
`time=1792580127.642476`, durée 2747 ms, `requested_effort=null`,
`omitted_parameters=["parallel_tool_calls"]`, HTTP 400 ; tour Desktop
`01a15e1a-09db-7571-8024-02f1184f8ae7`, session/thread
`01a15e1a-09d3-7311-8467-30cac73689d3`.
La correspondance repose sur modèle, intervalle et erreur ; aucun identifiant
unique propagé de bout en bout n'a été conservé par l'adaptateur.

Le journal natif `~/.ollama/logs/launchd-serve.log` confirme à 12:55:30
`POST /api/chat` **400**, puis `POST /api/codex/v1/responses` **400**.
`launchd-serve-error.log` montre le runner Qwen lancé avec `-c 4096`,
`n_ctx_slot=4096`, `task.n_tokens=4489`, puis `send_error` avec le même message
et `stop processing: n_tokens=0`. Extrait filtré conservé dans
`ollama-second-engine-error.txt`. Le refus est donc généré par le moteur
`llama-server` derrière Ollama ; Ollama l'enveloppe, LiteLLM le propage sous
`BadRequestError`, l'adaptateur remplace son détail par `litellm_http_error`.
Il n'est pas produit par une validation de paramètre de l'adaptateur.

L'API retrouve aussi le premier refus, identifiant
`b2a97044-15f7-44b4-8d49-c9cff8126619`, 10:51:03 UTC :
`UnsupportedParamsError` pour `parallel_tool_calls`, généré par LiteLLM.
Cela confirme les **deux causes distinctes**.

### Correction proposée — non appliquée

Pour le seul alias **`local-ollama/qwen3:4b-instruct`**, configurer
`num_ctx: 8192` dans ses `litellm_params` existants. Conserver tous les autres
champs de cette entrée, son identité et ses contrôles financiers ; aucun réglage
global Ollama, aucun changement GPT, Qwen oMLX, FREE ou PAID. Le réglage doit
rester propre à cette route, sans élargir le catalogue de capacités annoncé.

Le composant LiteLLM consulté déclare `num_ctx` comme taille de contexte et
construit le corps Ollama avec `options: optional_params` ; la cible de transport
est donc `options.num_ctx=8192` sur `/api/chat`. Ce passage devra être vérifié
sur la version effectivement déployée avant activation. À l'inverse,
`max_tokens`/`max_completion_tokens` deviennent `num_predict` : augmenter ces
champs ne corrige pas la taille du contexte. Aucun budget de raisonnement n'est
en cause : l'effort était absent.

8192 est une proposition bornée permettant au prompt observé de 4489 tokens
et à une réponse courte de tenir ; sa capacité réelle, son coût mémoire et la
marge pour les conversations longues restent **NOT_TESTED**. Le contexte effectif
de 4096 est prouvé, mais l'origine exacte de ce défaut (modèle, environnement ou
configuration) n'est pas déterminée et n'est pas nécessaire pour proposer cette
surcharge de route. Ne pas tronquer silencieusement les messages/outils.

Après validation utilisateur seulement : préparer le diff de cette unique entrée,
vérifier hors inférence la transformation en `options.num_ctx`, puis autoriser
une unique recette courte sur le chemin Desktop complet et constater le contexte
réellement appliqué. Aucun succès fonctionnel Ollama n'est déclaré à ce stade.
Rollback ciblé proposé : restaurer la valeur antérieure de `num_ctx` de cette
entrée (ou retirer uniquement ce champ s'il était absent), selon le mécanisme
normal de déploiement LiteLLM. Le rollback global de l'option B reste distinct.

**État final : diagnostic VERIFIED ; correction proposée NON APPLIQUÉE ;
route Ollama fonctionnelle NOT_TESTED après correction ; P3-A PARTIAL.**
Aucun troisième essai, aucun appel payant, aucun changement actif, aucun
commit/push. RTK, OpenClaw, Agent Standup, MCP historique, `local_llm`,
`drop_params` global et routes GPT non modifiés. Arrêt après ce diagnostic.


## Politique de contexte Ollama 128K — qualification avant activation

La demande actuelle **remplace la proposition précédente à 8192** : cible globale
`OLLAMA_CONTEXT_LENGTH=131072`, cible Qwen `num_ctx=131072`, surcharges persistantes
par modèle dans LiteLLM. **Aucun de ces changements n'est activé** : capacité du
modèle compatible, mais coexistence mémoire non qualifiée dans l'état observé.
Aucune nouvelle génération ni chargement de modèle n'a été provoqué.

### Provenance exacte de 4096 et priorités

Le LaunchAgent actif `~/Library/LaunchAgents/org.gangneux.ollama-serve.plist`
porte explicitement `EnvironmentVariables.OLLAMA_CONTEXT_LENGTH="4096"`.
La capture historique `diagnostics/ollama-max-models-20261020/launchagent-before.plist`
contenait déjà cette valeur. L'auteur/date d'introduction initiale ne sont pas
établis ; la source effective de la limite observée, elle, est identifiée.
`/api/show` Qwen n'annonce aucun `num_ctx` dans ses paramètres ; l'API native
LiteLLM `/model/info` confirme l'absence de ce champ sur sa route active.
Le runner du second refus était lancé avec `-c 4096` et a constaté
`n_ctx_slot=4096`. **EmbeddingGemma n'est pas la cause de cette limite.**

La source Ollama locale (`server/routes.go:modelOptionsWithEmbeddingBatchDefault`)
établit l'ordre : défaut global → GenerationDefaults → paramètres du modèle
→ `request.options`. Une valeur par requête peut donc remplacer la politique.
EmbeddingGemma possède explicitement `num_ctx=2048`, `num_batch=2048` et une
capacité déclarée de 2048 : cette surcharge reste prioritaire sur le futur défaut
global, tant qu'un client ne fournit pas une autre valeur. Aucun de ses paramètres
ni artefacts n'a été modifié.

### Valeurs demandées, transmises et réellement appliquées

| Objet | Valeur demandée | Transmission qualifiée | Application réelle observée | Statut |
|---|---:|---|---|---|
| Défaut global Ollama | 131072 | Candidat LaunchAgent avec cette unique variable modifiée ; non chargé | 4096 dans le LaunchAgent actif et le runner du second refus | PARTIAL / activation différée |
| `local-ollama/qwen3:4b-instruct` | 131072 | LiteLLM installé 1.104.5 : test pur `get_optional_params` puis `OllamaChatConfig.transform_request` produit `options.num_ctx=131072`, sans envoi réseau | 4096 pour la requête existante ; 131072 non chargé | Transformation VERIFIED ; application 128K NOT_TESTED |
| `embeddinggemma:latest` | conserver 2048 | Paramètre natif persistant `num_ctx=2048` ; route LiteLLM sans surcharge | Runner historique `-c 2048` ; pas de nouvelle allocation/test embeddings | Paramètres préservés VERIFIED ; application après changement global NOT_TESTED |
| oMLX, GPT et autres fournisseurs | inchangés | Aucun champ de contexte modifié | Preuves antérieures conservées ; aucun nouveau test d'inférence | Préservation de cette intervention |

Qwen annonce dans son GGUF `qwen3.context_length=262144` : 131072 ne dépasse
pas cette **capacité déclarée**. Cela ne prouve ni l'allocation possible avec les
autres consommateurs ni la qualité à 128K. Ne pas annoncer un 128K appliqué.
Le test de transformation porte sur le composant **effectivement déployé**, pas
seulement une déclaration JSON. Il ne prouve pas encore un POST Desktop→Ollama
à cette valeur, puisqu'aucun nouveau POST n'a été autorisé ici avant qualification.

L'adaptateur reconstruit une liste explicite de champs dans `chat_request` et
n'envoie ni `num_ctx` ni `extra_body` vers LiteLLM. La route peut donc fournir
la valeur centrale sans changement du code Codex. Le routeur LiteLLM fusionne
cependant les paramètres de déploiement puis les kwargs client : une requête
Chat Completions directe peut potentiellement remplacer le défaut. **Ce réglage
est un défaut configurable, pas une limite inviolable pour tous les clients.**
Aucune garantie universelle d'absence de surcharge n'est revendiquée. Un contrôle
strict par identité demanderait une politique serveur séparée, non ajoutée ici.
`max_tokens`/`max_completion_tokens` deviennent `num_predict`, pas `num_ctx`.

### Mémoire : raison de la non-activation

Le LaunchAgent ne définit aucun `OLLAMA_KV_CACHE_TYPE` ; le défaut documenté par
la source Ollama est F16. Le lancement observé n'ajoute aucun `--cache-type-k/v`.
D'après les métadonnées Qwen (36 couches, 8 têtes KV, dimensions K/V 128),
l'estimation du seul cache est :

`131072 × 36 × 8 × 128 × 2 (K+V) × 2 octets = 18 Gio`.

À 4096, la même estimation est 0,5625 Gio : hausse potentielle d'environ
**17,44 Gio par séquence**, hors poids, buffers, checkpoints et autres allocations.
La quantification Q4_K_M des poids ne quantifie pas automatiquement le cache KV.
Ne pas modifier le type du cache pour faire tenir le changement sans décision.

Le Mac possède 48 Gio. À la collecte : swap utilisé **6867,56 Mio** sur 8192 Mio,
compresseur **439423 pages de 16 Kio**, pages wired **1765203**, et
`memory_pressure -Q` indique 29 % de mémoire libre selon sa métrique (ce n'est pas
une réserve GPU garantie). Les journaux oMLX à 12:51 indiquent une empreinte
physique proche de **20,03 GB**, poids **19,95 GB**, plafond dynamique **30 GB**,
avec throttling/insufficient_headroom déjà observés. Ce relevé oMLX est historique
horodaté, pas une nouvelle mesure d'allocation simultanée à 128K.
Au chargement Qwen de 12:55, Ollama rapportait seulement **8,3 Gio libres**.

Ces données ne démontrent pas une impossibilité absolue de 128K, mais ne
permettent pas de qualifier sa coexistence avec oMLX ; activer ce défaut sans
marge pourrait provoquer pression mémoire, swap ou refus d'allocation à la
prochaine requête. Le code `usesAutomaticNumCtx` et
`reduceAutoNumCtxForLoadOOM` montre en outre qu'une valeur explicite désactive
la réduction automatique du contexte à l'OOM. Ne pas compter sur une réduction
silencieuse à 4096 pour protéger le Mac. Aucun stress test ni changement oMLX,
concurrence, cache KV ou limite de modèles chargés n'a été réalisé.

Référence : [contexte Ollama](https://docs.ollama.com/context-length) — un
contexte supérieur augmente la mémoire nécessaire ; la version locale inspectée
reste la référence pour les priorités et le comportement de cette installation.

### Candidats réversibles et centralisation

Sous `artifacts/llm-router-p3a/ollama-context-policy/` (ignoré par Git) :
`qualification.json`, `launchagent-before.plist`,
`launchagent-candidate-NOT-ACTIVE.plist`, `route-change-PROPOSED.json`.
Le candidat plist a été reparsé et comparé ; seule la valeur globale est changée.
Le document de route est un **diff conceptuel, pas un payload API à appliquer
aveuglément**. Les preuves de transformation et de relecture des trois routes
proviennent du script de lecture `option-b/context-readonly.py`.

Architecture retenue pour l'activation future : un défaut global dans le
LaunchAgent, puis `litellm_params.num_ctx` dans le déploiement natif existant de
chaque modèle nécessitant une surcharge. Pour Qwen : déploiement existant
`867c15c5-d096-4f1e-b5ac-3781a56d6083`, ajouter uniquement `num_ctx=131072` via
l'API officielle de gestion en préservant tous ses autres paramètres. Ne pas
recréer le modèle. L'API `/model/info` reste la source centrale relue ; aucune
liste de contextes par modèle ne doit être dupliquée dans l'adaptateur Codex.
La synchronisation actuelle du catalogue n'est pas qualifiée pour refléter
automatiquement ce champ dans les limites affichées par Desktop : l'admission
prudente 8192 de ce catalogue reste inchangée et ne doit pas être appelée 128K.

Rollback futur ciblé : restaurer uniquement la variable globale à sa valeur
avant modification (4096 dans cette capture), puis recharger le LaunchAgent à
un moment sans session active ; retirer uniquement la surcharge `num_ctx` ajoutée
à la route Qwen si elle était absente avant activation. Préserver les autres
modifications concurrentes, ne pas restaurer aveuglément un ancien plist complet.
EmbeddingGemma et oMLX ne font partie ni de l'activation ni du rollback de route.

**BLOCKER :** marge mémoire de coexistence oMLX + Qwen 128K non qualifiée.
**EVIDENCE :** cache KV estimé 18 Gio, swap déjà utilisé, observations mémoire
horodatées ci-dessus ; absence de test d'allocation simultanée.
**ATTEMPTS :** lecture configuration/capacités/logs et priorités ; relevé mémoire ;
transformation pure sur LiteLLM déployé. Aucune inférence, aucun essai répété pour
faire passer l'allocation.
**NEXT REQUIRED ACTION :** décider d'un mode d'exploitation mémoire compatible
avec 128K (créneau sans concurrence oMLX, ou étude d'un cache KV quantifié avec
qualification distincte), puis qualifier une allocation ciblée avant génération.
Ces options ne sont ni activées ni garanties ici. Aucun réglage oMLX modifié.

**P3-A reste PARTIAL.** Politique demandée préparée, application non effectuée ;
global actif 4096, Qwen appliqué historiquement 4096, EmbeddingGemma 2048 préservé.
Pas de redémarrage du proxy qui transporte GPT. Pas de test témoin requis par
une modification active : aucune configuration n'a été modifiée. Aucun appel
payant, téléchargement, recréation de modèle, modification RTK/OpenClaw/MCP
historique, commit ou push.


## Correction Qwen3 4B à 8192 — déploiement et arrêt sur échec Desktop

**Décision utilisateur appliquée :** défaut global Ollama **4096 inchangé**,
Qwen3 4B **8192 sur sa seule route LiteLLM**, EmbeddingGemma **2048 inchangé**,
oMLX **131072 conservé sans modification ni requalification**. Cette décision
remplace les candidats 128K de la section précédente ; ils restent inactifs.
Pas de cache KV quantifié, téléchargement ou recréation de modèle.

### Configuration et imposition serveur

PATCH officiel `/model/867c15c5-d096-4f1e-b5ac-3781a56d6083/update`, limité à
`{"litellm_params":{"num_ctx":8192}}`. Relecture native `/model/info` : 8192.
Empreintes de toutes les autres entrées avant/après PATCH identiques. Modèle
stocké nativement en base LiteLLM, aucune écriture directe en base. Le snapshot
reproductible `infrastructure/deployments/litellm/local-models.json` reflète ce seul
ajout Qwen ; les autres entrées sont conservées.

Un défaut de route seul étant remplaçable par le client, un callback documenté
`async_pre_call_deployment_hook` impose 8192 **après la fusion des paramètres**.
Source : `infrastructure/deployments/litellm/qwen_context.py`, instance
`qwen_context.policy`. Il cible uniquement `ollama_chat/qwen3:4b-instruct` à
`http://172.29.2.27:11434`, corrige `num_ctx` direct et les valeurs contradictoires
imbriquées dans `extra_body`/`options`, et empêche la suppression de ce champ via
`additional_drop_params`. Les autres déploiements sont retournés inchangés.
Ce n'est pas une modification globale de `drop_params` ou des permissions.

Configuration du callback persistée dans le fichier YAML et montée par config
Swarm immuable `litellm_qwen_context_v1`, avec
`litellm_config_qwen8k_v1` pour le YAML. Les sources du dépôt et du répertoire
normal `/srv/docker-local/compose/litellm/` concordent. Un rechargement de la
seule gateway a été nécessaire pour installer le callback ; readiness 200,
conteneur healthy ensuite. PostgreSQL est resté sur sa tâche démarrée cinq heures
auparavant. Aucun redémarrage Ollama, oMLX ou application Desktop effectué.

Après redémarrage réel de la gateway : relecture du modèle **8192**, et import du
callback depuis son chemin réellement monté puis passage dans le dispatcher
installé : valeur cliente **131072 ramenée à 8192**. Trois tests purs dans
LiteLLM **1.104.5** réussis : surcharges None/4096/131072 avec champs imbriqués,
non-modification des autres modèles, transformation fournisseur en
`options.num_ctx=8192`. Deux tests témoins `unittest discover -s witness-a`
réussis. Ces tests n'émettent aucune inférence.

L'adaptateur Codex n'a pas été modifié : son allowlist ne transmet pas de
`num_ctx` client ni de `extra_body`. Il ne réinjecte donc pas 4096. La valeur est
ajoutée et imposée dans LiteLLM. La protection est qualifiée sur ce déploiement
et les formes de paramètres testées ; aucun test réseau contradictoire générant
une inférence supplémentaire n'a été effectué.

Référence du mécanisme : [callbacks LiteLLM](https://docs.litellm.ai/docs/observability/custom_callback),
section Per-Attempt Deployment Hooks ; présence et invocation vérifiées dans la
version installée. Aucun fork de LiteLLM ni modification de son code interne.

### Paramètres et preuve effective

| Niveau | Valeur / preuve | Qualification |
|---|---|---|
| Globale Ollama | `OLLAMA_CONTEXT_LENGTH=4096` ; empreinte LaunchAgent identique au diagnostic précédent | VERIFIED, inchangé |
| Route Qwen native LiteLLM | `litellm_params.num_ctx=8192`, relu avant et après redémarrage | VERIFIED |
| Surcharge cliente | Callback déployé, dispatcher testé 131072→8192 ; tests imbriqués et suppression | VERIFIED hors inférence |
| Requête LiteLLM → Ollama | Capture HTTP filtrée : modèle `qwen3:4b-instruct`, `options={"num_ctx":8192}`, `stream=false`, **12 outils** | VERIFIED |
| Runner Ollama | `/api/ps` : `context_length=8192`, `size_vram=3856589127`, digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` | VERIFIED |
| Traitement supérieur à 4096 | Premier succès : **4719 tokens d'entrée**, 15 de sortie | VERIFIED, 4719 < 8192 |
| EmbeddingGemma | Paramètres existants 2048 conservés, aucune modification de sa route | Préservation ; aucune nouvelle inférence |
| oMLX / GPT / raisonnement | Aucun paramètre modifié ; pas de nouvelle inférence de contrôle | Préservation de cette intervention |

L'estimation KV F16 à 8192 est **1,125 Gio** (contre 18 Gio à 128K). Ce calcul
ne remplace pas la mesure : le runner observé déclare environ **3,59 Gio** de
`size_vram`. Aucun stress test concurrent oMLX n'est revendiqué.

### Unique tour Desktop : contexte corrigé, fin de tour échouée

Un seul tour a été lancé manuellement via l'app-server du binaire embarqué
Desktop 0.163.0-alpha.10.2, avec authentification existante et trajet
Desktop → proxy 11434 → adaptateur 11439 → LiteLLM → Ollama. Aucun appel outil
n'était demandé, mais les **12 outils** restaient présents dans la requête.
Ce test ne requalifie pas un aller-retour d'exécution d'outil Ollama.

Session `01a15e39-6a83-7662-bdb3-e32038ed7419`, tour
`01a15e39-6b3c-7d32-bc76-c654186bbfd8`. Consigne : produire un titre court
sur la correction du contexte. Titre affiché :
**« Correction du contexte Qwen3 4B pour OpenClaw »**.

**Transparence sur le nombre réel d'appels :** ce tour unique a provoqué
**trois requêtes backend automatiques**, et non une seule génération serveur.
Aucune relance manuelle n'a été faite. Les deux premières ont réussi :

- `chatcmpl-8d9ba067-b208-4954-a29b-4aeb988ee89a`,
  11:29:44.423–11:29:50.569 UTC, 4719 tokens prompt / 15 sortie ;
- `chatcmpl-d634b19d-5375-4ad9-b87f-75f830d5576d`,
  11:29:50.925–11:29:51.163 UTC, 4737 tokens prompt / 1 sortie.

La troisième, `568aeae1-d09a-4ef5-a340-b8ac4b7a1ed4`,
11:29:51.713–11:29:52.012 UTC, échoue avec `BadRequestError`, HTTP 400,
corps fournisseur décodé depuis `error_information` de l'API native `/spend/logs` :

```json
{"error":{"code":400,"message":"Cannot have 2 or more assistant messages at the end of the list.","type":"invalid_request_error"}}
```

Le refus actuel concerne la **structure d'historique acceptée par le backend
Ollama**, pas le dépassement de 4096. La raison pour laquelle Desktop a poursuivi
après le premier titre n'a pas été diagnostiquée dans ce lot : ne pas attribuer
une cause protocolaire sans preuve. Aucune correction de l'historique ni nouvelle
inférence entreprise après cet échec, conformément à la consigne d'arrêt.
La capture réseau, bornée volontairement à une requête, ne couvre que le premier
appel. Les trois statuts sont corrélés via activité adaptateur et journaux natifs
LiteLLM, pas extrapolés à partir de cette seule capture.

### Persistance, synchronisation et compatibilité OpenClaw

La persistance **après redémarrage LiteLLM est VERIFIED** pour le champ natif et
le montage du callback. Le synchroniseur Codex existant agit sur catalogue/routes
Codex, pas sur les déploiements natifs LiteLLM ; aucun changement de son code.
Toutefois le cycle de synchronisation demandé n'a **pas été déclenché ni qualifié
après ce test** : arrêt sur échec Desktop prioritaire. Pas de nouveau redémarrage
pour prolonger la recette. La limite prudente 8192 déjà annoncée dans le catalogue
Codex n'a pas été modifiée.

Lecture seule d'OpenClaw : `agents.defaults.utilityModel` vaut actuellement
`ollama/qwen3:4b-instruct`, et Pro/Perso autorisent aussi leurs alias LiteLLM
`local-ollama/qwen3:4b-instruct`. Le titre court produit établit l'aptitude bornée
à cet usage ; **aucun parcours de génération de titre déclenché par OpenClaw
n'a été exécuté**. Le chemin natif `ollama/...` peut contourner LiteLLM : le
callback de cette route ne lui impose pas 8192. Ne pas prétendre qu'un réglage
exclusivement LiteLLM force la valeur des requêtes natives OpenClaw. L'agent,
ses configurations Pro/Perso et le provider Ollama sont restés inchangés.

### Preuves et rollback ciblé

`artifacts/llm-router-p3a/qwen8k/` : `route-update.json`, `wire.jsonl`,
`runner.json`, `activity.json`, `validation.json`, `preservation.json`,
`openclaw-readonly.json`, scripts de déploiement/contrôle.
Tour complet : `option-b/desktop-ollama-8k-final.json`.
Sources : `qwen_context.py`, `test_qwen_context.py`, YAML, stack et snapshot
`local-models.json` dans `infrastructure/deployments/litellm/`.

Préimages serveur : `/srv/docker-local/compose/litellm/p3a-qwen8k-before/`
contient `config.yaml` et `stack.yml`. Rollback **non exécuté** :

1. Retirer seulement `qwen_context.policy` des callbacks et sa config montée,
   restaurer la référence YAML antérieure `litellm_config_v2` après vérification
   qu'aucun changement concurrent ne serait écrasé ; redéployer normalement la
   gateway, conserver toutes les autres configurations.
2. Via PATCH officiel du même modèle, retirer la surcharge ajoutée avec
   `litellm_params.num_ctx=null` (suppression native à requalifier par relecture),
   ou rétablir une valeur explicitement validée. Ne pas effacer le déploiement.
3. Relire `/model/info` et la santé de la gateway. Les configs Swarm antérieures
   restent présentes ; ne pas supprimer les objets partagés ou secrets.

**État final :** Qwen route configurée, transmise et réellement appliquée à
**8192 VERIFIED** ; dépassement de l'ancienne limite 4096 traité. **Validation
Desktop complète FAILED**, compatibilité OpenClaw native et synchronisation
**NOT_TESTED**. Le critère global de la mission n'est donc pas déclaré atteint ;
**P3-A reste PARTIAL**. Aucun appel payant, modification budgets/permissions,
RTK, OpenClaw, Muse-Glimmer, MCP historique, niveaux de raisonnement, commit/push.
Arrêt après récupération de l'erreur structurée et documentation, sans nouvelle
inférence.


## Correction multi-tour Ollama — historique, outils et fin de réponse

**Incident corrigé et qualification ciblée VERIFIED.** Un seul tour Desktop réel
après identification de la cause et validation hors inférence : deux requêtes
Ollama réussies, appel d'outil exécuté (exit 0), résultat repris puis réponse finale,
sans reconnexion. **8192 reste imposé et appliqué**, global Ollama 4096 inchangé.
Ce résultat remplace le statut FAILED du tour précédent pour cet incident ; il
ne requalifie pas les limites cloud/UI ou les autres critères P3-A antérieurs.

### Cause initiale démontrée : réponse SSE incomplète dans notre adaptateur

Les événements `error` conservés dans
`option-b/desktop-ollama-8k-final.json` donnent, pour les deux premiers succès
backend, `willRetry=true`, puis exactement :

`stream disconnected before completion: failed to parse ResponseCompleted: missing field reasoning_tokens`

L'adaptateur `response_object` produisait
`usage.output_tokens_details={}` lorsque LiteLLM/Ollama ne fournissait pas
`completion_tokens_details`. Desktop avait déjà reçu le message assistant,
mais ne pouvait pas parser la fin `response.completed`. Il relançait donc la
requête en conservant cet historique. Après deux réponses assistant, la nouvelle
requête échouait côté moteur Ollama sur la fin d'historique.

**Composants responsables :** le défaut initial de protocole Responses est dans
**l'adaptateur local** ; **Desktop** ajoute les réponses reçues et déclenche ses
relances automatiques après erreur de parsing. Notre conversion reproduit les
rôles fournis, LiteLLM les conserve ; le refus HTTP 400 est généré par le
`llama-server` derrière Ollama. Rien ne justifie de supprimer les messages côté
proxy, de fusionner tous les assistant, ou de modifier les routes fonctionnelles.

Le parseur du **binaire Desktop 0.163.0-alpha.10.2** a été testé sans fournisseur
avec une réponse simulée produite par le correctif : `completed`, **une requête
mock, aucune erreur**. Le tour réel corrigé ne présente ensuite aucune relance,
ce qui confirme le lien causal sans nouvelle génération exploratoire.

### Reconstruction historique : preuve et limites

Les corps complets des trois anciennes requêtes n'étaient pas enregistrés ; la
capture de cette ancienne recette ne conservait que modèle/options/nombre
d'outils pour le premier appel. Le stockage LiteLLM avait les prompts désactivés.
Il est donc **impossible de reconstruire rétrospectivement tout le préfixe, les
rôles exacts et les IDs d'outils des trois requêtes**. Ne pas présenter comme
observées des structures déduites. Aucun contenu de prompt n'a été extrait ou
recopié dans les nouvelles preuves.

| Ancienne requête | Structure effectivement observable | Déduction limitée |
|---|---|---|
| `chatcmpl-8d9ba067-b208-4954-a29b-4aeb988ee89a` | Desktop : message utilisateur puis message assistant ; HTTP 200, 4719 tokens d'entrée, 15 de sortie | Préfixe HTTP exact non conservé ; aucun outil exécuté observable |
| `chatcmpl-d634b19d-5375-4ad9-b87f-75f830d5576d` | Reconnexion 1 après `reasoning_tokens` absent ; second message assistant ; HTTP 200, 4737 tokens d'entrée, 1 de sortie | Ajout/reprise du premier assistant lors du retry compatible avec les traces ; liste HTTP exacte non conservée |
| `568aeae1-d09a-4ef5-a340-b8ac4b7a1ed4` | Reconnexion 2, puis erreur fournisseur `Cannot have 2 or more assistant messages at the end of the list.` | Le garde du moteur établit deux rôles assistant en fin de liste ; leurs IDs exacts ne sont pas récupérables |

Preuve nouvelle dérivée sans texte : `incident-structure.json`, avec types des
items, phases et erreurs de parsing seulement. Les fichiers historiques d'origine
sont conservés tels quels ; aucun duplicata de leurs prompts n'a été créé.

### Contraintes Ollama et perte d'IDs dans LiteLLM

L'API Ollama locale accepte `Message.Role`, `ToolCalls[].ID`, `ToolCallID` et
`ToolName` (`api/types.go`). Son pont `llamaServerChatMessage` transmet ces
associations au runner. Le refus de deux assistant **en fin** est une contrainte
de continuation/prefill du backend `llama-server`, pas une interdiction générale
de tous les messages assistant adjacents dans toute API Ollama.

Le code amont primaire [llama.cpp, garde de continuation](https://github.com/ggml-org/llama.cpp/blob/a97cce86a8addeb9f40cba7a261c94b1f0c576cb/tools/server/server-common.cpp#L1215)
active la continuation d'un dernier assistant lorsque le prefill est actif et
rejette deux assistant terminaux ; il rejette aussi la continuation d'un assistant
porteur d'appels d'outils non résolus. Ce commit est une référence amont explicite,
pas une affirmation d'identité du binaire installé avec ce commit. L'installation
locale a réellement retourné le message correspondant dans sa réponse structurée.
Le template GGUF a été lu en mémoire pour diagnostic ; la chaîne de refus n'y
figure pas. Aucun template ni réglage de prefill n'a été modifié.

LiteLLM **1.104.5 installé**, `OllamaChatConfig.transform_request`, conserve les
rôles et `tool_call_id` des résultats, mais reconstruit les tool calls assistant
avec nom/arguments **sans recopier leur ID**. Un test pur sur ce composant démontre
l'absence d'ID avant correctif, puis sa présence après le complément ciblé.
Ce défaut d'association est distinct de la cause initiale des retries.

### Correctifs appliqués, limités à Qwen3 4B

Dans `codex/litellm-adapter/adapter.py`, uniquement pour
`local-ollama/qwen3:4b-instruct` :

- compléter `usage.output_tokens_details.reasoning_tokens` par l'entier **0**
  quand le fournisseur omet ce détail ; conserver une valeur fournie. Ce zéro est
  un **défaut de protocole**, pas une mesure de pensée ni un changement de niveau
  de raisonnement. La trace le marque `reasoning_tokens_protocol_default=true` ;
- traduire aussi les items `custom_tool_call`/`custom_tool_call_output` en appels
  de fonctions et résultats en conservant `call_id`, namespace et arguments ;
- rattacher les items d'appels adjacents à leur message assistant de texte du
  même segment d'appel. Texte et tous les appels sont conservés ; **deux messages
  assistant textuels distincts ne sont ni joints ni supprimés** ;
- associer chaque résultat par son `call_id`, même si les résultats arrivent hors
  ordre ; rejeter explicitement les IDs dupliqués, résultats sans appel ou appels
  sans résultat dans une requête de reprise destinée au modèle ;
- tracer seulement types/rôles et IDs d'association à l'entrée, après conversion,
  et à la sortie. Aucun texte, argument, résultat textuel ou header ajouté aux
  nouvelles traces structurelles.

Dans le callback existant `infrastructure/deployments/litellm/qwen_context.py`,
uniquement pour le déploiement `ollama_chat/qwen3:4b-instruct` à sa base existante :
conserver la transformation officielle LiteLLM puis restaurer les IDs des tool
calls et `tool_name` des résultats via `extra_body.messages`, mécanisme de
surcharge post-transformation pris en charge par le handler installé. Pas de fork,
monkeypatch ou modification des sources internes LiteLLM. Correspondance stricte
un-à-un ; pas de changement des contenus. L'imposition `num_ctx=8192` reste dans
ce même callback, sans réduction ni augmentation.

Le code du callback est livré comme config Swarm immuable
`litellm_qwen_context_v2`, instance et YAML inchangés. Un rechargement gateway
était nécessaire pour charger cette version ; readiness **200**. L'adaptateur
seul a été rechargé par `launchctl kickstart -k` puis `/health=ok`. Pas de
redémarrage Ollama, oMLX, Desktop, MCP ou de changement du proxy historique.

### Validation hors inférence

- **16 tests adaptateur** PASS, dont cinq nouvelles régressions : détail d'usage
  absent/None/réel et maintien des autres routes, appels parallèles + custom et
  résultats inversés, conservation de l'historique terminal problématique sans
  fusion aveugle, rejets d'associations incohérentes et absence de texte dans les
  traces. L'historique synthétique `[user, assistant, assistant]` reste intact :
  le correctif empêche le retry fautif, il ne réécrit pas arbitrairement l'entrée.
- **4 tests dans LiteLLM installé** PASS : maintien 8192 contre surcharges clientes,
  autres modèles inchangés, transformation contexte et restauration effective des
  IDs par surcharge post-transformation. Le test d'IDs conserve aussi texte,
  arguments et résultats synthétiques sans les remplacer.
- **2 tests témoins** PASS.
- **Un tour mock Desktop** PASS : aucun fournisseur appelé, une requête et aucune
  reconnexion. Ce mock n'est pas une inférence supplémentaire.

### Tour réel unique et structure des deux requêtes

Session `01a15e46-a276-7be1-ba02-3d291b5aec19`, tour
`01a15e46-a334-73b0-b6e7-4ca29abecb89`, durée **9074 ms**, statut **completed**.
Consigne technique bornée : un seul outil de commande locale inoffensif, puis
conclusion. Le harnais interrompt sur une erreur annonçant un retry ; cette
condition n'a pas été rencontrée. La qualification utilise l'app-server du binaire
Desktop embarqué avec le trajet proxy historique → adaptateur → LiteLLM → Ollama ;
elle ne constitue pas une nouvelle recette graphique de la fenêtre Desktop.

| Requête | Structure réellement capturée à l'entrée Ollama | Résultat natif LiteLLM |
|---|---|---|
| 1 | `system, system, user, user` ; 12 outils disponibles ; `options.num_ctx=8192` | `chatcmpl-2484b08f-f0d6-483e-a6dd-2881fa9b8772`, success, prompt 4742 / sortie 33, coût 0 |
| 2 | Même préfixe, puis `assistant(tool_calls[id=C])`, `tool(tool_call_id=C, tool_name=exec_command)` ; 12 outils ; `options.num_ctx=8192` | `chatcmpl-c6f3a261-81f8-4fea-9eff-b81cd95e2dfe`, success, prompt 4832 / sortie 12, coût 0 |

`C = XjWxt0ZTGXaVXSuN4Jo6PsG4ZXAW1Cq9` : identique dans la réponse d'appel,
l'item Desktop `commandExecution`, le replay Responses, le Chat Completions,
et **la requête native `/api/chat` réellement capturée**. Commande exécutée avec
`exitCode=0`, puis réponse assistant finale. Aucune troisième requête, aucune
reconnexion, aucune erreur. Les arguments et le résultat textuel réels de l'outil
ne sont pas archivés : le test prouve l'exécution et l'association par ID ; les
contenus sont contrôlés par les tests synthétiques et transitent en mémoire.

Relecture `/api/ps` après le tour : Qwen **context_length=8192**. Donc le détail
usage corrigé et la restauration des IDs n'annulent pas le contexte imposé.

### Préservation et limites

LaunchAgent Ollama identique à son empreinte de référence : global **4096**,
pas de cache KV quantifié ajouté. Configuration OpenClaw identique à l'empreinte
relevée lors du lot précédent. EmbeddingGemma, oMLX, GPT, Mistral, autres alias,
niveaux de raisonnement, permissions et budgets n'ont fait l'objet d'aucune
écriture dans ce lot. Aucun appel à RTK, OpenClaw, `llm-router` ou `local_llm`.

La relecture `/model/info` concorde avec les anciennes empreintes pour tous les
alias hors Qwen, **sauf Muse-Glimmer** : cette référence date du lot précédent,
pas d'une préimage immédiate de cette intervention. Contrôle ciblé : Muse est
**`blocked=true`** ; il n'a été ni réactivé ni appelé. Ne pas attribuer à ce lot
une variation d'empreinte antérieure/concurrente sans audit ; aucune tentative de
restauration ou d'écriture sur ce modèle. Cette réserve de comparaison reste
explicite, même si les seules mutations exécutées ici concernent l'adaptateur et
le callback Qwen.

Les appels parallèles/custom et les résultats hors ordre sont **qualifiés hors
inférence**. Le seul tour réel a utilisé un appel de fonction unique suivi de son
résultat et d'une conclusion ; pas de revendication de validation réelle de tous
les outils ni des longues conversations. Les anciennes listes complètes des
messages HTTP restent irrécupérables. Ces limites ne remettent pas en cause le
reproche initial démontré et sa correction vérifiée.

### Preuves et rollback ciblé conservant 8192

Preuves filtrées : `artifacts/llm-router-p3a/ollama-multiturn/` :
`incident-structure.json`, `mock-parser.json`, `desktop-tool-qualification.json`,
`adapter-structure.json`, `wire.jsonl`, `server-readback.jsonl`,
`preservation.json`, `final-validation.json` et scripts de recette. Capture
fermée après sa durée bornée ; pas de pcap, corps HTTP brut, prompts, arguments
ou résultats textuels sauvegardés. Fichiers temporaires de test distants retirés.

Préimages locales `adapter.py.before`, `test_adapter.py.before`,
`qwen_context.py.before` dans ce dossier de preuves ; préimages serveur
`/srv/docker-local/compose/litellm/p3a-multiturn-before/` pour callback et stack.
Rollback **non exécuté** :

1. Revenir uniquement sur les blocs de conversion/usage/traces Ollama ajoutés
   dans l'adaptateur, d'après la préimage, après contrôle des modifications
   concurrentes. Recharger seulement son LaunchAgent et vérifier `/health`.
2. Restaurer la référence de config callback de **v2 à v1** dans le stack normal
   et son fichier source précédent, sans toucher au YAML, aux autres configs,
   secrets ou routes ; redéployer seulement les changements nécessaires à la
   gateway et vérifier readiness.
3. **Ne retirer ni `litellm_params.num_ctx=8192` ni sa règle d'imposition** : la
   version v1 du callback les conserve déjà. Global 4096 et EmbeddingGemma 2048
   restent également inchangés. Le rollback de ce lot réintroduirait le défaut
   de parsing/IDs connu ; ne pas le présenter comme une correction alternative.

**Résultat de ce lot : VERIFIED**, incident multi-tour résolu sur le trajet réel
qualifié. Aucun autre tour d'inférence lancé ; aucune inférence payante, aucun
commit/push. Arrêt après cette validation. Les critères P3-A hors de ce lot
conservent leurs qualifications et limites précédentes ; pas de P3-C.
