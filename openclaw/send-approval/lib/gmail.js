import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
import { digest } from './approval.js';
import { within } from './files.js';
const exec = promisify(execFile);
export async function runGog(args, signal) {
  const r = await exec('/opt/homebrew/bin/gog', args, { shell: false, timeout: 30000, maxBuffer: 2 * 1024 * 1024, signal });
  return r.stdout;
}
export function readArgs(p) {
  const allowed = new Set(['action', 'query', 'messageId', 'threadId', 'attachmentId', 'labelId', 'max', 'page']);
  if (Object.keys(p).some(k => !allowed.has(k))) throw Error('Paramètre Gmail non autorisé');
  const id = (v) => { if (typeof v !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_:-]{0,1023}$/u.test(v)) throw Error('Identifiant invalide'); return v; };
  const args = ['--account', 'auto', '--json', '--no-input', '--readonly', '--gmail-no-send', 'gmail'];
  if (p.action === 'search') {
    if (typeof p.query !== 'string' || !p.query || p.query.length > 2000 || /[\0\r\n]/u.test(p.query)) throw Error('Recherche invalide');
    const max = p.max ?? 20; if (!Number.isInteger(max) || max < 1 || max > 100) throw Error('Limite invalide');
    args.push('search', `(${p.query})`, '--max', String(max));
    if (p.page) args.push('--page', id(p.page));
  } else if (p.action === 'get') args.push('get', id(p.messageId));
  else if (p.action === 'thread') args.push('thread', 'get', id(p.threadId));
  else if (p.action === 'labels') args.push('labels', 'list');
  else if (p.action === 'label') args.push('labels', 'get', id(p.labelId));
  else if (p.action === 'attachment') args.push('attachment', id(p.messageId), id(p.attachmentId));
  else throw Error('Action de lecture non autorisée');
  return args;
}
export async function gmailRead(p, ctx, workspace, runner = runGog) {
  if (ctx.agentId !== 'perso') throw Error('Gmail réservé à Perso');
  const args = readArgs(p);
  if (p.action !== 'attachment') return runner(args,ctx.abortSignal);
  const root = await fs.realpath(workspace), base = path.join(root,'.gmail-downloads');
  await fs.mkdir(base,{recursive:true,mode:0o700});
  if (!within(await fs.realpath(base),root)) throw Error('Répertoire de téléchargement hors workspace');
  const dir = await fs.mkdtemp(path.join(base,'read-')); await fs.chmod(dir,0o700);
  const destination = path.join(dir,'attachment.bin');
  try {
    await runner([...args,'--out',destination],ctx.abortSignal);
    const data = await fs.readFile(destination);
    return JSON.stringify({ path:destination,bytes:data.length,sha256:digest(data) });
  } catch(e) { await fs.rm(dir,{recursive:true,force:true}); throw e; }
}
export function mailPacket(p) {
  const fields = new Set(['to','cc','bcc','subject','body','attachments']);
  if (Object.keys(p).some(k=>!fields.has(k))) throw Error('Paramètre d’envoi inconnu');
  const addresses = list => {
    if (!Array.isArray(list) || list.length > 20 || list.some(x => typeof x !== 'string' || !/^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+$/u.test(x))) throw Error('Destinataire invalide');
    return [...list];
  };
  const packet = { to:addresses(p.to),cc:addresses(p.cc??[]),bcc:addresses(p.bcc??[]),subject:p.subject,body:p.body,attachments:[] };
  if (!packet.to.length || typeof p.subject!=='string' || !p.subject || p.subject.length>998 || /[\r\n\0]/u.test(p.subject) || typeof p.body!=='string' || Buffer.byteLength(p.body)>65536) throw Error('Message incomplet ou trop grand');
  let bytes = 0;
  if (!Array.isArray(p.attachments??[]) || (p.attachments??[]).length>10) throw Error('Pièces jointes invalides');
  packet.attachments=(p.attachments??[]).map(a=>{
    if (Object.keys(a).some(k=>!['name','contentType','contentBytes'].includes(k)) || typeof a.name!=='string' || !a.name || /[\r\n\0"\\/]/u.test(a.name) || typeof a.contentType!=='string' || !/^[\w.+-]+\/[\w.+-]+$/u.test(a.contentType) || typeof a.contentBytes!=='string') throw Error('Pièce jointe invalide');
    const content=Buffer.from(a.contentBytes,'base64'); if(content.toString('base64')!==a.contentBytes) throw Error('Base64 non canonique');
    bytes+=content.length;if(bytes>3*1024*1024)throw Error('Pièces jointes trop grandes');
    return { name:a.name,contentType:a.contentType,contentBytes:a.contentBytes };
  });return packet;
}
export function mime(packet) {
  const boundary=`approved-${digest(packet)}`;
  const b64=s=>Buffer.from(s).toString('base64').match(/.{1,76}/g)?.join('\r\n')??'';
  const parts=[`To: ${packet.to.join(', ')}`,`Cc: ${packet.cc.join(', ')}`,`Bcc: ${packet.bcc.join(', ')}`,`Subject: =?UTF-8?B?${Buffer.from(packet.subject).toString('base64')}?=`,`MIME-Version: 1.0`,`Content-Type: multipart/mixed; boundary="${boundary}"`,'',`--${boundary}`,'Content-Type: text/plain; charset=UTF-8','Content-Transfer-Encoding: base64','',b64(packet.body)];
  for(const a of packet.attachments) parts.push(`--${boundary}`,`Content-Type: ${a.contentType}`,`Content-Disposition: attachment; filename*=UTF-8''${encodeURIComponent(a.name)}`,'Content-Transfer-Encoding: base64','',a.contentBytes.match(/.{1,76}/g)?.join('\r\n')??'');
  return [...parts,`--${boundary}--`,''].join('\r\n');
}
export async function gmailSend(p, runner=runGog, signal) {
  const packet=mailPacket(p), dir=await fs.mkdtemp(path.join(process.env.TMPDIR??'/tmp','openclaw-approved-mail-'));
  await fs.chmod(dir,0o700);
  const file=path.join(dir,'message.eml');
  try {
    await fs.writeFile(file,mime(packet),{mode:0o400,flag:'wx'});
    const result=await runner(['--account','auto','--json','--no-input','gmail','send','--raw-file',file],signal);
    return {accepted:true,deliveryStatus:'unknown',sha256:digest(packet),result};
  } finally {await fs.rm(dir,{recursive:true,force:true});}
}
