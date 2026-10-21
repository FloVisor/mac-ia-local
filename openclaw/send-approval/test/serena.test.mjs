import test from 'node:test';
import assert from 'node:assert/strict';
import {createPolicy} from '../index.js';
test('Serena read contracts are Pro only and strict, including deferred calls',()=>{
 const policy=createPolicy(),ctx={agentId:'main',sessionId:'serena-test'};
 for(const [tool,args] of [['serena_repository_status',{repository:'FloVisor/mac-ia-local'}],['serena_find_symbol',{repository:'FloVisor/mac-ia-local',name_path_pattern:'main'}],['serena_symbols_overview',{repository:'FloVisor/mac-ia-local',relative_path:'mcp/test.py'}],['serena_find_references',{repository:'FloVisor/mac-ia-local',name_path:'main',relative_path:'mcp/test.py'}],['serena_search_pattern',{repository:'FloVisor/mac-ia-local',substring_pattern:'def main'}]]){
  const name=`docker_gateway_pro__${tool}`;
  for(const event of [{toolName:name,params:args},{toolName:'tool_call',params:{id:name,args}}]){
   assert.equal(policy(event,ctx),undefined);
   assert.equal(policy(event,{...ctx,agentId:'perso'}).block,true);
  }
  assert.equal(policy({toolName:name,params:{...args,command:'write'}},ctx).block,true);
  assert.equal(policy({toolName:name,params:{...args,repository:''}},ctx).block,true);
 }
 for(const tool of ['serena_edit','serena_execute_shell_command'])assert.equal(policy({toolName:`docker_gateway_pro__${tool}`,params:{repository:'x'}},ctx).block,true);
 for(const relative_path of ['/etc/passwd','../outside'])assert.equal(policy({toolName:'docker_gateway_pro__serena_find_symbol',params:{repository:'x',name_path_pattern:'main',relative_path}},ctx).block,true);
});
