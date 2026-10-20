import { resolveSecretRefValues } from "openclaw/plugin-sdk/secret-ref-runtime";
import { ConfigError } from "./errors.js";

export const DEFAULT_BASE_URL = "https://bookstack.gangneux.org";

function refKey(ref) {
  return `${ref.source}:${ref.provider}:${ref.id}`;
}

/** A SecretRef is an object with `source` and `id`; anything else is a literal value. */
export function isSecretRef(value) {
  return Boolean(value) && typeof value === "object" && typeof value.source === "string" && typeof value.id === "string";
}

/**
 * Resolve the API token from a configured value.
 *
 * The gateway materializes manifest-declared `secretInputs` before handing the
 * config to the plugin, so `api.pluginConfig.apiToken` is usually the plaintext
 * token. Cold readers (CLI, watcher) still see the raw SecretRef object.
 */
export async function resolveApiToken(value, { config } = {}) {
  if (typeof value === "string") {
    const token = value.trim();
    if (!token) throw new ConfigError("token_invalid", "Jeton BookStack vide.");
    return token;
  }
  if (!isSecretRef(value)) {
    throw new ConfigError(
      "missing_token",
      "Jeton BookStack non configuré (plugins.entries.bookstack-perso.config.apiToken doit être un SecretRef ou une valeur résolue).",
    );
  }
  const ref = { source: value.source, provider: value.provider ?? "default", id: value.id };
  let token;
  try {
    const resolved = await resolveSecretRefValues([ref], { config });
    token = resolved.get(refKey(ref));
  } catch (error) {
    throw new ConfigError("token_unresolved", `Résolution du SecretRef impossible: ${error.message}`);
  }
  if (typeof token !== "string" || !token.includes(":")) {
    throw new ConfigError("token_invalid", "Le secret BookStack doit contenir « ID:SECRET ».");
  }
  return token;
}

/** Resolve the BookStack base URL and API token from plugin config. Never logs the token. */
export async function resolveConfig(api) {
  const cfg = api.pluginConfig ?? {};
  const baseUrl = String(cfg.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
  let parsed;
  try {
    parsed = new URL(baseUrl);
  } catch {
    throw new ConfigError("invalid_base_url", `baseUrl invalide: ${baseUrl}`);
  }
  if (parsed.protocol !== "https:") {
    throw new ConfigError("insecure_base_url", "BookStack doit être joignable en HTTPS.");
  }
  const token = await resolveApiToken(cfg.apiToken, { config: api.config });
  return { baseUrl, host: parsed.host, token };
}
