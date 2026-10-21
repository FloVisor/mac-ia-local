// Offline integration check against the installed OpenClaw transport.
import assert from 'node:assert/strict';
import path from 'node:path';
import os from 'node:os';
import { pathToFileURL } from 'node:url';
import plugin, { MODEL, wrapStreamFn } from './index.js';

const root = path.join(os.homedir(), '.openclaw/runtime/current/lib/node_modules/openclaw');
// Version-specific verification imports; the extension itself uses only the public SDK.
const { r: nativeStream } = await import(pathToFileURL(path.join(root, 'node_modules/@openclaw/ai/dist/openai-completions-Cor8AOo9.mjs')));
const { s: providerLevel, o: listLevels } = await import(pathToFileURL(path.join(root, 'dist/thinking-pMCUcD4L.mjs')));
const model = { id: MODEL, provider: 'omlx', api: 'openai-completions', baseUrl: 'http://127.0.0.1:8000/v1',
  name: 'Qwen local', reasoning: true, input: ['text'], contextWindow: 131072, maxTokens: 8192,
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 } };
const catalog = [model];
assert.deepEqual(listLevels('omlx', MODEL, catalog, 'openclaw'), ['off', 'minimal', 'low', 'medium', 'high', 'ultra']);
let registration;
plugin.register({ registerProvider: p => { registration = p; } });
assert.equal(registration.id, 'omlx');
globalThis.fetch = () => { throw Error('NETWORK_FORBIDDEN'); };
const rows = [];
for (const agentId of ['main', 'perso']) {
  for (const [selected, budget] of [['off', null], ['minimal', null], ['low', 512], ['medium', 2048], ['high', 8192], ['ultra', 8192]]) {
    const level = providerLevel({ provider: 'omlx', model: MODEL, catalog, agentRuntime: 'openclaw', level: selected });
    let captured;
    const captureTransport = (m, c, options) => nativeStream(m, c, { ...options,
      onPayload: async (body, resolved) => {
        captured = await options.onPayload(body, resolved) ?? body;
        throw Error('OFFLINE_CAPTURE_COMPLETE');
      }
    });
    const wrapped = registration.wrapStreamFn({ provider: 'omlx', modelId: MODEL, model, thinkingLevel: level, agentId, streamFn: captureTransport });
    const result = await wrapped(model, { messages: [{ role: 'user', content: 'offline', timestamp: 0 }] },
      { reasoning: level, apiKey: 'offline-not-a-credential', maxTokens: 8192 }).result();
    assert.match(result.errorMessage ?? '', /OFFLINE_CAPTURE_COMPLETE/);
    assert.equal(captured.chat_template_kwargs.enable_thinking, budget !== null);
    assert.equal(captured.thinking_budget, budget ?? undefined);
    assert.equal(captured.reasoning_effort, undefined);
    assert.equal(captured.model, MODEL);
    assert.equal(captured.max_completion_tokens ?? captured.max_tokens, 8192);
    rows.push({ agentId, selected, providerLevel: level, enable_thinking: budget !== null, thinking_budget: budget });
  }
}
const passthrough = () => {};
for (const patch of [{ id: 'other' }, { provider: 'openai' }, { baseUrl: 'http://example.invalid/v1' }, { api: 'openai-responses' }]) {
  assert.equal(wrapStreamFn({ model: { ...model, ...patch }, thinkingLevel: 'medium', streamFn: passthrough }), passthrough);
}
let callbackCalled = false;
const callbackStream = async (m, c, opts) => opts.onPayload({ untouched: true }, m);
const callbackWrap = wrapStreamFn({ model, thinkingLevel: 'medium', streamFn: callbackStream });
const extra = await callbackWrap(model, {}, { onPayload: () => { callbackCalled = true; return { chat_template_kwargs: { preserve_thinking: true } }; } });
assert(callbackCalled);
assert.equal(extra.chat_template_kwargs.preserve_thinking, true);
assert.equal(extra.thinking_budget, 2048);
console.log(JSON.stringify({ status: 'PASS', generationRequests: 0, scopeGuards: 'PASS', payloadCallback: 'PASS', rows }, null, 2));
