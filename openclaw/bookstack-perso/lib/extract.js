import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { homedir } from "node:os";
import { join } from "node:path";
import { mkdir, writeFile, readFile, stat } from "node:fs/promises";
import { createHash } from "node:crypto";
import { ExtractError } from "./errors.js";

const pexec = promisify(execFile);

export const DOCREAD = process.env.DOCREAD_BIN ?? join(homedir(), ".local", "bin", "docread");

/** Run the shared Docling converter. Returns its JSON payload. */
export async function convertDocument(filePath, { agent, conversation, ocr = "auto", tables = false, timeoutMs = 900000 } = {}) {
  const args = [filePath, "--agent", agent, "--conversation", conversation, "--ocr", ocr];
  if (tables) args.push("--tables");
  let stdout;
  try {
    ({ stdout } = await pexec(DOCREAD, args, { timeout: timeoutMs, maxBuffer: 64 * 1024 * 1024 }));
  } catch (error) {
    const raw = (error.stdout || "").trim();
    let payload = null;
    try {
      payload = raw ? JSON.parse(raw.split("\n").pop()) : null;
    } catch {
      payload = null;
    }
    throw new ExtractError(
      payload?.error ?? "conversion_failed",
      payload?.message ?? (error.stderr || error.message || "échec du convertisseur").toString().slice(0, 500),
      payload,
    );
  }
  const line = stdout.trim().split("\n").pop();
  try {
    return JSON.parse(line);
  } catch {
    throw new ExtractError("invalid_converter_output", "Sortie du convertisseur illisible.");
  }
}

/**
 * Resolve a tool `filePath` argument to a real filesystem path.
 *
 * Attachments reach the agent as `media://inbound/<id>` references (the gateway
 * offloads non-image files without exposing a path), so the media store must be
 * accepted wherever a local path is expected.
 */
export function resolveSourcePath(stateDir, filePath) {
  const value = String(filePath ?? "").trim();
  if (!value.startsWith("media://inbound/")) return value;
  const id = value.slice("media://inbound/".length);
  if (!id || id.includes("/") || id.includes("\\") || id === "." || id === "..") {
    throw new ExtractError("invalid_media_ref", `Référence média invalide : ${value}`);
  }
  return join(stateDir, "media", "inbound", id);
}

/** Write a downloaded original into the agent's own document area. */
function slug(value, fallback) {
  const cleaned = String(value ?? "").replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  if (!cleaned) return fallback;
  if (cleaned.length <= 80) return cleaned;
  // Tronquer sans perdre l'extension : le convertisseur la déduit du nom.
  const dot = cleaned.lastIndexOf(".");
  const ext = dot > 0 && cleaned.length - dot <= 10 ? cleaned.slice(dot) : "";
  return cleaned.slice(0, 80 - ext.length) + ext;
}

export async function storeOriginal({ stateDir, agent, conversation, filename, buffer }) {
  const safe = slug(filename, "document");
  const digest = createHash("sha256").update(buffer).digest("hex").slice(0, 16);
  const workspace = agent === "main" ? "workspace" : `workspace-${agent}`;
  const dir = join(stateDir, workspace, ".documents", slug(agent, "main"), slug(conversation, "default"), "originals");
  await mkdir(dir, { recursive: true });
  const target = join(dir, `${digest}-${safe}`);
  await writeFile(target, buffer, { mode: 0o600 });
  return { path: target, sha256: digest, size: buffer.length };
}

export async function fileInfo(path) {
  const s = await stat(path);
  return { size: s.size, mtime: s.mtime.toISOString() };
}

export async function readText(path) {
  return readFile(path, "utf8");
}
