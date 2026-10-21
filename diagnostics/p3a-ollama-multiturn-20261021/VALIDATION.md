# P3-A — multi-tour Ollama


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
