import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const definitions=JSON.parse(fs.readFileSync(path.join(here,'schemas.json'),'utf8'));
const identities=Object.freeze({main:'openclaw-pro',perso:'openclaw-perso'});
export const toolNames=Object.freeze(definitions.map(x=>'llm_router_'+x.name));
export function prepare(ctx,name,args){
 const identity=identities[ctx.agentId];
 const def=definitions.find(x=>x.name===name);
 if(!identity||!ctx.sessionId||!def)throw Error('Trusted agent and session required');
 if(!args||typeof args!=='object'||Array.isArray(args))throw Error('Invalid arguments');
 if(Object.keys(args).some(k=>!Object.hasOwn(def.inputSchema.properties,k)))throw Error('Unsupported argument');
 const params=structuredClone(args);
 if(['submit','delegate'].includes(name))params.parent_session=ctx.sessionId;
 return {identity,params};
}
export function invoke(ctx,name,args,{home=process.env.HOME,python='/opt/homebrew/bin/python3',runner=path.resolve(here,'../../mcp/llm-router/router.py'),signal}={}){
 const {identity,params}=prepare(ctx,name,args);
 const config=path.join(home,'.config/llm-router',identity+'.json');
 const st=fs.lstatSync(config);
 if(!st.isFile()||st.isSymbolicLink()||(st.mode&0o077)||st.uid!==process.getuid())throw Error('Unsafe private router configuration');
 const c=JSON.parse(fs.readFileSync(config,'utf8'));
 if(c.identity!==identity||c.state_dir!==path.join(home,'.local/state/llm-router',identity)||c.key_file!==path.join(home,'.config/llm-router',identity+'-delegated.key'))throw Error('Router identity/config mismatch');
 return new Promise((resolve,reject)=>{
  // No inherited provider credentials, workspaces, or arbitrary executable arguments.
  const child=spawn(python,[runner,'--config',config],{env:{HOME:home,PATH:'/opt/homebrew/bin:/usr/bin:/bin',LANG:'en_US.UTF-8'},stdio:['pipe','pipe','pipe'],signal});
  let output='',diagnostic='',settled=false;
  const finish=(error,value)=>{if(settled)return;settled=true;clearTimeout(timer);child.kill();error?reject(error):resolve(value);};
  const timer=setTimeout(()=>finish(Error('Router transport deadline; task may remain active, recover by status/activity')),name==='delegate'?300000:30000);
  child.on('error',e=>finish(Error('Router process unavailable: '+e.code)));
  child.stderr.on('data',chunk=>{diagnostic=(diagnostic+chunk.toString()).slice(-4096);});
  child.stdout.on('data',chunk=>{
   output+=chunk.toString();
   if(output.length>2*1024*1024)return finish(Error('Router response too large'));
   let newline;
   while((newline=output.indexOf('\n'))>=0){
    const line=output.slice(0,newline);output=output.slice(newline+1);
    try{const r=JSON.parse(line);if(r.id===2){if(!r.result)throw Error('Invalid MCP response');finish(null,r.result);}}catch{finish(Error('Invalid router protocol'));}
   }
  });
  child.on('exit',(code,signal)=>{if(!settled)finish(Error('Router exited before response; code='+code+' signal='+signal+' diagnostic='+diagnostic.replace(/sk-[A-Za-z0-9_-]+/g,'<redacted>')));});
  child.stdin.on('error',()=>finish(Error('Router input closed')));
  child.stdin.end([
   {jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2024-11-05',capabilities:{},clientInfo:{name:'openclaw-isolated-router',version:'0.1.0'}}},
   {jsonrpc:'2.0',method:'notifications/initialized'},
   {jsonrpc:'2.0',id:2,method:'tools/call',params:{name,arguments:params}}
  ].map(x=>JSON.stringify(x)).join('\n')+'\n');
 });
}
export default {id:'llm-router',name:'Isolated LLM router',register(api){
 for(const def of definitions)api.registerTool(ctx=>({name:'llm_router_'+def.name,label:'LLM router '+def.name,description:def.description+' Instance privée de cet agent. LOCAL/FREE seulement ; aucun paiement délégué. Utiliser submit puis status/result pour les tâches longues.',parameters:def.inputSchema,execute:(_id,p,signal)=>invoke(ctx,def.name,p??{},{signal,runner:api.pluginConfig.routerPath})}),{names:['llm_router_'+def.name]});
}};
