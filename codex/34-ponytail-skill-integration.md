# Ponytail — skill natif global et attribution du 401

Mission du 21 octobre 2026. Ce rapport prolonge [l'évaluation initiale](33-ponytail-evaluation.md), sans réécrire sa capture historique.

## Installation

Skill installé dans `/Users/fngux2/.codex/skills/ponytail/` ; source maintenable dans [ponytail/skill](ponytail/skill/). Quatre fichiers : `SKILL.md`, `agents/openai.yaml`, `references/ponytail.md`, `LICENSE`. Aucun plugin, hook, carte du code, service ou réglage de modèle ajouté. `allow_implicit_invocation: true`. La découverte native passe de 18 à 19 skills, sans erreur ; Ponytail apparaît une seule fois, actif, de portée `user` et sans plugin associé.

Le corps de la référence et la licence sont repris à l'identique de [la référence évaluée](ponytail/ponytail.md) et sa licence MIT : DietrichGebert/ponytail 5.3.2, commit `16352ac229eb08a9598dcae48fe9f2b342567d86`. L'entrée du skill adapte explicitement la portée et la priorité : tâche courante uniquement, maintenabilité et analyse suffisante avant longueur du diff, aucun mode persistant ou changement de niveau. Les formulations amont « shortest diff wins » et « whole session » ne font pas autorité sur ces précisions.

Déclenchement : création/modification de code d'application, bibliothèque ou outil de développement ; refactorisation et simplification ; invocation explicite `$ponytail`. Exclusions automatiques : diagnostics d'infrastructure, incidents de production, administration système, configuration seule, explication de code et revue sans modification. L'invocation explicite reste possible. La sélection automatique est une décision du modèle, pas un filtre déterministe garantissant tous les prompts futurs.

Les règles utilisateur et AGENTS.md global/local restent prioritaires, notamment délégation MCP llm-router, RTK, Graphify, approbations et validations. Le skill les référence sans les recopier. L'installation ne les modifie pas.

## Origine exacte du HTTP 401

La requête refusée était **une sonde ad hoc de l'orchestrateur Codex**, lancée par `exec_command`, puis exécutée par un processus Python avec `urllib.request.urlopen(url, timeout=10)`. La boucle ciblait `/health` puis `/v1/models` sur `127.0.0.1:8000`. Aucun objet Request, aucun en-tête Authorization et aucun credential n'étaient fournis. Résultats conservés dans la conversation : health `healthy`, models **HTTP 401 Unauthorized**. La lecture du listener a identifié `omlx-server`, PID 49904, sur ce port.

Cet appel **n'a pas été déclenché** par le lanceur LOCAL/FREE, le serveur MCP llm-router ou LiteLLM. Il visait à découvrir un modèle local pour le pilote CLI ; c'était un choix de diagnostic inadapté à l'architecture de délégation, et non une preuve de panne du routeur. L'absence d'authentification côté client est établie ; aucune clé existante n'a été rejetée puisque cette sonde n'en envoyait pas. Le détail interne de la décision serveur n'a pas été relu dans les journaux oMLX.

### Chemins distingués

| Chemin | Preuve / statut |
|---|---|
| Sonde fautive : Codex → exec_command → Python urllib → `127.0.0.1:8000/v1/models` | Appel exact et HTTP 401 observés ; aucun nouveau GET ou essai d'authentification pendant la reprise. |
| Délégation : Codex → MCP llm-router (`router.py --config ~/.config/llm-router/codex.json`) → `https://litellm.gangneux.org/v1` | Configuration active `identity=codex`, `isolated_local_only=false` ; code catalogue `/models` et génération `/chat/completions` dirigés vers LiteLLM avec sa clé dédiée. |
| `local_url=http://127.0.0.1:8000/v1` dans le routeur | Paramètre d'une branche de secours explicitement conditionnée par `isolated_local_only`; cette branche est inactive. Aucun fallback direct ajouté. |
| LiteLLM → alias local oMLX | Tâche MCP terminée avec backend local et en-têtes LiteLLM ; alias sélectionné conservé. Le dernier saut fournisseur n'a pas été nouvellement corrélé aux journaux LiteLLM/oMLX. |
| Lanceur `codex/scripts/llm-router-direct.py` | Mode **DIRECT** documenté : sélection du modèle natif Codex via adaptateur `127.0.0.1:11439`, puis LiteLLM. Distinct du MCP ; non exécuté pour le 401 ni cette reprise. Il ne prouve pas une délégation directe vers oMLX. |
| Recettes natives CLI | Configuration habituelle : modèle demandé GPT-6.1-Sol, proxy `127.0.0.1:11434/api/codex/v1`, authentification déclarée `chatgpt`. Aucun nouveau provider réel oMLX ni route tierce PAID sélectionné. |

Trace réelle existante de la revue de déclenchement : tâche `972f5a7a-a96c-4292-95d2-95fc19a82c62`, requête `chatcmpl-114e6ede`, `x-litellm-call-id=e012fc63-7512-422d-9e4c-34553984427a`, retries/fallbacks déclarés à zéro. `actual_model=null`, `provider_model_confirmation=alias_only_unconfirmed` : ne pas transformer l'alias en preuve du modèle physique exécuté.

**Correction appliquée au diagnostic :** abandon de la sonde directe et de l'hypothèse d'un routage MCP cassé. Aucune correction de configuration n'est justifiée par ces preuves ; aucune n'a été faite. Aucun secret lu pour être transmis, aucune clé LiteLLM injectée dans oMLX, aucun changement d'authentification ou d'autre agent.

Deux analyses préparatoires réelles sont identifiées dans les traces MCP : la revue de déclenchement ci-dessus, puis la revue d'attribution `9e2c0615-1bd1-42ed-8cb5-5e85f5ff582f`. La première contient des propositions incomplètes et est écartée ; les critères retenus sont vérifiés par les essais natifs plutôt que validés par cette réponse. La seconde propose de transférer la clé LiteLLM vers la sonde oMLX : **recommandation rejetée**. Ses conclusions non étayées par les champs de modèle sont également écartées. Pas de nouvelle chaîne de délégations.

## Découverte, activation et contexte

Validateur officiel Skill Creator : PASS sur la source et sur l'installation. `skills/list` via le protocole natif app-server : découverte réelle avant/après et invariance des 18 autres métadonnées de skills. Aucun fichier partagé remplacé : le dossier cible était absent, puis créé exclusivement ; un manifeste conserve cet état initial et les SHA-256 des quatre fichiers. Une autre session ouverte n'a pas été traitée comme un conflit.

Trois captures **simulées** utilisent un serveur Responses factice local et des overrides de processus, sans inférence et sans modification de config : avant installation, après installation, invocation explicite. Le serveur temporaire est fermé après chaque capture ; ce n'est ni un routage vers oMLX ni un chemin de délégation.

Résultat : **469 caractères et octets UTF-8 supplémentaires** dans le texte des messages initiaux ; 471 caractères dans sa sérialisation JSON. L'ajout comprend l'entrée de catalogue et une nouvelle racine de chemins abrégés, qui renumérote les alias existants. Coût estimé : environ **120–160 tokens**, sans mesure par tokenizer. Corps du skill et référence absents du contexte initial ordinaire. L'invocation explicite injecte le corps principal ; la référence reste à lire seulement lors de l'application. Aucun marqueur du corps amont dans la capture de démarrage ordinaire.

La description reste visible au démarrage pour permettre la sélection implicite, conformément au [mécanisme natif de découverte progressive](https://developers.openai.com/blog/skills-agents-sdk). L'absence de doublon mesurée porte sur l'injection : une entrée, aucune copie dans AGENTS.md, aucun hook. Des principes conceptuels restent communs aux règles globales et à Ponytail ; ils ne constituent pas une nouvelle politique contradictoire.

Pour le témoin A/B, la désactivation éphémère a été vérifiée avec `-c 'skills.config=[{path="/Users/fngux2/.codex/skills/ponytail/SKILL.md",enabled=false}]'`. Sur cette version 0.160.0, cibler le dossier seul laisse le skill actif ; cibler le fichier déclaré par `skills/list` le désactive. Aucun appel à `skills/config/write`, aucun changement durable du fichier utilisateur. La [référence de configuration](https://developers.openai.com/codex/config-reference/) documente le mécanisme ; l'observation sur la version installée précise ici le sélecteur effectif.

## Pilote comportemental

Deux modifications du code réel `codex/agent-observer/collector.py`, sur copies isolées du module et de sa suite : filtrer les valeurs de tokens rejetées en réutilisant `number()`, et traiter comme UTC les dates ISO sans fuseau dans `stamp()`. Aucun collecteur autonome, service ou stockage applicatif réel lancé/modifié. Les prompts neutres demandent le changement et ses tests sans mentionner Ponytail ni solliciter la délégation.

Quatre nouvelles sessions CLI natives, séquentielles, effort low ; A = skill désactivé uniquement pour le processus, B = skill actif et sélection implicite. Ordre A-usage, B-usage, B-stamp, A-stamp. Les sessions de développement sont en sandbox workspace-write sur leur copie. Les deux contrôles séparés, administration et invocation explicite, sont en lecture seule. Aucun bypass d'approbation ni changement de règle MCP. Les inférences natives consomment l'abonnement Codex existant ; aucun coût supplémentaire d'API PAID n'est inféré ou revendiqué.

Chaque sortie est vérifiée par la suite de la copie, des assertions indépendantes et une comparaison AST des définitions préexistantes hors fonction ciblée. Les métriques viennent des événements CLI ; tokens d'entrée cumulés et cache ne sont pas un tarif ni le coût du seul skill.

| Tâche | Variante | Temps mural | Tokens entrée cumulés | Tokens sortie | Suite complète de la copie | Delta lignes de code |
|---|---|---:|---:|---:|---:|---:|
| `usage()` | A sans skill | 33,064 s | 144 104 | 1 240 | 20/20 | +4 |
| `usage()` | B implicite | 36,475 s | 156 777 | 1 329 | 21/21 | +4 |
| `stamp()` | A sans skill | 35,291 s | 151 599 | 1 533 | 20/20 | +3 |
| `stamp()` | B implicite | 41,221 s | 188 658 | 1 268 | 19/19 | +3 |

Les quatre cas passent également les assertions indépendantes (six pour `usage`, sept pour `stamp`, soit 26 assertions au total). Toutes les autres définitions préexistantes gardent leur AST. Aucun ajout de dépendance : `number()` est réutilisé, et `stamp()` utilise le module `datetime` déjà importé. Les correctifs de dates sont identiques ; les deux correctifs de tokens ont le même comportement, avec deux conditions de compréhension séparées en A et une conjonction en B.

Agrégat de deux tâches : A **68,355 s / 2 773 tokens sortie / 295 703 tokens entrée**, B **77,696 s / 2 597 tokens sortie / 345 435 tokens entrée**. B : **−6,35 % en sortie**, **+16,82 % en entrée cumulée**, **+13,67 % en latence**, même delta de code (+7 lignes). L'entrée hors cache calculée passe de 62 615 à 66 651 (**+6,45 %**). Le cache, les lectures supplémentaires et le nombre de tours empêchent d'attribuer ces écarts au seul coût du skill ; les populations de tests ajoutés diffèrent aussi.

**Résultat métier :** qualité fonctionnelle et réutilisation préservées sur ce pilote ; aucun gain de volume de code ni d'économie globale démontré. Le skill est conservé pour son guidage sélectif demandé, pas pour une promesse de réduction des tokens ou de latence.

**Activation réelle :** B-usage et B-stamp lisent chacun une fois le `SKILL.md` global et une fois sa référence, sans mention du skill dans le prompt. Les deux A ne les lisent pas. Le contrôle d'administration DNS (9,964 s) n'exécute aucune commande et ne charge aucun corps Ponytail. L'invocation `$ponytail` (14,378 s) charge nativement le corps principal, puis le modèle lit la référence une fois. Ces deux contrôles ne sont pas inclus dans l'agrégat A/B. Aucun item MCP n'apparaît dans ces six sessions CLI ; les deux délégations préparatoires sont distinctes et identifiées plus haut. Ce constat ne qualifie pas le déclenchement des délégations pour une mission plus complexe.

**Préservation :** les six empreintes protégées sont inchangées (AGENTS.md racine, AGENTS.md codex/, copie globale du dépôt, référence évaluée, AGENTS.md et config.toml utilisateur). Le collecteur réel est identique au baseline. Les deux tests témoins `python3 -m unittest discover -s witness-a -q` passent. Les quatre fichiers installés correspondent au manifeste et à la source, sans fichier supplémentaire. Les six arbres de copies temporaires ont été supprimés après conservation des baselines, des diffs de code/tests et des journaux. Aucun commit ni push.


## Desktop et limites

Interface Desktop non pilotable avec les capacités disponibles dans cette session : **NOT_RUN** pour activation dans une fenêtre Desktop. Aucun redémarrage de l'application ou interruption d'une session en cours. L'installation utilisateur utilise le mécanisme natif commun ; cela ne prouve pas le rafraîchissement de la fenêtre déjà ouverte. Une nouvelle session doit découvrir le skill ; sa validation UI reste à faire.

Les essais couvrent deux petits changements réels, pas une qualification statistique, tous les types de code ou un incident de production. Le choix automatique reste probabiliste. Les captures factices prouvent le contenu envoyé par le client, pas une décision de modèle. Les contrôles CLI réels complètent séparément cette preuve.

## Rollback

Commencer par vérifier les quatre empreintes dans `artifacts/ponytail-skill-20261021/install-manifest.json` et l'absence de fichiers ajoutés par un tiers. En cas de différence, préserver le contenu et examiner le conflit avant retrait. Si elles correspondent, retirer uniquement le dossier `/Users/fngux2/.codex/skills/ponytail/` (ou l'archiver hors de tout dossier de découverte des skills), puis démarrer une nouvelle session. Les corps déjà chargés restent dans l'historique d'un fil existant. La source du dépôt peut rester disponible pour réinstallation. Aucun config.toml, AGENTS.md, hook ou service à restaurer ; ne pas exécuter le désinstalleur du plugin amont.

Preuves détaillées locales : [artifacts/ponytail-skill-20261021](../artifacts/ponytail-skill-20261021/) : captures, inventaires, schémas natifs, manifeste, prompts/événements/diffs et résultats des tests. Dossier ignoré par Git : l'emporter avec le rapport pour conserver les preuves brutes.
