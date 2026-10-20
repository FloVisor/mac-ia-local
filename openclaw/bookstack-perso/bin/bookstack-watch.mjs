#!/usr/bin/env node
/**
 * Traitement des pièces jointes déposées dans BookStack depuis le navigateur.
 *
 * Aucun appel LLM : lecture API, extraction locale, écriture BookStack.
 * État persistant dans ~/.openclaw/state/bookstack-perso/watcher.json.
 */
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { resolveSecretRefValues } from "openclaw/plugin-sdk/secret-ref-runtime";
import { BookStackClient } from "../lib/http.js";
import { ActivityRegistry } from "../lib/registry.js";
import { pollOnce } from "../lib/watcher.js";

const STATE_DIR = process.env.OPENCLAW_STATE_DIR ?? join(homedir(), ".openclaw");
const CONFIG_PATH = process.env.OPENCLAW_CONFIG_PATH ?? join(STATE_DIR, "openclaw.json");

function loadConfig() {
  return JSON.parse(readFileSync(CONFIG_PATH, "utf8"));
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const limitArg = args.find((a) => a.startsWith("--limit="));
  const limit = limitArg ? Number(limitArg.split("=")[1]) : 20;

  const config = loadConfig();
  const pluginConfig = config.plugins?.entries?.["bookstack-perso"]?.config ?? {};
  const ref = pluginConfig.apiToken;
  if (!ref) throw new Error("apiToken SecretRef absent de la configuration du plugin.");
  const resolved = await resolveSecretRefValues([ref], { config });
  const token = resolved.get(`${ref.source}:${ref.provider}:${ref.id}`);
  if (typeof token !== "string" || !token.includes(":")) throw new Error("Jeton BookStack non résolu.");

  const baseUrl = String(pluginConfig.baseUrl ?? "https://bookstack.gangneux.org").replace(/\/+$/, "");
  const client = new BookStackClient({ baseUrl, host: new URL(baseUrl).host, token });
  const registry = new ActivityRegistry(STATE_DIR);

  const result = await pollOnce({ client, registry, stateDir: STATE_DIR, limit, dryRun });
  console.log(JSON.stringify({ ok: true, dryRun, ...result }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.code ?? "error", message: error.message }));
  process.exit(1);
});
