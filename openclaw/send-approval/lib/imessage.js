import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const run=promisify(execFile);
export function messagePacket(p){
 if(Object.keys(p).some(k=>!['to','text','service'].includes(k))||typeof p.to!=='string'||!(/^[+]\d{8,15}$/u.test(p.to)||/^[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+$/u.test(p.to))||typeof p.text!=='string'||!p.text||Buffer.byteLength(p.text)>65536||!['imessage','sms','auto'].includes(p.service??'imessage'))throw Error('Destinataire, texte ou canal invalide');
 return {to:p.to,text:p.text,service:p.service??'imessage'};
}
export async function sendMessage(p,signal,runner=run){const m=messagePacket(p);const r=await runner('/opt/homebrew/bin/imsg',['send','--to',m.to,'--text',m.text,'--service',m.service,'--no-sms-fallback','--json'],{shell:false,timeout:30000,maxBuffer:1024*1024,signal});return {accepted:true,deliveryStatus:'unknown',result:r.stdout};}
export function messageReadPlan(p){
 if(Object.keys(p).some(k=>!['action','chatId','limit'].includes(k)))throw Error('Paramètre iMessage inconnu');
 const limit=p.limit??20;if(!Number.isInteger(limit)||limit<1||limit>100)throw Error('Limite invalide');
 if(p.action==='chats')return ['chats','--limit',String(limit),'--json'];
 if(p.action==='history'&&Number.isInteger(p.chatId)&&p.chatId>0)return ['history','--chat-id',String(p.chatId),'--limit',String(limit),'--json'];
 throw Error('Lecture iMessage non qualifiée');
}
export async function readMessage(p,signal,runner=run){const r=await runner('/opt/homebrew/bin/imsg',messageReadPlan(p),{shell:false,timeout:15000,maxBuffer:1024*1024,signal});return r.stdout;}
