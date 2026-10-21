import fs from 'node:fs';
import path from 'node:path';
import { createMcpReads, deferredTarget } from './lib/mcp-reads.js';
import { contactsArgs, contactsRead } from './lib/contacts.js';
export { words } from './lib/message-policy.js';
import { digest, deny, request } from './lib/approval.js';
import { filePolicy } from './lib/files.js';
import { gmailRead, gmailSend, mailPacket } from './lib/gmail.js';
import { changePlan, validateChange, executeChange } from './lib/file-change.js';
import { messagePacket, sendMessage, messageReadPlan, readMessage } from './lib/imessage.js';
import { readPlan, systemRead, actionPlan, validatePlan, executePlan } from './lib/system.js';
const grantKey=Symbol.for('local.openclaw.send-approval.grants.v2');
const grants = globalThis[grantKey] ??= new Map();
const defaults={main:path.join(process.env.HOME,'.openclaw/workspace'),perso:path.join(process.env.HOME,'.openclaw/workspace-perso')};
export const protectedRoots=[path.join(process.env.HOME,'.openclaw/openclaw.json'),path.join(process.env.HOME,'.openclaw/extensions'),path.join(process.env.HOME,'.openclaw/runtime'),path.join(process.env.HOME,'.openclaw/agents'),path.join(process.env.HOME,'.openclaw/state'),path.join(process.env.HOME,'.openclaw/skills'),path.resolve(import.meta.dirname),path.join(process.env.HOME,'.openclaw/exec-approvals.json')];
const FREE = new Set(['read','ls','web_search','web_fetch','memory_search','memory_get','session_status','sessions_list','sessions_history','sessions_search','conversations_list','agents_list','tool_search','skills_search','skills_read','view_image','pdf','get_goal','ask_user','agents_wait','sessions_yield','heartbeat_respond']);
const BOOK_READ={bookstack_activity:[undefined,'list','search','status'],bookstack_structure:['tree'],bookstack_search:[undefined,'search'],bookstack_page:[undefined,'read','attachments'],bookstack_attachment:['list'],bookstack_comment:['list','read','search','thread'],bookstack_suivi:[undefined,'read'],bookstack_conversation:['list']};
const GRAPH_READ=new Set(['outlook_mail_read','outlook_calendar_read','microsoft_todo_read','onedrive_list','onedrive_read','onedrive_search','onedrive_agents_instructions']);
const GRAPH_WRITE=new Set(['outlook_mail_write','outlook_calendar_write','microsoft_todo_write','onedrive_create_folder','onedrive_upload','onedrive_update','onedrive_delete','onedrive_metadata_update']);
function grantRequest(event,ctx,p,action,summary,plan) {
  if(!event.toolCallId||!ctx.sessionId)return deny('Identité appel/session requise');
  const key=event.toolCallId;
  return request(p,ctx.agentId,action,summary,decision=>{
    grants.delete(key);
    if(decision==='allow-once'){
      if(plan){if(plan.content!==undefined)validateChange(plan);else validatePlan(plan);}
      for(const [k,v] of grants)if(v.expires<Date.now())grants.delete(k);
      if(grants.size>=128)throw Error('Trop d’accords en attente');
      grants.set(key,{agent:ctx.agentId,session:ctx.sessionId,name:event.toolName,hash:digest(p),plan,expires:Date.now()+10000});
    }
  });
}
export function consumeGrant(id,p,ctx,name) {
  const grant=grants.get(id);grants.delete(id);
  if(!grant||grant.expires<Date.now()||grant.agent!==ctx.agentId||grant.session!==ctx.sessionId||grant.name!==name||grant.hash!==digest(p))throw Error('Approbation native absente, consommée ou contenu modifié');
  return grant;
}
export function createPolicy(workspaces=defaults,roots=protectedRoots,options={}) {
 const mcp=options.mcpReads??createMcpReads();
 const check=(event,ctx={})=>{
  const name=event.toolName,p=event.params??{},agent=ctx.agentId;
  try {
    if(!['main','perso'].includes(agent))return deny('Identité agent absente ou inconnue');
    if(name==='tool_describe')return;
    // Isolated adapter binds agent/session and owns LOCAL/FREE-only credentials.
    if(['llm_router_submit','llm_router_delegate','llm_router_status','llm_router_result','llm_router_cancel','llm_router_activity','llm_router_catalogue'].includes(name))return;
    if(name==='tool_call'){
      const target=deferredTarget(p);
      const decision=check({...event,toolName:target.name,params:target.args},ctx);
      if(decision?.requireApproval)return deny('Action protégée : appeler directement l’outil dédié pour sa confirmation native');
      return decision;
    }
    const mcpDecision=mcp.check(name,p,ctx);
    if(mcpDecision!==null)return mcpDecision;
    if(name==='gmail_read')return agent==='perso'?undefined:deny('Gmail réservé à Perso');
    if(name==='contacts_read'){if(agent!=='perso')return deny('Contacts Apple réservés à Perso');contactsArgs(p);return;}
    if(name==='imessage_read'){messageReadPlan(p);return;}
    if(name==='imessage_send'){const m=messagePacket(p);return grantRequest(event,ctx,p,'envoyer ce message',`${m.service} vers ${m.to} ; texte=${JSON.stringify(m.text).slice(0,180)}`);}
    if(name==='system_read'){readPlan(p);return;}
    if(name==='session_status'&&p.model&&p.model!=='default')return deny('Sélection de modèle réservée au sélecteur utilisateur ; aucune escalade par outil');
    if(FREE.has(name))return;
    if(['write','edit','apply_patch'].includes(name))return filePolicy(event,ctx,workspaces,roots);
    if(name==='gmail_send'){
      if(agent!=='perso')return deny('Gmail réservé à Perso');
      const packet=mailPacket(p);
      const summary=`Gmail vers ${packet.to.join(',')} cc=${packet.cc.join(',')} bcc=${packet.bcc.join(',')} ; objet=${packet.subject} ; texte=${JSON.stringify(packet.body).slice(0,90)} ; pièces=${packet.attachments.map(a=>`${a.name}:${Buffer.from(a.contentBytes,'base64').length}B`).join(',')||'aucune'}`;
      return grantRequest(event,ctx,p,'envoyer ce mail',summary);
    }
    if(name==='file_change'){
      const plan=changePlan(p,ctx,workspaces,roots);
      if(plan.memory)return;
      return grantRequest(event,ctx,p,'modifier ce fichier',`${p.action} ${plan.target} ; préimage=${plan.state} ; ${Buffer.byteLength(plan.content)} octets ; récupération non garantie`,plan);
    }
    if(name==='system_action'){
      const plan=actionPlan(p,ctx,workspaces,roots);
      return grantRequest(event,ctx,p,'autoriser cette modification',plan.summary,plan);
    }
    if(name==='message'&&['read','search','channel-info','member-info','emoji-list','permissions'].includes(p.action))return;
    if(name==='message')return deny('Envois et actions de canal non qualifiés ; utiliser imessage_send pour un contenu lié à l’accord');
    if(GRAPH_READ.has(name))return agent==='main'?undefined:deny('Graph interdit à Perso');
    if(GRAPH_WRITE.has(name)){
      if(agent!=='main')return deny('Graph interdit à Perso');
      const graphFile=path.join(process.env.HOME,'.openclaw/extensions/microsoft-graph/dist/index.js');
      if(!options.graphExactSha256||digest(fs.readFileSync(graphFile))!==options.graphExactSha256)return deny('Connecteur Graph non qualifié ou mis à jour : mutations bloquées jusqu’à requalification');
      if(name==='outlook_mail_write'&&p.action==='send_draft')return deny('Utiliser send_exact avec destinataires, corps et pièces jointes inline ; le brouillon distant reste inchangé');
      // Graph owns its bound snapshots and sole native prompt (warning policy enabled).
      return;
    }
    if(Object.hasOwn(BOOK_READ,name)){
      if(agent!=='perso')return deny('BookStack réservé à Perso');
      if(BOOK_READ[name].includes(p.action))return;
      const deletion=p.action==='delete'||p.action?.startsWith('delete_');
      const archive=['archive','unarchive'].includes(p.action);
      const kind=deletion?'Suppression effective ; récupération non garantie':archive?'Archivage/désarchivage réversible':'Modification de données';
      const target=JSON.stringify({tool:name,action:p.action??'default',activity:p.activityId,book:p.bookId,page:p.pageId,id:p.id,attachment:p.attachmentId,chapter:p.chapterId,comment:p.commentId});
      // Existing tool confirm=true remains an intent flag; the native gate owns approval.
      return request(p,agent,deletion?'supprimer ces données':'modifier BookStack',`${kind} ; BookStack ${target}`);
    }
    if(name==='bookstack_import')return deny('Import/OCR avec effets de bord multiples non qualifié ; blocage conservateur');
    if(name==='exec')return deny('Shell non qualifié : utiliser gmail_read, gmail_send, system_read ou system_action ; aucun shell arbitraire');
    if(name==='sessions_send'){
      if(agent!=='main'||!String(p.sessionKey??'').startsWith('agent:perso:'))return deny('Délégation non autorisée');
      return request(p,agent,'transmettre à Perso',`Délégation explicite Pro vers Perso : ${String(p.sessionKey)} ; texte=${JSON.stringify(p.message).slice(0,160)}`);
    }
    if(['orion__search_tools','orion__get_contract','outline__search_tools','outline__get_contract'].includes(name))return agent==='main'?undefined:deny('Outils pro interdits à Perso');
    return deny(`Outil/action non qualifié : ${name}. Aucun effet de bord autorisé par défaut`);
  }catch(error){return deny(error.message);}
 };
 return check;
}
export const policy=createPolicy();
const str={type:'string'},id={type:'string',minLength:1,maxLength:1024};
const attachment={type:'object',additionalProperties:false,required:['name','contentType','contentBytes'],properties:{name:str,contentType:str,contentBytes:{type:'string',maxLength:4*1024*1024}}};
const schema=(props,required)=>({type:'object',additionalProperties:false,properties:props,required});
export default {
 id:'send-approval',name:'Send approval',
 register(api){
  const entries=api.config?.agents?.entries??{};
  const workspaces=Object.fromEntries(['main','perso'].map(id=>[id,entries[id]?.workspace??defaults[id]]));
  const activeRoots=[...protectedRoots,...(api.config?.plugins?.load?.paths??[]).map(p=>fs.realpathSync(p))];
  const mcpReads=createMcpReads();
  api.on('before_tool_call',createPolicy(workspaces,activeRoots,{...api.pluginConfig,mcpReads}),{priority:Number.MAX_SAFE_INTEGER});
  api.on('after_tool_call',(event,ctx)=>mcpReads.observe(event,ctx));
  api.on('message_sending',()=>({cancel:true,cancelReason:'Approbation native liée au contenu requise ; utiliser imessage_send'}),{priority:Number.MAX_SAFE_INTEGER});
  const definitions=[
   {name:'contacts_read',description:'Lecture seule des Contacts Apple iCloud de Perso via perso-contacts : status, containers, search, get. Aucune confirmation, aucune écriture.',parameters:schema({action:{type:'string',enum:['status','containers','search','get']},query:str,id:str,fields:str,container:str,limit:{type:'integer',minimum:1,maximum:100},fuzzy:{type:'boolean'}},['action']),run:(id,p,ctx)=>{if(ctx.agentId!=='perso')throw Error('Contacts réservés à Perso');return contactsRead(p,ctx.abortSignal);}},
   {name:'imessage_read',description:'Lecture iMessage/SMS sans shell : chats ou history, sans conversion de pièces jointes.',parameters:schema({action:{type:'string',enum:['chats','history']},chatId:{type:'integer',minimum:1},limit:{type:'integer',minimum:1,maximum:100}},['action']),run:(id,p,ctx)=>readMessage(p,ctx.abortSignal)},
   {name:'imessage_send',description:'Envoi de texte SMS/iMessage avec accord natif ponctuel lié au destinataire, canal et texte exact. Aucun fallback SMS automatique.',parameters:schema({to:str,text:str,service:{type:'string',enum:['imessage','sms','auto']}},['to','text']),run:(id,p,ctx)=>{consumeGrant(id,p,ctx,'imessage_send');return sendMessage(p,ctx.abortSignal);}},
   {name:'gmail_read',description:'Lecture Gmail personnelle sans shell ni approbation : search, get, thread, labels, label, attachment. Téléchargements dans le workspace Perso uniquement.',parameters:schema({action:{enum:['search','get','thread','labels','label','attachment'],type:'string'},query:str,messageId:id,threadId:id,attachmentId:id,labelId:id,max:{type:'integer',minimum:1,maximum:100},page:id},['action']),run:(id,p,ctx)=>gmailRead(p,ctx,workspaces[ctx.agentId])},
   {name:'gmail_send',description:'Envoi Gmail personnel avec accord natif ponctuel ; destinataires, objet, corps et pièces jointes base64 immuables. Ne jamais envoyer via exec.',parameters:schema({to:{type:'array',items:str},cc:{type:'array',items:str},bcc:{type:'array',items:str},subject:str,body:str,attachments:{type:'array',items:attachment}},['to','subject','body']),run:(id,p,ctx)=>{consumeGrant(id,p,ctx,'gmail_send');return gmailSend(p,undefined,ctx.abortSignal);}},
   {name:'file_change',description:'Modification de fichier avec préimage vérifiée et accord natif hors USER.md, MEMORY.md et memory/ propres à l’agent. Actions write ou edit, chemin canonique.',parameters:schema({action:{type:'string',enum:['write','edit']},path:str,content:str,oldText:str,newText:str},['action','path']),run:(id,p,ctx)=>{const plan=changePlan(p,ctx,workspaces,activeRoots);if(plan.memory)return executeChange(plan);return executeChange(consumeGrant(id,p,ctx,'file_change').plan);}},
   {name:'system_read',description:'Lectures système sans shell : os, services, service, processes, disk, network.',parameters:schema({action:{type:'string',enum:['os','services','service','processes','disk','network']},service:str},['action']),run:(id,p,ctx)=>systemRead(p,ctx.abortSignal)},
   {name:'system_action',description:'Accord natif ponctuel pour suppression définitive, corbeille, chmod, installation/désinstallation Homebrew ou redémarrage LaunchAgent. Chemins canoniques, aucune commande shell.',parameters:schema({action:{type:'string',enum:['delete','trash','chmod','install_package','uninstall_package','restart_service']},path:str,recursive:{type:'boolean'},mode:str,package:str,service:str},['action']),run:(id,p,ctx)=>executePlan(consumeGrant(id,p,ctx,'system_action').plan,ctx.abortSignal)},
  ];
  for(const def of definitions)api.registerTool(ctx=>({name:def.name,label:def.name,description:def.description,parameters:def.parameters,async execute(id,p,signal){
   if(!['main','perso'].includes(ctx.agentId)||(def.name.startsWith('gmail_')&&ctx.agentId!=='perso'))throw Error('Agent non autorisé');
   const result=await def.run(id,p,{...ctx,abortSignal:signal});return {content:[{type:'text',text:typeof result==='string'?result:JSON.stringify(result)}]};
  }}),{names:[def.name]});
  api.logger.info('send-approval v0.2.1: MCP read contracts and deferred dispatch restored; native send approvals preserved');
 }
};
