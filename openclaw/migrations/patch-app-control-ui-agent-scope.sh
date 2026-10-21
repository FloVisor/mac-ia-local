#!/bin/sh
# Patche le bundle Control UI embarqué dans OpenClaw.app pour que le store de
# dossiers envoie l'agent courant (agentId) à sessions.groups.list/defaults et
# se recharge au changement d'agent.
#
# Nécessite l'autorisation macOS « Gestion des apps » pour le terminal appelant.
# À réappliquer après chaque mise à jour de l'application.
#
# Usage : sh patch-app-control-ui-agent-scope.sh [--check]
set -eu

APP="/Applications/OpenClaw.app/Contents/Resources/runtime/lib/node_modules/openclaw/dist/control-ui/assets"
CORE="$APP/control-ui-core-JPg57hSA.js"

[ -f "$CORE" ] || { echo "introuvable: $CORE" >&2; exit 1; }

if grep -q "agentScope:ag" "$CORE"; then
	echo "agent-scope déjà patché"
	exec python3 "$(dirname "$0")/patch-app-control-ui-group-route.py" ${1:+"$1"}
fi

if [ "${1:-}" = "--check" ]; then
	echo "non patché"
	exit 1
fi

cp "$CORE" "$CORE.bak-agent-scope"

python3 - "$CORE" <<'PY'
import sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()

edits = [
    # 1. helper local au store de dossiers, alimenté par le callback agentScope
    ("function Wh(e){let t=-1,n=0,r=0,i=`idle`,a=null,o=null,",
     "function Wh(e){let ag=()=>e.agentScope?.()??{},ah=null,t=-1,n=0,r=0,i=`idle`,a=null,o=null,"),
    # 2. lecture du catalogue et des defaults scopée par agent
    ("let i=await t.client.request(Kh,{});", "let i=await t.client.request(Kh,ag());"),
    ("let i=await t.client.request(qh,{});", "let i=await t.client.request(qh,ag());"),
    # 3. mutations scopées par agent
    ("delete:t=>h(`sessions.groups.delete`,{name:t},",
     "delete:t=>h(`sessions.groups.delete`,{name:t,...ag()},"),
    ("put:(e,t)=>h(`sessions.groups.put`,{names:[...e],...t===void 0?{}:{sectionOrder:[...t]}},g)",
     "put:(e,t)=>h(`sessions.groups.put`,{names:[...e],...t===void 0?{}:{sectionOrder:[...t]},...ag()},g)"),
    ("rename:(t,n)=>h(`sessions.groups.rename`,{name:t,to:n},",
     "rename:(t,n)=>h(`sessions.groups.rename`,{name:t,to:n,...ag()},"),
    ("update:(t,n)=>h(`sessions.groups.update`,{name:t,...n},",
     "update:(t,n)=>h(`sessions.groups.update`,{name:t,...n,...ag()},"),
    # 4. helper de portée agent dans la fabrique du store (selectedId vide =
    #    agent par défaut) puis injection du callback au point de création
    ("n.bootRecord?.profileId,s=()=>{",
     "n.bootRecord?.profileId,ag=()=>{let n=t?.state?.selectedId?.trim()||ga({hello:e.snapshot.hello});return n?{agentId:n}:{}},s=()=>{"),
    ("retryDelayMs:Zg})", "retryDelayMs:Zg,agentScope:ag})"),
    # 5. le cache de chargement doit dépendre de l'agent, sinon le second
    #    onglet réutilise la réponse du premier (epoch de connexion inchangé)
    ("if(t===r.epoch)return a??e.readState().groupSettings;",
     "if(t===r.epoch&&ah===JSON.stringify(ag()))return a??e.readState().groupSettings;"),
    ("let o=Ye(e.snapshot(),Kh);s();let c=++n;",
     "let o=Ye(e.snapshot(),Kh);s();ah=JSON.stringify(ag());let c=++n;"),
    # 6. ne jamais publier une réponse chargée pour un autre agent : les deux
    #    onglets partagent le même état, le dernier chargement écraserait l'autre
    ("u=(t,n,r)=>{let a=e.readState(),o=t.map(e=>e.name),",
     "u=(t,n,r)=>{if(ah!==JSON.stringify(ag()))return;let a=e.readState(),o=t.map(e=>e.name),"),
    # 7. cache par agent : les deux onglets partagent le store, un seul jeu de
    #    dossiers ne peut pas servir les deux (le dernier chargé gagne)
    ("function Wh(e){let ag=()=>e.agentScope?.()??{},ah=null,t=-1,n=0,r=0,i=`idle`,a=null,o=null,",
     "function Wh(e){let ag=()=>e.agentScope?.()??{},ah=null,ac=new Map(),t=-1,n=0,r=0,i=`idle`,a=null,o=null,"),
    ("u=(t,n,r)=>{if(ah!==JSON.stringify(ag()))return;let a=e.readState(),o=t.map(e=>e.name),",
     "u=(t,n,r)=>{if(ah!==JSON.stringify(ag()))return;ac.set(ah,{settings:[...t],sectionOrder:[...n]});let a=e.readState(),o=t.map(e=>e.name),"),
    ("p=async()=>{let r=e.connection.capture();if(!r)return null;if(t===r.epoch&&ah===JSON.stringify(ag()))return a??e.readState().groupSettings;let o=Ye(e.snapshot(),Kh);s();ah=JSON.stringify(ag());let c=++n;",
     "p=async()=>{let r=e.connection.capture();if(!r)return null;let k=JSON.stringify(ag());if(ac.has(k)){t=r.epoch,ah=k;let c=ac.get(k);u(c.settings,c.sectionOrder,`ready`);return c.settings}if(t===r.epoch&&ah===k)return a??e.readState().groupSettings;let o=Ye(e.snapshot(),Kh);s();ah=k;let c=++n;"),
    # 8. rechargement des dossiers au changement d'agent
    ("he=Mf(t,(n,r)=>{s(),T(),n&&b===e.snapshot.client&&j.refreshSelection(()=>t.state.selectedId,r)})",
     "he=Mf(t,(n,r)=>{s(),T(),M.invalidate(),M.load(),n&&b===e.snapshot.client&&j.refreshSelection(()=>t.state.selectedId,r)})"),
]

for old, new in edits:
    if s.count(old) != 1:
        raise SystemExit(f"ancre absente ou ambiguë ({s.count(old)}): {old[:60]}")
    s = s.replace(old, new, 1)

open(path, "w", encoding="utf-8").write(s)
print("patch appliqué")
PY

# Le gateway sert les variantes précompressées : sans elles, le patch est ignoré.
brotli -f -q 11 -o "$CORE.br" "$CORE"
gzip -9 -c "$CORE" > "$CORE.gz"

python3 "$(dirname "$0")/patch-app-control-ui-group-route.py"
echo "OK — recharger la fenêtre OpenClaw (sans réinitialiser de session)"
