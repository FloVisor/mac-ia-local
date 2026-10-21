import test from 'node:test';
import assert from 'node:assert/strict';
import {createPolicy} from '../index.js';

test('Docker time is read-only, agent scoped, direct and deferred',()=>{
 const policy=createPolicy();
 for(const [profile,agent,other] of [['pro','main','perso'],['perso','perso','main']]){
  for(const [tool,args] of [['get_current_time',{timezone:'Europe/Paris'}],['convert_time',{source_timezone:'UTC',time:'12:00',target_timezone:'Europe/Paris'}]]){
   const name=`docker_gateway_${profile}__${tool}`,ctx={agentId:agent,sessionId:'docker-time-test'};
   assert.equal(policy({toolName:name,params:args},ctx),undefined);
   assert.equal(policy({toolName:'tool_call',params:{id:`mcp:docker_gateway_${profile}:${name}`,args}},ctx),undefined);
   assert.equal(policy({toolName:name,params:args},{...ctx,agentId:other}).block,true);
   assert.equal(policy({toolName:name,params:{...args,command:'unexpected'}},ctx).block,true);
   assert.equal(policy({toolName:name,params:{}},ctx).block,true);
  }
  assert.equal(policy({toolName:`docker_gateway_${profile}__unknown`,params:{}},{agentId:agent}).block,true);
 }
 assert.equal(policy({toolName:'another_server__get_current_time',params:{timezone:'UTC'}},{agentId:'main'}).block,true);
});
