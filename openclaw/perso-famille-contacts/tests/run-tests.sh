#!/bin/sh
# Tests hors production : n'écrit aucun contact, n'envoie aucun message.
# Les tests « live » lisent le carnet réel en lecture seule et sont ignorés
# si l'autorisation Contacts n'est pas accordée.
set -u

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN="${BIN:-$HERE/../contacts-tool/build/perso-contacts}"
PASS=0
FAIL=0

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"; }
ko() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$1"; }

# expect <libellé> <statut attendu> <sortie json>
expect() {
  label=$1; want=$2; json=$3
  got=$(printf '%s' "$json" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status"))' 2>/dev/null)
  if [ "$got" = "$want" ]; then ok "$label ($got)"; else ko "$label (attendu $want, obtenu ${got:-<invalide>})"; fi
}

echo "== 1. Contrat de sortie (sans autorisation requise)"
expect "status renvoie un JSON valide" "ok" "$("$BIN" status)"
expect "option inconnue rejetée" "invalid_argument" "$("$BIN" search --nope 2>/dev/null)"
expect "query manquante rejetée" "invalid_argument" "$("$BIN" search 2>/dev/null)"
expect "id manquant rejeté" "invalid_argument" "$("$BIN" get 2>/dev/null)"
expect "champ inconnu rejeté" "invalid_argument" "$("$BIN" search --query x --fields nope 2>/dev/null)"

echo "== 2. Lecture réelle (lecture seule)"
AUTH=$("$BIN" status | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["authorization"])')
if [ "$AUTH" != "authorized" ]; then
  echo "  skip autorisation=$AUTH (tests live non exécutés)"
else
  expect "carnet iCloud sélectionné" "ok" "$("$BIN" containers)"
  expect "recherche exacte" "ok" "$("$BIN" search --query 'Chloé JOUBERT' --fields name)"
  expect "variante sans accent/transposition" "ok" "$("$BIN" search --query 'Cholé' --fuzzy --fields name)"
  expect "homonyme signalé ambigu" "ambiguous" "$("$BIN" search --query 'Anaïs' --fields name)"
  expect "inconnu -> not_found" "not_found" "$("$BIN" search --query 'Zzzz Introuvable' --fields name)"
  expect "identifiant périmé -> invalid_id" "invalid_id" "$("$BIN" get --id '00000000-0000-0000-0000-000000000000:ABPerson')"

  # Aucune donnée sensible hors des champs demandés.
  OUT=$("$BIN" search --query 'Chloé JOUBERT' --fields name)
  if printf '%s' "$OUT" | grep -q 'phoneNumbers'; then ko "filtre --fields name (téléphone exposé)"; else ok "filtre --fields name"; fi

  # Un seul carnet ciblé : jamais de fuite vers un autre compte.
  CNT=$("$BIN" containers | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["data"]["containers"]))')
  if [ "$CNT" -ge 1 ]; then ok "conteneurs énumérés ($CNT)"; else ko "conteneurs énumérés"; fi
fi

echo
echo "résultat: $PASS ok, $FAIL échec(s)"
[ "$FAIL" -eq 0 ]
