import { randomUUID } from "node:crypto";
import { BookStackClient } from "./http.js";
import { ActivityRegistry } from "./registry.js";
import * as gw from "./gateway.js";
import { SUIVI_PAGE } from "./suivi.js";

export const PRESENTATION_PAGE = "Présentation";
export const DOCUMENTS_CHAPTER = "Documents";
export const NOTES_CHAPTER = "Notes";

export function bookUrl(baseUrl, book) {
  return `${baseUrl}/books/${book.slug || book.id}`;
}

export function pageUrl(baseUrl, page) {
  return `${baseUrl}/books/${page.book_slug || page.book_id}/page/${page.slug || page.id}`;
}

export function chapterUrl(baseUrl, chapter) {
  return `${baseUrl}/books/${chapter.book_slug || chapter.book_id}/chapter/${chapter.slug || chapter.id}`;
}

export function makeRegistry(stateDir) {
  return new ActivityRegistry(stateDir);
}

/** Find an activity by explicit id, exact name, or BookStack book id. */
export async function findActivity(registry, { id, name, bookId }) {
  if (id) return registry.findActivity({ id });
  if (bookId) return registry.findActivity({ bookId });
  if (name) {
    const matches = await registry.findActivitiesByName(name);
    if (matches.length === 1) return matches[0];
    if (matches.length > 1) {
      const error = new Error(`Plusieurs activités portent le nom « ${name} ». Préciser l'identifiant.`);
      error.code = "ambiguous_activity";
      error.candidates = matches.map((a) => ({ id: a.id, name: a.name, bookId: a.bookId }));
      throw error;
    }
  }
  return null;
}

/**
 * Create (or resume) an activity: BookStack book + initial structure +
 * conversation group + first conversation. Idempotent by name.
 */
export async function createActivity({ client, registry, baseUrl, name, description, agentId, sessionKey, createConversation = true }) {
  const existing = await registry.findActivitiesByName(name);
  if (existing.length > 1) {
    const error = new Error(`Plusieurs activités portent déjà le nom « ${name} ».`);
    error.code = "ambiguous_activity";
    error.candidates = existing.map((a) => ({ id: a.id, name: a.name, bookId: a.bookId }));
    throw error;
  }

  let activity = existing[0] ?? null;
  const steps = [];

  if (!activity) {
    const book = await client.post("/books", {
      name,
      ...(description ? { description } : {}),
      tags: [{ name: "openclaw-activity", value: "perso" }],
    });
    activity = {
      id: randomUUID(),
      name,
      bookId: book.id,
      bookSlug: book.slug,
      baseUrl,
      agentId,
      group: null,
      conversations: [],
      status: "book_created",
      createdAt: new Date().toISOString(),
    };
    await registry.upsertActivity(activity);
    steps.push({ step: "book", ok: true, bookId: book.id });
  } else {
    steps.push({ step: "book", ok: true, bookId: activity.bookId, reused: true });
  }

  // Initial structure: presentation page + Documents/Notes chapters.
  if (!activity.presentationPageId) {
    const page = await client.post("/pages", {
      book_id: activity.bookId,
      name: PRESENTATION_PAGE,
      markdown: `# ${name}\n\n${description ?? "Fiche de présentation de l'activité."}\n`,
      tags: [{ name: "openclaw-role", value: "presentation" }],
    });
    activity.presentationPageId = page.id;
    await registry.upsertActivity(activity);
    steps.push({ step: "presentation", ok: true, pageId: page.id });
  }

  for (const chapterName of [DOCUMENTS_CHAPTER, NOTES_CHAPTER]) {
    const key = chapterName === DOCUMENTS_CHAPTER ? "documentsChapterId" : "notesChapterId";
    if (activity[key]) continue;
    // `documentsChapterId: null` explicite = chapitre Documents supprimé volontairement.
    if (chapterName === DOCUMENTS_CHAPTER && activity.documentsChapterId === null) continue;
    const chapter = await client.post("/chapters", {
      book_id: activity.bookId,
      name: chapterName,
      description: chapterName === DOCUMENTS_CHAPTER
        ? "Documents originaux et extractions."
        : "Notes et compléments rédigés.",
      tags: [{ name: "openclaw-role", value: chapterName.toLowerCase() }],
    });
    activity[key] = chapter.id;
    await registry.upsertActivity(activity);
    steps.push({ step: `chapter:${chapterName}`, ok: true, chapterId: chapter.id });
  }

  // Page Suivi à la racine (idempotente, jamais de doublon).
  if (!activity.suiviPageId) {
    const suivi = await ensureSuiviPage({ client, registry, activity, baseUrl });
    activity = suivi.activity;
    steps.push({ step: "suivi", ok: true, pageId: suivi.page.id, created: suivi.created });
  }

  // Conversation group (native sidebar group).
  if (!activity.group) {
    const groupName = await uniqueGroupName(name);
    await gw.ensureGroup(groupName);
    activity.group = groupName;
    activity.status = "group_created";
    await registry.upsertActivity(activity);
    steps.push({ step: "group", ok: true, group: groupName });
  }

  // First conversation.
  if (createConversation && activity.conversations.length === 0) {
    const created = await gw.createSession({
      agentId,
      label: "Général",
      group: activity.group,
      uniqueSuffix: activity.name,
    });
    activity.conversations.push({ key: created.key, sessionId: created.sessionId, label: "Général" });
    activity.status = "ready";
    await registry.upsertActivity(activity);
    if (sessionKey) await registry.bindSession(sessionKey, activity.id, { role: "origin" });
    steps.push({ step: "conversation", ok: true, sessionKey: created.key, sessionId: created.sessionId });
  }

  if (activity.status !== "ready") {
    activity.status = "ready";
    await registry.upsertActivity(activity);
  }

  return { activity, steps };
}

async function uniqueGroupName(name) {
  const groups = await gw.listGroups();
  if (!groups.includes(name)) return name;
  const owned = await gw.listSessions({ group: name });
  if (owned.length === 0) return name;
  for (let i = 2; i < 100; i += 1) {
    const candidate = `${name} (${i})`;
    if (!groups.includes(candidate)) return candidate;
  }
  throw new Error(`Impossible de trouver un nom de groupe libre pour « ${name} ».`);
}

/** Resolve the activity for the current conversation: binding first, then sidebar group. */
export async function resolveActivityForSession({ registry, sessionKey, group }) {
  const direct = await registry.resolveActivityForSession(sessionKey);
  if (direct.activity) return direct;
  if (group) {
    const byGroup = await registry.resolveActivityForGroup(group);
    if (byGroup) {
      await registry.bindSession(sessionKey, byGroup.id, { role: "group-member" });
      return { activity: byGroup, binding: { activityId: byGroup.id }, source: "group" };
    }
  }
  return { activity: null, binding: null, source: "none" };
}

export function clientFor(config) {
  return new BookStackClient(config);
}

/**
 * Garantit la présence de la page « Suivi » à la racine du livre.
 *
 * Idempotent : réutilise l'identifiant enregistré, sinon retrouve une page
 * racine nommée « Suivi », sinon la crée. Ne supprime jamais de doublon :
 * en cas d'ambiguïté, la première page racine est réutilisée et l'anomalie est
 * signalée dans le retour.
 */
export async function ensureSuiviPage({ client, registry, activity, baseUrl, create = true }) {
  const bookId = activity.bookId;

  if (activity.suiviPageId) {
    const page = await client.get(`/pages/${activity.suiviPageId}`).catch(() => null);
    if (page && page.book_id === bookId) {
      return { page, created: false, source: "registry", activity };
    }
  }

  const book = await client.get(`/books/${bookId}`);
  const rootPages = (book.contents ?? []).filter((item) => item.type === "page");
  const matches = rootPages.filter((p) => String(p.name ?? "").trim().toLowerCase() === SUIVI_PAGE.toLowerCase());

  if (matches.length > 0) {
    const page = await client.get(`/pages/${matches[0].id}`);
    activity.suiviPageId = page.id;
    await registry.upsertActivity(activity);
    return {
      page,
      created: false,
      source: "book",
      activity,
      ...(matches.length > 1
        ? { warning: `${matches.length} pages « Suivi » à la racine ; la page ${page.id} est utilisée, aucune suppression automatique.` }
        : {}),
    };
  }

  if (!create) return { page: null, created: false, source: "absent", activity };

  const page = await client.post("/pages", {
    book_id: bookId,
    name: SUIVI_PAGE,
    markdown: `# Suivi — ${activity.name}\n`,
    tags: [{ name: "openclaw-role", value: "suivi" }],
  });
  activity.suiviPageId = page.id;
  await registry.upsertActivity(activity);
  return { page, created: true, source: "created", activity };
}
