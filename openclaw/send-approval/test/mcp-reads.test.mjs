import test from 'node:test';
import assert from 'node:assert/strict';
import {createPolicy} from '../index.js';
import {createMcpReads} from '../lib/mcp-reads.js';
import {contactsArgs,contactsRead} from '../lib/contacts.js';
const ctx={agentId:'main',sessionId:'read-session'};
const contract=(access='read')=>({content:[{type:'text',text:JSON.stringify({name:'search_glpi_ticket',registry:'tool_glpi_wrapper',access,parameters:{type:'object'}})}]});
test('Contacts use read-only argv without shell and preserve Perso scope',async()=>{
 const policy=createPolicy();
 assert.equal(policy({toolName:'contacts_read',params:{action:'status'}},{agentId:'perso'}),undefined);
 assert.equal(policy({toolName:'contacts_read',params:{action:'status'}},ctx).block,true);
 for(const p of [{action:'request-access'},{action:'delete'},{action:'search',query:'x',command:'evil'}])assert.throws(()=>contactsArgs(p));
 let count=0;await contactsRead({action:'search',query:'neutral; $x',fields:'name'},undefined,async(file,args,opts)=>{count++;assert.equal(opts.shell,false);assert.ok(file.endsWith('/.local/bin/perso-contacts'));assert.deepEqual(args,['search','--query','neutral; $x','--fields','name']);return{stdout:'{}'};});assert.equal(count,1);
});
test('Orion discovery and Outline reads, direct and deferred, need no approval',()=>{
 const policy=createPolicy();
 for(const name of ['orion__list_registries','orion__search_tools','orion__get_contract','orion__get_skill','outline__fetch','outline__list_collections']){
  assert.equal(policy({toolName:name,params:{}},ctx),undefined);
  assert.equal(policy({toolName:'tool_call',params:{id:`mcp:${name.split('__')[0]}:${name}`,args:{}}},ctx),undefined);
  assert.equal(policy({toolName:name,params:{}},{...ctx,agentId:'perso'}).block,true);
 }
 assert.equal(policy({toolName:'tool_describe',params:{id:'orion__exec_tool'}},ctx),undefined);
});
test('exec_tool reads require a real matching contract result in same session',()=>{
 const mcpReads=createMcpReads(),policy=createPolicy(undefined,undefined,{mcpReads});
 const params={tool_name:'search_glpi_ticket',params:{ticket_status:'en_cours'}};
 const call={toolName:'orion__exec_tool',params};
 assert.equal(policy(call,ctx).block,true);
 assert.equal(policy({...call,params:{...params,access:'read',readOnly:true}},ctx).block,true);
 mcpReads.observe({toolName:'orion__get_contract',params:{tool_name:params.tool_name},result:contract()},ctx);
 assert.equal(policy(call,ctx),undefined);
 assert.equal(policy({toolName:'tool_call',params:{id:'orion__exec_tool',args:params}},ctx),undefined);
 assert.equal(policy(call,{...ctx,sessionId:'different'}).block,true);
 assert.equal(policy({...call,params:{...params,registry:'different'}},ctx).block,true);
 mcpReads.observe({toolName:'orion__get_contract',params:{tool_name:params.tool_name},result:contract('write')},ctx);
 assert.equal(policy(call,ctx).block,true);
});
test('deferred actual get_contract result works; fabricated nested params do not',()=>{
 const mcpReads=createMcpReads(),policy=createPolicy(undefined,undefined,{mcpReads});
 const p={id:'orion__get_contract',args:{tool_name:'search_glpi_ticket'}};
 mcpReads.observe({toolName:'tool_call',params:p,result:{details:{tool:{name:'orion__get_contract'},result:contract()}}},ctx);
 assert.equal(policy({toolName:'orion__exec_tool',params:{tool_name:'search_glpi_ticket'}},ctx),undefined);
 for(const params of [{id:'orion__search_tools',name:'exec',args:{}},{id:'tool_call',args:{}},{id:'mcp:outline:orion__search_tools',args:{}},{id:'orion__search_tools',args:{},command:'evil'}])assert.equal(policy({toolName:'tool_call',params},ctx).block,true);
});
test('wrapper cannot bypass sender gates or side-effect refusals',()=>{
 const policy=createPolicy();
 for(const [id,args] of [['imessage_send',{to:'+33000000000',text:'neutral'}],['gmail_send',{to:['neutral@example.invalid'],subject:'neutral',body:'neutral'}],['exec',{command:'true'}],['orion__set_document_tags',{}],['outline__create_comment',{}]])assert.equal(policy({toolName:'tool_call',toolCallId:'test',params:{id,args}},{agentId:'perso',sessionId:'test'}).block,true);
 assert.ok(policy({toolName:'gmail_send',toolCallId:'mail',params:{to:['neutral@example.invalid'],subject:'neutral',body:'neutral'}},{agentId:'perso',sessionId:'test'}).requireApproval);
 assert.ok(policy({toolName:'imessage_send',toolCallId:'sms',params:{to:'+33000000000',text:'neutral',service:'sms'}},{agentId:'perso',sessionId:'test'}).requireApproval);
});
