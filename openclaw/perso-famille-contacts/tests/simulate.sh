#!/bin/sh
# Simulation de la chaîne de résolution : aucune commande d'envoi n'est exécutée.
# Usage: ./simulate.sh
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN="${BIN:-$HERE/../contacts-tool/build/perso-contacts}"
WS="${WS:-$HERE/../workspace-perso}"

resolve() {
  # resolve <identifiant> <champs> -> imprime la commande d'envoi simulée
  id=$1; fields=$2
  fiche="$WS/famille/personnes/$id.md"
  [ -f "$fiche" ] || { echo "  [refus] fiche inconnue: $id"; return 1; }
  name=$(sed -n 's/^# \(.*\) (`.*`)$/\1/p' "$fiche" | head -1)
  json=$("$BIN" search --query "$name" --fields "$fields" --limit 5)
  status=$(printf '%s' "$json" | python3 -c 'import sys,json;print(json.load(sys.stdin)["status"])')
  case "$status" in
    ok)
      value=$(printf '%s' "$json" | python3 -c '
import sys,json
d=json.load(sys.stdin)["data"]["candidates"][0]
if sys.argv[1]=="phone":
    p=[x["value"] for x in (d.get("phoneNumbers") or []) if x["label"]=="mobile"] or [x["value"] for x in (d.get("phoneNumbers") or [])]
else:
    p=[x["value"] for x in (d.get("emailAddresses") or [])]
print(p[0] if p else "")' "$fields")
      if [ -z "$value" ]; then echo "  [refus] $name : aucun $fields"; return 1; fi
      if [ "$fields" = "phone" ]; then
        echo "  [sim] imsg send --to \"$value\" --text \"<message>\"   # $name"
      else
        echo "  [sim] gog gmail send --to \"$value\" --subject \"<sujet>\" --body \"<corps>\" --attach <rapport.pdf>   # $name"
      fi
      ;;
    ambiguous) echo "  [question] $name : plusieurs fiches, préciser"; return 1 ;;
    not_found) echo "  [refus] $name : aucune fiche Contacts"; return 1 ;;
    *) echo "  [erreur] $name : $status"; return 1 ;;
  esac
}

echo "== Scénario 3 : SMS à Chloé"
resolve chloe phone
echo "== Scénario 6 : SMS à Timéo"
resolve fils phone
echo "== Scénario 7 : mari de Melissa"
resolve benjamin phone
echo "== Scénario 8 : mail à Anaïs (simulation)"
resolve epouse email
