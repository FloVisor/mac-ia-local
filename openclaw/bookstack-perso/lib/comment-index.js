import { readFile, writeFile, mkdir, rename } from "node:fs/promises";
import { dirname, join } from "node:path";
import { normalize } from "./comments.js";

/**
 * Index lexical local des commentaires BookStack.
 *
 * Dérivé de recherche reconstructible : jamais une seconde documentation
 * éditable. Aucune dépendance externe, aucun moteur vectoriel.
 */
export class CommentIndex {
  constructor(stateDir) {
    this.path = join(stateDir, "state", "bookstack-perso", "comments-index.json");
    this.data = null;
  }

  async load() {
    if (this.data) return this.data;
    try {
      this.data = JSON.parse(await readFile(this.path, "utf8"));
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
      this.data = { version: 1, syncedAt: null, records: {} };
    }
    return this.data;
  }

  async save() {
    await mkdir(dirname(this.path), { recursive: true, mode: 0o700 });
    const tmp = `${this.path}.tmp`;
    await writeFile(tmp, `${JSON.stringify(this.data, null, 2)}\n`, { mode: 0o600 });
    await rename(tmp, this.path);
  }

  /** Replace every record of one page (detects deletions, not just updates). */
  async replacePage(pageId, records) {
    const data = await this.load();
    for (const [id, rec] of Object.entries(data.records)) {
      if (rec.pageId === pageId) delete data.records[id];
    }
    for (const rec of records) data.records[String(rec.id)] = rec;
    data.syncedAt = new Date().toISOString();
    await this.save();
    return records.length;
  }

  async removePage(pageId) {
    const data = await this.load();
    let removed = 0;
    for (const [id, rec] of Object.entries(data.records)) {
      if (rec.pageId === pageId) { delete data.records[id]; removed += 1; }
    }
    await this.save();
    return removed;
  }

  async stats() {
    const data = await this.load();
    const records = Object.values(data.records);
    return {
      syncedAt: data.syncedAt,
      comments: records.length,
      pages: new Set(records.map((r) => r.pageId)).size,
      archived: records.filter((r) => r.archived).length,
    };
  }

  /**
   * Lexical search with accent-insensitive matching and simple stemming.
   * Returns every match (paginated by the caller), never a hidden global cap.
   */
  async search({ query, bookId, chapterId, pageId, author, since, until, archived = "all", offset = 0, limit = 20 }) {
    const data = await this.load();
    const terms = tokenize(query);
    const rows = [];
    for (const rec of Object.values(data.records)) {
      if (bookId && rec.bookId !== bookId) continue;
      if (chapterId && rec.chapterId !== chapterId) continue;
      if (pageId && rec.pageId !== pageId) continue;
      if (author && normalize(rec.author ?? "") !== normalize(author)) continue;
      if (since && rec.createdAt < since) continue;
      if (until && rec.createdAt > until) continue;
      if (archived === "only" && !rec.archived) continue;
      if (archived === "exclude" && rec.archived) continue;
      const haystack = normalize(`${rec.text} ${rec.pageName ?? ""} ${rec.author ?? ""}`);
      const score = scoreMatch(haystack, terms);
      if (terms.length > 0 && score === 0) continue;
      rows.push({ ...rec, score, snippet: snippet(rec.text, terms) });
    }
    rows.sort((a, b) => b.score - a.score || String(b.createdAt).localeCompare(String(a.createdAt)));
    const total = rows.length;
    const page = rows.slice(offset, offset + limit);
    return { total, offset, limit, hasMore: offset + page.length < total, results: page };
  }
}

function tokenize(query) {
  return normalize(query)
    .split(/[^a-z0-9€.,]+/)
    .map((t) => t.replace(/^[.,]+|[.,]+$/g, ""))
    .filter((t) => t.length >= 2);
}

function scoreMatch(haystack, terms) {
  if (terms.length === 0) return 1;
  let score = 0;
  for (const term of terms) {
    if (haystack.includes(term)) score += 2;
    else if (term.length > 4 && haystack.includes(term.slice(0, Math.max(4, term.length - 2)))) score += 1;
  }
  return score;
}

function snippet(text, terms) {
  const plain = String(text ?? "").replace(/\s+/g, " ").trim();
  if (!plain) return "";
  const norm = normalize(plain);
  let idx = -1;
  for (const term of terms) {
    idx = norm.indexOf(term);
    if (idx >= 0) break;
  }
  if (idx < 0) return plain.slice(0, 200);
  const start = Math.max(0, idx - 80);
  return `${start > 0 ? "…" : ""}${plain.slice(start, start + 220)}${start + 220 < plain.length ? "…" : ""}`;
}
