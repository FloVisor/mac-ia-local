import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { homedir } from "node:os";
import { join } from "node:path";

const pexec = promisify(execFile);

/**
 * Gateway RPC through the local OpenClaw CLI.
 *
 * The plugin SDK's in-process gateway bridge is restricted to bundled or
 * trusted-official plugins, so a local plugin uses the CLI transport, which
 * authenticates with the Gateway token from the state directory (never from
 * plugin config or the model context).
 */
export class GatewayError extends Error {
  constructor(method, message) {
    super(`Gateway ${method}: ${message}`);
    this.code = "gateway_error";
    this.method = method;
  }
}

function cliPath() {
  const override = process.env.BOOKSTACK_OPENCLAW_CLI;
  if (override && override.includes("/")) return override;
  return join(homedir(), ".openclaw", "bin", "openclaw");
}

export async function gatewayCall(method, params = {}, { timeoutMs = 30000 } = {}) {
  try {
    const { stdout } = await pexec(
      cliPath(),
      ["gateway", "call", method, "--json", "--params", JSON.stringify(params)],
      { timeout: timeoutMs, maxBuffer: 16 * 1024 * 1024 },
    );
    const text = stdout.trim();
    return text ? JSON.parse(text) : null;
  } catch (error) {
    const detail = (error.stderr || error.stdout || error.message || "").toString().trim();
    throw new GatewayError(method, detail.slice(0, 500) || "échec inconnu");
  }
}

export async function listGroups() {
  const result = await gatewayCall("sessions.groups.list");
  return Array.isArray(result?.groups) ? result.groups.map((g) => g.name) : [];
}

export async function ensureGroup(name) {
  const groups = await listGroups();
  if (groups.includes(name)) return { created: false, groups };
  const next = [...groups, name];
  await gatewayCall("sessions.groups.put", { names: next });
  return { created: true, groups: next };
}

export async function renameGroup(from, to) {
  return gatewayCall("sessions.groups.rename", { name: from, to });
}

export async function deleteGroup(name) {
  return gatewayCall("sessions.groups.delete", { name });
}

/**
 * Create an independent session.
 *
 * `label` is unique per agent in OpenClaw, so the visible name goes into
 * `displayName` and the label is made unique with the activity name.
 */
export async function createSession({ agentId, label, group, uniqueSuffix }) {
  const params = { agentId };
  if (label) {
    params.displayName = label;
    params.label = uniqueSuffix ? `${label} — ${uniqueSuffix}` : label;
  }
  if (group) params.category = group;
  return gatewayCall("sessions.create", params);
}

export async function patchSession(key, patch) {
  return gatewayCall("sessions.patch", { key, ...patch });
}

export async function listSessions({ agentId, group, limit = 200 } = {}) {
  const params = { limit };
  if (agentId) params.agentId = agentId;
  if (group) params.group = group;
  const result = await gatewayCall("sessions.list", params);
  return Array.isArray(result?.sessions) ? result.sessions : [];
}

export async function getSession(key, agentId) {
  const params = { limit: 200 };
  if (agentId) params.agentId = agentId;
  const result = await gatewayCall("sessions.list", params);
  const rows = Array.isArray(result?.sessions) ? result.sessions : [];
  return rows.find((row) => row.key === key) ?? null;
}
