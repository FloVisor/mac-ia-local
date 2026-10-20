import { createHash } from "node:crypto";

/** Strip HTML to plain text while keeping paragraph/line structure. */
export function htmlToText(html) {
  if (!html) return "";
  return String(html)
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(p|div|li|h[1-6]|blockquote|tr)>/gi, "\n")
    .replace(/<li[^>]*>/gi, "- ")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#0?39;/gi, "'")
    .replace(/&[a-z#0-9]+;/gi, " ")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Convert plain text or Markdown-ish input to BookStack-compatible HTML. */
export function textToHtml(text) {
  const escaped = String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  const blocks = escaped.split(/\n{2,}/).map((block) => {
    const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) return "";
    if (lines.every((l) => /^[-*]\s+/.test(l))) {
      return `<ul>${lines.map((l) => `<li>${l.replace(/^[-*]\s+/, "")}</li>`).join("")}</ul>`;
    }
    return `<p>${lines.join("<br>")}</p>`;
  });
  return blocks.filter(Boolean).join("\n");
}

/** Normalize for accent-insensitive, case-insensitive matching. */
export function normalize(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

export function commentHash(comment) {
  return createHash("sha256")
    .update(`${comment.id}|${comment.updated_at}|${comment.html ?? ""}|${comment.archived ?? ""}`)
    .digest("hex")
    .slice(0, 16);
}

/**
 * Fetch every comment of a page, including nested replies.
 *
 * The list endpoint returns metadata only, so each root comment is read to get
 * its content and direct replies. Replies are then read recursively because a
 * single read is not guaranteed to return every nesting level.
 */
export async function fetchPageComments(client, pageId, { includeArchived = true } = {}) {
  const listing = await client.get("/comments", { count: 500, "filter[commentable_id]": pageId });
  const roots = (listing.data ?? []).filter((c) => c.parent_id === null);
  const out = [];
  const seen = new Set();

  async function readTree(id, depth) {
    if (seen.has(id) || depth > 8) return;
    seen.add(id);
    const full = await client.get(`/comments/${id}`).catch(() => null);
    if (!full) return;
    const node = {
      id: full.id,
      localId: full.local_id,
      parentId: full.parent_id,
      pageId: full.commentable_id,
      html: full.html ?? "",
      text: htmlToText(full.html),
      contentRef: full.content_ref ?? "",
      archived: Boolean(full.archived),
      createdAt: full.created_at,
      updatedAt: full.updated_at,
      author: full.created_by?.name ?? null,
      authorId: full.created_by?.id ?? null,
      depth,
    };
    if (includeArchived || !node.archived) out.push(node);
    for (const reply of full.replies ?? []) {
      await readTree(reply.id, depth + 1);
    }
  }

  for (const root of roots) await readTree(root.id, 0);
  return out;
}

/** Build a flat, searchable record for one comment. */
export function toIndexRecord(comment, { bookId, chapterId, pageName, pageSlug, bookName }) {
  return {
    id: comment.id,
    localId: comment.localId,
    parentId: comment.parentId,
    pageId: comment.pageId,
    pageName: pageName ?? null,
    pageSlug: pageSlug ?? null,
    bookId: bookId ?? null,
    bookName: bookName ?? null,
    chapterId: chapterId ?? null,
    author: comment.author,
    authorId: comment.authorId,
    createdAt: comment.createdAt,
    updatedAt: comment.updatedAt,
    archived: comment.archived,
    contentRef: comment.contentRef,
    text: comment.text,
    hash: commentHash(comment),
  };
}
