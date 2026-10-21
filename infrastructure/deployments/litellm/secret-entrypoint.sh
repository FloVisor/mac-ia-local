#!/bin/sh
set -eu
LITELLM_MASTER_KEY="$(cat /run/secrets/litellm_master_key)"
LITELLM_SALT_KEY="$(cat /run/secrets/litellm_salt_key)"
UI_PASSWORD="$(cat /run/secrets/litellm_bootstrap_password)"
DATABASE_URL="postgresql://litellm:$(cat /run/secrets/litellm_db_password)@litellm_postgres:5432/litellm"
export LITELLM_MASTER_KEY LITELLM_SALT_KEY UI_PASSWORD DATABASE_URL
exec /app/docker/prod_entrypoint.sh "$@"
