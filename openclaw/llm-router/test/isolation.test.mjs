import test from 'node:test';
import assert from 'node:assert/strict';
import { prepare,toolNames } from '../index.js';
import { createPolicy } from '../../send-approval/index.js';
test('identity and parent session come only from runtime',()=>{
 const p={profile:'testing',task:'public synthetic task'};
 assert.deepEqual(prepare({agentId:'main',sessionId:'pro-session'},'submit',p),{identity:'openclaw-pro',params:{...p,parent_session:'pro-session'}});
 assert.equal(prepare({agentId:'perso',sessionId:'perso-session'},'submit',p).identity,'openclaw-perso');
 for(const key of ['agent','identity','parent_session','key_file','paid_authorization','mode'])assert.throws(()=>prepare({agentId:'main',sessionId:'s'},'submit',{...p,[key]:'perso'}));
 for(const ctx of [{agentId:'technique',sessionId:'s'},{agentId:'main'},{}])assert.throws(()=>prepare(ctx,'submit',p));
});
test('only seven adapter tools pass the existing default deny policy',()=>{
 const check=createPolicy();
 for(const agentId of ['main','perso'])for(const toolName of toolNames)assert.equal(check({toolName,params:{}},{agentId,sessionId:'s'}),undefined);
 for(const toolName of ['llm_router_pay','exec','process','message'])assert.equal(check({toolName,params:{}},{agentId:'main',sessionId:'s'}).block,true);
 assert.equal(check({toolName:toolNames[0],params:{}},{agentId:'unknown'}).block,true);
});

test('model cannot grant itself DIRECT selection',()=>{
 const check=createPolicy();
 for(const model of ['litellm-paid/paid/task-advanced','paid-openrouter/glm-5.3','unknown-alias'])assert.equal(check({toolName:'session_status',params:{model}},{agentId:'main',sessionId:'s'}).block,true);
 assert.equal(check({toolName:'session_status',params:{}},{agentId:'main',sessionId:'s'}),undefined);
});
