# Ponytail — évaluation et intégration ponctuelle (2026-10-21)

## Décision

Pas d'installation globale du plugin. Alternative préparée : [référence à la demande](ponytail/ponytail.md), hors des répertoires de découverte des skills. Aucun hook, aucune activation automatique, aucune configuration existante modifiée. Cette référence est utilisable explicitement dans Desktop et CLI ; son chargement automatique et les commandes du plugin ne sont pas disponibles.

Source examinée : [DietrichGebert/ponytail v5.3.2](https://github.com/DietrichGebert/ponytail/tree/v5.3.2), commit `16352ac229eb08a9598dcae48fe9f2b342567d86`, publication du 16 octobre 2026. `main` observé au commit `09c434ab73ca43761c5d8b0c5d341926c2fba710` diffère déjà du tag sur le manifeste et certains hooks. L'évaluation utilise le tag, pas une branche flottante. Corps officiel conservé sans modification, hors métadonnées, et licence MIT jointe ; une adaptation de portée explicite limite son effet à la tâche.

## Modes et intégration officielle

- `lite` : réaliser la demande et présenter une option plus simple à l'utilisateur ; ce mode peut introduire un arbitrage humain inutile pour nos tâches déjà autorisées.
- `full` : défaut ; réutilisation, bibliothèque standard, fonctionnalités natives, dépendances installées, puis changement minimal complet.
- `ultra` : remet aussi en question le besoin ; risque de friction avec l'autonomie demandée.
- `off` : désactive le mode via les hooks ; ne retire pas rétroactivement les instructions déjà présentes dans l'historique.
- Six skills : ponytail, review, audit, debt, gain, help. Les variantes review/audit élargissent les axes de contrôle, sans remplacer les validations du dépôt.

L'[installation officielle Codex](https://github.com/DietrichGebert/ponytail/blob/v5.3.2/INSTALL.md) ajoute un marketplace et un plugin, demande la confiance dans les hooks et un nouveau fil ; Desktop requiert un redémarrage selon l'amont. Elle n'a pas été exécutée.

Le [manifeste](https://github.com/DietrichGebert/ponytail/blob/v5.3.2/.codex-plugin/plugin.json) charge les six skills et `hooks/claude-codex-hooks.json`. Ce fichier déclare **trois événements**, malgré le texte amont « two lifecycle hooks » : SessionStart, SubagentStart et UserPromptSubmit, avec timeout de 5 secondes par commande sur ce tag. SessionStart injecte le corps filtré, active le mode et tente une carte du code. Le runtime Codex reconnaît `PLUGIN_DATA` et y stocke son état. Les hooks n'ont pas été exécutés lors de cette mission.

## Interactions vérifiées

| Élément existant | Recouvrement / choix |
|---|---|
| AGENTS.md global et règles du dépôt | Réutilisation, changement minimal, préservation des travaux, tests proportionnés déjà présents. Ne pas copier l'AGENTS.md amont par-dessus les nôtres. |
| Skills | La description amont vise toute tâche de code : une installation globale ajouterait un déclencheur très large. Référence préparée hors découverte automatique. |
| RTK | Compression des seules commandes autorisées ; Ponytail agit sur les décisions de code. Aucun préfixe MCP ni changement RTK. |
| Graphify | Navigation existante réutilisée selon les règles ; carte automatique Ponytail redondante, non déployée. Aucune indexation supplémentaire nécessaire pour ces fichiers connus. |
| llm-router | Délégation et paramètres de raisonnement inchangés. L'adaptation leur donne explicitement priorité. Aucun fallback ni accès payant ajouté. |
| Approbations et sécurité | Aucun changement de config, de confiance dans les hooks ou de règles d'exécution. Le pilote CLI utilise le sandbox read-only, sans bypass. |
| Tests et validation | Le minimum de code ne réduit pas les contrôles nécessaires. La référence amont conserve les garde-fous et son exigence de vérification de logique non triviale. |

La [documentation OpenAI sur les skills](https://developers.openai.com/blog/skills-agents-sdk) distingue métadonnées de découverte et chargement du corps à l'activation. Notre fichier n'est pas installé comme skill : il n'ajoute même pas de métadonnées au contexte habituel. Taille de la référence ponctuelle : **3 930 octets UTF-8**, mesurés, sans assimilation à un nombre de tokens.

Context7 a été consulté (`/dietrichgebert/ponytail`) ; ses extraits confirment les voies plugin/skills, mais les sources du tag font foi pour le nombre d'événements et les timeouts. L'essai de récupération de la documentation OpenAI au format `.md` a été refusé par l'outil web pour son type MIME ; la page HTML officielle avait déjà été consultée. Aucun contournement.

## Recette et preuves

Pilote natif Codex CLI **0.160.0**, modèle demandé `gpt-6.1-sol`, raisonnement `low`. Deux sessions éphémères indépendantes, ordre A puis B, chacune contenant les mêmes trois cas synthétiques : helper de configuration existant, déduplication Unicode dans une fonction partagée avec deux appelants, résolution de fichiers avec frontière de sécurité et liens symboliques. A = instructions existantes ; B = mêmes instructions plus référence ponctuelle. Prompts neutres, sans consigne de déléguer.

Le contexte est fourni dans le prompt : cette recette mesure la production et la validation de petits changements, pas une exploration réelle de dépôt ni une intégration de hooks. Le code produit n'est pas appliqué au dépôt. Les deux sessions conservent la configuration utilisateur, les règles d'exécution et les MCP ; seules les options modèle/effort, sortie JSON et sandbox read-only sont explicites.

Les vérifications fonctionnelles indépendantes comprennent : identité AST du helper, appel réel à ce helper, comportement historique des flottants, rejets d'entrées, Unicode, conservation de l'ordre et des entrées, deux appelants, type de retour, traversée de répertoires, liens internes/externes/cassés, absences et répertoires. Les tests générés sont examinés puis exécutés séparément si réalisable ; ils ne servent pas seuls de juge.

Les preuves locales sont conservées sous [artifacts/ponytail-20261021](../artifacts/ponytail-20261021/) (ignoré par Git) : sources épinglées et empreintes, prompts exacts, schéma JSON, runner `run_ab.py`, réponses et événements JSONL A/B, `metrics.json`, validateur `validate_ab.py`, résultats et empreintes des fichiers protégés. Une preuve ignorée par Git reste locale : elle doit accompagner ce rapport pour transporter la recette.

### Analyse préparatoire déléguée

Appel réel `llm-router.submit` avant l'analyse correspondante : tâche `321eab63-a085-4da6-b0c5-d0a1849e8a14`, modèle local sélectionné `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit`, effort medium, sans cloud ni secret. Résultat terminé en **86,860 s**, 3 450 tokens totaux déclarés par le routeur. Modèle fournisseur : **alias seulement, non confirmé**.

Résultat **rejeté** : mécanismes et métriques inventés (`config.ponytail.enabled`, masquage dynamique, `rtk.token_stats`, `graphify.traverse_log`, offset ±120 ms). La recette a été reprise directement, sans seconde délégation. Ce coût préparatoire est distinct des mesures A/B. Aucun résultat délégué n'est traité comme preuve métier.

## Résultats mesurés

| Mesure | A : actuel | B : référence ponctuelle | Écart B/A |
|---|---:|---:|---:|
| Lignes de code non vides (trois fichiers complets) | 40 | 36 | −10,0 % |
| Tokens de sortie déclarés par Codex | 3 058 | 2 609 | −14,7 % |
| Tokens d'entrée cumulés | 105 145 | 81 392 | −22,6 % |
| Dont entrée en cache | 78 848 | 54 656 | caches différents |
| Entrée hors cache (différence arithmétique) | 26 297 | 26 736 | +1,7 % |
| Temps mural de la session CLI, démarrage inclus | 57,210 s | 57,945 s | +1,3 % |
| Contrôles indépendants réussis | 27/27 | 27/27 | égalité |
| Suites de tests produites, exécutées ensuite | 3/3 | 3/3 | égalité |
| Lignes de tests fournies, non vides | 56 | 46 | observation, pas critère de qualité |
| Classes ajoutées / dépendances tierces | 0 / 0 | 0 / 0 | égalité |

Pertinence : les deux variantes réutilisent exactement le helper existant et corrigent la déduplication dans la fonction partagée. B remplace le couple liste/ensemble par un dictionnaire ordonné avec `setdefault`, ce qui explique les quatre lignes gagnées ; les deux solutions restent lisibles et passent les cas Unicode, itérateurs et appelants. Les deux protègent les chemins par résolution puis vérification d'appartenance par composants, sans comparaison fragile de préfixes de chaînes.

Les sessions ont chacune exécuté un appel de commande. Le témoin a signalé un refus du heredoc implicite en lecture seule, puis a utilisé `python3 -c` ; ce bruit de harness participe au résultat et n'est pas une performance intrinsèque de Ponytail. Les deux ont fourni sans exécuter les fixtures de fichiers/liens dans leur session. Après revue du code et des tests générés, **les six suites ont été réellement exécutées par l'orchestrateur**, dans des répertoires temporaires supprimés automatiquement, en plus des 54 contrôles indépendants au total.

**Conclusion bornée :** réduction de code et de sortie observée sur ce pilote, aucune accélération observée, aucune économie d'entrée hors cache. Les entrées cumulées dépendent des tours d'outils et du cache ; elles ne mesurent ni un coût facturé ni le seul coût de la référence. Aucun tarif ou montant économisé n'est inféré. Un essai par variante, ordre fixe A→B, trois cas regroupés par session, instructions/skills existants nombreux et charge machine non contrôlée : aucune significativité, aucune causalité générale et aucune extrapolation aux pourcentages publicitaires amont.

Les six empreintes protégées sont identiques avant/après : AGENTS.md du dépôt et de codex/, copie des instructions globales du dépôt, .gitignore, config.toml et AGENTS.md utilisateur. La référence a été vérifiée hors découverte automatique, avec corps officiel inchangé. Aucun moteur ni service n'a été reconfiguré ; le test témoin de configuration n'était donc pas requis. Aucun commit ni push.

**NOT_RUN :** interface Desktop, plugin global, confiance/exécution des hooks, niveaux persistants, tâches sur un dépôt réel à explorer, campagne statistique, recette de délégation dans chacune des sessions A/B et effet en production. La délégation préparatoire est bien réelle mais a été rejetée, comme décrit plus haut. La présence inchangée des règles MCP et d'approbation n'est pas une qualification end-to-end de leur exécution.

## Utilisation proposée, sans déploiement global

Dans une nouvelle session Desktop ou CLI, demander explicitement :

> Pour cette tâche, lis `codex/ponytail/ponytail.md` et applique sa référence ponctuelle, puis réalise : [demande].

Depuis un autre dépôt, fournir le chemin absolu `/Users/fngux2/Workspaces/mac-ia-local/codex/ponytail/ponytail.md`. Il s'agit du comportement **full**, avec un transport léger sans hook ; ce n'est pas une simulation du mode `lite`. L'intensité n'est pas le niveau de raisonnement du modèle. Aucune commande `/ponytail` ni persistance de mode n'est promise. Les six skills et l'interface band/board ne sont pas installés ; l'amont décrit band/board pour Claude Code.

## Rollback

Aucun état global à restaurer. Pour cesser l'usage, ne plus appeler la référence et commencer un nouveau fil : les instructions déjà chargées restent dans l'historique du fil courant. Pour supprimer les livrables, retirer uniquement `codex/ponytail/ponytail.md`, sa `LICENSE` et ce rapport après vérification qu'ils n'ont pas été modifiés depuis ; les preuves locales peuvent être archivées puis supprimées séparément. Ne pas lancer le désinstalleur global amont : il n'a rien installé ici et intervient sur d'autres emplacements.
