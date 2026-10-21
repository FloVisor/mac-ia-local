#!/bin/sh
set -eu
MCP_GATEWAY_AUTH_TOKEN="$(cat /run/secrets/gateway_token)"
[ -n "$MCP_GATEWAY_AUTH_TOKEN" ]
export MCP_GATEWAY_AUTH_TOKEN
exec /docker-mcp gateway run "$@"
