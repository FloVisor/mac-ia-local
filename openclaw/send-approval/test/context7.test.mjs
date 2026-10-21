import test from 'node:test';
import assert from 'node:assert/strict';
import {createPolicy} from '../index.js';

test('Context7 exact Pro read contracts, direct and deferred, fail closed',()=>{
 const policy=createPolicy(),ctx={agentId:'main',sessionId:'context7-test'};
 const cases=[['resolve-library-id',{libraryName:'React',query:'useState'}],['query-docs',{libraryId:'/websites/react_dev',query:'useState'}],['query-docs',{libraryId:'/websites/react_dev',query:'useState',language:'JavaScript'}]];
 for(const [tool,args] of cases){
  const name=`docker_gateway_pro__${tool}`;
  for(const event of [{toolName:name,params:args},{toolName:'tool_call',params:{id:`mcp:docker_gateway_pro:${name}`,args}}]){
   assert.equal(policy(event,ctx),undefined);
   assert.equal(policy(event,{...ctx,agentId:'perso'}).block,true);
  }
  for(const bad of [{},{...args,query:''},{...args,query:1},{...args,command:'unexpected'},{...args,language:null}])assert.equal(policy({toolName:name,params:bad},ctx).block,true);
  for(const server of ['docker_gateway_perso','other_server'])assert.equal(policy({toolName:`${server}__${tool}`,params:args},ctx).block,true);
 }
 for(const tool of ['future-tool','delete','resolve_library_id'])assert.equal(policy({toolName:`docker_gateway_pro__${tool}`,params:{}},ctx).block,true);
 assert.equal(policy({toolName:'tool_call',params:{id:'mcp:other:docker_gateway_pro__query-docs',args:cases[1][1]}},ctx).block,true);
});
