/** Minimal JSON Schema helpers (no runtime dependency). */
export const str = (description) => ({ type: "string", ...(description ? { description } : {}) });
export const num = (description) => ({ type: "number", ...(description ? { description } : {}) });
export const bool = (description) => ({ type: "boolean", ...(description ? { description } : {}) });
export const obj = (properties, required = []) => ({
  type: "object",
  properties,
  ...(required.length ? { required } : {}),
  additionalProperties: false,
});
