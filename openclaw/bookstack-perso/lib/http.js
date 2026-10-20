import { ConfigError, BookStackError } from "./errors.js";

const MAX_RETRIES = 2;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Minimal BookStack API client.
 * - Auth header is only ever sent to the configured BookStack host.
 * - Redirects are never followed, so the token cannot leak to another origin.
 * - 429/5xx are retried with backoff; 401/403 are surfaced as-is.
 */
export class BookStackClient {
  constructor({ baseUrl, host, token }) {
    this.baseUrl = baseUrl;
    this.host = host;
    this.token = token;
  }

  url(path, query) {
    const u = new URL(`${this.baseUrl}/api${path}`);
    if (u.host !== this.host) throw new ConfigError("host_mismatch", "URL hors du domaine BookStack configuré.");
    for (const [k, v] of Object.entries(query ?? {})) {
      if (v !== undefined && v !== null && v !== "") u.searchParams.set(k, String(v));
    }
    return u;
  }

  async request(method, path, { query, json, form, raw = false, timeoutMs = 60000 } = {}) {
    const url = this.url(path, query);
    const headers = { Authorization: `Token ${this.token}`, Accept: "application/json" };
    let body;
    if (json !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(json);
    } else if (form !== undefined) {
      body = form;
    }

    let lastError;
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt += 1) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      let response;
      try {
        response = await fetch(url, {
          method,
          headers,
          body,
          redirect: "manual",
          signal: controller.signal,
        });
      } catch (error) {
        clearTimeout(timer);
        lastError = new BookStackError(
          error.name === "AbortError" ? "timeout" : "network_error",
          `Requête BookStack échouée: ${error.message}`,
          null,
        );
        if (attempt < MAX_RETRIES) {
          await sleep(500 * (attempt + 1));
          continue;
        }
        throw lastError;
      }
      clearTimeout(timer);

      if (response.status === 429 || response.status >= 500) {
        const retryAfter = Number(response.headers.get("retry-after") ?? 0);
        const waitMs = retryAfter > 0 ? retryAfter * 1000 : 800 * (attempt + 1);
        if (attempt < MAX_RETRIES) {
          await sleep(waitMs);
          continue;
        }
      }

      if (response.status === 401 || response.status === 403) {
        throw new BookStackError(
          response.status === 401 ? "unauthorized" : "forbidden",
          response.status === 401
            ? "BookStack a refusé le jeton (401). Vérifier le SecretRef et les droits du compte."
            : "BookStack a refusé l'opération (403). Les droits du compte ne permettent pas cette action.",
          response.status,
        );
      }
      if (response.status === 404) {
        throw new BookStackError("not_found", "Objet BookStack introuvable (404).", 404);
      }
      if (response.status === 422) {
        const payload = await response.json().catch(() => null);
        throw new BookStackError("validation_failed", "BookStack a rejeté les données (422).", 422, payload);
      }
      if (response.status === 302 || response.status === 301 || response.status === 303) {
        throw new BookStackError("unexpected_redirect", "BookStack a répondu par une redirection inattendue.", response.status);
      }
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new BookStackError("http_error", `BookStack HTTP ${response.status}: ${text.slice(0, 300)}`, response.status);
      }

      if (raw) return response;
      if (response.status === 204) return null;
      const text = await response.text();
      if (!text) return null;
      try {
        return JSON.parse(text);
      } catch {
        return text;
      }
    }
    throw lastError ?? new BookStackError("unknown", "Échec BookStack inconnu.");
  }

  get(path, query) {
    return this.request("GET", path, { query });
  }

  post(path, json) {
    return this.request("POST", path, { json });
  }

  put(path, json) {
    return this.request("PUT", path, { json });
  }

  del(path) {
    return this.request("DELETE", path);
  }

  /** Multipart upload (attachments, images). */
  upload(path, { fields = {}, file, fileField = "file", filename, contentType }) {
    const form = new FormData();
    for (const [k, v] of Object.entries(fields)) form.append(k, String(v));
    form.append(fileField, new Blob([file], { type: contentType ?? "application/octet-stream" }), filename);
    return this.request("POST", path, { form, timeoutMs: 180000 });
  }

  /** Download binary content (attachment file, export). */
  async download(path, query) {
    const response = await this.request("GET", path, { query, raw: true, timeoutMs: 180000 });
    const buffer = Buffer.from(await response.arrayBuffer());
    return {
      buffer,
      contentType: response.headers.get("content-type") ?? "application/octet-stream",
      disposition: response.headers.get("content-disposition") ?? "",
    };
  }
}
