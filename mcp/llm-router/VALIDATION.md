# Recette du 21 octobre 2026

## IMPLEMENTED

Serveur `llm-router` indépendant, sept outils MCP, cinq profils compatibles
fonctionnellement, worker détaché et verrou exclusif, idempotence, reprise,
états et récupération paginée. Stockage applicatif privé unique pour tâches,
événements bornés, cache et circuit breakers. Décision locale prioritaire,
confidentialité explicite, contrôle des membres de pools, refus des embeddings
et de Muse-Glimmer. Transport génération SSE, adaptation raisonnement, contrôles
objectifs limités et primitives internes d'autorisations ponctuelles.

## VERIFIED — tests locaux sans facturation

**41 tests PASS** via `python3 -m unittest discover -s mcp/llm-router -q`.
Backend HTTP simulé sur loopback ; les preuves portent sur le routeur, pas sur
la disponibilité réelle des fournisseurs.

Couverture : cinq profils, contrat stdio et requête malformée, provenance/usage,
idempotence et conflit de politique, soumissions concurrentes sans double appel,
annulation en file et demande en cours préservée, état incertain après interruption,
préférence locale, cloud non approuvé refusé, modèle désactivé refusé,
pool incompatible refusé, capacités/contexte refusés, 403 suspendu sans répétition,
429/Retry-After persistant sans répétition, catalogue périmé non utilisé,
raisonnement cloud sans budget numérique inventé, mapping local Ultra,
comparaison objective détectant 8 au lieu de 7, JSON/propriétés et syntaxe Python,
troncature, événements bornés sans marqueur confidentiel ni clé de test,
pagination, isolation Pro/Perso, permissions disque, échéance pré-appel,
reprise après fermeture du client stdio, SSE et interruption sans retry.

Autorisations : accord, refus, expiration avant/après émission, révocation,
réutilisation, mauvais modèle/identité/tâche/périmètre/montant, budget inconnu ou
insuffisant, concurrence avec un seul gagnant. Validation du contrat DIRECT
sans confirmation par appel et refus d'une sélection provenant d'un prompt.
Ce sont des **tests de primitives**, pas une authentification cliente déployée.

## VERIFIED — modèle local réel

Commande `python3 mcp/llm-router/smoke_local.py` : vrai MCP stdio dans un
sous-processus isolé, `initialize` indique `llm-router 0.1.0`, sept outils exposés.
Soumission puis fermeture du client ; résultat récupéré depuis le stockage.

- Task ID observé : `815d8e01-7e35-478e-8bc2-bad0fdfd9290`.
- État `completed`, réponse exacte `OK`, contrôle objectif `passed`.
- Modèle effectif `mlx-community--Qwen3.6-35B-A3B-4bit`.
- `finish_reason=stop`, 35 tokens entrée / 1 sortie / 36 total.
- Durée ponctuelle 458 ms, cinq événements ; ce n'est pas un benchmark.
- Raisonnement demandé `off`, désactivation envoyée, application non confirmée
  par télémétrie (`confirmed=null`). Coût non exposé (`null`).
- Resoumission identique : même tâche, aucun nouveau travail créé.
- Fichiers temporaires supprimés après sortie du worker isolé.

Le test utilise oMLX directement dans le mode de recette explicite, pas LiteLLM.
Aucun restart, panne réelle ou changement de configuration de service.

## VERIFIED — préservation du MCP historique

SHA-256 avant/après, pour source et binaire :
`2e62e38e968ce9dd1b9765180a2003e37dd55aa611b6949705fa2fdd9a5d0625`.

- `mcp/local-llm-mcp/local-llm-mcp.py`
- `~/.codex/bin/local-llm-mcp`

Aucun diff dans `mcp/local-llm-mcp/`. Aucun enregistrement client modifié,
aucun déploiement dans Codex/OpenClaw. Les modifications préexistantes du dépôt
n'ont pas été incluses dans ce lot ; aucun commit/push.

## PARTIAL

- Métadonnées opérateur : exemple limité à Qwen ; autres modèles/pools à qualifier
  et enrichir sans confondre catalogue, fenêtres annoncées et droits effectifs.
- Contrôle contexte conservateur, pas de tokenizer complet des messages.
- JSON/propriétés et AST seulement, pas JSON Schema complet ou tests de code.
- Transport d'outils/vision non implémenté, rejet explicite.
- Échéance pendant génération signalée, pas d'annulation active fournisseur.
- Un worker redémarré marque `unknown` ; pas de supervision LaunchAgent installée.
- Secours local de production fermé : pas de garantie fraîche de non-révocation.
- Adaptateurs de raisonnement cloud non qualifiés ; budgets non envoyés.
- Modèle effectif des pools limité à la provenance exposée par la réponse API.

## Finalisation ciblée — 21 octobre 2026

**Blocage de clé levé. Accès et routage réels LOCAL/FREE VERIFIED. Conformité
stricte des réponses gratuites PARTIAL.** Les 41 tests historiques ci-dessus
n'ont pas été relancés. Trois nouveaux tests ciblés PASS et compilation Python :
lecture sécurisée du fichier, priorité sans changement d'environnement,
refus des permissions trop larges/liens symboliques, préservation privée d'un
résultat rejeté, absence du contenu dans l'activité et distinction alias/provenance.

### Identité, clé et permissions — VERIFIED

Identités existantes relues par API : `mcp-delegate` et
`mcp-delegate-cloud-approved`, rôle `internal_user`, modèles utilisateur vides,
aucune équipe, aucune clé initiale. La mention documentaire « local-only » de
`mcp-delegate` était une politique préparée, pas une restriction serveur à élargir.
L'instruction présente autorise une clé LOCAL/FREE : réutilisation de
`mcp-delegate`, **aucune identité ni politique globale modifiée**.

Une seule clé créée par `/key/generate`, alias `llm-router-local-free`, type
`llm_api`, routes `llm_api_routes`, propriétaire `mcp-delegate`, sans équipe payante.
Relecture persistée par `/key/info` et `/key/list` : exactement une clé, exactement
les 13 alias LOCAL/FREE explicitement autorisés dans les politiques existantes,
aucun wildcard, aucun alias PAID, aucun Muse-Glimmer. Les trois modèles locaux
incluent EmbeddingGemma dans les droits de clé ; le routeur de tâches reste chat-only.
Ni plafond financier ni expiration ajoutés à cette clé non payante ; ce n'est pas
une clé destinée à l'escalade ou à la sélection DIRECTE payante.

Le catalogue authentifié `/v1/models` correspond exactement à cette liste de 13.
Le serveur renvoie **403** sur `paid/task-advanced`, Muse-Glimmer et l'API de gestion
`GET /key/list` avec cette clé. Les sondes de modèles utilisent volontairement un
corps incomplet `model` seul : refus avant inférence, et aucun payload valide de
génération payante envoyé. Les modèles payants restent administrativement dans
LiteLLM ; aucun n'a été bloqué/débloqué pour obtenir ces résultats.

Secret stocké uniquement à `~/.config/llm-router/litellm-local-free.key` (0600),
dossier 0700 ; configuration privée 0600 dans le même dossier. `key_file` est lu
par le nouveau MCP sans export de variable ni modification du MCP historique.
L'administration d'émission est restée sur le serveur ; aucune MASTER_KEY
transmise au routeur, au Mac ou aux clients. Le secret n'est pas dans les sources,
preuves filtrées ou sorties de commandes.

Le runtime isolé conserve l'identité locale `isolated-test` dans
`~/.local/state/llm-router/litellm-qualification`, distincte de son propriétaire
LiteLLM `mcp-delegate`. Il n'est pas l'identité d'une session Codex/OpenClaw
raccordée. Les métadonnées de routage locales qualifiées portent sur Qwen local,
Groq/Qwen et Mistral/Ministral uniquement. Les autres alias visibles ne sont pas
implicitement qualifiés par leur présence. Pour les deux routes gratuites, 8192
est une limite d'admission conservatrice de recette, pas une fenêtre maximale vérifiée.

### Recette réelle et limites de contenu

| Tâche | Alias demandé/sélectionné | Fournisseur et modèle confirmés par journaux natifs | Tokens entrée/sortie | Résultat |
|---|---|---|---|---|
| `5f3554e8-0c8e-49a6-8e24-0ca46581be4c` | local Qwen, choisi sans modèle imposé | oMLX / `mlx-community--Qwen3.6-35B-A3B-4bit` | 35 / 1 | `completed`, réponse exacte `OK`, qualité PASS |
| `f2bd8696-0aee-41d7-b2c6-5bab09de1b07` | `free-groq/qwen3.8-27b` | Groq / `qwen/qwen3.8-27b` via FreeLLMAPI | 47 / 2 | HTTP terminé, `stop`, contrôle exact FAIL, tâche `failed` |
| `507488bb-e3ea-4da9-a531-5958d91a51ab` | `free-mistral/ministral-8b-2512` | Mistral / `ministral-8b-2512` via FreeLLMAPI | 38 / 13 | JSON entouré de balises Markdown, contrôle JSON strict FAIL, tâche `failed` |

**Trois inférences au total**, dont une locale et deux gratuites. La seconde
route gratuite est une tâche distincte après échec de conformité, pas un fallback
automatique du routeur. Aucun autre appel après ce deuxième refus de qualité.
Les échecs restent enregistrés ; ils ne sont ni transformés en PASS ni effacés.
Le premier contenu rejeté n'avait pas été conservé par la version initiale : sa
divergence exacte n'est pas reconstituable. Le second contenu est récupérable :
objet `{"ok":true}` à l'intérieur d'un bloc Markdown. Le contrôle strict reste
inchangé ; ce n'est pas du JSON brut conforme à la demande.

Après ce défaut de diagnostic observé, correction ciblée : le contenu rejeté est
conservé **dans le résultat privé seulement**, sans prompts/réponses dans les
événements. Vérifié par le second appel réel et un test ciblé de confidentialité.
La qualité générique des modèles gratuits n'est pas déclarée qualifiée.

Les soumissions ont été faites par un MCP stdio puis son client fermé.
Une nouvelle connexion MCP a récupéré `status/result`, y compris les résultats
terminaux et le second rejet. Aucun redémarrage du client n'a nécessité une
nouvelle génération. Un seul stockage applicatif et le worker existant sont utilisés.

### Provenance — VERIFIED par corrélation, pas par alias

LiteLLM remplace le champ `model` de ces réponses par son alias. Le routeur
conserve donc `response_model` et laisse `actual_model=null` lorsque seul l'alias
est connu. Correction ciblée : capture du `request_id` de complétion et des
en-têtes `x-litellm-call-id`, `x-litellm-model-id`, retries/fallbacks.
Pas de credential administratif ajouté au worker pour lire les spend logs.

| Tâche | Request ID de complétion | Déploiement LiteLLM |
|---|---|---|
| Locale | `chatcmpl-0c363bee` | `17720d29-9da3-4888-aef8-f6db0cc5bd96` |
| Groq | `chatcmpl-2e7a9295-dc80-4d1b-9f21-1db6a552d54b` | `ceb9e83e-8d7d-4adf-bb98-713f0269a714` |
| Mistral | `f4248dcc141444068cc4dcb12e502ad1` | `1e5399c3-5ebd-4f11-aab1-70904d039812` |

Les `/spend/logs?request_id=...` natifs confirment respectivement les destinations
`openai/mlx-community--Qwen3.6-35B-A3B-4bit`,
`openai/groq:qwen/qwen3.8-27b`, `openai/mistral:ministral-8b-2512`.
Ces chaînes sont des destinations d'adaptateurs ; les identifiants fournisseur
sont ceux du tableau précédent, pas les alias publics LiteLLM.
Les journaux FreeLLMAPI **21 et 22** confirment respectivement Groq/Qwen et
Mistral/Ministral, une tentative chacun, aux mêmes instants et avec les mêmes tokens.
Le coût observé LiteLLM est **0 USD pour chacun des trois appels**, cache désactivé
sur ces réponses. Le coût peut rester `null` dans les événements du routeur
lorsqu'aucun montant n'est exposé dans les en-têtes SSE ; il n'est pas inventé.

### Permissions, timeouts et isolation — VERIFIED dans cette portée

Relecture de la configuration Swarm réellement montée sous
`/etc/litellm/config.yaml` : retries globaux **0**, fallbacks **[]**, logs de messages
désactivés, prompts exclus des spend logs, credentials clientes désactivés.
API `/model/info` avant/après : **définitions des 17 déploiements strictement
inchangées**, dont timeout 300 s, stream timeout 3600 s et max retries 0.
Les trois réponses et spend logs portent retries **0** / fallbacks **0**.
FreeLLMAPI : une tentative dans chacun des deux journaux de cette recette.

Routeur isolé : connexion 20 s, inactivité 90 s explicitement configurées,
aucune limite totale de génération ajoutée. Les durées effectives courtes ne
qualifient pas un comportement à 300/3600 s ; aucun timeout forcé ou panne réseau.
LiteLLM final `healthy`, DB `connected` ; FreeLLMAPI `ok`, trois upstreams prêts.
Budget partagé PAID relu **40 USD / 1mo**, équipe et état identiques au précontrôle.
Aucun changement de service, modèle, pool, budget, réseau ou réglage global.

Le MCP historique et son binaire gardent le SHA-256 cité plus haut.
`~/.codex/config.toml` garde son empreinte de début de finalisation :
`8efac2b85762485e5b9fa79efad6a895c7c2f70b6e1041a2d950970b0fd7b530`.
Aucune configuration cliente OpenClaw modifiée, aucun raccordement ni extension.

### BLOCKED / NOT_TESTED restant

- **Blocage `LLM_ROUTER_LITELLM_KEY` : LEVÉ**, remplacement par lecture privée
  `key_file`, sans variable globale ni secret du MCP historique modifié.
- **Chemin LOCAL/FREE : VERIFIED pour authentification, routage, inférence,
  récupération asynchrone et provenance corrélée.** Réponses gratuites non conformes
  aux contrôles stricts : **PARTIAL**, explicitement distinct d'un échec d'accès.
- Courtier privilégié et sélection DIRECTE authentifiée : **BLOCKED / non raccordés**,
  selon le périmètre demandé ; aucune clé ni inférence PAID activée.
- Les limites générales antérieures (grands contextes, tools/vision, annulation
  active, etc.) restent celles de la section PARTIAL. Aucun test massif ou phase 3.

Preuves filtrées locales sous `artifacts/llm-router-finalization/` (ignoré par Git) :
`preflight.json`, `issuance.json`, `catalogue-permissions.json`, `real-tasks.json`,
`free-json-task.json`, `final-verification.json`, `free-evidence.json`,
`free-evidence-ministral.json`, `management-refusal.json`. Aucun secret dans ces
rapports. Les sources de recette sont conservées ; `qualify_litellm.py` est un test
réel explicite, **à ne pas relancer pour relire des résultats déjà persistés**.

Sources d'interface consultées : [clés virtuelles LiteLLM](https://docs.litellm.ai/docs/proxy/virtual_keys),
[spend tracking](https://docs.litellm.ai/docs/proxy/cost_tracking), confrontées au
comportement de la version installée. Aucune modification directe de base interne
LiteLLM ou FreeLLMAPI ; émission et lectures par API native uniquement.

**Point d'arrêt : finalisation ciblée terminée avec les réserves ci-dessus.
Aucune autorisation de raccordement Codex/OpenClaw n'est déduite de cette recette.**

## P3-B — validation supplémentaire ciblée

Voir [rapport P3-B](../../codex/21-llm-router-p3b.md). Les 41 tests historiques
ne sont pas relancés. Nouveau test d'autorisations adversariales concurrentes
avec fournisseur simulé PASS ; trois tests de l'adaptateur et un de synchronisation
PASS. Huit catalogues de clés vérifiés ; les deux clés DELEGATED refusent PAID.
Tâche locale réelle `41e74897-2c1f-4c13-8944-8ca5d662d63c` via l'API native
OpenClaw dans la session Pro : JSON brut conforme, coût LiteLLM observé 0 USD ;
lecture croisée Perso refusée. La découverte autonome du modèle reste BLOCKED,
la GUI et les générations DIRECT/PAID restent NOT_TESTED. Aucun test Cloud ajouté,
aucun échec strict précédent reclassé. Courtier PAID de production désactivé.
