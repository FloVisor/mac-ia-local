import { mkdir, readFile, rename, writeFile, open } from "node:fs/promises";
import { dirname, join } from "node:path";
import { randomUUID } from "node:crypto";

/**
 * Registre local des activités BookStack.
 *
 * Contenu : associations stables (livre <-> groupe de conversations) et
 * liaison conversation -> activité. Aucune copie de la documentation.
 *
 * Écritures : fichier JSON remplacé atomiquement (write temp + rename) sous
 * verrou exclusif, pour rester sûr en cas d'opérations simultanées.
 */
export class ActivityRegistry {
  constructor(stateDir) {
    this.path = join(stateDir, "state", "bookstack-perso", "registry.json");
    this.lockPath = `${this.path}.lock`;
    this.cache = null;
  }

  async ensureDir() {
    await mkdir(dirname(this.path), { recursive: true, mode: 0o700 });
  }

  async withLock(fn) {
    await this.ensureDir();
    let handle;
    for (let attempt = 0; attempt < 100; attempt += 1) {
      try {
        handle = await open(this.lockPath, "wx", 0o600);
        break;
      } catch (error) {
        if (error.code !== "EEXIST") throw error;
        await new Promise((r) => setTimeout(r, 50));
      }
    }
    if (!handle) throw new Error("Verrou du registre BookStack indisponible (autre opération en cours).");
    try {
      return await fn();
    } finally {
      await handle.close().catch(() => {});
      const { unlink } = await import("node:fs/promises");
      await unlink(this.lockPath).catch(() => {});
    }
  }

  async read() {
    if (this.cache) return this.cache;
    await this.ensureDir();
    try {
      const raw = await readFile(this.path, "utf8");
      const parsed = JSON.parse(raw);
      this.cache = normalizeRegistry(parsed);
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
      this.cache = normalizeRegistry({});
    }
    return this.cache;
  }

  async write(data) {
    await this.ensureDir();
    const tmp = `${this.path}.${randomUUID()}.tmp`;
    await writeFile(tmp, `${JSON.stringify(data, null, 2)}\n`, { mode: 0o600 });
    await rename(tmp, this.path);
    this.cache = data;
  }

  /** Read-modify-write under lock. */
  async mutate(fn) {
    return this.withLock(async () => {
      this.cache = null;
      const data = await this.read();
      const result = await fn(data);
      await this.write(data);
      return result;
    });
  }

  async listActivities() {
    const data = await this.read();
    return Object.values(data.activities);
  }

  async findActivity({ id, name, bookId, group }) {
    const data = await this.read();
    const all = Object.values(data.activities);
    if (id) return all.find((a) => a.id === id) ?? null;
    if (bookId) return all.find((a) => a.bookId === Number(bookId)) ?? null;
    if (group) return all.find((a) => a.group === group) ?? null;
    if (name) {
      const needle = name.trim().toLowerCase();
      return all.find((a) => a.name.trim().toLowerCase() === needle) ?? null;
    }
    return null;
  }

  async findActivitiesByName(name) {
    const needle = name.trim().toLowerCase();
    const data = await this.read();
    return Object.values(data.activities).filter((a) => a.name.trim().toLowerCase() === needle);
  }

  async upsertActivity(activity) {
    return this.mutate((data) => {
      const existing = data.activities[activity.id];
      data.activities[activity.id] = {
        ...existing,
        ...activity,
        updatedAt: new Date().toISOString(),
      };
      return data.activities[activity.id];
    });
  }

  async removeActivity(id) {
    return this.mutate((data) => {
      const removed = data.activities[id] ?? null;
      delete data.activities[id];
      for (const [key, binding] of Object.entries(data.bindings)) {
        if (binding.activityId === id) delete data.bindings[key];
      }
      return removed;
    });
  }

  /** Conversation -> activity binding, keyed by the durable session key. */
  async bindSession(sessionKey, activityId, extra = {}) {
    return this.mutate((data) => {
      data.bindings[sessionKey] = {
        activityId,
        sessionKey,
        ...extra,
        boundAt: new Date().toISOString(),
      };
      return data.bindings[sessionKey];
    });
  }

  async unbindSession(sessionKey) {
    return this.mutate((data) => {
      const previous = data.bindings[sessionKey] ?? null;
      delete data.bindings[sessionKey];
      return previous;
    });
  }

  async getBinding(sessionKey) {
    const data = await this.read();
    return data.bindings[sessionKey] ?? null;
  }

  async resolveActivityForSession(sessionKey) {
    const data = await this.read();
    const binding = data.bindings[sessionKey];
    if (binding) {
      const activity = data.activities[binding.activityId];
      if (activity) return { activity, binding, source: "binding" };
    }
    return { activity: null, binding: null, source: "none" };
  }

  /** Fallback: resolve by the sidebar group of the session (native group identity). */
  async resolveActivityForGroup(group) {
    if (!group) return null;
    const data = await this.read();
    return Object.values(data.activities).find((a) => a.group === group) ?? null;
  }
}

function normalizeRegistry(raw) {
  return {
    version: 1,
    activities: raw?.activities && typeof raw.activities === "object" ? raw.activities : {},
    bindings: raw?.bindings && typeof raw.bindings === "object" ? raw.bindings : {},
    processed: raw?.processed && typeof raw.processed === "object" ? raw.processed : {},
  };
}
