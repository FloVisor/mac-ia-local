#!/bin/sh
set -eu
ENCRYPTION_KEY="$(cat /run/secrets/freellmapi_encryption_key)"
export ENCRYPTION_KEY
exec /usr/local/bin/docker-entrypoint.sh "$@"
