import { str, num, bool, obj } from "./schema.js";
import { resolveConfig } from "./config.js";
import { BookStackClient } from "./http.js";
import { ConfigError, BookStackError } from "./errors.js";
import { makeRegistry, findActivity } from "./activities.js";
import { CommentIndex } from "./comment-index.js";
import { syncBookComments, syncPageComments } from "./comment-sync.js";
import { fetchPageComments, htmlToText, textToHtml } from "./comments.js";
import * as gw from "./gateway.js";

const text = (value) => ({
  content: [{ type: "text", text: typeof value === "string" ? value : JSON.stringify(value, null, 2) }],
  details: value,
});

function fail(code, message, extra = {}) {
  const payload = { ok: false, error: code, message, ...extra };
  return { content: [{ type: "text", text: JSON.stringify(payload, null, 2) }], details: payload };
}

function commentUrl(baseUrl, page, comment) {
  const book = page.book_slug ?? page.book_id;
  const slug = page.slug ?? page.id;
  return `${baseUrl}/books/${book}/page/${slug}#comment${comment.local_id ?? comment.id}`;
}

export function buildCommentTool(api, stateDir) {
  return {
    name: "bookstack_comment",
    label: "BookStack commentaires",
    description:
      "Gère les commentaires BookStack d'une page: list, read, create, reply, update, archive, unarchive, delete, search, sync, thread. Les commentaires restent natifs (HTML côté BookStack, texte côté LLM) et ne modifient jamais le Markdown de la page.",
    parameters: obj({
      action: str("list | read | create | reply | update | archive | unarchive | delete | search | sync | thread"),
      pageId: num("Page concernée."),
      commentId: num("Identifiant global du commentaire."),
      replyTo: num("local_id du commentaire parent (reply)."),
      text: str("Texte du commentaire (converti en HTML)."),
      query: str("Recherche lexicale (search)."),
      activityId: str("Activité (search/sync)."),
      name: str("Nom de l'activité (search/sync)."),
      chapterId: num("Filtre chapitre (search)."),
      author: str("Filtre auteur (search)."),
      since: str("Date minimale ISO (search)."),
      until: str("Date maximale ISO (search)."),
      archived: str("all | only | exclude (search, défaut all)."),
      offset: num("Pagination (search)."),
      limit: num("Taille de page (search, défaut 20)."),
      includeArchived: bool("Inclure les fils archivés (list/thread)."),
      confirm: bool("Confirmation explicite pour delete."),
    }, ["action"]),
    async run(params, ctx) {
      try {
        const config = await resolveConfig(api);
        const client = new BookStackClient(config);
        const registry = makeRegistry(stateDir);
        const index = new CommentIndex(stateDir);
        const action = params.action;

        const resolveActivity = async () => {
          if (params.activityId || params.name) {
            return findActivity(registry, { id: params.activityId, name: params.name });
          }
          const row = ctx?.sessionKey ? await gw.getSession(ctx.sessionKey, ctx?.agentId).catch(() => null) : null;
          const group = row?.category ?? null;
          const binding = ctx?.sessionKey ? await registry.getBinding(ctx.sessionKey) : null;
          if (binding) return registry.findActivity({ id: binding.activityId });
          if (group) return registry.resolveActivityForGroup(group);
          return null;
        };

        if (action === "list" || action === "thread") {
          if (!params.pageId) return fail("missing_page", "pageId requis.");
          const page = await client.get(`/pages/${params.pageId}`);
          const rows = await fetchPageComments(client, params.pageId, {
            includeArchived: params.includeArchived !== false,
          });
          const filtered = action === "thread" && params.commentId
            ? rows.filter((c) => c.id === params.commentId || c.parentId === params.commentId)
            : rows;
          return text({
            ok: true,
            page: { id: page.id, name: page.name },
            count: filtered.length,
            comments: filtered.map((c) => ({
              id: c.id,
              localId: c.localId,
              parentId: c.parentId,
              depth: c.depth,
              author: c.author,
              createdAt: c.createdAt,
              updatedAt: c.updatedAt,
              archived: c.archived,
              contentRef: c.contentRef || null,
              text: c.text,
              url: commentUrl(config.baseUrl, page, c),
            })),
            note: "Commentaires natifs BookStack; le Markdown de la page n'est pas modifié.",
          });
        }

        if (action === "read") {
          if (!params.commentId) return fail("missing_comment", "commentId requis.");
          const c = await client.get(`/comments/${params.commentId}`);
          const page = await client.get(`/pages/${c.commentable_id}`).catch(() => null);
          return text({
            ok: true,
            comment: {
              id: c.id,
              localId: c.local_id,
              parentId: c.parent_id,
              pageId: c.commentable_id,
              author: c.created_by?.name ?? null,
              createdAt: c.created_at,
              updatedAt: c.updated_at,
              archived: Boolean(c.archived),
              contentRef: c.content_ref || null,
              text: htmlToText(c.html),
              html: c.html,
              url: page ? commentUrl(config.baseUrl, page, c) : null,
            },
            replies: (c.replies ?? []).map((r) => ({
              id: r.id,
              localId: r.local_id,
              parentId: r.parent_id,
              author: r.created_by?.name ?? null,
              createdAt: r.created_at,
              archived: Boolean(r.archived),
              text: htmlToText(r.html),
            })),
          });
        }

        if (action === "create" || action === "reply") {
          // Un commentaire au niveau activité utilise la page de présentation.
          if (!params.pageId && action === "create") {
            const activity = await resolveActivity();
            if (activity?.presentationPageId) {
              params = { ...params, pageId: activity.presentationPageId };
            }
          }
          if (!params.pageId) {
            return fail("missing_page", "pageId requis (aucune page de présentation pour cette activité).");
          }
          if (!params.text) return fail("missing_text", "text requis.");
          const body = { page_id: params.pageId, html: textToHtml(params.text) };
          if (action === "reply") {
            if (!params.replyTo) return fail("missing_reply_to", "replyTo (local_id du parent) requis.");
            body.reply_to = params.replyTo;
          }
          const created = await client.post("/comments", body);
          const page = await client.get(`/pages/${params.pageId}`).catch(() => null);
          await syncPageComments({
            client,
            index,
            pageId: params.pageId,
            bookId: page?.book_id ?? null,
            chapterId: page?.chapter_id ?? null,
            pageName: page?.name ?? null,
            pageSlug: page?.slug ?? null,
          }).catch(() => {});
          return text({
            ok: true,
            comment: {
              id: created.id,
              localId: created.local_id,
              parentId: created.parent_id,
              pageId: created.commentable_id,
              author: created.created_by?.name ?? null,
              archived: Boolean(created.archived),
            },
            url: page ? commentUrl(config.baseUrl, page, created) : null,
            note: "Commentaire natif créé; le Markdown de la page est inchangé.",
          });
        }

        if (action === "update") {
          if (!params.commentId) return fail("missing_comment", "commentId requis.");
          if (!params.text) return fail("missing_text", "text requis.");
          const before = await client.get(`/comments/${params.commentId}`);
          const updated = await client.put(`/comments/${params.commentId}`, { html: textToHtml(params.text) });
          const page = await client.get(`/pages/${updated.commentable_id}`).catch(() => null);
          await syncPageComments({
            client,
            index,
            pageId: updated.commentable_id,
            bookId: page?.book_id ?? null,
            chapterId: page?.chapter_id ?? null,
            pageName: page?.name ?? null,
            pageSlug: page?.slug ?? null,
          }).catch(() => {});
          return text({
            ok: true,
            comment: {
              id: updated.id,
              localId: updated.local_id,
              author: updated.created_by?.name ?? null,
              updatedAt: updated.updated_at,
              text: htmlToText(updated.html),
            },
            previousText: htmlToText(before.html),
            note: "Seul le commentaire est modifié; la page reste intacte.",
          });
        }

        if (action === "archive" || action === "unarchive") {
          if (!params.commentId) return fail("missing_comment", "commentId requis.");
          const current = await client.get(`/comments/${params.commentId}`);
          if (current.parent_id !== null) {
            return fail("not_a_thread_root", "Seul le commentaire racine d'un fil peut être archivé ou désarchivé.");
          }
          const updated = await client.put(`/comments/${params.commentId}`, { archived: action === "archive" });
          const page = await client.get(`/pages/${updated.commentable_id}`).catch(() => null);
          await syncPageComments({
            client,
            index,
            pageId: updated.commentable_id,
            bookId: page?.book_id ?? null,
            chapterId: page?.chapter_id ?? null,
            pageName: page?.name ?? null,
            pageSlug: page?.slug ?? null,
          }).catch(() => {});
          return text({
            ok: true,
            comment: { id: updated.id, localId: updated.local_id, archived: Boolean(updated.archived) },
            note: "Un fil archivé n'est ni une décision validée ni un problème résolu.",
          });
        }

        if (action === "delete") {
          if (!params.commentId) return fail("missing_comment", "commentId requis.");
          const current = await client.get(`/comments/${params.commentId}`);
          const replies = current.replies ?? [];
          if (params.confirm !== true) {
            return fail("confirmation_required", "Suppression non confirmée. Renvoyer avec confirm=true.", {
              target: {
                id: current.id,
                localId: current.local_id,
                author: current.created_by?.name ?? null,
                replies: replies.length,
              },
            });
          }
          await client.del(`/comments/${params.commentId}`);
          await syncPageComments({
            client,
            index,
            pageId: current.commentable_id,
            bookId: null,
            chapterId: null,
            pageName: null,
          }).catch(() => {});
          return text({
            ok: true,
            deleted: { id: current.id, localId: current.local_id, replies: replies.length },
            note: "Suppression définitive côté BookStack; aucune restauration n'est garantie par l'API.",
          });
        }

        if (action === "sync") {
          const activity = await resolveActivity();
          if (!activity) return fail("no_activity", "Aucune activité liée. Préciser activityId ou name.");
          const result = await syncBookComments({ client, index, bookId: activity.bookId });
          return text({
            ok: true,
            activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
            ...result,
            stats: await index.stats(),
          });
        }

        if (action === "search") {
          if (!params.query) return fail("missing_query", "query requis.");
          const activity = await resolveActivity();
          const limit = Math.min(Math.max(params.limit ?? 20, 1), 100);
          const offset = Math.max(params.offset ?? 0, 0);
          const result = await index.search({
            query: params.query,
            bookId: activity?.bookId ?? null,
            chapterId: params.chapterId ?? null,
            pageId: params.pageId ?? null,
            author: params.author ?? null,
            since: params.since ?? null,
            until: params.until ?? null,
            archived: params.archived ?? "all",
            offset,
            limit,
          });
          const stats = await index.stats();
          return text({
            ok: true,
            scope: activity ? { activity: activity.name, bookId: activity.bookId } : "index",
            total: result.total,
            offset: result.offset,
            limit: result.limit,
            hasMore: result.hasMore,
            nextOffset: result.hasMore ? result.offset + result.results.length : null,
            index: stats,
            results: result.results.map((r) => ({
              kind: r.parentId === null ? "comment" : "reply",
              id: r.id,
              localId: r.localId,
              parentId: r.parentId,
              pageId: r.pageId,
              pageName: r.pageName,
              author: r.author,
              createdAt: r.createdAt,
              archived: r.archived,
              snippet: r.snippet,
              url: `${config.baseUrl}/books/${activity?.bookSlug ?? activity?.bookId ?? r.bookId}/page/${r.pageSlug ?? r.pageId}#comment${r.localId}`,
            })),
            note: result.hasMore
              ? "Suite disponible: relancer avec offset=nextOffset. Aucun plafond global."
              : "Tous les résultats correspondants ont été parcourus.",
          });
        }

        return fail("unknown_action", `Action inconnue: ${action}`);
      } catch (error) {
        if (error instanceof ConfigError) return fail(error.code, error.message);
        if (error instanceof BookStackError) return fail(error.code, error.message, { status: error.status });
        if (error.code === "gateway_error") return fail("gateway_error", error.message);
        return fail("unexpected_error", `${error.name}: ${error.message}`);
      }
    },
  };
}
