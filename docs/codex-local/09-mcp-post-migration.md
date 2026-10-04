# Matrice MCP post-migration — test de non-régression

Date : 2026-10-04 · Rejeu exact de la matrice Phase 2 (02-mcp-matrix.md)

| MCP | Test | Avant migration | Après migration | Régession ? |
|---|---|---|---|---|
| **n8n-mcp** | initialize | OK 0.55s, n8n-documentation-mcp 2.91.0 | **OK 0.56s**, n8n-documentation-mcp 2.91.0 | NON |
| n8n-mcp | tools/list | OK, 28 tools | **OK, 28 tools** | NON |
| n8n-mcp | n8n_health_check (read-only) | OK 0.41s, success=true status=ok | **OK 0.42s, success=true status=ok** | NON |
| **node_repl** | initialize | OK 0.12s, rmcp 1.5.0 | **OK 0.12s**, rmcp 1.5.0 | NON |
| node_repl | tools/list | OK, 4 tools (js, js_add_node_module_dir, js_reset, turn_ended) | **OK, 4 tools** | NON |
| cua_repl | (indirect, doctor) | enabled | **enabled** | NON |
| code-review / codex_app | — | disabled | **disabled** (inchangé) | NON |

`codex doctor` : « MCP 2 server (2 stdio) · 0 disabled » — identique avant/après.

**Résultat : ZÉRO RÉGRESSION.** Les MCP ne dépendent pas du backend LLM (confirmé empiriquement).

Test MCP via Codex + vLLM (Phase 8) : n8n_health_check appelé exactement 1 fois, status `ok` — le tool calling vLLM→MCP fonctionne.
