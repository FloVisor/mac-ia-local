# local-llm-mcp — serveur MCP de délégation vers le LLM local

Serveur MCP (stdio, JSON-RPC) qui expose un unique outil `delegate` redirigeant
une tâche autonome vers le modèle local **mlx-community--Qwen3.6-35B-A3B-4bit** servi par oMLX.
Objectif : permettre à Codex (GPT-6) de déléguer les tâches simples, indépendantes
ou répétitives au modèle local, sans consommer le contexte ni les tokens cloud.

- Source : [local-llm-mcp.py](local-llm-mcp.py) (copie exacte du binaire déployé `~/.codex/bin/local-llm-mcp`)
- Statut : **fonctionnel, testé de bout en bout le 2026-10-17** ; garde de contexte
  relevée à 128K et revalidée le 2026-10-19 (voir [Tests](#tests))

## Architecture

```
Codex (GPT-6)
  └─ MCP local_llm (stdio, ~/.codex/bin/local-llm-mcp)
       └─ HTTP POST http://127.0.0.1:8000/v1/chat/completions   (wire oMLX standard, auth Bearer)
            └─ oMLX 0.7.1rc1 → mlx-community--Qwen3.6-35B-A3B-4bit
```

Points clés :

- **Non destructif** : utilise le wire `/v1` standard d'oMLX, jamais le wire
  Codex `/api/codex/v1` (aucun token cloud impliqué).
- **Pas de fallback** : si le modèle local est indisponible, une erreur claire
  est retournée (`ERROR: Local model ... unreachable`). Pas de bascule cloud.
- **Sans état** : chaque appel `delegate` est une requête chat/completions
  indépendante ; le serveur ne garde aucun contexte entre les appels.
- **Un seul outil** : `delegate(profile, task)` — surface minimale, pas de
  lecture de fichiers, pas d'exécution de commandes.

## Installation

Le serveur est un script Python 3 autonome (stdlib uniquement, aucune dépendance).

```sh
# Copier la source versionnée vers l'emplacement Codex
cp mcp/local-llm-mcp/local-llm-mcp.py ~/.codex/bin/local-llm-mcp
chmod +x ~/.codex/bin/local-llm-mcp

# Prérequis : oMLX actif (LaunchAgent org.gangneux.omlx-serve) et modèle épinglé
curl -s http://127.0.0.1:8000/health
```

## Configuration Codex

Bloc existant dans `~/.codex/config.toml` (déjà en place, ne pas modifier) :

```toml
[mcp_servers.local_llm]
command = "/Users/fngux2/.codex/bin/local-llm-mcp"
startup_timeout_sec = 30
```

La garde de contexte n'est **pas** dans `config.toml` : elle est portée par le
script (`MAX_TASK_TOKENS`, défaut `131072`). Un changement de garde se fait donc
dans la source versionnée puis par redéploiement du binaire — voir
[Installation](#installation).

Variables d'environnement optionnelles (non définies par défaut) :

| Variable | Défaut | Rôle |
|---|---|---|
| `LOCAL_LLM_MCP_BASE_URL` | `http://127.0.0.1:8000/v1` | Base URL du wire OpenAI-compatible oMLX |
| `LOCAL_LLM_MCP_TIMEOUT` | `600` | Timeout HTTP par requête (secondes) |
| `LOCAL_LLM_MCP_MAX_TASK_TOKENS` | `131072` | Garde de contexte : rejet au-delà (comptage réel `/tokenize`) |

## Outil disponible

### `delegate`

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `profile` | enum | oui | `analysis`, `coding`, `documentation`, `review`, `testing` |
| `task` | string | oui | Description complète et autonome de la tâche, avec tout le contexte nécessaire |

Réponse : texte préfixé par les métadonnées
`[profile=… model=mlx-community--Qwen3.6-35B-A3B-4bit server=oMLX:8000 …]` suivi de la
réponse du modèle. En cas d'échec : `ERROR: …` avec `isError: true`.

**Garde 128K** : la tâche est **rejetée au-delà de 131 072 tokens** (comptage réel
via `POST /tokenize` d'oMLX, tokeniseur du modèle ; fail-closed si le comptage
est indisponible). Cette valeur est alignée sur le cap serveur oMLX du modèle
(`max_model_len: 131072`) et sur le catalogue Codex `qwen36-omlx` ; le plafond
dur reste le serveur (prompt système + tâche > 131072 → HTTP 400
`context_length_exceeded`). Réglable via `LOCAL_LLM_MCP_MAX_TASK_TOKENS`.

> Historique : garde à 32 768 tokens du 2026-10-17 au 2026-10-19, relevée à
> 131 072 le 2026-10-19 ([validation](../../diagnostics/local-llm-mcp-ctx128k-20261019/README.md)).

## Profils d'agents

Chaque profil sélectionne un prompt système distinct :

| Profil | Prompt système (résumé) |
|---|---|
| `analysis` | Analyste technique précis : décomposer la tâche, séparer faits et hypothèses, réponse structurée |
| `coding` | Agent de code prudent : changements minimaux, corrects, chirurgicaux, conventions du dépôt |
| `review` | Relecteur rigoureux : uniquement des problèmes à haute confiance avec fichier/lignes/preuves |
| `testing` | Agent de test : plus petit ensemble de tests couvrant le changement, commandes exactes |
| `documentation` | Rédacteur de doc : concis, factuel, cohérent avec la structure existante |

## Modèle : mlx-community--Qwen3.6-35B-A3B-4bit (oMLX)

| Propriété | Valeur (vérifiée via `/v1/models` et `/tokenize`) |
|---|---|
| Serveur | oMLX 0.7.1rc1, `127.0.0.1:8000`, LaunchAgent `org.gangneux.omlx-serve` |
| Architecture | hybride GDN (10/40 couches full-attention, 2 KV heads) |
| Paramètres | 35B total, ~3B actifs (MoE) |
| Quantification | 4 bits |
| Contexte | 131 072 tokens (`max_model_len`, cap par modèle dans `~/.omlx/model_settings.json`) |
| Mémoire résidente | ~21,4 Go (RSS mesurée, modèle chargé) |
| Capacités | completion, tools, thinking natif |

## Raisonnement natif

Le MCP n'impose pas de `reasoning_effort` : le modèle Qwen3.6 utilise son
thinking natif. Seul le contenu final (`content`) est retourné à Codex.
Le thinking est désactivé par profil pour `testing` et `documentation`
(`chat_template_kwargs.enable_thinking = false`), activé pour les autres.

## Fonctionnement des délégations

1. Codex (GPT-6) décide de déléguer et appelle `mcp__local_llm__delegate` avec
   un profil et une tâche **autonome** (tout le contexte doit être inclus dans
   `task`, car le serveur est sans état).
2. Le MCP compte les tokens de la tâche via `/tokenize` (rejet > 131 072), puis
   construit la requête : prompt système du profil + tâche, pas de streaming.
3. oMLX traite la requête (modèle épinglé, déjà chargé).
4. Le MCP retourne la réponse préfixée des métadonnées à Codex, qui valide et
   intègre le résultat.

La délégation n'est pertinente que pour des tâches **autonomes** : le modèle
local ne voit ni le dépôt, ni les fichiers, ni l'historique de conversation.

## Sécurité et isolation

- **Auth Bearer** : clé lue dans `~/.omlx/settings.json` (source unique),
  jamais codée en dur ; le MCP ne touche jamais le wire Codex cloud.
- **Boucle locale uniquement** : `127.0.0.1:8000` par défaut.
- **Pas d'accès au système de fichiers** : le serveur ne lit ni n'écrit aucun
  fichier projet ; il ne transmet que le texte de `task`.
- **Pas d'exécution de commandes** : seule la génération de texte est possible.
- **Timeout borné** : 600 s par requête (configurable).
- **Isolation des projets** : le modèle local ne reçoit que le contenu explicite
  du paramètre `task` ; aucun chemin, aucun fichier n'est exposé par le serveur
  lui-même. La responsabilité de ne pas inclure de secrets dans `task` incombe
  à l'appelant (Codex), conformément aux règles globales AGENTS.md.

## Tests

Test de bout en bout réalisé le **2026-10-17** (probe JSON-RPC stdio direct,
identique au protocole de [02-mcp-matrix.md](../../codex/02-mcp-matrix.md)) :

| Test | Résultat |
|---|---|
| `initialize` | **PASS** — protocolVersion 2024-11-05, serverInfo local-llm-mcp 1.1.0 |
| `tools/list` | **PASS** — 1 tool `delegate`, schéma complet (5 profils) |
| `tools/call delegate` (profile=analysis) | **PASS** — réponse réelle du modèle via oMLX (request_id, duration_ms) |
| `resources/list` / `resources/templates/list` | Non supporté (par design, `-32601`) — confirmé via session Codex du 2026-10-17 |
| Découverte par Codex | **PASS** — namespace `mcp__local_llm` + tool `delegate` visible dans la session Codex du 2026-10-17 |
| Garde 32K (2026-10-17) | **PASS** — tâche 67 507 tokens rejetée proprement ; tâche courte acceptée |
| Garde 128K (2026-10-19) | **PASS** — tâche 40 000 tokens acceptée (35,1 s) ; tâche 150 000 tokens rejetée proprement |

Captures : [diagnostics/local-llm-mcp/](../../diagnostics/local-llm-mcp/) ·
[garde 128K](../../diagnostics/local-llm-mcp-ctx128k-20261019/README.md)

### À valider

- Appel `delegate` **depuis Codex** (la session du 17/10 a découvert l'outil mais
  l'appel n'a pas été consigné comme exécuté ; le test stdio direct ci-dessus
  valide le chemin complet serveur → oMLX → modèle).
- Profils `coding`, `review`, `documentation` (seuls `analysis` et `testing` ont
  été appelés).
- Comportement en erreur : oMLX arrêté (message `unreachable` attendu).
- Latence de bout en bout sur une tâche réelle (chargement à froid du modèle).

## Limitations

- Sans état : aucun suivi multi-tours ; chaque délégation doit être autonome.
- Un seul modèle, pas de fallback — indisponibilité = erreur explicite.
- Pas de streaming : réponse complète après génération (jusqu'à 600 s).
- `resources/list` non implémenté (serveur tools-only).
- Le modèle local ne voit pas le dépôt : ses réponses de code/doc doivent être
  validées par Codex avant application.
