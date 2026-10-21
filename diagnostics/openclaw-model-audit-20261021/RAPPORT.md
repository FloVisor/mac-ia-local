# Audit OpenClaw / LiteLLM — 21 octobre 2026

État : corrections appliquées et parcours locaux Pro/Perso validés. Qualification globale Cloud, reasoning et grandes fenêtres NON terminée. Aucun appel payant ; aucune nouvelle génération gratuite externe. Deux générations OpenClaw via LiteLLM vers oMLX local seulement. Pas de modification d'historique existant, de credential, de quota ni de permission.

## Corrections effectivement appliquées

- OpenClaw : 26 déclarations de modèles ajustées dans les quatre providers LiteLLM. Plafond client jusqu'à 131072 lorsque les métadonnées l'autorisent ; Codestral et task-coding limités à 128000. Ollama direct 4096 et route Ollama 8192 conservés : réglages distincts documentés, callback serveur 8192 inchangé.
- oMLX via LiteLLM : contexte 8192 → 131072, sortie 2048 → 8192, alignés sur l'accès direct. Authentification oMLX existante réutilisée en mémoire : GET /v1/models HTTP200, Qwen3.6 max_model_len=131072 ; model_settings.max_context_window=131072 également. Aucun secret dans les preuves.
- Budgets de sortie client : 8192 pour oMLX, OpenRouter individuels et PAID ; 2048 conservés pour Groq (8000 TPM locaux), Mistral et pools (plafond commun de sortie non établi). Ce sont des budgets applicatifs, PAS des maxima fournisseur ni des fenêtres qualifiées par génération.
- LiteLLM : métadonnées des quatre pools corrigées au minimum des contextes de leurs membres ; sortie déclarée et défaut max_tokens ramenés à un budget explicite de 2048. Ce défaut n'est pas une interdiction de surcharge par un autre client. Les anciennes valeurs de sortie égales au contexte complet n'étaient pas des plafonds de sortie qualifiés.
- FreeLLMAPI : Codestral 2508 contextWindow 256000 → 128000 par PATCH /api/models/281, puis relecture. La documentation officielle actuelle annonce 128k. Aucun quota augmenté.
- Extension locale litellm-compat : normalisation limitée aux erreurs des deux providers gratuits annonçant un reset en heures/jours. Message original conservé, attribution explicite à l'amont, filtre natif de limite longue activé. Aucun patch OpenClaw core ni changement du backoff des erreurs temporaires ordinaires. Plugin installé et activé, Gateway génération 3.

Les sections agents, outils et authentification sont identiques à la préimage. Seules les sections models et plugins ont changé. Les configurations Codex, RTK, Graphify et les backends de génération n'ont pas été modifiées.

## Inventaire final OpenClaw

Chaque alias ci-dessous existe pour Pro et Perso. Identifiants complets et endpoints dans openclaw-final.json. Préfixes : litellm-free-pro / litellm-free-perso ; les trois alias PAID utilisent litellm-paid-pro / litellm-paid-perso. Endpoint commun HTTPS : https://litellm.gangneux.org/v1.

La colonne contexte amont est une métadonnée/configuration, pas une preuve de génération à cette taille. Les quotas se cumulent avec la fenêtre de contexte ; 8000 TPM peut rendre impossible un prompt OpenClaw de 20000 tokens même si le modèle théorique accepte 128K.

| Alias LiteLLM | Contexte client | Sortie client | Contexte amont connu | Tools / streaming / reasoning | État |
|---|---:|---:|---|---|---|
| `local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit` | 131072 | 8192 | 131072 effectif annoncé oMLX | Tools + streaming PASS ; reasoning NOT_RUN | OK sur parcours testé |
| `local-ollama/qwen3:4b-instruct` | 8192 | 2048 | 8192 imposé par callback LiteLLM | Tools/thinking annoncés ; OpenClaw via cette route NOT_RUN | OK statique |
| `free-groq/qwen3.8-27b` | 131072 | 2048 | 262144 (catalogue/configuration) | Tools annoncés ; streaming/reasoning de bout en bout NOT_RUN | INCONNU |
| `free-groq/gpt-oss-120b` | 131072 | 2048 | 131072 (catalogue/configuration) | Tools annoncés ; streaming/reasoning de bout en bout NOT_RUN | INCONNU |
| `free-openrouter/dots-3-note-preview:free` | 131072 | 8192 | 512000 (catalogue/configuration) | Tools annoncés ; streaming/reasoning de bout en bout NOT_RUN | INCONNU |
| `free-openrouter/north-mini-code:free` | 131072 | 8192 | 256000 (catalogue/configuration) | Tools annoncés ; streaming/reasoning de bout en bout NOT_RUN | INCONNU |
| `free-mistral/ministral-8b-2512` | 131072 | 2048 | 262144 (catalogue/configuration) | Streaming court PASS précédent ; tools non prouvé ; reasoning NOT_RUN | INCONNU |
| `free-mistral/codestral-2508` | 128000 | 2048 | 128000 (catalogue/configuration) | Tools annoncés ; streaming/reasoning de bout en bout NOT_RUN | INCONNU |
| `free/task-fast` | 131072 | 2048 | 262144 (minimum membres) | Tools annoncés par membres ; pool réel NOT_RUN | OK statique / dynamique INCONNU |
| `free/task-coding` | 128000 | 2048 | 128000 (minimum membres) | Tools annoncés par membres ; pool réel NOT_RUN | OK statique / dynamique INCONNU |
| `free/task-reasoning` | 131072 | 2048 | 131072 (minimum membres) | Tools annoncés par membres ; pool réel NOT_RUN | OK statique / dynamique INCONNU |
| `free/task-long-context` | 131072 | 2048 | 256000 (minimum membres) | Tools annoncés par membres ; pool réel NOT_RUN | OK statique / dynamique INCONNU |
| `paid-openrouter/deepseek-v4.1-flash-1017` | 131072 | 8192 | 1048576 (catalogue OpenRouter) | Tools/reasoning annoncés ; aucun appel payant | INCONNU |
| `paid-openrouter/glm-5.3` | 131072 | 8192 | 1048576 (catalogue OpenRouter) | Tools/reasoning annoncés ; aucun appel payant | INCONNU |
| `paid/task-advanced` | 131072 | 8192 | 1048576 (catalogue OpenRouter) | Tools/reasoning annoncés ; aucun appel payant | INCONNU |

Autres modèles : oMLX direct Qwen3.6 131072/8192 ; Ollama direct Qwen3 4096/256 avec num_ctx=4096 et think=false. oMLX annonce aussi Qwen3-Coder-30B 262144, absent des routes OpenClaw relevées. EmbeddingGemma est un modèle d'embeddings (contexte actif Ollama 2048), exclu des conversations. Muse-Glimmer est installé mais bloqué dans LiteLLM et absent des allowlists OpenClaw relevées.

## Fournisseurs, endpoints et limites

- Local oMLX : modèle openai/mlx-community--Qwen3.6-35B-A3B-4bit ; LiteLLM utilise http://ollama-tailscale:8000/v1 ; accès direct Mac http://127.0.0.1:8000/v1. Le test OpenClaw via LiteLLM confirme le chemin local utilisable.
- Local Ollama : ollama_chat/qwen3:4b-instruct ; http://172.29.2.27:11434 ; accès direct Mac http://127.0.0.1:11434. Contexte de cette route forcé à 8192 par qwen_context, IDs d'outils restaurés par le callback existant, inchangé.
- FREE : tous via http://freellmapi_api:3001/v1 ; modèle OpenAI-compatible explicitement préfixé par groq:, mistral:, openrouter: ou auto:. Correspondances exactes dans litellm-final.json.
- PAID : OpenRouter natif deepseek/deepseek-v4.1-flash-1017, z-ai/glm-5.3 ; paid/task-advanced pointe sur le premier, ce n'est pas un pool constaté. Endpoint fournisseur natif non surchargé dans la configuration. Métadonnées publiques OpenRouter consultées sans inférence.
- LiteLLM : timeout 300s, stream_timeout 3600s et max_retries=0 pour toutes les routes relevées. router_settings.num_retries=0, fallbacks=[] ; aucun override de fallback dans les paramètres de modèles relevés.
- FreeLLMAPI : output-limit mode=off, compression mode=off ; fusion mode=auto mais liste models vide. Aucun écrêtage global de sortie configuré par ce mécanisme. Réserves/headroom non explicitement configurées dans les valeurs relues ; ce n'est pas la preuve de l'absence de valeurs par défaut dans le code.

| Modèle FREE | RPM locaux | RPD locaux | TPM locaux | TPD locaux |
|---|---:|---:|---:|---:|
| groq / openai/gpt-oss-120b | 30 | 1000 | 8000 | 200000 |
| groq / qwen/qwen3.8-27b | 30 | 250 | 8000 | 200000 |
| mistral / codestral-2508 | 2 | None | 500000 | None |
| mistral / ministral-8b-2512 | 2 | None | 500000 | None |
| openrouter / cohere/north-mini-code:free | 20 | 50 | None | None |
| openrouter / dots-studio/dots-3-note-preview:free | 20 | 50 | None | None |

`None` signifie non configuré/inconnu, pas illimité. Les quotas réels des comptes fournisseurs ne sont pas déduits de ces réglages locaux. OpenRouter gratuit peut partager ses quotas entre modèles.

## Pools et fallbacks payants

| Pool | Membres actuels |
|---|---|
| task-fast | Groq Qwen3.8, Mistral Ministral, OpenRouter Dots gratuit |
| task-coding | Mistral Codestral, OpenRouter North gratuit, Groq GPT-OSS |
| task-reasoning | Groq GPT-OSS, Groq Qwen3.8, OpenRouter North gratuit |
| task-long-context | OpenRouter Dots gratuit, OpenRouter North gratuit, Mistral Ministral |

Les chaînes ont été relues par /api/profiles et /api/profiles/:id/models. Aucun membre payant dans ces quatre listes. L'ordre stocké ne garantit pas une priorité stricte : le routeur FreeLLMAPI peut réordonner les membres. La stratégie et les scopes décrits dans l'audit antérieur n'ont pas été modifiés ; leur preuve antérieure n'est pas présentée comme une nouvelle lecture de chaque clé fournisseur.

Les modèles par défaut des deux agents restent oMLX local. Les clés DIRECT gratuites des deux agents voient 13 routes et aucune route paid. Les sections modelPolicy séparent Pro/Perso. L'outil session_status ne peut sélectionner aucun modèle autre que default ; test de politique PASS. La délégation trie local avant gratuit, exige l'accord Cloud et bloque les tâches contenant des secrets sur une route distante. Le courtier DELEGATED payant reste non raccordé : refus paid_broker_not_connected, tests PASS. Aucun fallback payant configuré côté LiteLLM.

Limite de cette assurance : cela prouve les chemins automatiques inspectés, pas un contrôle de contenu universel. Une clé DIRECT payante existe pour une sélection manuelle autorisée ; elle n'a pas été utilisée ici. La détection de secrets de la délégation ne constitue pas un filtre complet des conversations DIRECT, notamment pour les secrets opaques ou déjà présents dans un historique. Cette garantie globale n'est pas revendiquée.

## Diagnostic 429 — 16:44–16:45 CEST

Sept réponses 429 visibles dans OpenClaw ; sept reprises temporisées : 955, 2430, 4077, 11651, 15990, 15224, 30000 ms. Sources : /tmp/openclaw/openclaw-2026-10-21.log, docker logs LiteLLM et FreeLLMAPI sur la période UTC 14:44–14:46.

FreeLLMAPI journalise sept fois `routing exhausted (no upstream tried)` et `mistral/ministral-8b-2512: 1 key(s) — rpm/rpd-limit:1`. La configuration relue précise 2 RPM et aucun RPD explicite pour ce modèle. Ce sont donc des refus d'admission du routeur local, pas sept refus réseau de Mistral. Le motif agrégé ne détaille pas individuellement RPM et RPD ; l'espacement des succès et le réglage 2 RPM sont cohérents avec une fenêtre RPM.

Des appels réels intercalés réussissent : 14:44:24→26, 14:44:58→14:45:00, 14:45:30→31 UTC. Les deux premiers transportent respectivement 25446 et 25638 tokens d'entrée selon ces logs. LiteLLM relaie le message `All models exhausted ... Soonest reset ~17h`, sans fallback de groupe ; ses retries sont désactivés. Pas d'amplification LiteLLM démontrée. L'amplification visible est celle des reprises OpenClaw ; les refus FreeLLMAPI ne déclenchent pas d'appel fournisseur.

La durée ~17h est une estimation amont trompeuse dans ce cas : une route redevient admissible bien avant. Les headers HTTP historiques complets, dont Retry-After, ne sont pas disponibles dans les traces collectées ; aucune valeur n'a été inventée ni nouvelle requête limitée lancée pour les obtenir.

Correctif client : litellm-compat conserve le message et rend sa revendication de reset long reconnaissable par le filtre natif. Tests hors réseau du classificateur natif, de l'itérateur et de result() PASS ; erreurs temporaires ordinaires inchangées. La suppression des retries longs n'a pas été requalifiée par un appel réel 429, conformément à l'interdiction de relancer le fournisseur limité. Le calcul du reset FreeLLMAPI reste à corriger en amont ; aucun patch fournisseur ajouté.

## Validation réelle

| Contrôle | Résultat et portée |
|---|---|
| Auth oMLX existante, métadonnées | PASS HTTP200, aucune clé modifiée ou affichée |
| Schéma OpenClaw et relecture des changements | PASS |
| API LiteLLM, quatre pools ; API FreeLLMAPI Codestral | PASS, modifications relues |
| Extension retry, classificateur natif, erreurs temporaires et périmètre | PASS hors réseau |
| Isolation adaptateur / protection sélection DIRECT | PASS, 3 tests |
| Politique délégation | PASS, 17 tests |
| Courtier payant | PASS, 21 tests, exécuteurs simulés, aucun appel payant |
| OpenClaw Perso / LiteLLM / oMLX avec outil read | PASS : appel call_6b5ce327, résultat même toolCallId, isError=false, texte témoin exact |
| OpenClaw Pro / LiteLLM / oMLX simple | PASS : PRO_OK |
| Identité effective, terminaison et absence fallback des deux essais | PASS : une tentative chacune, finish/stop, rerouted=false |
| Gateway après changements | PASS : ok=true, plugin actif, aucune erreur plugin |
| 128K intégral et plafonds de sortie Cloud | NOT_RUN : métadonnées/configuration ne prouvent pas une génération à la limite |
| Reasoning via chaque alias, JSON structuré, usage/reasoning_tokens | NOT_RUN ; aucune capacité artificiellement ajoutée |
| Nouvelle erreur 429 réelle après correctif | NOT_RUN : pas de sollicitation du fournisseur limité |
| Reprise dans les conversations d'origine, dont dossier Ministral | NOT_RUN : historiques préservés ; session affectée/export antérieur conservés |

Le témoin /tmp utilisé pour la lecture a été supprimé après vérification. Les sessions de diagnostic et exports privés restent des preuves identifiées ; aucun dossier métier n'a été altéré. La revue locale déléguée a échoué et contenait des recommandations non vérifiées ; elle a été rejetée, sans fallback Cloud.

## Diff et rollback

Diff des seules déclarations OpenClaw : changes.json (valeurs avant/après). Configurations finales expurgées : openclaw-final.json et litellm-final.json. Sauvegarde OpenClaw privée : ~/.openclaw/backups-model-audit-20261021/openclaw.json. Préimages privées distantes : /srv/docker-local/compose/litellm/preimages/model-audit-20261021/models.json. Aucun secret dans ce dossier de diagnostic.

Depuis la racine du dépôt :

```sh
# Désactiver seulement l'extension de normalisation.
openclaw plugins disable litellm-compat
# Restaurer seulement les champs des modèles modifiés ; refuse les conflits.
python3 openclaw/litellm-compat/rollback-models.py
# Restaurer les métadonnées distantes via les APIs natives et relire le résultat.
ssh root@docker-02 python3 - < openclaw/litellm-compat/rollback-remote.py
```

Les scripts de rollback ont été contrôlés syntaxiquement, pas exécutés. Ils ne restaurent pas un fichier global à l'aveugle. Le rollback distant rétablit volontairement les anciennes métadonnées erronées. La sauvegarde de l'incident Ministral antérieur reste distincte ; ce rollback conserve son contexte 131072.

## Sources et limites restantes

- Métadonnées runtime oMLX authentifiées ; configuration effective OpenClaw ; APIs natives LiteLLM et FreeLLMAPI.
- https://docs.mistral.ai/models/codestral-25-08 : 128k et function calling ; contradiction avec ancien catalogue FreeLLMAPI corrigée.
- https://console.groq.com/docs/model/openai/gpt-oss-120b : contexte 131072, sortie maximale théorique 65536, outils/JSON/reasoning ; quotas locaux distincts.
- https://openrouter.ai/api/v1/models : métadonnées sauvegardées dans openrouter.json. Dots 512000/460800 ; North 256000/64000 ; DeepSeek 1048576/393216 ; GLM 1048576/943718 (contexte/sortie maximum annoncés). Aucun test d'inférence correspondant.

Risques matériels : quotas Cloud pouvant rendre les prompts OpenClaw trop grands ; resets FreeLLMAPI encore imprécis ; capacités/usage variables selon membre du pool ; reasoning oMLX direct préservé mais équivalence via alias LiteLLM non qualifiée ; absence de filtre universel de secrets en DIRECT. Le fonctionnement global n'est pas annoncé PASS.
