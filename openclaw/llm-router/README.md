# OpenClaw — adaptateur isolé llm-router (P3-B)

`main` → `openclaw-pro`, `perso` → `openclaw-perso`, depuis le contexte
`registerTool` du runtime. Sept outils `llm_router_*` encapsulent le MCP stdio
existant ; aucun serveur générique ayant accès aux deux magasins n'est exposé.
`parent_session` est injecté par l'adaptateur, jamais accepté depuis le modèle.
Chaque processus Python reçoit seulement sa configuration privée, son stockage
et sa clé DELEGATED LOCAL/FREE. Aucune lecture de workspace ou de mémoire.
Isolation applicative, pas frontière entre processus malveillants du même compte macOS.

La configuration opérateur du plugin doit indiquer `routerPath` absolu : les
plugins sont capturés par OpenClaw et leurs chemins relatifs changent au déploiement.
Le manifeste doit déclarer `contracts.tools`, sinon le plugin apparaît chargé
sans publier ses outils. Aucun patch du runtime OpenClaw.

## DIRECT

Les providers `litellm-free-pro`, `litellm-paid-pro`, `litellm-free-perso` et `litellm-paid-perso` utilisent leurs propres credentials
DIRECT dans les magasins natifs de chaque agent, importés avec
`openclaw models auth paste-api-key --agent …`. Aucun secret dans openclaw.json.
Les noms distincts évitent l’héritage natif des credentials du compte principal.
Chaque `modelPolicy.allow` exclut les providers de l’autre agent.
Le sélecteur utilisateur constitue l'autorisation, sans nouvelle confirmation.
Les appels d'outil `session_status(model=…)` ne peuvent pas choisir un modèle
(à l'exception du retour `default`) : le modèle ne peut pas se donner le droit DIRECT.
Ni subagent ni appel générique ne bénéficie de cette permission.

La liste des modèles approuvés est explicite pour éviter que la découverte
Ollama annonce Muse-Glimmer. Le modèle initial et l'authentification oMLX restent
inchangés. Les nouvelles routes ont une admission conservatrice 8192/2048 ;
ce n'est pas une fenêtre maximale qualifiée. Tools, reasoning et grands contextes
Cloud restent NOT_TESTED. Les budgets numériques oMLX restent dans leur plugin.

## Synchronisation

`catalogue.py` lit `/v1/models` avec les clés clientes et croise une liste
opérateur explicitement approuvée (`client-policies.json`). Il produit un patch
et un diff, sans appliquer de configuration. Il exclut les embeddings et Muse,
préserve les définitions personnalisées/existantes (y compris désactivées), les
secrets et les modèles par défaut. Les nouvelles routes sont NOT_TESTED.
Comparer le diff, puis `openclaw config patch --file … --dry-run --json` avant
application. Revoir aussi `agents.entries.*.modelPolicy.allow` : une nouvelle
entrée catalogue n'accorde pas silencieusement une nouvelle permission.
Pas de synchronisation automatique de nouveaux modèles ni de suppression.

## DELEGATED payant

**Désactivé.** Le plugin ne reçoit aucune clé DIRECT. Les deux clés DELEGATED
refusent PAID côté LiteLLM. Les primitives `authorization.py` sont testées avec
un exécuteur simulé, mais aucun courtier de production, credential PAID ou outil
d'émission d'accord n'est raccordé. Un plafond opérationnel serveur et une
réservation fiable du budget partagé restent à qualifier avant activation.
Une consigne, un alias DIRECT ou un jeton fourni dans le prompt n'autorise rien.

Voir [rapport P3-B](../../codex/21-llm-router-p3b.md) pour preuves et rollback.
