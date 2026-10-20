import { resolveSecretRefValues } from "openclaw/plugin-sdk/secret-ref-runtime";
import { ConfigError } from "./errors.js";

export const DEFAULT_BASE_URL = "https://bookstack.gangneux.org";

function refKey(ref) {
  return `${ref.source}:${ref.provider}:${ref.id}`;
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
  const ref = cfg.apiToken;
  if (!ref || typeof ref !== "object" || !ref.source || !ref.id) {
    throw new ConfigError(
      "missing_token",
      "Jeton BookStack non configuré (plugins.entries.bookstack-perso.config.apiToken doit être un SecretRef).",
    );
  }
  let token;
  try {
    const resolved = await resolveSecretRefValues([ref], { config: api.config });
    token = resolved.get(refKey(ref));
  } catch (error) {
    throw new ConfigError("token_unresolved", `Résolution du SecretRef impossible: ${error.message}`);
  }
  if (typeof token !== "string" || !token.includes(":")) {
    throw new ConfigError("token_invalid", "Le secret BookStack doit contenir « ID:SECRET ».");
  }
  return { baseUrl, host: parsed.host, token };
}
