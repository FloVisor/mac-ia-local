# local-llm-mcp — captures de validation

Date : 2026-10-17 · Probe JSON-RPC stdio direct (read-only, aucune écriture hors captures).

## Fichiers

- `stdio-test.stdout.jsonl` — réponses brutes du serveur : `initialize`, `tools/list`, `tools/call delegate` (profile=analysis).
- `stderr.log` — log de démarrage du serveur (`starting: model=muse-glimmer:30b-mlx base_url=http://127.0.0.1:11434/v1 effort=high`).
  Non versionné (exclu par `*.log` dans `.gitignore`) ; contenu :
  `[local-llm-mcp] starting: model=muse-glimmer:30b-mlx base_url=http://127.0.0.1:11434/v1 effort=high`.

## Résultats

| Test | Résultat |
|---|---|
| initialize | PASS — protocolVersion 2024-11-05, serverInfo local-llm-mcp 1.0.0 |
| tools/list | PASS — 1 tool `delegate` (5 profils : analysis, coding, documentation, review, testing) |
| tools/call delegate (analysis) | PASS — `[profile=analysis model=muse-glimmer:30b-mlx reasoning_effort=high] DELEGUE` (réponse réelle du modèle via Ollama) |

## Contexte

- Session Codex du 2026-10-17 08:21 : découverte du namespace `mcp__local_llm` et de
  l'outil `delegate` confirmée (tool_search_output) ; `resources/list` correctement
  refusé (`-32601`, serveur tools-only). Aucun appel `delegate` consigné comme exécuté
  dans cette session — d'où le probe stdio direct ci-dessus, qui valide le chemin
  complet serveur → Ollama → muse-glimmer:30b-mlx.
- Reste à valider : appel `delegate` depuis Codex, profils autres qu'analysis,
  comportement Ollama arrêté, latence de bout en bout.
