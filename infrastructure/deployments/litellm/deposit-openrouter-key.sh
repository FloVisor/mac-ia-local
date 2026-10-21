#!/bin/sh
# Operator runs interactively over SSH. Never pass a key as an argument.
set +x
set -eu
umask 077
dir=/srv/docker-local/compose/litellm/secrets
test "$(id -u)" = 0
test -d "$dir"
tmp=$(mktemp "$dir/.openrouter-paid.XXXXXX")
trap 'rm -f "$tmp"' EXIT HUP INT TERM
systemd-ask-password 'Clé OpenRouter dédiée LiteLLM (10 USD/mois) :' > "$tmp"
test -s "$tmp"
chmod 600 "$tmp"
mv "$tmp" "$dir/openrouter-paid-api-key"
printf '%s\n' 'Clé déposée en root:root 0600. Aucun appel OpenRouter, aucune activation.'
