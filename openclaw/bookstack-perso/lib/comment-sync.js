import { fetchPageComments, toIndexRecord } from "./comments.js";

/**
 * Synchronise l'index des commentaires pour un livre.
 *
 * - parcourt toutes les pages du livre (pagination complète) ;
 * - relit les commentaires de chaque page et remplace ses enregistrements,
 *   ce qui détecte aussi les suppressions ;
 * - ne fait aucun appel LLM.
 */
export async function syncBookComments({ client, index, bookId, maxPages = 0, onProgress }) {
  const pages = [];
  let offset = 0;
  const count = 200;
  for (;;) {
    const listing = await client.get("/pages", { count, offset, "filter[book_id]": bookId });
    const rows = listing.data ?? [];
    pages.push(...rows);
    offset += rows.length;
    if (rows.length < count || offset >= (listing.total ?? 0)) break;
    if (maxPages && pages.length >= maxPages) break;
  }

  let comments = 0;
  let syncedPages = 0;
  for (const page of pages) {
    // La liste des pages ne renvoie pas chapter_id : lire la page.
    const full = await client.get(`/pages/${page.id}`).catch(() => null);
    const chapterId = full?.chapter_id ?? page.chapter_id ?? null;
    const rows = await fetchPageComments(client, page.id);
    const records = rows.map((c) =>
      toIndexRecord(c, { bookId, chapterId, pageName: page.name, pageSlug: page.slug, bookName: null }),
    );
    await index.replacePage(page.id, records);
    comments += records.length;
    syncedPages += 1;
    onProgress?.({ pageId: page.id, pageName: page.name, comments: records.length });
  }

  return { bookId, pages: syncedPages, comments, totalPages: pages.length };
}

/** Synchronise une seule page (après écriture ou sur demande). */
export async function syncPageComments({ client, index, pageId, bookId, chapterId, pageName, pageSlug }) {
  const rows = await fetchPageComments(client, pageId);
  const records = rows.map((c) => toIndexRecord(c, { bookId, chapterId, pageName, pageSlug }));
  await index.replacePage(pageId, records);
  return { pageId, comments: records.length };
}
