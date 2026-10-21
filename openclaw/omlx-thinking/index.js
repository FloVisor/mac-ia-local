import { definePluginEntry } from 'openclaw/plugin-sdk/plugin-entry';
// Public provider hook only; no catalog, auth, model or agent defaults changed.
export const MODEL = 'mlx-community--Qwen3.6-35B-A3B-4bit';
export const BUDGETS = Object.freeze({ minimal: 0, low: 512, medium: 2048, high: 8192, ultra: 8192 });

function matches(model) {
  return model?.provider === 'omlx' && model.id === MODEL &&
    model.api === 'openai-completions' && model.baseUrl?.replace(/\/$/, '') === 'http://127.0.0.1:8000/v1';
}

export function wrapStreamFn(ctx) {
  if (!matches(ctx.model) || !ctx.streamFn) return ctx.streamFn;
  const underlying = ctx.streamFn;
  return (model, context, options) => {
    if (!matches(model)) return underlying(model, context, options);
    const level = options?.reasoning ?? ctx.thinkingLevel;
    // Missing/unknown effort keeps existing native behavior, including defaults.
    if (level !== 'off' && level !== 'none' && !Object.hasOwn(BUDGETS, level)) {
      return underlying(model, context, options);
    }
    const original = options?.onPayload;
    return underlying(model, context, {
      ...options,
      onPayload: async (payload, resolvedModel) => {
        const replacement = await original?.(payload, resolvedModel);
        const body = replacement ?? payload;
        const enabled = level !== 'off' && level !== 'none' && level !== 'minimal';
        body.chat_template_kwargs = { ...body.chat_template_kwargs, enable_thinking: enabled };
        delete body.reasoning_effort;
        delete body.chat_template_kwargs.reasoning_effort;
        if (enabled) body.thinking_budget = BUDGETS[level];
        else delete body.thinking_budget;
        return body;
      }
    });
  };
}

export default definePluginEntry({
  id: 'omlx-thinking',
  name: 'oMLX Qwen thinking budgets',
  register(api) {
    api.registerProvider({ id: 'omlx', label: 'oMLX', auth: [], wrapStreamFn });
  }
});
