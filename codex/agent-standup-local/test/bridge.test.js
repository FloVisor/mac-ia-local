const {test}=require('node:test');
const assert=require('node:assert/strict');
const p=require('../../../artifacts/agent-standup-p3c/extension/p3c.js');
const root='11111111-1111-1111-1111-111111111111',child='22222222-2222-2222-2222-222222222222',task='33333333-3333-3333-3333-333333333333';
const native={id:child,parent:root,kind:'native_subagent',nickname:'Lovelace',model:'gpt-declared',actual_model:null,agent_path:'/root/map',state:'completed',started:1,history:[{at:1,state:'running'},{at:2,state:'completed'}]};
const mcp={id:'router:'+task,task_id:task,parent:child,kind:'mcp_delegation',profile:'testing',alias:'free/pool',actual_model:null,state:'failed',started:1.5,history:[{at:1.5,state:'queued'},{at:2,state:'running'},{at:3,state:'failed'}]};
const timeline=()=>({id:root,proj:'_codex',agents:[{id:'main'}],events:[]});
test('hierarchy, real names, explicit native/MCP, provenance unknown',()=>{
 const t=p.enrich(timeline(),[native,mcp]);assert.equal(t.agents.length,3);
 const n=t.agents.find(a=>a.type==='codex-native'),m=t.agents.find(a=>a.type==='mcp-delegation');
 assert.equal(n.name,'Lovelace');assert.equal(n.parent,'main');assert.equal(m.parent,n.id);assert.equal(m.p3c.executed_label,'inconnu');assert.equal(m.p3c.state,'failed');
 assert.equal(t.events.filter(e=>e.kind==='order').length,2);assert(!t.events.some(e=>e.kind==='usage'||e.kind==='report'));
});
test('stable event identities on reload; no inferred edges for orphans/cycles',()=>{
 const a=p.enrich(timeline(),[native,mcp]),b=p.enrich(timeline(),[native,mcp]);assert.deepEqual(a,b);assert.equal(new Set(a.events.map(e=>e.k)).size,a.events.length);
 assert.equal(p.descendants(root,[{id:'a',parent:'b'},{id:'b',parent:'a'}]).length,0);
});
test('six source states retained without silence-to-completed inference',()=>{
 for(const state of ['queued','running','completed','failed','cancelled','unknown']) {
  const t=p.enrich(timeline(),[{...native,state,history:[{at:1,state}]}]);assert.equal(t.agents[1].p3c.state,state);assert.equal(t.events.find(e=>e.kind==='p3cstate').state,state);
 }
});

test('historical parents outside recent session cap remain selectable without duplicates',()=>{
 const recent={id:'recent'}, old={id:root};
 const rows=p.includeParentSessions([recent],[native,{...native,id:'sibling'},mcp],id=>id===root?old:null);
 assert.deepEqual(rows,[recent,old]);
 assert.deepEqual(p.includeParentSessions(rows,[native],()=>old),rows);
 assert.deepEqual(p.includeParentSessions([recent],[native],()=>null),[recent]);
});

test('Live Call switcher keeps live states and includes distinct historical sessions',()=>{
 const vm=require('node:vm'),fs=require('node:fs');
 const ctx=vm.createContext({setInterval:()=>{},L:(fr)=>fr});
 vm.runInContext(fs.readFileSync(require('node:path').join(__dirname,'../p3c-ui.js'),'utf8'),ctx);
 const live={proj:'_codex',id:'live',state:'working',title:'Live'};
 const old={proj:'_codex',id:root,title:'Old'};
 const rows=ctx.p3cSessionChoices([live],[live,old,old]);
 assert.equal(rows.length,2);assert.equal(rows[0],live);
 assert.equal(rows[1].state,'idle');assert.equal(rows[1].historical,true);
 assert.match(rows[1].title,/historique/);
});

test('unattached delegation has a selectable container without a Codex parent',()=>{
 const orphan={...mcp,parent:null};
 const all=p.projected([orphan]);
 assert.equal(orphan.parent,null);
 const t=p.enrich({id:'p3c-unattached',agents:[{id:'main'}],events:[]},[orphan]);
 assert.equal(t.agents.length,2);assert.equal(t.agents[1].p3c.state,'failed');
 assert.equal(all.find(n=>n.id==='p3c-unattached').unattached,true);
});
test('terminal state supports vanish bookkeeping while retaining history',()=>{
 const vm=require('node:vm'),fs=require('node:fs');
 const S={clock:42,agents:{},doneAt:{},status:{},waitOn:{main:new Set(['child'])},gone:new Set()};
 const ctx=vm.createContext({S,setInterval:()=>{}});
 vm.runInContext(fs.readFileSync(require('node:path').join(__dirname,'../p3c-ui.js'),'utf8'),ctx);
 ctx.p3cApplyState({agent:'child',to:'main',state:'failed'});
 assert.equal(S.doneAt.child,42);assert.equal(S.status.child,'done');assert.equal(S.waitOn.main.size,0);
});
