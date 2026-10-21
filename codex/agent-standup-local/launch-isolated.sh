#!/bin/bash
set -euo pipefail
P3C_REPO="$(cd "$(dirname "$0")/../.." && pwd)"
P3C_WORK="$P3C_REPO/artifacts/agent-standup-p3c"
P3C_CODE='/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'
export AGENT_STANDUP_PREFS="$P3C_WORK/prefs.json"
export P3C_OFFLINE_TEST=1
"$P3C_CODE" --new-window --user-data-dir "$P3C_WORK/isolated-profile" --extensions-dir "$P3C_WORK/isolated-extensions" --extensionDevelopmentPath "$P3C_WORK/extension" --skip-welcome --skip-release-notes
