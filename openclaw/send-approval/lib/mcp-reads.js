import { deny } from './approval.js';
const ORION_READ=new Set(['list_registries','search_tools','get_contract','list_skills','get_skill','search_skill','list_knowledge_bases','search_knowledge','tag_dictionary','find_by_tags','get_document_tags','suggest_document_tags','suggest_activity_tags','resources_list','resources_read','prompts_list','prompts_get']);
export function deferredTarget(p) {
 const selectors=['id','toolId','name'].filter(k=>p[k]!==undefined);
 if(selectors.length!==1||Object.keys(p).some(k=>![selectors[0],'args','input'].includes(k))||p.args!==undefined&&p.input!==undefined)throw Error('Appel différé ambigu : utiliser id et args');
 let name=p[selectors[0]];
 if(typeof name!=='string')throw Error('Identifiant différé invalide');
 if(name.includes(':')) {
  const parts=name.split(':');
  if(parts.length!==3||!['mcp','openclaw'].includes(parts[0])||!parts[1]||!parts[2])throw Error('Identifiant catalogue invalide');
  if(parts[0]==='mcp'&&!parts[2].startsWith(parts[1]+'__'))throw Error('Serveur catalogue incohérent');
  name=parts[2];
 }
 if(['tool_call','tool_search','tool_describe'].includes(name))throw Error('Enveloppe imbriquée interdite');
 const args=p.args??p.input??{};
 if(!args||typeof args!=='object'||Array.isArray(args))throw Error('Arguments différés invalides');
 return {name,args};
}
function scope(ctx){return ctx.agentId+':'+(ctx.sessionId??ctx.sessionKey??'');}
function jsonResult(r){
 if(!r||r.isError||r.details?.status==='error')return;
 if(r.structuredContent??r.details?.structuredContent)return r.structuredContent??r.details.structuredContent;
 const text=r.content?.filter(c=>c.type==='text').map(c=>c.text).join('\n');
 if(text){try{return JSON.parse(text);}catch{}}
}
export function createMcpReads(){
 // Only actual get_contract tool results populate this session-scoped cache.
 // Parameters supplied by the model never confer read permission.
 const contracts=new Map();
 return {
  check(name,p,ctx){
   if(name.startsWith('docker_gateway_pro__serena_')){
    if(ctx.agentId!=='main')return deny('Serena Pro réservé à son agent');
    const tool=name.slice('docker_gateway_pro__'.length);
    const contracts={serena_repository_status:['repository'],serena_find_symbol:['repository','name_path_pattern'],serena_symbols_overview:['repository','relative_path'],serena_find_references:['repository','name_path','relative_path'],serena_search_pattern:['repository','substring_pattern']};
    const required=contracts[tool];
    const optional=tool==='serena_find_symbol'?['relative_path','include_body','depth']:tool==='serena_symbols_overview'?['depth']:tool==='serena_search_pattern'?['relative_path']:[];
    if(!required||!p||typeof p!=='object'||Array.isArray(p)||Object.keys(p).some(k=>![...required,...optional].includes(k))||required.some(k=>typeof p[k]!=='string'||!p[k].trim()))return deny('Arguments Serena invalides');
    if(p.relative_path!==undefined&&(typeof p.relative_path!=='string'||p.relative_path.startsWith('/')||p.relative_path.split('/').includes('..'))||p.depth!==undefined&&(!Number.isInteger(p.depth)||p.depth<0||p.depth>5)||p.include_body!==undefined&&typeof p.include_body!=='boolean')return deny('Arguments Serena invalides');
    return undefined;
   }
   // Microsoft Learn: exact observed documentary contracts, Pro only.
   if(['docker_gateway_pro__microsoft_docs_search','docker_gateway_pro__microsoft_docs_fetch','docker_gateway_pro__microsoft_code_sample_search'].includes(name)){
    if(ctx.agentId!=='main')return deny('Microsoft Learn Pro réservé à son agent');
    const fetch=name.endsWith('__microsoft_docs_fetch'),sample=name.endsWith('__microsoft_code_sample_search');
    const required=fetch?['url']:['query'];
    const allowed=sample?['query','language']:required;
    if(!p||typeof p!=='object'||Array.isArray(p)||Object.keys(p).some(k=>!allowed.includes(k))||required.some(k=>typeof p[k]!=='string'||!p[k].trim())||p.language!==undefined&&(typeof p.language!=='string'||!p.language.trim()))return deny('Arguments Microsoft Learn invalides');
    if(fetch){let u;try{u=new URL(p.url);}catch{return deny('URL Microsoft Learn invalide');}if(u.protocol!=='https:'||u.username||u.password||!(u.hostname==='microsoft.com'||u.hostname.endsWith('.microsoft.com')))return deny('URL Microsoft Learn non officielle');}
    return undefined;
   }
   // Context7 official read-only contracts, only through the Pro endpoint.
   if(['docker_gateway_pro__resolve-library-id','docker_gateway_pro__query-docs'].includes(name)){
    if(ctx.agentId!=='main')return deny('Context7 Pro réservé à son agent');
    const resolve=name.endsWith('__resolve-library-id');
    const required=resolve?['libraryName','query']:['libraryId','query'];
    const allowed=resolve?required:[...required,'language'];
    if(!p||typeof p!=='object'||Array.isArray(p)||Object.keys(p).some(k=>!allowed.includes(k))||required.some(k=>typeof p[k]!=='string'||!p[k].trim())||p.language!==undefined&&(typeof p.language!=='string'||!p.language.trim()))return deny('Arguments Context7 invalides');
    return undefined;
   }
   // Approved Docker time witnesses only; each profile belongs to one agent.
   const timeTool=/^docker_gateway_(pro|perso)__(get_current_time|convert_time)$/.exec(name);
   if(timeTool){
    if(ctx.agentId!==(timeTool[1]==='pro'?'main':'perso'))return deny('Profil Docker MCP réservé à son agent');
    const keys=timeTool[2]==='get_current_time'?['timezone']:['source_timezone','time','target_timezone'];
    if(Object.keys(p).length!==keys.length||keys.some(k=>typeof p[k]!=='string'||!p[k].trim()))return deny('Arguments time invalides');
    return undefined;
   }
   if(!name.startsWith('orion__')&&!name.startsWith('outline__'))return null;
   if(ctx.agentId!=='main')return deny('Outils pro interdits à Perso');
   if(name.startsWith('orion__')&&ORION_READ.has(name.slice(7)))return undefined;
   if(name==='orion__exec_tool'){
    if(!ctx.sessionId&&!ctx.sessionKey)return deny('Identité de session MCP requise');
    const c=contracts.get(scope(ctx)+':'+(p.registry??'')+':'+p.tool_name);
    if(c&&c.expires>Date.now()&&c.access==='read')return undefined;
    return deny('Lecture MCP non qualifiée : appeler orion__get_contract dans cette session ; les mutations restent bloquées');
   }
   if(name.startsWith('outline__')&&new Set(['fetch','list_collection_documents','list_collections','list_comments','list_documents','list_templates','list_users','resources_list','resources_read']).has(name.slice(9)))return undefined;
   return deny('Mutation ou opération MCP non qualifiée : aucun envoi sans confirmation technique');
  },
  observe(event,ctx){
   if(ctx.agentId!=='main'||event.error||!ctx.sessionId&&!ctx.sessionKey)return;
   let name=event.toolName,p=event.params??{},result=event.result;
   if(name==='tool_call'){
    let target;try{target=deferredTarget(p);}catch{return;}
    const actual=result?.details;
    if(actual?.tool?.name!==target.name||actual.status)return;
    name=target.name;p=target.args;result=actual.result;
   }
   if(name!=='orion__get_contract'||typeof p.tool_name!=='string')return;
   const c=jsonResult(result),key=scope(ctx)+':'+(p.registry??'')+':'+p.tool_name;
   contracts.delete(key);
   if(!c||c.name!==p.tool_name||typeof c.registry!=='string'||p.registry&&p.registry!==c.registry||!['read','write'].includes(c.access)||!c.parameters)return;
   for(const [k,v] of contracts)if(v.expires<Date.now())contracts.delete(k);
   if(contracts.size>=256)return;
   contracts.set(key,{access:c.access,expires:Date.now()+300000});
  }
 };
}
