// Qualification against the installed runtime; private imports ONLY in tests.
// The deployed plugin itself uses only the documented api.on interface.
import test from 'node:test';
import assert from 'node:assert/strict';
import { homedir } from 'node:os';
import { pathToFileURL } from 'node:url';
import { readdir } from 'node:fs/promises';
import { policy, consumeGrant } from '../index.js';
const dist = `${homedir()}/.openclaw/runtime/current/lib/node_modules/openclaw/dist`;
const files = await readdir(dist);
const load = prefix => import(pathToFileURL(`${dist}/${files.find(f => f.startsWith(prefix) && f.endsWith('.mjs'))}`));
const { a: initialize } = await load('hook-runner-');
const { n: embedded } = await load('embedded-mode-');
const { v: run, Y: broker } = await load('agent-tools.before-tool-call-');
const registration = { pluginId: 'send-approval', hookName: 'before_tool_call', handler: policy, priority: Number.MAX_SAFE_INTEGER };
const registry = { typedHooks: [registration], hooks: [], plugins: [], trustedToolPolicies: [] };
initialize(registry); embedded(true);
const event = () => ({ toolName: 'gmail_send', toolCallId: crypto.randomUUID(), params: { to: ['nobody@example.invalid'], subject: 'Neutralized', body: 'Exact content' }, ctx: { agentId: 'perso', sessionId: 'native-test-session' } });
for (const decision of ['allow-once', 'deny', 'timeout', 'cancelled', undefined, 'allow-always', 'bogus']) {
  test(`installed runtime decision ${decision}`, async () => {
    let executions = 0, requests = 0;
    broker({ request: async ({ request }) => { requests++; assert.deepEqual(request.allowedDecisions, ['allow-once', 'deny']); return { decision }; } });
    const args=event(), result = await run(args);
    if (!result.blocked) { consumeGrant(args.toolCallId,result.params,args.ctx,args.toolName); executions++; } // neutralized tool: counter only
    assert.equal(requests, 1);
    assert.equal(executions, decision === 'allow-once' ? 1 : 0);
  });
}
test('installed runtime transport error blocks tool', async () => {
  broker({ request: async () => { throw Error('SIMULATED_TRANSPORT_ERROR'); } });
  assert.equal((await run(event())).blocked, true);
});
test('installed runtime freezes args and demands fresh approval for changed action', async () => {
  const args = event(); const original = structuredClone(args.params); let requests = 0;
  broker({ request: async () => { requests++; args.params.body = 'CHANGED'; return { decision: 'allow-once' }; } });
  const result = await run(args);
  assert.equal(result.blocked, false); assert.deepEqual(result.params, original);
  broker({ request: async () => { requests++; return { decision: 'deny' }; } });
  assert.equal((await run({ ...args, toolCallId: crypto.randomUUID() })).blocked, true);
  assert.equal(requests, 2);
});
test('installed runtime rejects lower-priority parameter rewrite', async () => {
  registry.typedHooks.push({ pluginId: 'test-only', hookName: 'before_tool_call', priority: -1, handler: () => ({ params: { command: 'imsg send --to OTHER --text CHANGED' } }) });
  broker({ request: async () => ({ decision: 'allow-once' }) });
  const args = event(), result = await run(args);
  assert.equal(result.blocked, false); assert.deepEqual(result.params, args.params);
  registry.typedHooks.pop();
});
test('installed runtime lower-priority veto and hook exception both block', async () => {
  for (const handler of [() => ({ block: true, blockReason: 'TEST_VETO' }), () => { throw Error('TEST_HOOK_FAILURE'); }]) {
    registry.typedHooks.push({ pluginId: 'test-only', hookName: 'before_tool_call', priority: -1, handler });
    broker({ request: async () => ({ decision: 'allow-once' }) });
    assert.equal((await run(event())).blocked, true);
    registry.typedHooks.pop();
  }
});
