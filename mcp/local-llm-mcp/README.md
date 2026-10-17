# local-llm-mcp — serveur MCP de délégation vers le LLM local

Serveur MCP (stdio, JSON-RPC) qui expose un unique outil `delegate` redirigeant
une tâche autonome vers le modèle local **muse-glimmer:30b-mlx** servi par Ollama.
Objectif : permettre à Codex (GPT-6) de déléguer les tâches simples, indépendantes
ou répétitives au modèle local, sans consommer le contexte ni les tokens cloud.

- Source : [local-llm-mcp.py](local-llm-mcp.py) (copie exacte du binaire déployé `~/.codex/bin/local-llm-mcp`)
- Statut : **fonctionnel, testé de bout en bout le 2026-10-17** (voir [Tests](#tests))

## Architecture

```
Codex (GPT-6)
  └─ MCP local_llm (stdio, ~/.codex/bin/local-llm-mcp)
       └─ HTTP POST http://127.0.0.1:11434/v1/chat/completions   (wire Ollama standard, sans auth)
            └─ Ollama 0.35.1 (patché PR#18413) → muse-glimmer:30b-mlx
```

Points clés :

- **Non destructif** : utilise le wire `/v1` standard d'Ollama, jamais le wire
  Codex `/api/codex/v1` (aucune auth, aucun token cloud impliqué).
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

# Prérequis : Ollama actif et modèle présent
curl -s http://127.0.0.1:11434/api/version
ollama list | grep muse-glimmer
```

## Configuration Codex

Bloc existant dans `~/.codex/config.toml` (déjà en place, ne pas modifier) :

```toml
[mcp_servers.local_llm]
command = "/Users/fngux2/.codex/bin/local-llm-mcp"
startup_timeout_sec = 30
```

Variables d'environnement optionnelles (non définies par défaut) :

| Variable | Défaut | Rôle |
|---|---|---|
| `LOCAL_LLM_MCP_BASE_URL` | `http://127.0.0.1:11434/v1` | Base URL du wire OpenAI-compatible Ollama |
| `LOCAL_LLM_MCP_TIMEOUT` | `600` | Timeout HTTP par requête (secondes) |

## Outil disponible

### `delegate`

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `profile` | enum | oui | `analysis`, `coding`, `documentation`, `review`, `testing` |
| `task` | string | oui | Description complète et autonome de la tâche, avec tout le contexte nécessaire |

Réponse : texte préfixé par les métadonnées
`[profile=… model=muse-glimmer:30b-mlx reasoning_effort=high]` suivi de la
réponse du modèle. En cas d'échec : `ERROR: …` avec `isError: true`.

## Profils d'agents

Chaque profil sélectionne un prompt système distinct :

| Profil | Prompt système (résumé) |
|---|---|
| `analysis` | Analyste technique précis : décomposer la tâche, séparer faits et hypothèses, réponse structurée |
| `coding` | Agent de code prudent : changements minimaux, corrects, chirurgicaux, conventions du dépôt |
| `review` | Relecteur rigoureux : uniquement des problèmes à haute confiance avec fichier/lignes/preuves |
| `testing` | Agent de test : plus petit ensemble de tests couvrant le changement, commandes exactes |
| `documentation` | Rédacteur de doc : concis, factuel, cohérent avec la structure existante |

## Modèle : muse-glimmer:30b-mlx

| Propriété | Valeur (vérifiée via `/api/show`) |
|---|---|
| Architecture | `muse_glimmer` (52 blocs) |
| Paramètres | 32.3B |
| Quantification | nvfp4 |
| Contexte | 131 072 tokens |
| Taille sur disque | ~19.1 GB |
| Capacités | completion, vision, tools, thinking |

## Raisonnement High

Chaque requête envoyée par le MCP force `"reasoning_effort": "high"` dans le
payload chat/completions. Le modèle produit donc un raisonnement interne
approfondi avant sa réponse ; seul le contenu final (`content`) est retourné à
Codex (le champ `reasoning` est ignoré). Ce choix est volontairement codé en dur
(`REASONING_EFFORT = "high"`) : la qualité prime sur la latence pour les tâches
déléguées.

## Fonctionnement des délégations

1. Codex (GPT-6) décide de déléguer et appelle `mcp__local_llm__delegate` avec
   un profil et une tâche **autonome** (tout le contexte doit être inclus dans
   `task`, car le serveur est sans état).
2. Le MCP construit la requête : prompt système du profil + tâche, modèle
   `muse-glimmer:30b-mlx`, `reasoning_effort=high`, pas de streaming.
3. Ollama traite la requête (chargement du modèle à froid si nécessaire).
4. Le MCP retourne la réponse préfixée des métadonnées à Codex, qui valide et
   intègre le résultat.

La délégation n'est pertinente que pour des tâches **autonomes** : le modèle
local ne voit ni le dépôt, ni les fichiers, ni l'historique de conversation.

## Sécurité et isolation

- **Aucune auth, aucun secret** : le MCP n'utilise pas `~/.codex/auth.json` et
  ne touche jamais le wire Codex cloud (`/api/codex/v1`).
- **Boucle locale uniquement** : `127.0.0.1:11434` par défaut.
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
identique au protocole de [02-mcp-matrix.md](../../docs/codex-local/02-mcp-matrix.md)) :

| Test | Résultat |
|---|---|
| `initialize` | **PASS** — protocolVersion 2024-11-05, serverInfo local-llm-mcp 1.0.0 |
| `tools/list` | **PASS** — 1 tool `delegate`, schéma complet (5 profils) |
| `tools/call delegate` (profile=analysis, tâche simple) | **PASS** — réponse réelle du modèle : `[profile=analysis model=muse-glimmer:30b-mlx reasoning_effort=high] DELEGUE` |
| `resources/list` / `resources/templates/list` | Non supporté (par design, `-32601`) — confirmé via session Codex du 2026-10-17 |
| Découverte par Codex | **PASS** — namespace `mcp__local_llm` + tool `delegate` visible dans la session Codex du 2026-10-17 |

Captures : [diagnostics/local-llm-mcp/](../../diagnostics/local-llm-mcp/)

### À valider

- Appel `delegate` **depuis Codex** (la session du 17/10 a découvert l'outil mais
  l'appel n'a pas été consigné comme exécuté ; le test stdio direct ci-dessus
  valide le chemin complet serveur → Ollama → modèle).
- Profils `coding`, `review`, `testing`, `documentation` (seul `analysis` a été
  appelé).
- Comportement en erreur : Ollama arrêté (message `unreachable` attendu).
- Latence de bout en bout sur une tâche réelle (chargement à froid du modèle).

## Limitations

- Sans état : aucun suivi multi-tours ; chaque délégation doit être autonome.
- Un seul modèle, pas de fallback — indisponibilité = erreur explicite.
- Pas de streaming : réponse complète après génération (jusqu'à 600 s).
- `resources/list` non implémenté (serveur tools-only).
- Le modèle local ne voit pas le dépôt : ses réponses de code/doc doivent être
  validées par Codex avant application.
