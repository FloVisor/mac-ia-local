import test from "node:test";
import assert from "node:assert/strict";
import { assertImportPath, resolveSourcePath } from "../lib/extract.js";

const GMAIL_ID = "ANGjdJ" + "x".repeat(340);

test("rejette un attachmentId Gmail comme filePath", () => {
  assert.throws(() => assertImportPath(GMAIL_ID), (e) => e.code === "invalid_file_path");
});

test("accepte un chemin local et une référence media://", () => {
  assert.equal(assertImportPath("/tmp/maaf/Devis.pdf"), "/tmp/maaf/Devis.pdf");
  assert.equal(assertImportPath("media://inbound/a.pdf"), "media://inbound/a.pdf");
});

test("resolveSourcePath mappe media://inbound vers le store média", () => {
  assert.equal(resolveSourcePath("/state", "media://inbound/a.pdf"), "/state/media/inbound/a.pdf");
  assert.throws(() => resolveSourcePath("/state", "media://inbound/../x"), (e) => e.code === "invalid_media_ref");
});
