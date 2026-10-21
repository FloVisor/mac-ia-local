import test from "node:test";
import assert from "node:assert/strict";
import {
  EXTRACTION_START,
  EXTRACTION_END,
  extractionBlock,
  appendExtraction,
  mergeExtraction,
  replaceSection,
  applyEdit,
  headingsOf,
} from "../lib/markdown.js";

const conversion = { markdown: "Texte OCR", ocr_executed: true, ocr_mode: "pdf_aware", pages: 14 };
const block = extractionBlock({ filename: "f.pdf", source: "test", sha256: "abc123", conversion });

test("extractionBlock est délimité par les marqueurs", () => {
  assert.ok(block.startsWith(EXTRACTION_START));
  assert.ok(block.endsWith(EXTRACTION_END));
  assert.match(block, /Texte OCR/);
});

test("appendExtraction conserve le contenu existant", () => {
  const existing = "# Présentation\n\nFiche de présentation de l'activité.\n";
  const out = appendExtraction(existing, block);
  assert.ok(out.startsWith("# Présentation"));
  assert.match(out, /Fiche de présentation de l'activité\./);
  assert.ok(out.includes(block));
});

test("appendExtraction remplace un bloc existant sans dupliquer", () => {
  const once = appendExtraction("# P\n\nCorps humain", block);
  const twice = appendExtraction(once, block);
  assert.equal(twice.split(EXTRACTION_START).length - 1, 1);
  assert.match(twice, /Corps humain/);
});

test("appendExtraction sur page vide ne produit pas de blanc initial", () => {
  assert.equal(appendExtraction("", block), block);
});

test("mergeExtraction préserve le contenu humain après le bloc", () => {
  const existing = `# Fiche\n\n${block}\n\nNote humaine ajoutée.`;
  const merged = mergeExtraction(existing, { filename: "f.pdf", source: "s", sha256: "abc123", conversion });
  assert.match(merged.markdown, /Note humaine ajoutée\./);
  assert.equal(merged.markdown.split(EXTRACTION_START).length - 1, 1);
  assert.equal(merged.preserved.length, 1);
});

test("mergeExtraction sur page sans marqueurs ajoute sans supprimer", () => {
  const existing = "# Présentation\n\nContenu rédigé à la main.";
  const merged = mergeExtraction(existing, { filename: "f.pdf", source: "s", sha256: "abc123", conversion });
  assert.match(merged.markdown, /Contenu rédigé à la main\./);
  assert.ok(merged.markdown.includes(EXTRACTION_START));
});

test("replaceSection remplace le corps et garde la suite", () => {
  const md = "# T\n\n## Budget\n\n100 €\n\n## Notes\n\nà faire";
  const r = replaceSection(md, "Budget", "200 €");
  assert.ok(r.ok);
  assert.match(r.markdown, /## Budget\n\n200 €/);
  assert.match(r.markdown, /## Notes\n\nà faire/);
  assert.doesNotMatch(r.markdown, /100 €/);
});

test("replaceSection accepte un titre avec dièses et casse différente", () => {
  const md = "## Budget\n\n100 €";
  const r = replaceSection(md, "## budget", "200 €");
  assert.ok(r.ok);
  assert.match(r.markdown, /200 €/);
});

test("replaceSection signale une section absente avec les titres disponibles", () => {
  const r = replaceSection("# T\n\n## Budget\n\n100 €", "Assurance", "x");
  assert.equal(r.ok, false);
  assert.equal(r.error, "section_not_found");
  assert.deepEqual(r.headings, ["# T", "## Budget"]);
});

test("replaceSection ne déborde pas sur une sous-section", () => {
  const md = "## A\n\n### A1\n\ntexte\n\n## B\n\nfin";
  const r = replaceSection(md, "A1", "remplacé");
  assert.ok(r.ok);
  assert.match(r.markdown, /### A1\n\nremplacé/);
  assert.match(r.markdown, /## B\n\nfin/);
});

test("applyEdit exige une occurrence unique", () => {
  assert.equal(applyEdit("a b a", "a", "x").error, "ambiguous_text");
  assert.equal(applyEdit("a b", "z", "x").error, "text_not_found");
  const ok = applyEdit("a b", "b", "c");
  assert.ok(ok.ok);
  assert.equal(ok.markdown, "a c");
});

test("headingsOf liste les titres", () => {
  assert.deepEqual(headingsOf("# T\n\ntexte\n\n## S"), ["# T", "## S"]);
});
