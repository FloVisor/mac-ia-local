import { str, num, bool, obj } from "./schema.js";
import { resolveConfig } from "./config.js";
import { ConfigError, BookStackError, ExtractError } from "./errors.js";
import { BookStackClient } from "./http.js";
import { makeRegistry, createActivity, findActivity, resolveActivityForSession, bookUrl, pageUrl, chapterUrl, PRESENTATION_PAGE, DOCUMENTS_CHAPTER, NOTES_CHAPTER } from "./activities.js";
import * as gw from "./gateway.js";
import { convertDocument, storeOriginal, resolveSourcePath, assertImportPath } from "./extract.js";
import { CommentIndex } from "./comment-index.js";

const text = (value) => ({ content: [{ type: "text", text: typeof value === "string" ? value : JSON.stringify(value, null, 2) }], details: value });

function fail(code, message, extra = {}) {
  const payload = { ok: false, error: code, message, ...extra };
  return { content: [{ type: "text", text: JSON.stringify(payload, null, 2) }], details: payload };
}

async function withContext(api, ctx, fn) {
  try {
    const config = await resolveConfig(api);
    const client = new BookStackClient(config);
    const registry = makeRegistry(api.runtime?.stateDir ?? process.env.OPENCLAW_STATE_DIR ?? `${process.env.HOME}/.openclaw`);
    return await fn({ config, client, registry, ctx });
  } catch (error) {
    if (error instanceof ConfigError) return fail(error.code, error.message);
    if (error instanceof BookStackError) return fail(error.code, error.message, { status: error.status, details: error.details });
    if (error instanceof ExtractError) return fail(error.code, error.message, error.details ? { details: error.details } : {});
    if (error.code === "ambiguous_activity") return fail("ambiguous_activity", error.message, { candidates: error.candidates });
    if (error.code === "gateway_error") return fail("gateway_error", error.message);
    return fail("unexpected_error", `${error.name}: ${error.message}`);
  }
}

/** Find an extraction page in this activity whose provenance carries the same hash. */
async function findExistingImport({ client, activity, sha256 }) {
  const result = await client.get("/search/book/" + activity.bookId, { query: sha256, count: 10 });
  for (const row of result.data ?? []) {
    if (row.type !== "page") continue;
    const page = await client.get(`/pages/${row.id}`).catch(() => null);
    if (!page) continue;
    const tags = Array.isArray(page.tags) ? page.tags : [];
    if (!tags.some((t) => t.name === "openclaw-role" && t.value === "extraction")) continue;
    if ((page.markdown ?? "").includes(sha256)) return page;
  }
  return null;
}

/**
 * Rebuild an extraction page while preserving human-authored sections.
 *
 * The generated part is delimited by markers; anything a person added outside
 * them (notes, corrections) is carried over verbatim.
 */
function mergeExtraction(existingMarkdown, { filename, source, sha256, conversion }) {
  const START = "<!-- openclaw:extraction:start -->";
  const END = "<!-- openclaw:extraction:end -->";
  const generated = [
    START,
    "## Provenance",
    `- Fichier original : ${filename}`,
    `- Source : ${source}`,
    `- Ré-extrait le : ${new Date().toISOString()}`,
    `- Empreinte SHA-256 (16) : ${sha256}`,
    `- Méthode : Docling${conversion.ocr_executed ? " + OCR" : ""} (${conversion.ocr_mode})`,
    `- Pages : ${conversion.pages ?? "?"}`,
    "",
    "## Texte extrait",
    "",
    conversion.markdown ?? "",
    END,
  ].join("\n");

  const startIdx = existingMarkdown.indexOf(START);
  const endIdx = existingMarkdown.indexOf(END);
  let preserved = "";
  if (startIdx >= 0 && endIdx > startIdx) {
    preserved = existingMarkdown.slice(endIdx + END.length).trim();
  } else {
    // Page héritée sans marqueurs : retirer l'ancien texte extrait quand il est
    // reconnaissable, pour ne conserver que les ajouts humains.
    const previous = (conversion.markdown ?? "").trim();
    const lastIdx = previous ? existingMarkdown.lastIndexOf(previous) : -1;
    if (lastIdx >= 0) {
      preserved = existingMarkdown.slice(lastIdx + previous.length).trim();
    } else {
      const marker = existingMarkdown.indexOf("## Texte extrait");
      if (marker >= 0) {
        const after = existingMarkdown.slice(marker);
        const split = after.indexOf("\n\n", after.indexOf("\n\n") + 2);
        preserved = split > 0 ? after.slice(split).trim() : "";
      }
    }
  }
  const firstLine = existingMarkdown.split("\n")[0] ?? "";
  const title = firstLine.startsWith("# ") ? firstLine : "";
  const body = [title, "", generated, preserved ? `\n${preserved}` : ""].filter(Boolean).join("\n");
  return { markdown: body, preserved: preserved ? ["contenu humain après le bloc d'extraction"] : [] };
}

/**
 * Resolve the activity for the current conversation.
 * Binding first, then the session's native sidebar group (so a conversation
 * created from the UI inside an activity group resolves without the skill).
 */
async function currentActivity({ registry, ctx }) {
  const sessionKey = ctx?.sessionKey;
  if (!sessionKey) return { activity: null, reason: "no_session" };
  let group = null;
  try {
    const row = await gw.getSession(sessionKey, ctx?.agentId);
    group = row?.category ?? null;
  } catch {
    group = null;
  }
  const resolved = await resolveActivityForSession({ registry, sessionKey, group });
  return resolved.activity ? resolved : { activity: null, reason: "unbound", group };
}

export function buildTools(api) {
  const stateDir = api.runtime?.stateDir ?? process.env.OPENCLAW_STATE_DIR ?? `${process.env.HOME}/.openclaw`;

  return [
    {
      name: "bookstack_activity",
      label: "BookStack activité",
      description:
        "Gère les activités BookStack de Perso (un livre = un groupe de conversations). Actions: list, search, create, open, rename, archive, unarchive, delete, export, status. Une activité est identifiée par son nom, son identifiant interne ou son identifiant de livre.",
      parameters: obj({
        action: str("list | search | create | open | rename | archive | unarchive | delete | export | status"),
        name: str("Nom de l'activité (create, search, rename)."),
        newName: str("Nouveau nom (rename)."),
        activityId: str("Identifiant interne de l'activité."),
        bookId: num("Identifiant du livre BookStack."),
        description: str("Description du livre (create)."),
        query: str("Terme de recherche (search)."),
        format: str("Format d'export: markdown | html | plaintext | pdf | zip (export)."),
        confirm: bool("Confirmation explicite pour delete."),
      }, ["action"]),
      async run(params, ctx) {
        return withContext(api, ctx, async ({ config, client, registry }) => {
          const action = params.action;
          if (action === "list") {
            const activities = await registry.listActivities();
            return text({
              ok: true,
              count: activities.length,
              activities: activities.map((a) => ({
                id: a.id,
                name: a.name,
                bookId: a.bookId,
                group: a.group,
                status: a.status,
                archived: Boolean(a.archived),
                url: `${config.baseUrl}/books/${a.bookSlug ?? a.bookId}`,
                conversations: a.conversations?.length ?? 0,
              })),
            });
          }

          if (action === "search") {
            const q = params.query ?? params.name ?? "";
            const activities = await registry.listActivities();
            const needle = q.trim().toLowerCase();
            const local = activities.filter((a) => !needle || a.name.toLowerCase().includes(needle));
            const remote = needle ? await client.get("/search", { query: needle, count: 10 }) : { data: [] };
            return text({
              ok: true,
              activities: local.map((a) => ({ id: a.id, name: a.name, bookId: a.bookId, url: `${config.baseUrl}/books/${a.bookSlug ?? a.bookId}` })),
              bookstack: (remote.data ?? []).map((r) => ({ type: r.type, id: r.id, name: r.name, url: r.url })),
            });
          }

          if (action === "create") {
            if (!params.name) return fail("missing_name", "Le nom de l'activité est requis.");
            const result = await createActivity({
              client,
              registry,
              baseUrl: config.baseUrl,
              name: params.name,
              description: params.description,
              agentId: ctx?.agentId ?? "perso",
              sessionKey: ctx?.sessionKey,
            });
            const a = result.activity;
            return text({
              ok: true,
              activity: { id: a.id, name: a.name, bookId: a.bookId, group: a.group, status: a.status },
              url: `${config.baseUrl}/books/${a.bookSlug ?? a.bookId}`,
              conversations: a.conversations,
              steps: result.steps,
            });
          }

          if (action === "open") {
            const activity = await findActivity(registry, { id: params.activityId, name: params.name, bookId: params.bookId });
            if (!activity) return fail("activity_not_found", "Activité introuvable.");
            if (ctx?.sessionKey) await registry.bindSession(ctx.sessionKey, activity.id, { role: "explicit" });
            return text({
              ok: true,
              activity: { id: activity.id, name: activity.name, bookId: activity.bookId, group: activity.group },
              url: `${config.baseUrl}/books/${activity.bookSlug ?? activity.bookId}`,
              boundTo: ctx?.sessionKey ?? null,
            });
          }

          if (action === "rename") {
            const activity = await findActivity(registry, { id: params.activityId, name: params.name, bookId: params.bookId });
            if (!activity) return fail("activity_not_found", "Activité introuvable.");
            if (!params.newName) return fail("missing_new_name", "Le nouveau nom est requis.");
            const book = await client.put(`/books/${activity.bookId}`, { name: params.newName });
            let groupRenamed = false;
            if (activity.group) {
              try {
                await gw.renameGroup(activity.group, params.newName);
                activity.group = params.newName;
                groupRenamed = true;
              } catch (error) {
                activity.groupRenamePending = params.newName;
              }
            }
            activity.name = params.newName;
            activity.bookSlug = book.slug ?? activity.bookSlug;
            await registry.upsertActivity(activity);
            return text({ ok: true, activity: { id: activity.id, name: activity.name, bookId: activity.bookId, group: activity.group }, groupRenamed });
          }

          if (action === "archive" || action === "unarchive") {
            const activity = await findActivity(registry, { id: params.activityId, name: params.name, bookId: params.bookId });
            if (!activity) return fail("activity_not_found", "Activité introuvable.");
            const book = await client.get(`/books/${activity.bookId}`);
            const tags = (book.tags ?? []).filter((t) => t.name !== "openclaw-status");
            if (action === "archive") tags.push({ name: "openclaw-status", value: "archived" });
            await client.put(`/books/${activity.bookId}`, { tags });
            activity.archived = action === "archive";
            await registry.upsertActivity(activity);
            return text({
              ok: true,
              activity: { id: activity.id, name: activity.name, archived: activity.archived },
              note: "L'archivage utilise un tag BookStack (openclaw-status=archived) : ni suppression ni changement de droits.",
            });
          }

          if (action === "delete") {
            const activity = await findActivity(registry, { id: params.activityId, name: params.name, bookId: params.bookId });
            if (!activity) return fail("activity_not_found", "Activité introuvable.");
            if (params.confirm !== true) {
              return fail("confirmation_required", `Suppression du livre « ${activity.name} » (id ${activity.bookId}) et de son contenu. Renvoyer avec confirm=true.`, {
                activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
              });
            }
            await client.del(`/books/${activity.bookId}`);
            await registry.removeActivity(activity.id);
            return text({
              ok: true,
              deleted: { id: activity.id, name: activity.name, bookId: activity.bookId },
              note: "Le livre est envoyé à la corbeille BookStack. Les conversations OpenClaw sont conservées.",
            });
          }

          if (action === "export") {
            const activity = await findActivity(registry, { id: params.activityId, name: params.name, bookId: params.bookId });
            if (!activity) return fail("activity_not_found", "Activité introuvable.");
            const format = params.format ?? "markdown";
            const { buffer, contentType } = await client.download(`/books/${activity.bookId}/export/${format}`);
            const stored = await storeOriginal({
              stateDir,
              agent: ctx?.agentId ?? "perso",
              conversation: ctx?.sessionKey ?? "default",
              filename: `${activity.name}.${format === "plaintext" ? "txt" : format}`,
              buffer,
            });
            return text({ ok: true, activity: { id: activity.id, name: activity.name }, format, path: stored.path, bytes: stored.size, contentType });
          }

          if (action === "status") {
            const resolved = await currentActivity({ registry, ctx });
            if (!resolved.activity) return text({ ok: true, bound: false, reason: resolved.reason });
            const a = resolved.activity;
            return text({
              ok: true,
              bound: true,
              source: resolved.source,
              activity: { id: a.id, name: a.name, bookId: a.bookId, group: a.group, status: a.status },
              url: `${config.baseUrl}/books/${a.bookSlug ?? a.bookId}`,
            });
          }

          return fail("unknown_action", `Action inconnue: ${action}`);
        });
      },
    },

    {
      name: "bookstack_structure",
      label: "BookStack structure",
      description:
        "Gère la structure d'une activité: lister le contenu d'un livre, créer/renommer/déplacer/supprimer un chapitre ou une page. Sans activité explicite, utilise l'activité liée à la conversation.",
      parameters: obj({
        action: str("tree | create_chapter | create_page | update_page | move | delete"),
        activityId: str(),
        name: str("Nom de l'activité si activityId est absent ; sinon titre du chapitre ou de la page créé."),
        chapterId: num(),
        pageId: num(),
        title: str("Titre du chapitre ou de la page (prime sur name)."),
        markdown: str(),
        description: str(),
        targetChapterId: num("Chapitre de destination (move)."),
        targetBookId: num("Livre de destination (move), ou identification de l'activité."),
        confirm: bool(),
      }, ["action"]),
      async run(params, ctx) {
        return withContext(api, ctx, async ({ config, client, registry }) => {
          const action = params.action;
          let activity = null;
          if (params.activityId) activity = await findActivity(registry, { id: params.activityId });
          else if (params.targetBookId) activity = await findActivity(registry, { bookId: params.targetBookId });
          else if (params.name) activity = await findActivity(registry, { name: params.name });
          else {
            const resolved = await currentActivity({ registry, ctx });
            activity = resolved.activity;
          }
          // Avec une activité explicite, `name` désigne le titre de l'objet créé.
          const explicitActivity = Boolean(params.activityId || params.targetBookId);
          const title = params.title ?? (explicitActivity ? params.name : undefined);

          if (action === "tree") {
            if (!activity) return fail("no_activity", "Aucune activité liée à cette conversation. Préciser activityId ou name.");
            const book = await client.get(`/books/${activity.bookId}`);
            return text({
              ok: true,
              activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
              url: `${config.baseUrl}/books/${book.slug ?? book.id}`,
              content: (book.contents ?? book.content ?? []).map((item) => ({
                type: item.type,
                id: item.id,
                name: item.name,
                url: item.type === "chapter" ? chapterUrl(config.baseUrl, item) : pageUrl(config.baseUrl, item),
                children: (item.pages ?? []).map((p) => ({ type: "page", id: p.id, name: p.name, url: pageUrl(config.baseUrl, p) })),
              })),
            });
          }

          if (action === "create_chapter") {
            if (!activity) return fail("no_activity", "Aucune activité liée.");
            if (!title) return fail("missing_title", "Titre du chapitre requis : passer `title` (ou `name` avec activityId).");
            const chapter = await client.post("/chapters", {
              book_id: activity.bookId,
              name: title,
              ...(params.description ? { description: params.description } : {}),
            });
            return text({ ok: true, chapter: { id: chapter.id, name: chapter.name }, url: chapterUrl(config.baseUrl, chapter) });
          }

          if (action === "create_page") {
            if (!activity) return fail("no_activity", "Aucune activité liée.");
            if (!title) return fail("missing_title", "Titre de la page requis : passer `title` (ou `name` avec activityId).");
            const body = { name: title, markdown: params.markdown ?? "" };
            if (params.chapterId) body.chapter_id = params.chapterId;
            else body.book_id = activity.bookId;
            const page = await client.post("/pages", body);
            return text({ ok: true, page: { id: page.id, name: page.name }, url: pageUrl(config.baseUrl, page) });
          }

          if (action === "update_page") {
            if (!params.pageId) return fail("missing_page", "pageId requis.");
            const current = await client.get(`/pages/${params.pageId}`);
            const body = {};
            if (params.title) body.name = params.title;
            if (params.markdown !== undefined) body.markdown = params.markdown;
            if (Object.keys(body).length === 0) return fail("nothing_to_update", "Aucun champ à modifier.");
            body.changelog = `Mise à jour OpenClaw (révision ${current.revision_count ?? "?"})`;
            const page = await client.put(`/pages/${params.pageId}`, body);
            return text({ ok: true, page: { id: page.id, name: page.name, revision: page.revision_count }, url: pageUrl(config.baseUrl, page) });
          }

          if (action === "move") {
            if (!params.pageId && !params.chapterId) return fail("missing_target", "pageId ou chapterId requis.");
            if (params.pageId) {
              const body = {};
              if (params.targetChapterId) body.chapter_id = params.targetChapterId;
              else if (params.targetBookId) body.book_id = params.targetBookId;
              else return fail("missing_destination", "targetChapterId ou targetBookId requis.");
              const page = await client.put(`/pages/${params.pageId}`, body);
              return text({ ok: true, moved: { type: "page", id: page.id }, url: pageUrl(config.baseUrl, page) });
            }
            if (!params.targetBookId) return fail("missing_destination", "targetBookId requis pour un chapitre.");
            const chapter = await client.put(`/chapters/${params.chapterId}`, { book_id: params.targetBookId });
            return text({ ok: true, moved: { type: "chapter", id: chapter.id }, url: chapterUrl(config.baseUrl, chapter) });
          }

          if (action === "delete") {
            if (!params.pageId && !params.chapterId) return fail("missing_target", "pageId ou chapterId requis.");
            if (params.confirm !== true) {
              return fail("confirmation_required", "Suppression non confirmée. Renvoyer avec confirm=true.", {
                target: params.pageId ? { type: "page", id: params.pageId } : { type: "chapter", id: params.chapterId },
              });
            }
            if (params.pageId) await client.del(`/pages/${params.pageId}`);
            else await client.del(`/chapters/${params.chapterId}`);
            return text({ ok: true, deleted: params.pageId ? { type: "page", id: params.pageId } : { type: "chapter", id: params.chapterId } });
          }

          return fail("unknown_action", `Action inconnue: ${action}`);
        });
      },
    },

    {
      name: "bookstack_search",
      label: "BookStack recherche",
      description:
        "Recherche dans BookStack (périmètre: livre de l'activité liée, ou global). Retourne des aperçus courts avec identifiants et liens; ne charge pas le contenu complet.",
      parameters: obj({
        query: str("Terme de recherche."),
        scope: str("activity (défaut) | global"),
        activityId: str(),
        corpus: str("both (défaut) | pages | comments"),
        count: num("Nombre de résultats par corpus (max 50)."),
        page: num("Page de résultats pages (1-based)."),
        commentOffset: num("Offset des résultats commentaires."),
        archived: str("all (défaut) | only | exclude — état des fils de commentaires."),
      }, ["query"]),
      async run(params, ctx) {
        return withContext(api, ctx, async ({ config, client, registry }) => {
          const count = Math.min(Math.max(params.count ?? 10, 1), 50);
          const scope = params.scope ?? "activity";
          const corpus = params.corpus ?? "both";
          if (scope !== "activity" && scope !== "global") {
            return fail("invalid_scope", `scope invalide: ${scope}. Valeurs acceptées: activity | global.`);
          }
          if (!["both", "pages", "comments"].includes(corpus)) {
            return fail("invalid_corpus", `corpus invalide: ${corpus}. Valeurs acceptées: both | pages | comments.`);
          }
          let activity = null;
          if (params.activityId) activity = await findActivity(registry, { id: params.activityId });
          else if (scope === "activity") {
            const resolved = await currentActivity({ registry, ctx });
            activity = resolved.activity;
          }
          if (scope === "activity" && !activity) {
            return fail("no_activity", "Aucune activité liée à cette conversation. Utiliser scope=global ou préciser activityId.");
          }

          const out = {
            ok: true,
            scope: activity ? { activity: activity.name, bookId: activity.bookId } : "global",
            corpus,
          };

          if (corpus === "pages" || corpus === "both") {
            const path = activity ? `/search/book/${activity.bookId}` : "/search";
            const result = await client.get(path, { query: params.query, count, page: params.page ?? 1 });
            out.pages = {
              total: result.total ?? (result.data ?? []).length,
              page: params.page ?? 1,
              results: (result.data ?? []).map((r) => ({
                type: r.type,
                id: r.id,
                name: r.name,
                preview: String(r.preview_html?.content ?? r.preview_html ?? "")
                  .replace(/<[^>]+>/g, " ")
                  .replace(/&[a-z#0-9]+;/gi, " ")
                  .replace(/\s+/g, " ")
                  .trim()
                  .slice(0, 240),
                url: r.url ?? null,
              })),
            };
          }

          if (corpus === "comments" || corpus === "both") {
            const index = new CommentIndex(stateDir);
            const stats = await index.stats();
            const offset = Math.max(params.commentOffset ?? 0, 0);
            const found = await index.search({
              query: params.query,
              bookId: activity?.bookId ?? null,
              archived: params.archived ?? "all",
              offset,
              limit: count,
            });
            out.comments = {
              total: found.total,
              offset: found.offset,
              hasMore: found.hasMore,
              nextOffset: found.hasMore ? found.offset + found.results.length : null,
              index: stats,
              results: found.results.map((r) => ({
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
            };
            if (stats.comments === 0) {
              out.comments.note = "Index vide : lancer bookstack_comment action=sync pour indexer les commentaires de l'activité.";
            }
          }

          out.note = "Aperçus uniquement : lire la page ou le fil pour le contenu complet. La recherche native BookStack n'indexe pas les commentaires.";
          return text(out);
        });
      },
    },

    {
      name: "bookstack_page",
      label: "BookStack page",
      description:
        "Lit une page BookStack (contenu Markdown/HTML, métadonnées, révision) ou liste les pièces jointes d'une page. Utiliser après une recherche pour charger seulement les pages utiles.",
      parameters: obj({
        action: str("read | attachments"),
        pageId: num(),
        id: num("Alias de pageId (tolérance d'appel)."),
        attachmentId: num(),
        maxChars: num("Budget de caractères pour le contenu (défaut 20000)."),
      }, ["action"]),
      async run(params, ctx) {
        return withContext(api, ctx, async ({ config, client }) => {
          const pageId = params.pageId ?? params.id;
          if (params.action === "read") {
            if (!pageId) return fail("missing_page", "pageId requis.");
            const page = await client.get(`/pages/${pageId}`);
            const budget = Math.min(Math.max(params.maxChars ?? 20000, 500), 200000);
            const markdown = page.markdown ?? null;
            const html = page.html ?? "";
            const body = markdown ?? html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
            const truncated = body.length > budget;
            return text({
              ok: true,
              page: {
                id: page.id,
                name: page.name,
                bookId: page.book_id,
                chapterId: page.chapter_id,
                revision: page.revision_count,
                updatedAt: page.updated_at,
                editor: page.editor,
              },
              url: pageUrl(config.baseUrl, page),
              content: truncated ? body.slice(0, budget) : body,
              truncated,
              totalChars: body.length,
              note: truncated ? `Contenu tronqué à ${budget} caractères sur ${body.length}.` : undefined,
            });
          }
          if (params.action === "attachments") {
            if (!pageId) return fail("missing_page", "pageId requis.");
            const result = await client.get("/attachments", { count: 100 });
            const rows = (result.data ?? []).filter((a) => a.uploaded_to === pageId);
            return text({
              ok: true,
              pageId,
              attachments: rows.map((a) => ({ id: a.id, name: a.name, extension: a.extension, external: a.external, updatedAt: a.updated_at })),
            });
          }
          return fail("unknown_action", `Action inconnue: ${params.action}`);
        });
      },
    },

    {
      name: "bookstack_attachment",
      label: "BookStack pièce jointe",
      description:
        "Ajoute, télécharge ou supprime une pièce jointe BookStack. Pour un import: ajoute l'original à une page puis crée/complète la page d'extraction.",
      parameters: obj({
        action: str("upload | download | delete | list"),
        pageId: num(),
        attachmentId: num(),
        filePath: str("Chemin local du fichier à joindre, ou référence media://inbound/<id>."),
        name: str(),
        confirm: bool(),
      }, ["action"]),
      async run(params, ctx) {
        return withContext(api, ctx, async ({ config, client }) => {
          if (params.action === "list") {
            const result = await client.get("/attachments", { count: 500 });
            const rows = params.pageId ? (result.data ?? []).filter((a) => a.uploaded_to === params.pageId) : result.data ?? [];
            return text({ ok: true, attachments: rows.map((a) => ({ id: a.id, name: a.name, pageId: a.uploaded_to, extension: a.extension, external: a.external })) });
          }
          if (params.action === "upload") {
            if (!params.pageId || !params.filePath) return fail("missing_params", "pageId et filePath requis.");
            const { readFile } = await import("node:fs/promises");
            const { basename } = await import("node:path");
            const sourcePath = resolveSourcePath(stateDir, params.filePath);
            const buffer = await readFile(sourcePath);
            const filename = params.name ?? basename(sourcePath);
            const attachment = await client.upload("/attachments", {
              fields: { name: filename, uploaded_to: params.pageId },
              file: buffer,
              filename,
            });
            return text({ ok: true, attachment: { id: attachment.id, name: attachment.name, pageId: attachment.uploaded_to } });
          }
          if (params.action === "download") {
            if (!params.attachmentId) return fail("missing_attachment", "attachmentId requis.");
            const meta = await client.get(`/attachments/${params.attachmentId}`);
            if (meta.external) return text({ ok: true, external: true, link: meta.content ?? null });
            const buffer = Buffer.from(meta.content ?? "", "base64");
            const stored = await storeOriginal({
              stateDir,
              agent: ctx?.agentId ?? "perso",
              conversation: ctx?.sessionKey ?? "default",
              filename: meta.name ?? `attachment-${meta.id}`,
              buffer,
            });
            return text({ ok: true, attachment: { id: meta.id, name: meta.name }, path: stored.path, bytes: stored.size, sha256: stored.sha256 });
          }
          if (params.action === "delete") {
            if (!params.attachmentId) return fail("missing_attachment", "attachmentId requis.");
            if (params.confirm !== true) return fail("confirmation_required", "Suppression non confirmée. Renvoyer avec confirm=true.");
            await client.del(`/attachments/${params.attachmentId}`);
            return text({ ok: true, deleted: { attachmentId: params.attachmentId } });
          }
          return fail("unknown_action", `Action inconnue: ${params.action}`);
        });
      },
    },

    {
      name: "bookstack_import",
      label: "BookStack import",
      description:
        "Importe un document dans l'activité liée: conserve l'original en pièce jointe, extrait le texte (OCR si nécessaire), crée la page d'extraction avec provenance. Ne produit ni résumé ni analyse.",
      parameters: obj({
        filePath: str("Chemin local du document, ou référence de pièce jointe media://inbound/<id>."),
        activityId: str(),
        chapterId: num("Chapitre de destination (défaut: Documents)."),
        title: str("Titre de la page d'extraction."),
        ocr: str("auto | off | full_page | layout | pdf_aware"),
        tables: bool(),
        source: str("Provenance (email, URL, upload…)."),
        pageId: num("Page d'extraction existante (reextract)."),
        action: str("import (défaut) | reextract"),
        force: bool("Créer une nouvelle version même si le document est déjà importé."),
      }, ["filePath"]),
      async run(params, ctx) {
        return withContext(api, ctx, async ({ config, client, registry }) => {
          let activity = null;
          if (params.activityId) activity = await findActivity(registry, { id: params.activityId });
          else {
            const resolved = await currentActivity({ registry, ctx });
            activity = resolved.activity;
          }
          if (!activity) return fail("no_activity", "Aucune activité liée à cette conversation. Ouvrir une activité d'abord.");

          const { readFile, stat } = await import("node:fs/promises");
          const { basename } = await import("node:path");
          const rawPath = assertImportPath(params.filePath);
          const sourcePath = resolveSourcePath(stateDir, rawPath);

          if (params.action === "reextract") {
            if (!params.pageId) return fail("missing_page", "pageId requis pour relancer une extraction.");
            const existing = await client.get(`/pages/${params.pageId}`);
            const buffer = await readFile(sourcePath);
            const filename = basename(sourcePath);
            const original = await storeOriginal({
              stateDir,
              agent: ctx?.agentId ?? "perso",
              conversation: ctx?.sessionKey ?? "default",
              filename,
              buffer,
            });
            const conversion = await convertDocument(original.path, {
              agent: ctx?.agentId ?? "perso",
              conversation: ctx?.sessionKey ?? "default",
              ocr: params.ocr ?? "auto",
              tables: params.tables ?? false,
            });
            const merged = mergeExtraction(existing.markdown ?? "", {
              filename,
              source: params.source ?? "relance",
              sha256: original.sha256,
              conversion,
            });
            const page = await client.put(`/pages/${params.pageId}`, {
              markdown: merged.markdown,
              changelog: `Ré-extraction OpenClaw (révision ${existing.revision_count ?? "?"})`,
            });
            return text({
              ok: true,
              action: "reextract",
              page: { id: page.id, name: page.name, revision: page.revision_count },
              url: `${config.baseUrl}/books/${activity.bookSlug ?? activity.bookId}/page/${page.slug ?? page.id}`,
              conversion: {
                pages: conversion.pages,
                ocrExecuted: conversion.ocr_executed,
                ocrMode: conversion.ocr_mode,
                markdownChars: conversion.markdown_chars,
              },
              preservedHumanSections: merged.preserved ?? [],
            });
          }

          const info = await stat(sourcePath);
          const buffer = await readFile(sourcePath);
          const filename = basename(sourcePath);
          const title = params.title ?? filename.replace(/\.[^.]+$/, "");

          const original = await storeOriginal({
            stateDir,
            agent: ctx?.agentId ?? "perso",
            conversation: ctx?.sessionKey ?? "default",
            filename,
            buffer,
          });

          // Doublon : même empreinte déjà importée dans cette activité.
          if (params.force !== true) {
            const existing = await findExistingImport({ client, activity, sha256: original.sha256 });
            if (existing) {
              return text({
                ok: true,
                duplicate: true,
                activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
                page: { id: existing.id, name: existing.name, revision: existing.revision_count },
                url: `${config.baseUrl}/books/${activity.bookSlug ?? activity.bookId}/page/${existing.slug ?? existing.id}`,
                sha256: original.sha256,
                note: "Document déjà importé (même empreinte). Utiliser force=true pour créer une nouvelle version, ou action=reextract pour relancer la conversion.",
              });
            }
          }

          const conversion = await convertDocument(original.path, {
            agent: ctx?.agentId ?? "perso",
            conversation: ctx?.sessionKey ?? "default",
            ocr: params.ocr ?? "auto",
            tables: params.tables ?? false,
          });

          const chapterId = params.chapterId ?? activity.documentsChapterId ?? null;
          const provenance = [
            `- Fichier original : ${filename}`,
            `- Source : ${params.source ?? "fichier local"}`,
            `- Importé le : ${new Date().toISOString()}`,
            `- Empreinte SHA-256 (16) : ${original.sha256}`,
            `- Méthode : Docling${conversion.ocr_executed ? " + OCR" : ""} (${conversion.ocr_mode})`,
            `- Pages : ${conversion.pages ?? "?"}`,
            `- État : ${conversion.ok ? "converti" : "échec"}`,
          ].join("\n");

          const markdown = [
            `# ${title}`,
            "",
            "<!-- openclaw:extraction:start -->",
            "## Provenance",
            provenance,
            "",
            "## Texte extrait",
            "",
            conversion.markdown ?? "",
            "<!-- openclaw:extraction:end -->",
          ].join("\n");

          const pageBody = { name: title, markdown, tags: [{ name: "openclaw-role", value: "extraction" }] };
          if (chapterId) pageBody.chapter_id = chapterId;
          else pageBody.book_id = activity.bookId;
          const page = await client.post("/pages", pageBody);

          const attachment = await client.upload("/attachments", {
            fields: { name: filename, uploaded_to: page.id },
            file: buffer,
            filename,
          });

          return text({
            ok: true,
            activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
            page: { id: page.id, name: page.name },
            url: `${config.baseUrl}/books/${activity.bookSlug ?? activity.bookId}/page/${page.slug ?? page.id}`,
            attachment: { id: attachment.id, name: attachment.name },
            original: { path: original.path, sha256: original.sha256, bytes: info.size },
            conversion: {
              pages: conversion.pages,
              ocrExecuted: conversion.ocr_executed,
              ocrMode: conversion.ocr_mode,
              markdownChars: conversion.markdown_chars,
              outputDir: conversion.output_dir,
            },
          });
        });
      },
    },

    {
      name: "bookstack_conversation",
      label: "BookStack conversation",
      description:
        "Gère les conversations d'une activité: lister, créer une conversation indépendante dans le groupe de l'activité, déplacer une conversation existante, lier la conversation courante à une activité.",
      parameters: obj({
        action: str("list | create | move | bind | unbind"),
        activityId: str(),
        name: str("Nom de l'activité."),
        label: str("Libellé de la nouvelle conversation."),
        sessionKey: str("Conversation à déplacer (move)."),
      }, ["action"]),
      async run(params, ctx) {
        return withContext(api, ctx, async ({ config, registry }) => {
          const action = params.action;
          if (action === "bind") {
            const activity = await findActivity(registry, { id: params.activityId, name: params.name });
            if (!activity) return fail("activity_not_found", "Activité introuvable.");
            if (!ctx?.sessionKey) return fail("no_session", "Aucune conversation courante.");
            await registry.bindSession(ctx.sessionKey, activity.id, { role: "explicit" });
            return text({ ok: true, bound: { sessionKey: ctx.sessionKey, activityId: activity.id, name: activity.name } });
          }
          if (action === "unbind") {
            if (!ctx?.sessionKey) return fail("no_session", "Aucune conversation courante.");
            const previous = await registry.unbindSession(ctx.sessionKey);
            return text({ ok: true, unbound: ctx.sessionKey, previous });
          }

          let activity = null;
          if (params.activityId || params.name) activity = await findActivity(registry, { id: params.activityId, name: params.name });
          else {
            const resolved = await currentActivity({ registry, ctx });
            activity = resolved.activity;
          }
          if (!activity) return fail("no_activity", "Aucune activité liée.");

          if (action === "list") {
            const rows = await gw.listSessions({ agentId: activity.agentId ?? ctx?.agentId, group: activity.group });
            return text({
              ok: true,
              activity: { id: activity.id, name: activity.name, group: activity.group },
              conversations: rows.map((r) => ({ key: r.key, sessionId: r.sessionId, label: r.label, archived: r.archived })),
            });
          }

          if (action === "create") {
            if (!params.label) return fail("missing_label", "Le libellé de la conversation est requis.");
            const created = await gw.createSession({
              agentId: activity.agentId ?? ctx?.agentId ?? "perso",
              label: params.label,
              group: activity.group,
              uniqueSuffix: activity.name,
            });
            activity.conversations = [...(activity.conversations ?? []), { key: created.key, sessionId: created.sessionId, label: params.label }];
            await registry.upsertActivity(activity);
            return text({
              ok: true,
              conversation: { key: created.key, sessionId: created.sessionId, label: params.label, group: activity.group },
              note: "Conversation indépendante créée (historique vide).",
            });
          }

          if (action === "move") {
            if (!params.sessionKey) return fail("missing_session", "sessionKey requis.");
            await gw.patchSession(params.sessionKey, { category: activity.group });
            await registry.bindSession(params.sessionKey, activity.id, { role: "moved" });
            return text({
              ok: true,
              moved: { sessionKey: params.sessionKey, group: activity.group, activityId: activity.id },
              note: "Historique conservé; le déplacement ne réinitialise pas le contexte.",
            });
          }

          return fail("unknown_action", `Action inconnue: ${action}`);
        });
      },
    },
  ];
}
