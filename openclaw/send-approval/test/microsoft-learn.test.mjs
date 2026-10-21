import test from 'node:test';
import assert from 'node:assert/strict';
import {createPolicy} from '../index.js';
test('Microsoft Learn: contrats exacts, agent Pro, aucune extension implicite',()=>{
 const policy=createPolicy(),ctx={agentId:'main',sessionId:'learn-test'};
 for(const [tool,args] of [['microsoft_docs_search',{query:'Windows Server 2025'}],['microsoft_docs_fetch',{url:'https://learn.microsoft.com/en-us/windows-server/'}],['microsoft_code_sample_search',{query:'Get-Service',language:'powershell'}]]){
  const name='docker_gateway_pro__'+tool;
  for(const event of [{toolName:name,params:args},{toolName:'tool_call',params:{id:'mcp:docker_gateway_pro:'+name,args}}]){
   assert.equal(policy(event,ctx),undefined);assert.equal(policy(event,{...ctx,agentId:'perso'}).block,true);
  }
  for(const bad of [{},{...args,command:'x'},{...args,[tool==='microsoft_docs_fetch'?'url':'query']:''}])assert.equal(policy({toolName:name,params:bad},ctx).block,true);
  for(const server of ['docker_gateway_perso','other'])assert.equal(policy({toolName:server+'__'+tool,params:args},ctx).block,true);
 }
 for(const url of ['http://learn.microsoft.com/','https://microsoft.com.evil.test/','https://user:pass@learn.microsoft.com/','file:///tmp/a'])assert.equal(policy({toolName:'docker_gateway_pro__microsoft_docs_fetch',params:{url}},ctx).block,true);
 assert.equal(policy({toolName:'docker_gateway_pro__microsoft_delete',params:{}},ctx).block,true);
});
