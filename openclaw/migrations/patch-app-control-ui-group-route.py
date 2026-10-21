#!/usr/bin/env python3
"""Correctif complémentaire ciblé : dossiers du formulaire liés à son agent.

Aucun changement de configuration, de base ou de permission. Ancres strictes,
préparation complète avant écriture, sauvegardes et variantes compressées.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

CORE = 'control-ui-core-JPg57hSA.js'
NEW = 'control-ui-boot-new-D7uPHpvm.js'
MARKER = '/*openclaw-group-route-v1*/'


def replace_once(s, old, new):
    if s.count(old) != 1:
        raise ValueError(f'ancre absente ou ambiguë ({s.count(old)}): {old[:100]}')
    return s.replace(old, new, 1)


# Chaque formulaire possède un store Wh distinct, à identité immuable. Sa
# publication déclenche un rendu, sans remplacer les dossiers de la sidebar.
SCOPES = '''function groupRouteScopes(makeStore, options, notify){const scopes=new Map();return{get(agentId){const id=agentId?.trim();if(!id)throw Error(`Missing group route agent`);if(scopes.has(id))return scopes.get(id);let state={groups:[],groupSettings:[],sectionOrder:[]};const store=makeStore({...options,agentScope:()=>({agentId:id}),readState:()=>state,publish:next=>{state=next;notify()}});const view={get state(){return state},groupsLoad:store.load,groupsGeneration:store.generation,groupsStatus:store.status,groupsInvalidate:store.invalidate};scopes.set(id,{...view,get state(){return state},dispose:store.dispose});return scopes.get(id)},dispose(){for(const scope of scopes.values())scope.dispose();scopes.clear()}}}'''



DEFAULT_MARKER = '/*openclaw-group-default-v2*/'


def upgrade_default_agent(new):
    if DEFAULT_MARKER in new:
        return new
    old = 'let i=vo(t),a=``,o=!1,s,c,l,groupAgentId=i.agentId||e.agents.state.selectedId||e.agents.state.agentsList?.defaultId;if(i.group){'
    replacement = DEFAULT_MARKER + 'let i=vo(t),a=``,o=!1,s,c,l,groupAgents=e.agents.state.agentsList??(i.group?await e.agents.ensureList():null),groupRows=Ce(groupAgents?.agents??[]),groupDefault=groupRows.some(e=>e.id===groupAgents?.defaultId)?groupAgents.defaultId:groupRows[0]?.id,groupAgentId=Mo(i,groupRows,groupDefault);if(i.group&&groupAgentId){'
    new = replace_once(new, old, replacement)
    new = replace_once(new, 'o=u?.worktree===!0}let u={...i,requestedAgentId:i.agentId,groupAgentId,',
                       'o=u?.worktree===!0}else if(i.group){s=`unavailable`,l=`unavailable`}let u={...i,requestedAgentId:i.agentId,groupAgentId,')
    return new


def transform(core, new):
    if MARKER in core or MARKER in new:
        if MARKER not in core or MARKER not in new:
            raise ValueError('patch partiel : restauration ou diagnostic requis')
        return core, upgrade_default_agent(new)
    if 'agentScope:ag' not in core:
        raise ValueError('correctif agent-scope préalable requis')
    # Le cache antérieur était aussi rempli à loading et survivait à invalidate.
    # Ne réutiliser que les réponses complètes, et purger sur nouvelle tentative.
    core = replace_once(core, 'l=()=>{c(),r+=1,i=`loading`,e.publish({...e.readState()})}',
                        'l=()=>{c(),ac.delete(JSON.stringify(ag())),r+=1,i=`loading`,e.publish({...e.readState()})}')
    core = replace_once(core, 'ac.set(ah,{settings:[...t],sectionOrder:[...n]});',
                        'r===`ready`?ac.set(ah,{settings:[...t],sectionOrder:[...n]}):ac.delete(ah);')
    core = replace_once(core, 'if(ac.has(k)){t=r.epoch,ah=k;',
                        'if(t===r.epoch&&ac.has(k)){t=r.epoch,ah=k;')
    core = replace_once(core, 'function Wh(e){', MARKER + SCOPES + 'function Wh(e){')
    core = replace_once(core, 'retryDelayMs:Zg,agentScope:ag}),ee=',
                        'retryDelayMs:Zg,agentScope:ag}),routeGroups=groupRouteScopes(Wh,{connection:l,snapshot:()=>e.snapshot,refreshRows:()=>j.refresh({...j.lastOptions(),force:!0}),retryDelayMs:Zg},()=>E({...r})),ee=')
    core = replace_once(core, 'groupsLoad:M.load,groupsGeneration:M.generation,',
                        'groupsForAgent:agentId=>routeGroups.get(agentId),groupsLoad:M.load,groupsGeneration:M.generation,')
    core = replace_once(core, 'M.dispose(),b=null,x=null,', 'M.dispose(),routeGroups.dispose(),b=null,x=null,')
    # Le scope reste celui qui a résolu la route, même si un autre onglet
    # change la sélection globale. Aucun fallback vers le catalogue d'un autre.
    helper = 'function groupRouteStore(data,sessions){return data?.groupAgentId?sessions?.groupsForAgent(data.groupAgentId):sessions}'
    new = replace_once(new, 'function Do(e,t){', MARKER + helper + 'function Do(e,t){t=groupRouteStore(e,t);')
    new = replace_once(new, 'function Oo(e,t){', 'function Oo(e,t){t=groupRouteStore(e,t);')
    old = 'let i=vo(t),a=``,o=!1,s,c,l;if(i.group){let t=e.sessions.groupsGeneration(),n=await e.sessions.groupsLoad();c=e.sessions.groupsGeneration(),l=e.sessions.groupsStatus();'
    repl = 'let i=vo(t),a=``,o=!1,s,c,l,groupAgentId=i.agentId||e.agents.state.selectedId||e.agents.state.agentsList?.defaultId;if(i.group){let scope=e.sessions.groupsForAgent(groupAgentId),t=scope.groupsGeneration(),n=await scope.groupsLoad();c=scope.groupsGeneration(),l=scope.groupsStatus();'
    new = replace_once(new, old, repl)
    new = replace_once(new, 'let u={...i,requestedAgentId:i.agentId,groupStatus:s,',
                        'let u={...i,requestedAgentId:i.agentId,groupAgentId,groupStatus:s,')
    # Les retries doivent invalider et consulter le même scope que le loader.
    for old, repl in (
        ('e?.sessions.groupsStatus()===`loading`', 'groupRouteStore(t,e?.sessions)?.groupsStatus()===`loading`'),
        ('e?.sessions.groupsInvalidate()', 'groupRouteStore(t,e?.sessions)?.groupsInvalidate()'),
        ('e.context?.sessions.groupsStatus()===`loading`', 'groupRouteStore(e.data,e.context?.sessions)?.groupsStatus()===`loading`'),
        ('e.context?.sessions.groupsInvalidate()', 'groupRouteStore(e.data,e.context?.sessions)?.groupsInvalidate()'),
    ):
        # e?.sessions.groupsStatus occurs in two retry functions.
        count = new.count(old)
        expected = 2 if old == 'e?.sessions.groupsStatus()===`loading`' else 1
        if count != expected:
            raise ValueError(f'ancre retry ({count} au lieu de {expected}): {old}')
        new = new.replace(old, repl)
    # Changer l'agent dans un formulaire lié à un dossier ne doit jamais créer
    # une conversation de l'autre agent dans ce dossier.
    new = replace_once(new, 'if(Ao(r.data,r.context?.sessions))return{gate:`route-pending`,',
                        'if(r.data?.group&&z(r.data.groupAgentId)!==z(t.agentId))return{gate:`agent-not-allowed`,reason:w(`newSession.catalogUnavailable`)};if(Ao(r.data,r.context?.sessions))return{gate:`route-pending`,')
    return core, upgrade_default_agent(new)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--assets', type=Path, default=Path('/Applications/OpenClaw.app/Contents/Resources/runtime/lib/node_modules/openclaw/dist/control-ui/assets'))
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--prepare', type=Path, help='préparer les deux bundles sans appliquer')
    args = ap.parse_args()
    originals = {name: (args.assets / name).read_text() for name in (CORE, NEW)}
    candidates = dict(zip((CORE, NEW), transform(originals[CORE], originals[NEW])))
    changed = [name for name in candidates if candidates[name] != originals[name]]
    if args.check:
        print(json.dumps({'patched': not changed, 'files_needing_patch': changed}))
        return 0 if not changed else 1
    if args.prepare:
        args.prepare.mkdir(parents=True, exist_ok=True)
        for name, value in candidates.items():
            (args.prepare / name).write_text(value)
        print(json.dumps({'prepared': str(args.prepare), 'changed': changed}))
        return 0
    # Toutes les variantes sont prêtes et vérifiées syntaxiquement avant
    # modification. Aucun écrasement d'une sauvegarde existante divergente.
    with tempfile.TemporaryDirectory(prefix='openclaw-group-route-') as tmp:
        planned = {}
        for name in changed:
            raw = candidates[name].encode()
            staged = Path(tmp) / name
            staged.write_bytes(raw)
            subprocess.run(['node', '--input-type=module', '--check'], input=raw, check=True, capture_output=True)
            br = subprocess.run(['brotli', '-q', '11', '-c'], input=raw, check=True, capture_output=True).stdout
            for suffix, data in (('', raw), ('.gz', gzip.compress(raw, mtime=0)), ('.br', br)):
                target = args.assets / (name + suffix)
                old = target.read_bytes() if target.exists() else None
                backup_suffix = '.bak-group-default-v2' if MARKER in originals[name] else '.bak-group-route-v1'
                backup = Path(str(target) + backup_suffix)
                if old is not None and backup.exists() and backup.read_bytes() != old:
                    raise ValueError(f'sauvegarde divergente : {backup}')
                planned[target] = (data, old, backup)
        applied = []
        try:
            for target, (data, old, backup) in planned.items():
                if old is not None and not backup.exists():
                    backup.write_bytes(old)
                applied.append(target)
                target.write_bytes(data)
        except Exception:
            for target in reversed(applied):
                old = planned[target][1]
                if old is not None:
                    target.write_bytes(old)
                else:
                    target.unlink(missing_ok=True)
            raise
    print(json.dumps({'patched': True, 'changed': changed, 'sha256': {n: hashlib.sha256(candidates[n].encode()).hexdigest() for n in candidates}}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
