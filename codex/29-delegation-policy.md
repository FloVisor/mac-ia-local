# Politique de délégation Codex / llm-router — 21 octobre 2026

Politique déployée ; chemins réels local et gratuit validés sur les tâches décrites.
Sélection avancée validée avec doubles uniquement : aucune route actuelle n’a de
qualification avancée démontrée. Pas de promesse de qualité universelle.
Aucun appel facturé, commit/push, modification Desktop, OpenClaw, Agent Standup,
RTK, moteur, clé, permission MCP ou budget. P3-A/P3-C/P4 non rouverts.

## Diagnostic et changements

| Avant | Après / raison |
| --- | --- |
| Premier modèle compatible local/free/paid ; pas d’estimation de tâche | Type + complexité, contexte, capacités vérifiées et qualifications opérateur ; local prioritaire, aucune proposition payante automatique |
| Profils de consignes uniquement | Profils conservés ; ils ne constituent pas une qualification avancée |
| Cloud soumis à accord par tâche ; aucune détection de secrets | Même contrôle + `contains_secrets`, détecteur conservateur, contrôle avant dispatch ; secrets locaux même avec accord Cloud |
| Une seule tentative, résultats invalides rejetés | Rejet conservé ; récupération bornée à deux appels ; erreurs/tokens par tentative dans les métadonnées |
| JSON demandé seulement dans le texte | Groq : `response_format=json_object` pour `quality.kind=json`, validation stricte conservée |
| Instructions globales générales | Décision avant analyse profonde, trivial direct, tâches ordinaires Qwen, arbitrage GPT, gratuit justifié, paiement lié à la mission et techniquement fermé |

Pourquoi Qwen dominait : priorité locale volontaire, contexte 128K contre 8192
admis conservativement pour les gratuits ; profils sans différenciation de capacité,
aucune capacité avancée qualifiée, aucun fallback après échec. Pas de sélection
forcée par le profil. Catalogue réel : Qwen local, Groq Qwen3.8 27B, Mistral
Ministral 8B ; aucun pool ni OpenRouter Free visible/qualifié. Rien ajouté pour
simuler leur disponibilité. Distant ne signifie pas meilleur.

`advanced` exige `qualified_advanced_tasks` contenant le type demandé ; tous les
membres d’un pool doivent aussi satisfaire contexte, capacités, disponibilité et
qualification. Sans qualification : `return_to_gpt=true`, zéro inférence.
`trivial` et `strategic` reviennent également à GPT sans inférence ; ce sont des
indications de l’orchestrateur, pas une classification sémantique automatique.

Récupération : réponse tronquée/vide/invalide ou HTTP 502/503/504 → autre route
compatible non payante, sous accord Cloud et sans secrets. À défaut, un unique
retry local sur ces trois erreurs HTTP. Aucun changement/retry d’un modèle
explicitement imposé. Auth, quota, catalogue refusé ou envoi incertain : arrêt,
pas de contournement. Aucun troisième appel ni relance externe pour la même tâche.

## Fichiers

Modifiés :

- `~/.codex/AGENTS.md` : seule section de délégation ; reste identique à la préimage.
- `codex/global-instructions.md` : même section synchronisée, reste préservé ; copie documentaire, pas une deuxième source chargée.
- `mcp/llm-router/router.py` : contrat, sélection, confidentialité, récupération et adaptation JSON Groq.
- `mcp/llm-router/README.md` : contrat actif et limites.

Créés : `mcp/llm-router/test_delegation_policy.py`, ce rapport.
Preuves/sauvegardes privées : `artifacts/delegation-policy-20261021/` (0700).
Configuration active `~/.config/llm-router/codex.json` inchangée, empreinte vérifiée.
Aucun fichier sous `diagnostics/` modifié.

Déploiement : le lanceur existant cible les sources de ce dépôt ; nouveaux workers
et nouveaux processus MCP les chargent. Vérification réelle par les métadonnées
`compatible_local_first`, `output_format_sent` et le nouveau schéma `tools/list`.
Les stdio déjà ouverts peuvent conserver l’ancien schéma : contrat ancien utilisable,
champs étendus disponibles au prochain chargement. Aucun processus concurrent tué.

## Tests déterministes et contrôles

Baseline : 70 tests PASS. Livraison : **87 tests PASS**, dont 17 nouveaux ;
`python3 -m unittest discover -s mcp/llm-router -q`.
Deux tests témoins PASS : `python3 -m unittest discover -s witness-a -q`.
Avertissements ResourceWarning de connexions SQLite non fermées dans les fixtures
existantes conservés ; aucun échec. `git diff --check` PASS.

| Scénario | Preuve / résultat |
| --- | --- |
| Trivial, architecture stratégique | Double : zéro appel fournisseur, orchestrator_required ; arbitrage GPT observé séparément |
| Documentation et revue ordinaires | Double HTTP : modèles réellement envoyés = Qwen |
| Token, mot de passe, clé SSH, Bearer | Double : uniquement local, aucun contenu secret dans activity |
| Secret opaque signalé, local en échec | Double : pas de Cloud ; retry local transitoire au plus une fois |
| Complexité avancée | Double : gratuit effectivement appelé uniquement si qualifié ; sans qualification, zéro appel |
| Local indisponible | Double : gratuit autorisé réellement appelé ; secret reste local |
| Gratuit indisponible / deux réponses invalides | Double : arrêt borné, return_to_gpt |
| « Meilleur modèle », ancien accord/session | Double : aucune destination payante |
| Accord DeepSeek courant, révocation / fin | Double : DELEGATED reste fermé, même avec chaîne d’accord ; aucune consommation |
| Autorisations isolées, expiration, budgets, DIRECT | Tests historiques d’autorisation/courtier simulés inclus ; DIRECT distinct et contrôles conservés |
| Troncature, JSON invalide | Double HTTP : rejet puis route gratuite ; deux échecs restent failed |
| Auth/quota/réseau incertain | Double : aucun second dispatch ; refus du catalogue pendant récupération également bloquant |
| Tâches multiples / identités | Files secret et ordinaire séparées ; tests concurrents et isolation persistante existants PASS |
| Catalogue, contexte, pools, capacités | Tests de compatibilité et de chaque membre ; aucune capacité inconnue admise |
| Groq JSON natif | Paramètre réellement envoyé au double, balises Markdown toujours rejetées |
| Schéma MCP / supervision | Processus neuf : nouveaux champs présents ; collecteur existant en lecture seule retrouve les 3 tâches réelles |

Les budgets Qwen Off/Minimal=0, Low=512, Medium=2048, High=8192, Max=16384,
Ultra=High restent testés sur les payloads réellement reçus par le double.
`max_tokens = réserve réponse + pensée`, admission dans 131072, aucun budget
numérique Qwen appliqué au Cloud. Aucun rebench High/Max, aucun réglage moteur.
Plafond partagé 40 USD/mois et contrôles fournisseur préservés sans réécriture ;
refus budgétaires prouvés en simulation, solde fournisseur réel non relu.

## Recettes réelles et évaluation GPT

| Tâche | Destination / résultat |
| --- | --- |
| Préparation de matrice `d966ea03-80b9-4e1e-ae80-2f9305d43cd6` | Local ; sortie rejetée par GPT : API inventée et critère de confidentialité incorrect. Non utilisée comme recette exécutable |
| Revue ciblée `93c9803b-cd0b-476f-a3d9-40394a4d39eb` | Qwen local via LiteLLM ; JSON conforme, problème de fermeture correctement identifié ; 91 entrée + 58 sortie = 149 tokens, 2643 ms |
| Premier gratuit `9f8ad9df-d041-46d3-884a-ec21009473b7` | Groq via LiteLLM ; 125 tokens, JSON entouré de balises ; **FAILED objective_quality_failed**, preuve d’accès seulement |
| Gratuit après correction API `1285221e-889c-4a5d-9574-4e46410972aa` | Groq via LiteLLM ; JSON natif conforme, choix B et justification corrects ; 86 entrée + 35 sortie = 121 tokens, 527 ms ; **PASS borné** |
| Orchestration `0a61b902-c594-4eef-af2c-2f3f3f93d06c` | Agent natif choisit spontanément catalogue puis revue locale asynchrone ; 1062 tokens dont 512 de pensée, 30179 ms ; arbitrage final conservé chez GPT |

Prompt d’orchestration sans nom de MCP ni modèle imposé : comparaison de trois
méthodes de lecture de configuration, avec décision pour un système critique.
L’agent a conservé B, rejeté l’affirmation erronée sur la suppression d’un fichier
déjà ouvert sous POSIX et nuancé la fuite de ressources. Choix spontané observé,
validation critique observée ; pas de garantie universelle pour chaque futur tour.
Son identifiant de session n’était pas exposé : parent_session null conservé,
aucun rattachement artificiel. Les deux recettes explicites utilisent le vrai
parent `01a15ee9-85a7-7bf0-8ecb-5337970b362c`.

Pour les trois recettes réussies : finish_reason=stop, une tentative par tâche,
headers LiteLLM retries=0/fallbacks=0. Request IDs, identifiants LiteLLM,
usage et résultats privés dans les fichiers `*-evidence.json`.
Modèle fournisseur exact non confirmé : alias retourné, actual_model=null.
Catégories local/free attestées par les routes ; coût observé inconnu, pas zéro
inventé. Trois appels locaux et deux gratuits dans la mission ; aucun payant.

## Limites et protections conservées

- Aucune preuve qu’un gratuit actuel dépasse Qwen en analyse avancée ; métadonnées non inventées. Chemin avancé simulé seulement, retour GPT en production.
- Détection de secrets non exhaustive : opaque/inconnu doit être signalé ou rester local. Ne pas transmettre de secret inutile ; restrictions plus strictes des dépôts conservées. Le contenu transmis est le texte complet de la tâche, y compris les extraits que l’appelant y inclut.
- DELEGATED payant **désactivé**, même avec accord courant : pas d’adaptateurs de production prouvant consentement, borne de coût et coordination DIRECT/DELEGATED. Accord explicite est nécessaire, pas suffisant. Aucun contournement ; pas d’activation dans cette mission.
- Mistral, OpenRouter Free, pools et grandes fenêtres Cloud non requalifiés. JSON Object Groq n’est pas une garantie JSON Schema.
- Agent Standup : projection backend validée sans modification ; affichage webview de ces tâches NOT_RUN. Les tentatives sont disponibles dans l’activité routeur, sans changement du collecteur.

## Rollback

Sauvegardes, empreintes et diffs propres à cette mission dans
`artifacts/delegation-policy-20261021/{preimages,changes,preservation}.json`.

```sh
python3 artifacts/delegation-policy-20261021/rollback.py          # contrôle sans écriture
python3 artifacts/delegation-policy-20261021/rollback.py --apply  # retour arrière
```

Le script vérifie toutes les préconditions avant écriture ; refuse les changements
concurrents des fichiers/blocs possédés. Les instructions sont restaurées par bloc,
en préservant les autres sections. Reconstruction exacte des quatre préimages
vérifiée en mémoire ; rollback actif non exécuté. Tests et rapport conservés comme
preuves. Nouveaux workers après restauration ; nouvelle session pour instructions
et schéma. Aucun budget, clé, service moteur ou application à restaurer.

Sources techniques : [instructions globales Codex](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[mode JSON Groq](https://console.groq.com/docs/structured-outputs).
