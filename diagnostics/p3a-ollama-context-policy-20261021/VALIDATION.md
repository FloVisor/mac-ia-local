# P3-A — politique Ollama 128K, qualification avant activation


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
