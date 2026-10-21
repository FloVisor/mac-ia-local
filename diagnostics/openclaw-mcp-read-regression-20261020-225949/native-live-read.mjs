// Isolated qualification using the installed native agent tool factories/hooks.
// No model turn, transcript, business write, or direct database operation.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import plugin from '../../openclaw/send-approval/index.js';
const root=path.join(process.env.HOME,'.openclaw');
const dist=path.join(root,'runtime/current/lib/node_modules/openclaw/dist');
const files=fs.readdirSync(dist);
const load=p=>import(pathToFileURL(path.join(dist,files.find(f=>f.startsWith(p)&&f.endsWith('.mjs')))));
const cfg=JSON.parse(fs.readFileSync(path.join(root,'openclaw.json')));
const {a:initialize}=await load('hook-runner-');
const {n:embedded}=await load('embedded-mode-');
const {l:wrap,Y:broker,v:before}=await load('agent-tools.before-tool-call-');
const {t:after}=await load('hook-helpers-');
const {n:createMcp}=await load('agent-bundle-mcp-materialize-');
const {n:controls,t:catalog,m:ref}=await load('tool-search-DX');
const {i:filter}=await load('tool-policy-match-BX');
const hooks=[];let requests=0;
plugin.register({config:cfg,pluginConfig:cfg.plugins.entries['send-approval'].config,on:(hookName,handler,options)=>hooks.push({pluginId:'send-approval',hookName,handler,priority:options?.priority}),registerTool:()=>{},logger:{info:()=>{}}});
initialize({typedHooks:hooks,hooks:[],plugins:[],trustedToolPolicies:[]});embedded(true);
broker({request:async()=>{requests++;return {decision:'deny'};}});
const ctx={agentId:'main',sessionId:'mcp-read-neutral-qualification',sessionKey:'agent:main:mcp-read-neutral-qualification'};
let runtime;
const records=[];
function value(r){if(r.details?.structuredContent)return r.details.structuredContent;for(const c of r.content??[]){if(c.type==='text'){try{return JSON.parse(c.text);}catch{}}}return r;}
try{
 runtime=await createMcp({cfg,workspaceDir:cfg.agents.entries.main.workspace??path.join(root,'workspace')});
 const catalogRef=ref();
 const all=filter(runtime.tools,{deny:[...(cfg.tools.deny??[]),...(cfg.agents.entries.main.tools.deny??[])]});
 const tools=controls({config:cfg,catalogRef,executeTool:async p=>{
  const result=await p.tool.execute(p.toolCallId,p.input,p.signal);
  await after({toolName:p.toolName,toolCallId:p.toolCallId,startArgs:p.input,result,...ctx});
  return p.acceptResultBeforeProjection(result);
 }});
 const compact=catalog({config:cfg,catalogRef,tools:[...all,...tools],toolHookContext:ctx});
 const dispatch=wrap(compact.tools.find(t=>t.name==='tool_call'),ctx);
 const call=async(name,args)=>{
  const id=crypto.randomUUID();const result=await dispatch.execute(id,{id:name,args});
  await after({toolName:'tool_call',toolCallId:id,startArgs:{id:name,args},result,...ctx});
  const inner=result.details?.result;
  assert.ok(inner&&!result.details?.status&&!inner.details?.status,`${name}: ${JSON.stringify(result).slice(0,900)}`);
  records.push({tool:name,success:true,approvalCount:requests});return value(inner);
 };
 const registries=await call('orion__list_registries',{});
 records.at(-1).registryCount=registries.registries?.length;
 const search=await call('orion__search_tools',{query:'GLPI tickets en cours toutes entités',limit:3});
 records.at(-1).tools=(search.tools??[]).map(t=>({name:t.name,access:t.access,registry:t.registry}));
 await call('orion__get_contract',{tool_name:'search_glpi_ticket',registry:'tool_glpi_wrapper'});
 const tickets=await call('orion__exec_tool',{tool_name:'search_glpi_ticket',registry:'tool_glpi_wrapper',params:{ticket_status:'en_cours',Range:'0-2'}});
 records.at(-1).responseType=typeof tickets;
 records.at(-1).responseKeys=tickets&&typeof tickets==='object'?Object.keys(tickets):[];
 // No ticket titles or contents persisted.
 records.at(-1).responseBytes=Buffer.byteLength(JSON.stringify(tickets));
 records.at(-1).businessResult=tickets.result;
 assert.equal(requests,0);
 const denied=filter(runtime.tools,{deny:cfg.agents.entries.perso.tools.deny});
 assert.equal(denied.some(t=>t.name.startsWith('orion__')||t.name.startsWith('outline__')),false);
 records.push({test:'perso-native-MCP-deny',success:true});
 for(const [toolName,params] of [['imessage_send',{to:'+33000000000',text:'neutral',service:'sms'}],['gmail_send',{to:['neutral@example.invalid'],subject:'neutral',body:'neutral'}]]){
  const previous=requests;const result=await before({toolName,params,toolCallId:crypto.randomUUID(),ctx:{agentId:'perso',sessionId:'neutral-send-simulation'}});
  assert.equal(result.blocked,true);assert.equal(requests,previous+1);records.push({test:toolName+'-neutralized',requiresNativeApproval:true,executed:false});
 }
 console.log(JSON.stringify({ok:true,records,readApprovals:0,simulatedSendApprovals:2},null,2));
}finally{await runtime?.dispose();}
