#!/bin/sh
# Déploiement idempotent — À N'EXÉCUTER QU'APRÈS « VALIDE LE DÉPLOIEMENT ».
# Sauvegarde, applique, vérifie. Aucun redémarrage implicite.
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
STATE="${OPENCLAW_STATE_DIR:-$HOME/.openclaw}"
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP="$STATE/backups-perso-famille-$STAMP"
PERSO="$STATE/workspace-perso"
PRO="$STATE/workspace"

echo "== 1. Sauvegarde -> $BACKUP"
mkdir -p "$BACKUP"
cp "$STATE/openclaw.json" "$BACKUP/openclaw.json"
cp "$PERSO/AGENTS.md" "$BACKUP/perso-AGENTS.md"
cp "$PERSO/USER.md" "$BACKUP/perso-USER.md"
cp "$PRO/AGENTS.md" "$BACKUP/pro-AGENTS.md"
cp "$PRO/USER.md" "$BACKUP/pro-USER.md"
echo "   ok"

echo "== 2. Outil perso-contacts"
"$HERE/contacts-tool/build.sh" --install

echo "== 3. Workspace Perso"
mkdir -p "$PERSO/famille/personnes" "$PERSO/skills/famille-contacts"
cp "$HERE"/workspace-perso/famille/index.md "$PERSO/famille/index.md"
cp "$HERE"/workspace-perso/famille/personnes/*.md "$PERSO/famille/personnes/"
cp "$HERE"/workspace-perso/skills/famille-contacts/SKILL.md "$PERSO/skills/famille-contacts/SKILL.md"
echo "   ok (idempotent : écrasement des mêmes fichiers)"

echo "== 4. Workspace Pro"
mkdir -p "$PRO/pro"
cp "$HERE"/workspace-pro/pro/index.md "$PRO/pro/index.md"
echo "   ok"

echo "== 5. Configuration (patch validé)"
~/.openclaw/bin/openclaw config patch --file "$HERE/config/openclaw.patch.json"

echo "== 6. Vérifications"
~/.openclaw/bin/openclaw config validate
~/.openclaw/bin/openclaw doctor 2>&1 | grep -i -E "perso_contacts|message tool|error" || true
"$HERE/tests/run-tests.sh"

echo
echo "Terminé. Étapes manuelles restantes :"
echo "  - fusionner les blocs USER.md / AGENTS.md (fichiers *.patch.md)"
echo "  - accorder l'autorisation Contacts au helper (voir DEPLOIEMENT.md)"
echo "  - redémarrer le Gateway : openclaw gateway restart"
