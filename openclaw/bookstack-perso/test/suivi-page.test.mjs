import test from "node:test";
import assert from "node:assert/strict";
import { ensureSuiviPage } from "../lib/activities.js";

function stubClient({ book, pages = {}, created = [] }) {
  return {
    async get(path) {
      if (path.startsWith("/books/")) return book;
      const id = Number(path.replace("/pages/", ""));
      if (pages[id]) return pages[id];
      const error = new Error("not found");
      error.code = "not_found";
      throw error;
    },
    async post(path, body) {
      assert.equal(path, "/pages");
      const page = { id: 999, name: body.name, book_id: body.book_id, markdown: body.markdown, revision_count: 1 };
      created.push(page);
      return page;
    },
  };
}

function stubRegistry(activity) {
  return {
    async upsertActivity(next) {
      Object.assign(activity, next);
      return activity;
    },
  };
}

test("ensureSuiviPage réutilise l'identifiant du registre", async () => {
  const activity = { id: "a", name: "A", bookId: 1, suiviPageId: 10 };
  const client = stubClient({ book: { id: 1, contents: [] }, pages: { 10: { id: 10, name: "Suivi", book_id: 1 } } });
  const result = await ensureSuiviPage({ client, registry: stubRegistry(activity), activity, baseUrl: "https://x" });
  assert.equal(result.created, false);
  assert.equal(result.source, "registry");
  assert.equal(result.page.id, 10);
});

test("ensureSuiviPage retrouve une page racine existante sans en créer", async () => {
  const activity = { id: "a", name: "A", bookId: 1 };
  const client = stubClient({
    book: { id: 1, contents: [{ type: "page", id: 20, name: "Suivi" }] },
    pages: { 20: { id: 20, name: "Suivi", book_id: 1 } },
  });
  const result = await ensureSuiviPage({ client, registry: stubRegistry(activity), activity, baseUrl: "https://x" });
  assert.equal(result.created, false);
  assert.equal(result.source, "book");
  assert.equal(activity.suiviPageId, 20);
});

test("ensureSuiviPage signale un doublon sans supprimer", async () => {
  const activity = { id: "a", name: "A", bookId: 1 };
  const client = stubClient({
    book: { id: 1, contents: [{ type: "page", id: 20, name: "Suivi" }, { type: "page", id: 21, name: "suivi" }] },
    pages: { 20: { id: 20, name: "Suivi", book_id: 1 } },
  });
  const result = await ensureSuiviPage({ client, registry: stubRegistry(activity), activity, baseUrl: "https://x" });
  assert.equal(result.page.id, 20);
  assert.match(result.warning, /2 pages/);
});

test("ensureSuiviPage crée la page à la racine quand elle manque", async () => {
  const activity = { id: "a", name: "A", bookId: 1 };
  const created = [];
  const client = stubClient({ book: { id: 1, contents: [] }, created });
  const result = await ensureSuiviPage({ client, registry: stubRegistry(activity), activity, baseUrl: "https://x" });
  assert.equal(result.created, true);
  assert.equal(created.length, 1);
  assert.equal(created[0].book_id, 1);
  assert.equal(activity.suiviPageId, 999);
});

test("ensureSuiviPage ne crée rien en lecture seule", async () => {
  const activity = { id: "a", name: "A", bookId: 1 };
  const created = [];
  const client = stubClient({ book: { id: 1, contents: [] }, created });
  const result = await ensureSuiviPage({ client, registry: stubRegistry(activity), activity, baseUrl: "https://x", create: false });
  assert.equal(result.page, null);
  assert.equal(created.length, 0);
});
