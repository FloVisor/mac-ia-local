// Test ciblé du code des bundles préparés/servis, sans chargement du DOM ni écriture Gateway.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const dir=process.argv[2];
const core=fs.readFileSync(path.join(dir,'control-ui-core-JPg57hSA.js'),'utf8');
const page=fs.readFileSync(path.join(dir,'control-ui-boot-new-D7uPHpvm.js'),'utf8');
function between(s,a,b){const x=s.indexOf(a);assert(x>=0,a);const y=s.indexOf(b,x);assert(y>x,b);return s.slice(x,y)}
const code=between(core,'function groupRouteScopes(','var Gh,Kh,qh;')+'\n'+
 between(page,'function W(','function Eo(')+'\n'+
 between(page,'function groupRouteStore(','function No(')+'\n'+
 between(page,'async function Jm(','function Ym()')+'\n'+
 page.slice(page.indexOf('function Jl('),page.indexOf('function ',page.indexOf('function Jl(')+10));
let epoch=1, mode='normal', requests=[], delayedRelease;
const rows={main:[{name:'Pro A',position:0}],perso:[{name:'Appartement VARS',position:0},{name:'Projet Jardin 2026',position:1}]};
const client={async request(method,params){
 assert.deepEqual(Object.keys(params),['agentId']);assert(params.agentId in rows);
 requests.push({method,agentId:params.agentId});
 if(mode==='failure'&&params.agentId==='perso')throw Error('simulated unavailable');
 if(mode==='delay'&&method==='sessions.groups.list'&&params.agentId==='perso')await new Promise(resolve=>{delayedRelease=resolve});
 if(method==='sessions.groups.list')return {groups:structuredClone(rows[params.agentId]),sectionOrder:[]};
 assert.equal(method,'sessions.groups.defaults');
 return {defaults:rows[params.agentId].map(x=>({name:x.name,cwd:'/workspace/'+params.agentId,worktree:false}))};
}};
const connection={capture:()=>({epoch,client}),isCurrent:s=>s.epoch===epoch&&s.client===client};
const snapshot=()=>({});
const context=vm.createContext({Map,JSON,Promise,Error,clearTimeout,setTimeout,
 Kh:'sessions.groups.list',qh:'sessions.groups.defaults',Ye:()=>true,Fh:()=>({allowed:true}),Uh:()=>[],
 Lh:d=>d.groups,zh:d=>d.sectionOrder??[],Rh:(groups,d)=>groups.map(g=>({...g,...d.defaults.find(x=>x.name===g.name)})),
 vo:s=>{const p=new URLSearchParams(s);return {agentId:p.get('agent')??'',group:p.get('group')??'',catalogId:''}},
 Ce:agents=>agents,Al:()=>undefined,Y:String,z:s=>s?.trim().toLowerCase(),w:s=>s,
});
vm.runInContext(code,context);
let publications=0;
const scopes=context.groupRouteScopes(context.Wh,{connection,snapshot,refreshRows(){throw Error('unexpected write refresh')},retryDelayMs:()=>null},()=>publications++);
const sessions={groupsForAgent:id=>scopes.get(id),state:{groupSettings:rows.main},groupsGeneration:()=>999,groupsStatus:()=> 'ready'};
const e={sessions,agents:{state:{selectedId:'main',agentsList:{defaultId:'main',agents:[{id:'main'},{id:'perso'}]}}}};
const load=(agent,group)=>context.Jm(e,new URLSearchParams({agent,group}).toString());
const results=[];
function pass(name){results.push({test:name,status:'PASS'})}
// Global Pro + route Perso : les deux dossiers doivent rester résolus à la
// soumission, sans écraser le catalogue de la sidebar Pro.
for(const group of rows.perso.map(x=>x.name)){
 const data=await load('perso',group);
 assert.equal(data.groupStatus,'resolved');assert.equal(data.groupAgentId,'perso');
 assert.equal(context.Do(data,sessions),false);assert.equal(context.Ao(data,sessions),false);
 assert.equal(context.jo(data,sessions),group);
 assert.equal(data.groupCwd,'/workspace/perso');
}
assert.deepEqual(sessions.state.groupSettings,rows.main);pass('two Perso folders with global Pro; loader, submit guard, sidebar isolation');
const denied=await load('main',rows.perso[0].name);assert.equal(denied.groupStatus,'missing');assert.equal(context.Ao(denied,sessions),true);pass('Pro cannot resolve a Perso folder');
const pro=await load('main','Pro A');assert.equal(context.Ao(pro,sessions),false);
const perso=await load('perso',rows.perso[0].name);
e.agents.state.selectedId='perso';assert.equal(context.Do(pro,sessions),false);
e.agents.state.selectedId='main';assert.equal(context.Do(perso,sessions),false);pass('global selection changes do not invalidate the other route');
let before=requests.length;sessions.groupsForAgent('perso').groupsInvalidate();assert.equal(context.Do(perso,sessions),true);
const fresh=await load('perso',rows.perso[0].name);assert.equal(context.Do(fresh,sessions),false);assert.equal(requests.length,before+2);pass('retry invalidation purges cache and reloads list plus defaults');
mode='failure';sessions.groupsForAgent('perso').groupsInvalidate();const unavailable=await load('perso',rows.perso[0].name);
assert.equal(unavailable.groupStatus,'unavailable');assert.equal(context.Ao(unavailable,sessions),true);
assert.equal(context.Ao(pro,sessions),false);pass('failure stays closed within Perso; no Pro fallback');
mode='normal';sessions.groupsForAgent('perso').groupsInvalidate();assert.equal((await load('perso',rows.perso[1].name)).groupStatus,'resolved');pass('recovery after unavailable');
// Deux routes concurrentes, la réponse tardive de Perso reste dans son scope.
mode='delay';sessions.groupsForAgent('perso').groupsInvalidate();sessions.groupsForAgent('main').groupsInvalidate();
const pending=load('perso',rows.perso[0].name);await Promise.resolve();
const other=await load('main','Pro A');assert.equal(other.groupStatus,'resolved');
delayedRelease();const late=await pending;assert.equal(late.groupStatus,'resolved');
assert.equal(context.Do(other,sessions),false);assert.equal(context.Do(late,sessions),false);pass('concurrent Pro/Perso and delayed response isolated');
assert.throws(()=>sessions.groupsForAgent(''),/Missing group route agent/);pass('missing identity fails closed');
assert(page.includes('groupRouteStore(t,e?.sessions)?.groupsInvalidate()'));
assert(page.includes('groupRouteStore(e.data,e.context?.sessions)?.groupsInvalidate()'));
const mismatch=context.Jl({preferenceLoading:false},{agentId:'main',placementPreferenceReady:true,modelControl:{isRestoringPreference:()=>false}}, {mentions:[],pendingPlacement:{},requiresModelSetup:()=>false}, {data:{group:'Appartement VARS',groupAgentId:'perso'},context:{sessions}});
assert.equal(mismatch.gate,'agent-not-allowed');pass('retry paths wired and actual submit guard blocks changed identity');
mode='normal';e.agents.state.selectedId='perso';
const implicitPro=await context.Jm(e,new URLSearchParams({group:'Pro A'}).toString());
assert.equal(implicitPro.groupAgentId,'main','omitted route agent must use form default, not global Perso');
assert.equal(implicitPro.groupStatus,'resolved');assert.equal(context.Ao(implicitPro,sessions),false);
pass('implicit Pro route with global Perso uses form default');
for(const group of rows.perso.map(x=>x.name)){
 const denyImplicit=await context.Jm(e,new URLSearchParams({group}).toString());
 assert.equal(denyImplicit.groupAgentId,'main');assert.equal(denyImplicit.groupStatus,'missing');
}
pass('implicit Pro cannot resolve Perso folders');
const savedAgents=e.agents.state.agentsList;let hydrationCalls=0;
e.agents.ensureList=async()=>{hydrationCalls++;return savedAgents};e.agents.state.agentsList=null;
const cold=await context.Jm(e,new URLSearchParams({group:'Pro A'}).toString());
assert.equal(cold.groupAgentId,'main');assert.equal(cold.groupStatus,'resolved');assert.equal(hydrationCalls,1);
pass('cold implicit Pro hydrates agent defaults before loading folders');
e.agents.state.agentsList=savedAgents;
mode='normal';before=requests.length;epoch++;
const afterReconnect=await load('perso',rows.perso[0].name);
assert.equal(afterReconnect.groupStatus,'resolved');assert.equal(requests.length,before+2);pass('Gateway epoch change reloads scoped cache');
scopes.dispose();console.log(JSON.stringify({results,assertedTests:results.length,publications,requests:requests.length},null,2));
