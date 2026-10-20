#!/bin/sh
# Retour arrière — restaure la sauvegarde indiquée.
# Usage: ./rollback.sh <dossier de sauvegarde>
set -eu
[ $# -eq 1 ] || { echo "usage: $0 <backup-dir>"; exit 2; }
B="$1"
STATE="${OPENCLAW_STATE_DIR:-$HOME/.openclaw}"
[ -f "$B/openclaw.json" ] || { echo "sauvegarde invalide: $B"; exit 2; }

cp "$B/openclaw.json" "$STATE/openclaw.json"
if [ -f "$B/perso-AGENTS.md" ]; then cp "$B/perso-AGENTS.md" "$STATE/workspace-perso/AGENTS.md"; fi
if [ -f "$B/perso-USER.md" ]; then cp "$B/perso-USER.md" "$STATE/workspace-perso/USER.md"; fi
if [ -f "$B/pro-AGENTS.md" ]; then cp "$B/pro-AGENTS.md" "$STATE/workspace/AGENTS.md"; fi
if [ -f "$B/pro-USER.md" ]; then cp "$B/pro-USER.md" "$STATE/workspace/USER.md"; fi

rm -rf "$STATE/workspace-perso/famille" "$STATE/workspace-perso/skills/famille-contacts"
rm -f "$STATE/workspace/pro/index.md"
rm -f "$HOME/.local/bin/perso-contacts"

echo "restauré depuis $B — redémarrer le Gateway : openclaw gateway restart"
