import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import path from 'node:path';
const run=promisify(execFile);
export function contactsArgs(p){
 if(Object.keys(p).some(k=>!['action','query','id','fields','limit','fuzzy','container'].includes(k)))throw Error('Paramètre Contacts inconnu');
 if(!['status','containers','search','get'].includes(p.action))throw Error('Lecture Contacts uniquement');
 const args=[p.action];
 if(p.action==='search'&&typeof p.query!=='string'||p.action==='get'&&typeof p.id!=='string')throw Error('Cible Contacts requise');
 for(const key of ['query','id','fields','container'])if(p[key]!==undefined){
  if(typeof p[key]!=='string'||!p[key]||p[key].startsWith('-')||/[\r\n\0]/.test(p[key]))throw Error('Valeur Contacts invalide');
  if(key==='fields'&&!p[key].split(',').every(x=>['name','birthday','phone','email','address'].includes(x)))throw Error('Champ Contacts invalide');
  args.push('--'+key,p[key]);
 }
 if(p.limit!==undefined){if(!Number.isInteger(p.limit)||p.limit<1||p.limit>100)throw Error('Limite Contacts invalide');args.push('--limit',String(p.limit));}
 if(p.fuzzy===true)args.push('--fuzzy');
 return args;
}
export async function contactsRead(p,signal,runner=run){
 const r=await runner(path.join(process.env.HOME,'.local/bin/perso-contacts'),contactsArgs(p),{shell:false,signal,timeout:30000,maxBuffer:1024*1024});return r.stdout;
}
