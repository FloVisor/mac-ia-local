// Preserve the original upstream error. Do not infer a quota or a reset time.
export function normalizeMessage(text) {
  if (typeof text !== 'string' || !/All models exhausted:/i.test(text) ||
      !/rate-limited or on cooldown/i.test(text) || /\[upstream-long-reset\]/.test(text)) return text;
  const match = /Soonest reset\s*~?\s*(\d+(?:\.\d+)?)\s*(h|hours?|d|days?)\b/i.exec(text);
  if (!match || Number(match[1]) * (match[2].toLowerCase().startsWith('h') ? 3600 : 86400) <= 60) return text;
  // Native OpenClaw detects "usage limit" as long-window evidence. This is
  // explicitly an upstream claim, not a diagnosis of the provider's quota.
  return text + '\n[upstream-long-reset] usage limit: upstream reports a long reset; no immediate replay. Reset estimate is not independently verified.';
}
export function normalizeResult(message) {
  if (message && typeof message.errorMessage === 'string') message.errorMessage = normalizeMessage(message.errorMessage);
  return message;
}
export function wrapStreamFn(ctx) {
  const matches = m => ['litellm-free-pro', 'litellm-free-perso'].includes(m?.provider) &&
    m.api === 'openai-completions' && m.baseUrl?.replace(/\/$/, '') === 'https://litellm.gangneux.org/v1';
  if (!matches(ctx.model) || !ctx.streamFn) return ctx.streamFn;
  return (model, context, options) => {
    const stream = ctx.streamFn(model, context, options);
    if (!matches(model)) return stream;
    return new Proxy(stream, { get(target, key) {
      if (key === 'result') return async () => normalizeResult(await target.result());
      if (key === Symbol.asyncIterator) return async function* () {
        for await (const event of target) {
          if (event.type === 'error') normalizeResult(event.error);
          yield event;
        }
      };
      const value = Reflect.get(target, key, target);
      return typeof value === 'function' ? value.bind(target) : value;
    } });
  };
}
