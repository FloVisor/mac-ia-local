# P3-A — Qwen3 4B 8192


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
