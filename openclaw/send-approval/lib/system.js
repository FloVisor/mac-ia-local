import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { canonical, within, fingerprint } from './files.js';
import { digest } from './approval.js';
const run = promisify(execFile);
export function readPlan(p) {
  if (Object.keys(p).some(k=>!['action','service'].includes(k))) throw Error('Paramètres inconnus');
  if(p.action==='os')return ['/usr/bin/sw_vers',[]];
  if(p.action==='services')return ['/bin/launchctl',['list']];
  if(p.action==='processes')return ['/bin/ps',['-axo','pid,ppid,comm']];
  if(p.action==='disk')return ['/bin/df',['-h']];
  if(p.action==='network')return ['/sbin/ifconfig',[]];
  if(p.action==='service' && typeof p.service==='string' && /^[A-Za-z0-9.-]{1,150}$/u.test(p.service))return ['/bin/launchctl',['print',`gui/${process.getuid()}/${p.service}`]];
  throw Error('Lecture système non qualifiée');
}
export async function systemRead(p, signal, runner=run) {
  const [file,args]=readPlan(p);const result=await runner(file,args,{shell:false,timeout:15000,maxBuffer:1024*1024,signal});return result.stdout;
}
function treeHash(root) {
  let count=0,total=0;const entries=[];
  function walk(file) {
    if(++count>2000)throw Error('Arborescence trop grande pour suppression contrôlée');
    const stat=fs.lstatSync(file);
    if(stat.isSymbolicLink())throw Error('Suppression d’arborescence avec lien symbolique non qualifiée');
    if(stat.isFile()){total+=stat.size;if(total>64*1024*1024)throw Error('Suppression trop volumineuse');}
    entries.push([file,fingerprint(file)]);
    if(stat.isDirectory())for(const name of fs.readdirSync(file).sort())walk(path.join(file,name));
  }walk(root);return digest(entries);
}
export function actionPlan(p,ctx,workspaces,protectedRoots) {
  if(Object.keys(p).some(k=>!['action','path','recursive','mode','package','service'].includes(k)))throw Error('Paramètres inconnus');
  if(p.action==='install_package'||p.action==='uninstall_package'){
    if(typeof p.package!=='string'||! /^[A-Za-z0-9][A-Za-z0-9@+._-]{0,100}$/u.test(p.package))throw Error('Nom de paquet invalide');
    return {action:p.action,file:'/opt/homebrew/bin/brew',args:[p.action==='install_package'?'install':'uninstall',p.package],summary:`${p.action} ${p.package} ; logiciels système, effets de scripts du paquet possibles`};
  }
  if(p.action==='restart_service'){
    if(typeof p.service!=='string'||! /^[A-Za-z0-9.-]{1,150}$/u.test(p.service))throw Error('Service invalide');
    return {action:p.action,file:'/bin/launchctl',args:['kickstart','-k',`gui/${process.getuid()}/${p.service}`],summary:`Redémarrer ${p.service} ; interruption du service`};
  }
  if(!['delete','trash','chmod'].includes(p.action))throw Error('Action système non qualifiée');
  const root=workspaces[ctx.agentId];if(!root)throw Error('Agent inconnu');
  const target=canonical(p.path,root);
  if(!fs.existsSync(target))throw Error('Cible absente');
  if(target==='/'||target===process.env.HOME||target===root)throw Error('Racine protégée');
  if(Object.entries(workspaces).some(([id,r])=>id!==ctx.agentId&&within(target,fs.realpathSync(r))))throw Error('Workspace de l’autre agent interdit');
  if(protectedRoots.some(r=>within(target,r)))throw Error('Plan de contrôle protégé');
  const state=treeHash(target);
  if(p.action==='chmod'){
    if(typeof p.mode!=='string'||! /^[0-7]{3}$/u.test(p.mode)||!fs.lstatSync(target).isFile())throw Error('chmod : fichier ordinaire et mode octal à trois chiffres requis');
    return {action:p.action,target,mode:p.mode,state,summary:`chmod ${p.mode} ${target} ; changement des permissions`};
  }
  if(fs.lstatSync(target).isDirectory()&&p.action==='delete'&&p.recursive!==true)throw Error('Suppression de dossier : recursive=true requis');
  return {action:p.action,target,state,recursive:p.recursive===true,summary:`${p.action==='trash'?'Corbeille, réversible':'Suppression définitive, non réversible'} : ${target}${p.recursive?' (arborescence)':''}`};
}
export function validatePlan(plan) {if(plan.target&&treeHash(plan.target)!==plan.state)throw Error('Cible modifiée : nouvel accord requis');}
export async function executePlan(plan,signal,runner=run) {
  validatePlan(plan);
  if(plan.file){const r=await runner(plan.file,plan.args,{shell:false,timeout:300000,maxBuffer:1024*1024,signal});return r.stdout;}
  if(plan.action==='chmod'){await fsp.chmod(plan.target,parseInt(plan.mode,8));return {changed:plan.target};}
  if(plan.action==='delete'){await fsp.rm(plan.target,{recursive:plan.recursive,force:false});return {deleted:plan.target,reversible:false};}
  const trash=await fsp.realpath(path.join(process.env.HOME,'.Trash'));
  if(trash!==path.join(await fsp.realpath(process.env.HOME),'.Trash'))throw Error('Corbeille redirigée interdite');
  const destination=path.join(trash,`${path.basename(plan.target)}-${crypto.randomUUID()}`);
  await fsp.rename(plan.target,destination);return {trashed:plan.target,destination,reversible:true};
}
