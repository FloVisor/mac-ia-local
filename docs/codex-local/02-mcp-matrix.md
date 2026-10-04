# Matrice MCP — état avant migration (non-régression)

Date : 2026-10-03 · Testeur : probe JSON-RPC stdio direct (read-only, aucune opération métier destructive)

## MCP visibles par Codex

Source : `codex mcp list` + `~/.codex/config.toml` + plugins.

| MCP | Transport | Commande (sans secrets) | Statut avant | Test utilisé | Résultat | Latence |
|---|---|---|---|---|---|---|
| **n8n-mcp** | stdio | `~/.codex/bin/n8n-mcp` (wrapper Python → node n8n-mcp 2.91.0, clé via Keychain `codex-n8n-api-key`, N8N_API_URL=127.0.0.1:5678) | enabled, required, startup_timeout 30s | initialize + tools/list + `n8n_health_check` (read-only) | **PASS** — server n8n-documentation-mcp 2.91.0, 28 tools, health_check success=true status=ok | init 0.55s · tools 0.00s · health_check 0.41s |
| **node_repl** | stdio | `/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node_repl` (env: trusted paths, browser backends) | enabled, startup_timeout 120s | initialize + tools/list (read-only) | **PASS** — server rmcp 1.5.0, 4 tools (js, js_add_node_module_dir, js_reset, turn_ended) | init 0.12s · tools 0.00s |
| **cua_repl** | stdio (plugin desktop) | `cua_node/bin/node …/cua-repl.mjs` | enabled (desktop) | non testé directement — lié à l'app desktop, testé indirectement via desktop app-server OK (codex doctor) | PASS indirect (doctor: desktop app-server initialized) | n/a |
| **code-review** | stdio (plugin) | `/bin/sh -c exec "$CODEX_MCP_NODE_PATH" ./server.mjs` | **disabled** (plugin code-review activé mais MCP listé disabled) | non applicable | n/a | n/a |
| **codex_app** | stdio (plugin) | `launch_codex_app_tools_mcp ./server.mjs` | **disabled** | non applicable | n/a | n/a |

## Notes

- `codex doctor` : « MCP 2 server (2 stdio) · 0 disabled » — les 2 serveurs actifs de config.toml (node_repl, n8n-mcp) sont sains.
- n8n-mcp : 28 tools exposés (documentation, search/get/validate nodes, templates, workflows CRUD, health_check). Seul `n8n_health_check` (read-only) a été appelé.
- node_repl : 4 tools JS REPL ; aucun code exécuté (tools/list uniquement).
- cua_repl / codex_app / code-review : MCP gérés par les plugins/desktop, non modifiés par la mission.

## Critère de non-régression post-migration

Rejouer : initialize + tools/list sur n8n-mcp et node_repl, + 1 appel `n8n_health_check`. Résultat attendu : identique (PASS, latences comparables), car les MCP ne dépendent pas du backend LLM.
