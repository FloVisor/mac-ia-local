import fs from 'node:fs';
import fsp from 'node:fs/promises';
import { canonical, within, memoryPath, fingerprint } from './files.js';
export function changePlan(p,ctx,workspaces,protectedRoots){
 if(Object.keys(p).some(k=>!['action','path','content','oldText','newText'].includes(k))||!['write','edit'].includes(p.action))throw Error('Modification non qualifiée');
 const root=fs.realpathSync(workspaces[ctx.agentId]); const target=canonical(p.path,root);
 if(Object.entries(workspaces).some(([id,r])=>id!==ctx.agentId&&within(target,fs.realpathSync(r))))throw Error('Workspace de l’autre agent interdit');
 if(protectedRoots.some(r=>within(target,r)))throw Error('Plan de contrôle protégé');
 const exists=fs.existsSync(target);if(exists&&!fs.lstatSync(target).isFile())throw Error('Fichier ordinaire requis');
 if(exists&&fs.lstatSync(target).nlink>1)throw Error('Fichier avec liens physiques : cible ambiguë');
 const state=fingerprint(target);let content;
 if(p.action==='write')content=p.content;
 else {
  if(!exists||typeof p.oldText!=='string'||!p.oldText||typeof p.newText!=='string')throw Error('Édition invalide');
  const text=fs.readFileSync(target,'utf8');
  if(text.split(p.oldText).length!==2)throw Error('Préimage oldText absente ou ambiguë');
  content=text.replace(p.oldText,p.newText);
 }
 if(typeof content!=='string'||Buffer.byteLength(content)>128*1024)throw Error('Contenu absent ou trop grand');
 return {action:p.action,target,state,content,memory:memoryPath(target,root),exists};
}
export function validateChange(plan){if(fingerprint(plan.target)!==plan.state)throw Error('Fichier modifié après préparation : nouvel accord requis');}
export async function executeChange(plan){
 validateChange(plan);
 // No recursive parent creation. Open existing files without following a final symlink.
 const flags=plan.exists?fs.constants.O_RDWR|fs.constants.O_NOFOLLOW:fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW;
 const handle=await fsp.open(plan.target,flags,0o600);
 try {
  if(plan.exists)validateChange(plan);
  await handle.writeFile(plan.content,{encoding:'utf8'});await handle.truncate(Buffer.byteLength(plan.content));await handle.sync();
 }finally{await handle.close();}
 return {changed:plan.target,bytes:Buffer.byteLength(plan.content)};
}
