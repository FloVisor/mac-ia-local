'use strict';
const {spawn} = require('child_process');
const path = require('path');
const crypto = require('crypto');
let nodes = [], worker, pending = false, buffer = '', revision = '', next = 0, error = '';
const interval = 5000;
const UNATTACHED='p3c-unattached';
function projected(all) { return all.some(n=>n.kind==='mcp_delegation' && !n.parent) ? [...all.map(n=>n.kind==='mcp_delegation' && !n.parent ? {...n,parent:UNATTACHED,unattached:true}:n),{id:UNATTACHED,kind:'session_reference',state:'unknown',unattached:true}] : all; }
function refresh() {
  if (/^(off|0|false)$/i.test(process.env.AGENT_STANDUP_CODEX || '') || (process.env.AGENT_STANDUP_PROJECTS && !process.env.AGENT_STANDUP_CODEX && !process.env.CODEX_HOME)) return;
  if (Date.now() < next || pending) return;
  next = Date.now() + interval;
  if (!worker) {
    worker = spawn('python3', [path.join(__dirname, 'observer/collector_runner.py')], {
      stdio: ['pipe', 'pipe', 'ignore'], env: {PATH: process.env.PATH, HOME: process.env.HOME,
        ...(process.env.CODEX_HOME ? {CODEX_HOME:process.env.CODEX_HOME} : {}),
        ...(process.env.AGENT_STANDUP_CODEX ? {AGENT_STANDUP_CODEX:process.env.AGENT_STANDUP_CODEX} : {}),
        ...(process.env.P3C_ROUTER_DB ? {P3C_ROUTER_DB:process.env.P3C_ROUTER_DB} : {})}
    });
    worker.stdout.on('data', chunk => {
      buffer += chunk;
      if (buffer.length > 4*1024*1024) { shutdown(); error='collector_overflow'; return; }
      let i;
      while ((i=buffer.indexOf('\n')) >= 0) {
        const line=buffer.slice(0,i); buffer=buffer.slice(i+1); pending=false;
        try {
          const d=JSON.parse(line); nodes=Array.isArray(d.nodes) ? d.nodes : [];
          error=(d.errors || []).join(',');
          // Durations update in the UI; exclude wall-clock-only fields from invalidation.
          revision=crypto.createHash('sha256').update(JSON.stringify(nodes.map(n=>({...n,duration_ms:undefined})))).digest('hex');
        } catch { error='collector_invalid'; }
      }
    });
    const fail=()=>{worker=null;pending=false;nodes=[];revision='unavailable';error='collector_unavailable';next=Infinity;};
    worker.on('error',fail); worker.on('exit',fail); worker.stdin.on('error',()=>{pending=false;});
  }
  if (worker.stdin.writable) {pending=true;worker.stdin.write('refresh\n');}
}
function shutdown(){ if(worker){worker.removeAllListeners('exit');worker.kill();worker=null;} pending=false; }
const uid=n => (n.kind==='mcp_delegation'?'mcp-':'cx-')+(n.task_id || n.id);
function descendants(root, all=nodes) {
  const found = new Set([root]), result=[];
  for(let count=0;count<all.length;count++) {
    let added=false;
    for(const n of all) if(n.id!==root && n.parent && found.has(n.parent) && !found.has(n.id)) {found.add(n.id);result.push(n);added=true;}
    if(!added) break;
  }
  return result;
}
function decorate(n, id, parent) {
  const native=n.kind==='native_subagent', reference=n.kind==='session_reference';
  const task=n.agent_path || n.role || n.profile || (reference ? 'Trace de session absente' : 'Tâche détaillée non exposée');
  return {id,parent,own:n.nickname || (native?'Codex '+n.id.slice(0,8):'llm-router'),
    name:n.nickname || (native?'Codex '+n.id.slice(0,8):'llm-router'),
    role:task,type:native?'codex-native':reference?'session-reference':'mcp-delegation',
    p3c:{...n,...(n.unattached?{parent:null}:{}),category:native?'Sous-agent Codex':reference?'Session référencée':n.kind==='session'?'Session Codex':'Tâche MCP · llm-router',task,
      model_label:n.actual_model ? n.actual_model+' · confirmé' : (n.model || n.alias || 'modèle inconnu')+' · '+(n.kind==='mcp_delegation'?'demandé / alias':'déclaré'),
      executed_label:n.actual_model || 'inconnu',provider_label:n.provider || 'inconnu'}};
}
function enrich(tl, all=nodes) {
  all=projected(all);
  const root=all.find(n=>n.id===tl.id), selected=descendants(tl.id,all);
  const ids=new Map([[tl.id,'main'],...selected.map(n=>[n.id,uid(n)])]);
  tl.agents=tl.agents.map(a=>a.id==='main' && root ? {...a,p3c:decorate(root,'main',null).p3c}:a);
  const events=[];
  for(const n of selected) {
    const id=ids.get(n.id), parent=ids.get(n.parent);
    if(!parent) continue;
    tl.agents.push(decorate(n,id,parent));
    const hist=n.history || [], start=(n.started || hist[0]?.at || n.updated || Date.now()/1000)*1000;
    events.push({ts:start,agent:parent,to:id,kind:'order',bg:true,text:n.agent_path || n.profile || 'Tâche détaillée non exposée',title:n.nickname || n.profile || 'Codex',k:'p3c/order/'+id,p3c:true});
    for(let i=0;i<hist.length;i++) if(hist[i].at!=null) events.push({ts:hist[i].at*1000,agent:id,to:parent,kind:'p3cstate',state:hist[i].state,k:'p3c/state/'+id+'/'+i,p3c:true});
    if(!hist.length) events.push({ts:start,agent:id,to:parent,kind:'p3cstate',state:n.state,k:'p3c/state/'+id+'/current',p3c:true});
    // No synthetic report, output text or fake usage event.
  }
  tl.events=[...tl.events,...events].sort((a,b)=>a.ts-b.ts);
  const first=tl.events[0]?.ts || 0;
  tl.events=tl.events.map(e=>({...e,t:Math.max(0,e.ts-first)}));
  tl.durationMs=Math.max(0,(tl.events.at(-1)?.ts || first)-first);
  tl.p3c={error,revision};
  return tl;
}
function references(){refresh();return projected(nodes).filter(n=>n.kind==='session_reference');}
function hasSession(id){refresh();return projected(nodes).some(n=>n.id===id && n.kind==='session_reference');}
function includeParentSessions(rows, all, lookup) {
  const result=[...rows], known=new Set(rows.map(r=>r.id));
  // Collector retention remains authoritative; never scan more traces here.
  for(const n of all) if(n.parent && !known.has(n.parent)) {
    const r=lookup(n.parent);
    if(r) {result.push(r);known.add(r.id);}
  }
  return result;
}
function install(codex) {
  const original=codex.sessions, board=codex.boardRow, row=codex.row, originalTitle=codex.title;
  codex.sessions=(limit=80)=>{
    refresh(); const rows=includeParentSessions(original(limit),nodes,row), known=new Set(rows.map(r=>r.id));
    for(const n of references()) if(!known.has(n.id)) rows.push({id:n.id,file:'',size:0,mtime:Math.max(...projected(nodes).filter(x=>x.parent===n.id).map(x=>(x.updated || x.started || 0)*1000)),cwd:'',dir:'',p3cReference:true});
    return rows;
  };
  codex.row=id=>row(id) || codex.sessions().find(r=>r.id===id) || null;
  codex.title=r=>r.p3cReference ? (r.id===UNATTACHED?'Délégations MCP non rattachées':'Session référencée · trace absente · '+r.id.slice(0,8)) : originalTitle(r);
  codex.boardRow=(r,now)=>{
    const children=descendants(r.id,projected(nodes)), active=children.filter(n=>['running','queued'].includes(n.state)).length;
    return r.p3cReference ? {proj:codex.PROJ,id:r.id,title:codex.title(r),mtime:r.mtime,state:active?'working':'idle',subActive:active,subTotal:children.length,source:'codex',ageMs:now-r.mtime,dir:''} : {...board(r,now),subActive:active,subTotal:children.length};
  };
}
module.exports={projected,includeParentSessions,refresh,shutdown,enrich,descendants,decorate,install,references,hasSession,get revision(){refresh();return revision;},get nodes(){return nodes;}};
