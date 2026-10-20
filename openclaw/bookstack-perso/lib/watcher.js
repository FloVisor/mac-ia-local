import { readFile, writeFile, mkdir, rename } from "node:fs/promises";
import { dirname, join } from "node:path";
import { createHash } from "node:crypto";
import { BookStackClient } from "./http.js";
import { convertDocument, storeOriginal } from "./extract.js";
import { CommentIndex } from "./comment-index.js";
import { syncBookComments } from "./comment-sync.js";

const DOCUMENT_EXTENSIONS = new Set([
  "pdf", "docx", "doc", "pptx", "xlsx", "xls", "odt", "rtf", "csv",
  "png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp", "txt", "md", "html", "htm", "epub",
]);

const DECORATION_HINTS = /(logo|icone|icon|banner|banni[eè]re|favicon|avatar|sprite|background|fond)/i;

export class WatcherState {
  constructor(stateDir) {
    this.path = join(stateDir, "state", "bookstack-perso", "watcher.json");
    this.data = null;
  }

  async load() {
    if (this.data) return this.data;
    try {
      this.data = JSON.parse(await readFile(this.path, "utf8"));
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
      this.data = { version: 1, lastAttachmentId: 0, processed: {}, failures: {} };
    }
    return this.data;
  }

  async save() {
    await mkdir(dirname(this.path), { recursive: true, mode: 0o700 });
    const tmp = `${this.path}.tmp`;
    await writeFile(tmp, `${JSON.stringify(this.data, null, 2)}\n`, { mode: 0o600 });
    await rename(tmp, this.path);
  }
}

function isDocumentAttachment(attachment) {
  if (attachment.external) return false;
  const ext = String(attachment.extension ?? "").toLowerCase();
  if (!DOCUMENT_EXTENSIONS.has(ext)) return false;
  if (DECORATION_HINTS.test(attachment.name ?? "")) return false;
  return true;
}

/**
 * One polling pass: find new file attachments on pages of registered activity
 * books, extract them, and attach the extraction page. Idempotent by
 * attachment id + content hash; never recreates a deleted page.
 */
export async function pollOnce({ client, registry, stateDir, agent = "perso", limit = 20, dryRun = false }) {
  const state = new WatcherState(stateDir);
  const data = await state.load();
  const activities = await registry.listActivities();
  const bookIds = new Set(activities.map((a) => a.bookId));

  const listing = await client.get("/attachments", { count: 500, sort: "-id" });
  const candidates = (listing.data ?? [])
    .filter((a) => bookIds.size === 0 || true)
    .filter(isDocumentAttachment)
    .filter((a) => !data.processed[String(a.id)])
    .slice(0, limit);

  const results = [];
  for (const attachment of candidates) {
    const page = await client.get(`/pages/${attachment.uploaded_to}`).catch(() => null);
    if (!page) {
      results.push({ attachmentId: attachment.id, status: "skipped", reason: "page_unavailable" });
      continue;
    }
    const pageTags = Array.isArray(page.tags) ? page.tags : [];
    if (pageTags.some((t) => t.name === "openclaw-role" && t.value === "extraction")) {
      results.push({ attachmentId: attachment.id, status: "skipped", reason: "extraction_page" });
      continue;
    }
    const activity = activities.find((a) => a.bookId === page.book_id);
    if (!activity) {
      results.push({ attachmentId: attachment.id, status: "skipped", reason: "no_activity_for_book" });
      continue;
    }
    if (dryRun) {
      results.push({ attachmentId: attachment.id, status: "would_process", activity: activity.name, pageId: page.id });
      continue;
    }

    try {
      const meta = await client.get(`/attachments/${attachment.id}`);
      const buffer = Buffer.from(meta.content ?? "", "base64");
      const digest = createHash("sha256").update(buffer).digest("hex").slice(0, 16);
      const key = `${attachment.id}:${digest}`;
      if (data.processed[key]) {
        results.push({ attachmentId: attachment.id, status: "duplicate", key });
        continue;
      }

      const original = await storeOriginal({
        stateDir,
        agent,
        conversation: `watcher-${activity.id}`,
        filename: attachment.name ?? `attachment-${attachment.id}`,
        buffer,
      });
      const conversion = await convertDocument(original.path, {
        agent,
        conversation: `watcher-${activity.id}`,
        ocr: "auto",
      });

      const title = `${attachment.name ?? `Pièce jointe ${attachment.id}`} (extraction)`;
      const markdown = [
        `# ${title}`,
        "",
        "## Provenance",
        `- Pièce jointe BookStack : ${attachment.id} (${attachment.name})`,
        `- Page source : ${page.id} — ${page.name}`,
        `- Importé le : ${new Date().toISOString()}`,
        `- Empreinte SHA-256 (16) : ${original.sha256}`,
        `- Méthode : Docling${conversion.ocr_executed ? " + OCR" : ""} (${conversion.ocr_mode})`,
        `- Pages : ${conversion.pages ?? "?"}`,
        "",
        "## Texte extrait",
        "",
        conversion.markdown ?? "",
      ].join("\n");

      const pageBody = { name: title };
      if (activity.documentsChapterId) pageBody.chapter_id = activity.documentsChapterId;
      else pageBody.book_id = activity.bookId;
      const created = await client.post("/pages", {
        ...pageBody,
        markdown,
        tags: [{ name: "openclaw-role", value: "extraction" }, { name: "openclaw-source-attachment", value: String(attachment.id) }],
      });

      data.processed[key] = {
        attachmentId: attachment.id,
        pageId: created.id,
        activityId: activity.id,
        sha256: original.sha256,
        at: new Date().toISOString(),
      };
      data.lastAttachmentId = Math.max(data.lastAttachmentId ?? 0, attachment.id);
      await state.save();
      results.push({ attachmentId: attachment.id, status: "processed", pageId: created.id, activity: activity.name });
    } catch (error) {
      data.failures[String(attachment.id)] = { message: error.message, at: new Date().toISOString() };
      await state.save();
      results.push({ attachmentId: attachment.id, status: "failed", error: error.message });
    }
  }

  // Synchronisation légère des commentaires (aucun appel LLM) : détecte aussi
  // les suppressions, qu'une date de page ne signalerait pas.
  let comments = null;
  if (!dryRun) {
    const index = new CommentIndex(stateDir);
    comments = [];
    for (const activity of activities) {
      try {
        const synced = await syncBookComments({ client, index, bookId: activity.bookId });
        comments.push({ activityId: activity.id, ...synced });
      } catch (error) {
        comments.push({ activityId: activity.id, error: error.message });
      }
    }
  }

  return { scanned: (listing.data ?? []).length, candidates: candidates.length, results, comments };
}
