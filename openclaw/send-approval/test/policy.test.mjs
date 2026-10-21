import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import importedPlugin, { policy,createPolicy,consumeGrant } from '../index.js';
import { readArgs,gmailRead,mailPacket,mime,gmailSend } from '../lib/gmail.js';
import { actionPlan,executePlan } from '../lib/system.js';
import { changePlan,executeChange } from '../lib/file-change.js';
const ctx={agentId:'perso',sessionId:'test'};
const base=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'approval-policy-')));const roots={main:path.join(base,'main'),perso:path.join(base,'perso')};
for(const r of Object.values(roots)){fs.mkdirSync(r);fs.mkdirSync(path.join(r,'memory'));}
const local=createPolicy(roots,[]);const call=(toolName,params,c=ctx)=>({event:{toolName,params,toolCallId:crypto.randomUUID()},ctx:c});
const packet=()=>({to:['nobody@example.invalid'],subject:'Test',body:'Exact body',attachments:[{name:'test.txt',contentType:'text/plain',contentBytes:Buffer.from('exact bytes').toString('base64')}]});
test.after(()=>fs.rmSync(base,{recursive:true,force:true}));
test('all shell commands and unqualified execution paths fail closed',()=>{
 for(const toolName of ['exec','process','code_execution','nodes','browser','orion__exec_tool','outline__exec_tool','gateway','plugins','unknown'])assert.equal(policy({toolName,params:{command:'gog gmail search harmless'}},ctx).block,true,toolName);
});
test('dedicated reads do not ask; Graph/BookStack remain separated',()=>{
 for(const [toolName,params,c] of [['gmail_read',{action:'search',query:'in:inbox'},ctx],['system_read',{action:'os'},ctx],['outlook_mail_read',{action:'search'},{agentId:'main'}],['bookstack_page',{pageId:12},ctx],['bookstack_suivi',{},ctx]])assert.equal(local({toolName,params},c),undefined);
 assert.equal(local({toolName:'gmail_read'}, {agentId:'main'}).block,true);assert.equal(local({toolName:'outlook_mail_read'},ctx).block,true);
});
test('strict Gmail read argv: query is data, no flags/injection/control-flow',()=>{
 const args=readArgs({action:'search',query:'subject:x; rm -rf / $(whoami)'});assert.equal(args.at(-2),'--max');assert.ok(args.includes('(subject:x; rm -rf / $(whoami))'));assert.ok(args.includes('--readonly'));assert.ok(args.includes('--gmail-no-send'));
 for(const p of [{action:'send'},{action:'get',messageId:'--force'},{action:'search',query:'ok',exec:'evil'},{action:'search',query:'ok',max:101}])assert.throws(()=>readArgs(p));
 assert.ok(readArgs({action:'thread',threadId:'abc123'}).includes('get'));
});
test('attachment read destination is generated inside own workspace',async()=>{
 const data=Buffer.from('attachment');const result=JSON.parse(await gmailRead({action:'attachment',messageId:'abc',attachmentId:'xyz'},ctx,roots.perso,async args=>{fs.writeFileSync(args.at(-1),data);return '{}';}));assert.ok(result.path.startsWith(roots.perso+'/'));assert.equal(result.bytes,data.length);
 const parent=path.join(roots.perso,'.gmail-downloads');fs.rmSync(parent,{recursive:true});fs.symlinkSync(roots.main,parent);await assert.rejects(gmailRead({action:'attachment',messageId:'abc',attachmentId:'xyz'},ctx,roots.perso,async()=>{}));fs.unlinkSync(parent);
});
test('native grants bind agent/session/id/content and are consumable once',()=>{
 const {event}=call('gmail_send',packet());const gate=local(event,ctx);assert.deepEqual(gate.requireApproval.allowedDecisions,['allow-once','deny']);gate.requireApproval.onResolution('allow-once');
 assert.throws(()=>consumeGrant(event.toolCallId,{...event.params,body:'changed'},ctx,'gmail_send'));
 const c=call('gmail_send',packet());const g=local(c.event,ctx);g.requireApproval.onResolution('allow-once');consumeGrant(c.event.toolCallId,c.event.params,ctx,'gmail_send');assert.throws(()=>consumeGrant(c.event.toolCallId,c.event.params,ctx,'gmail_send'));
 for(const decision of ['deny','timeout','cancelled','allow-always']){const c=call('gmail_send',packet());local(c.event,ctx).requireApproval.onResolution(decision);assert.throws(()=>consumeGrant(c.event.toolCallId,c.event.params,ctx,'gmail_send'));}
 assert.throws(()=>consumeGrant('direct-api',packet(),ctx,'gmail_send'));
});
test('Gmail MIME binds body/recipients/attachment bytes, transport neutralized',async()=>{
 const p=packet();let called=0;const result=await gmailSend(p,async args=>{called++;const bytes=fs.readFileSync(args.at(-1),'utf8');assert.equal(bytes,mime(mailPacket(p)));assert.ok(bytes.includes('To: nobody@example.invalid'));assert.ok(bytes.includes(p.attachments[0].contentBytes));assert.ok(args.includes('--raw-file'));return '{}';});assert.equal(called,1);assert.equal(result.accepted,true);
 assert.throws(()=>mailPacket({...p,to:['x\r\nBcc:bad@example.invalid']}));assert.throws(()=>mailPacket({...p,attachments:[{...p.attachments[0],contentBytes:'invalid'}]}));
});
test('memory exception respects canonical paths, relative paths, own workspace and symlinks',()=>{
 for(const file of ['USER.md','MEMORY.md','memory/day.md']){const r=local({toolName:'write',params:{path:file,content:'memo'}},ctx);assert.ok(!r.block&&!r.requireApproval);assert.ok(r.params.path.startsWith(roots.perso+'/'));}
 const outside=path.join(base,'outside.md');fs.writeFileSync(outside,'other');fs.symlinkSync(outside,path.join(roots.perso,'memory','escape.md'));
 for(const file of ['../main/USER.md','memory/escape.md','../outside.md'])assert.equal(local({toolName:'write',params:{path:file,content:'x'}},ctx).block,true);
 assert.equal(local({toolName:'apply_patch',params:{input:'*** Begin Patch\n*** Delete File: memory/day.md\n*** End Patch'}},ctx).block,true);
 fs.symlinkSync(path.join(base,'absent'),path.join(roots.perso,'memory','dangling.md'));assert.equal(local({toolName:'write',params:{path:'memory/dangling.md',content:'x'}},ctx).block,true);
});
test('file_change approval protects exact preimage, native outside writes blocked',async()=>{
 const file=path.join(roots.perso,'ordinary.txt');fs.writeFileSync(file,'before');const p={action:'write',path:file,content:'after'};
 const c=call('file_change',p),gate=local(c.event,ctx);assert.ok(gate.requireApproval);gate.requireApproval.onResolution('allow-once');const grant=consumeGrant(c.event.toolCallId,p,ctx,'file_change');fs.writeFileSync(file,'concurrent');await assert.rejects(executeChange(grant.plan));assert.equal(fs.readFileSync(file,'utf8'),'concurrent');
 const own=changePlan({action:'write',path:'memory/new.md',content:'memo'},ctx,roots,[]);assert.equal(own.memory,true);await executeChange(own);assert.equal(fs.readFileSync(own.target,'utf8'),'memo');
});
test('deletions of memory always require approval; trash/delete/archive distinguished',()=>{
 const file=path.join(roots.perso,'USER.md');fs.writeFileSync(file,'keep');for(const action of ['delete','trash']){const gate=local(call('system_action',{action,path:file}).event,ctx);assert.ok(gate.requireApproval);assert.ok(gate.requireApproval.description.includes(action==='trash'?'réversible':'non réversible'));}assert.equal(fs.readFileSync(file,'utf8'),'keep');
 const a=local(call('bookstack_activity',{action:'archive',activityId:'a'}).event,ctx);const d=local(call('bookstack_activity',{action:'delete',activityId:'a'}).event,ctx);assert.match(a.requireApproval.description,/réversible/);assert.match(d.requireApproval.description,/Suppression effective/);
});
test('controlled system commands are fixed argv and are never run during qualification',()=>{
 for(const p of [{action:'install_package',package:'wget'},{action:'restart_service',service:'org.example.test'}]){const gate=local(call('system_action',p).event,ctx);assert.ok(gate.requireApproval);assert.deepEqual(gate.requireApproval.allowedDecisions,['allow-once','deny']);}
 assert.throws(()=>actionPlan({action:'install_package',package:'x;rm'},ctx,roots,[]));assert.throws(()=>actionPlan({action:'delete',path:roots.main},ctx,roots,[]));
});
test('known outgoing messages remain single-call gated, remote draft send remains blocked',()=>{
 assert.equal(local({toolName:'message',params:{action:'send',target:'x',message:'Hi'}},ctx).block,true);
 assert.ok(local(call('imessage_send',{to:'+33000000000',text:'Hi'}).event,ctx).requireApproval);
 assert.equal(local({toolName:'outlook_mail_write',params:{action:'send_draft',messageId:'x'}},{agentId:'main'}).block,true);
 assert.equal(local({toolName:'outlook_mail_write',params:{action:'send_exact'}},{agentId:'main'}).block,true);
});
test('iMessage transport is neutralized and exactly bound; no shell or fallback',async()=>{
 const {sendMessage}=await import('../lib/imessage.js');let count=0;
 await sendMessage({to:'+33000000000',text:'Exact text',service:'imessage'},undefined,async(file,args,options)=>{count++;assert.equal(file,'/opt/homebrew/bin/imsg');assert.ok(args.includes('Exact text'));assert.ok(args.includes('--no-sms-fallback'));assert.equal(options.shell,false);return {stdout:'{}'};});assert.equal(count,1);
});
test('all automatic channel sends are cancelled and direct plugin writes need a grant',()=>{
 const hooks={};let tools=[];importedPlugin.register({config:{agents:{entries:{main:{workspace:roots.main},perso:{workspace:roots.perso}}}},on:(n,h)=>{hooks[n]=h;},registerTool:f=>tools.push(f),logger:{info:()=>{}}});
 assert.equal(hooks.message_sending({to:'x',content:'unapproved'},{}).cancel,true);
 const sender=tools.map(f=>f(ctx)).find(t=>t.name==='imessage_send');return assert.rejects(sender.execute('api-bypass',{to:'+33000000000',text:'Do not send'}));
});
test('grant remains bound across duplicate module loads, but cannot be reused',async()=>{
 const c=call('gmail_send',packet());local(c.event,ctx).requireApproval.onResolution('allow-once');const other=await import('../index.js?cross-realm-proof');other.consumeGrant(c.event.toolCallId,c.event.params,ctx,'gmail_send');assert.throws(()=>consumeGrant(c.event.toolCallId,c.event.params,ctx,'gmail_send'));
});
test('hard links cannot extend own memory exception',()=>{
 const file=path.join(roots.main,'foreign.md');fs.writeFileSync(file,'private');const alias=path.join(roots.perso,'memory','hardlink.md');fs.linkSync(file,alias);assert.equal(local({toolName:'write',params:{path:alias,content:'x'}},ctx).block,true);assert.throws(()=>changePlan({action:'write',path:alias,content:'x'},ctx,roots,[]));
});
