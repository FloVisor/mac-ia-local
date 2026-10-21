import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';
vi.mock('./credential.js', async (importOriginal) => ({...await importOriginal<typeof import('./credential.js')>(), tokenForAuthorizedOperation: vi.fn(async ()=>'SIMULATED_TOKEN')}));
import entry, { beforeMicrosoftGraphToolCall, exactMailPayload, classifyApproval } from './index.js';
import { graphPolicyFixture } from './fixtures/graph-access-policy.js';
const ctx={agentId:'main',sessionId:'local-send-exact-test',workspaceDir:'/tmp'};
function runtime(){const factories:any[]=[];const config={enabled:true,warningApprovalsRequired:true,policy:graphPolicyFixture()};entry.register({pluginConfig:config,registerTool:(f:any)=>factories.push(f),on:()=>{},logger:{info:()=>{},warn:()=>{},error:()=>{}}} as any);return {config,tool:factories.map(f=>f(ctx)).find(t=>t.name==='outlook_mail_write')};}
const packet=()=>({action:'send_exact',to:['nobody@example.invalid'],subject:'Neutralized test',bodyText:'Exact approved body',exactAttachments:[{name:'test.txt',contentType:'text/plain',contentBytes:Buffer.from('exact attachment').toString('base64')}]});
afterEach(()=>vi.restoreAllMocks());
describe('local immutable Outlook send',()=>{
 it('critical per-call approval; request contains exact body/recipients/attachment bytes',async()=>{
  const {config,tool}=runtime();const p=packet();let request:any;
  const fetch=vi.spyOn(globalThis,'fetch').mockImplementation(async(input,init)=>{request={url:String(input),body:JSON.parse(String(init?.body))};return new Response(null,{status:202});});
  const gate:any=await beforeMicrosoftGraphToolCall(config,{toolName:'outlook_mail_write',toolCallId:'exact-1',params:p},ctx);
  expect(classifyApproval('outlook_mail_write',p)).toBe('critical');
  expect(gate.requireApproval.allowedDecisions).toEqual(['allow-once','deny']);
  expect(gate.requireApproval.description).toContain('nobody@example.invalid');expect(gate.requireApproval.description).toContain('SHA256=');
  await gate.requireApproval.onResolution('allow-once');
  const result=await tool.execute('exact-1',gate.params??p);expect(result.details.ok).toBe(true);
  expect(fetch).toHaveBeenCalledOnce();expect(request.url).toContain('/me/sendMail');
  expect(request.body.message).toEqual(exactMailPayload(p));expect(request.body.message.attachments[0].contentBytes).toBe(p.exactAttachments[0].contentBytes);
  await tool.execute('exact-1',p);expect(fetch).toHaveBeenCalledOnce();
 });
 it('denial, timeout, absent approval, changed recipient/body/attachment do not reach transport',async()=>{
  const {config,tool}=runtime();const fetch=vi.spyOn(globalThis,'fetch').mockRejectedValue(Error('must not call'));
  for(const decision of ['deny','timeout','cancelled']){
   const p=packet(),id=`denied-${decision}`;const gate:any=await beforeMicrosoftGraphToolCall(config,{toolName:'outlook_mail_write',toolCallId:id,params:p},ctx);
   await gate.requireApproval.onResolution(decision);const r=await tool.execute(id,p);expect(r.details.ok).toBe(false);
  }
  for(const field of ['to','bodyText','exactAttachments']){
   const p=packet(),id=`changed-${field}`;const gate:any=await beforeMicrosoftGraphToolCall(config,{toolName:'outlook_mail_write',toolCallId:id,params:p},ctx);await gate.requireApproval.onResolution('allow-once');
   const changed:any=structuredClone(p);if(field==='to')changed.to=['other@example.invalid'];else if(field==='bodyText')changed.bodyText='CHANGED';else changed.exactAttachments[0].contentBytes=Buffer.from('CHANGED').toString('base64');
   const r=await tool.execute(id,changed);expect(r.details.ok).toBe(false);
  }
  expect((await tool.execute('never-approved',packet())).details.ok).toBe(false);expect(fetch).not.toHaveBeenCalled();
 });
 it('warning writes offer no persistent permission; malformed base64 and missing content fail before transport',async()=>{
  const {config}=runtime();const gate:any=await beforeMicrosoftGraphToolCall(config,{toolName:'outlook_mail_write',toolCallId:'draft-once',params:{action:'create_draft',subject:'test',bodyText:'draft'}},ctx);
  expect(gate.requireApproval.allowedDecisions).toEqual(['allow-once','deny']);
  expect(()=>exactMailPayload({...packet(),exactAttachments:[{name:'x',contentType:'text/plain',contentBytes:'not base64'}]})).toThrow();
  expect(()=>exactMailPayload({...packet(),bodyText:undefined})).toThrow();
 });
});
