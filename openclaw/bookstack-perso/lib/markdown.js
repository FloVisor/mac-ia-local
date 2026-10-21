/** Markdown helpers shared by the BookStack tools (pure, no I/O). */

export const EXTRACTION_START = "<!-- openclaw:extraction:start -->";
export const EXTRACTION_END = "<!-- openclaw:extraction:end -->";

/** Build the delimited extraction block written into a page. */
export function extractionBlock({ filename, source, sha256, conversion, verb = "Importé le" }) {
  return [
    EXTRACTION_START,
    "## Provenance",
    `- Fichier original : ${filename}`,
    `- Source : ${source}`,
    `- ${verb} : ${new Date().toISOString()}`,
    `- Empreinte SHA-256 (16) : ${sha256}`,
    `- Méthode : Docling${conversion.ocr_executed ? " + OCR" : ""} (${conversion.ocr_mode})`,
    `- Pages : ${conversion.pages ?? "?"}`,
    "",
    "## Texte extrait",
    "",
    conversion.markdown ?? "",
    EXTRACTION_END,
  ].join("\n");
}

/**
 * Append an extraction block to an existing page without ever removing content.
 * If the page already carries a block, it is replaced in place (idempotent).
 */
export function appendExtraction(existingMarkdown, block) {
  const existing = existingMarkdown ?? "";
  const startIdx = existing.indexOf(EXTRACTION_START);
  const endIdx = existing.indexOf(EXTRACTION_END);
  if (startIdx >= 0 && endIdx > startIdx) {
    return existing.slice(0, startIdx) + block + existing.slice(endIdx + EXTRACTION_END.length);
  }
  const base = existing.replace(/\s*$/, "");
  return base ? `${base}\n\n${block}` : block;
}

/**
 * Rebuild an extraction page while preserving human-authored sections.
 *
 * With markers: the block is replaced, everything outside it is kept.
 * Without markers but with a legacy "## Texte extrait" section: the old
 * extracted text is dropped so only human additions survive.
 * Otherwise the page is not an extraction page: content is kept and the block
 * is appended (never destructive).
 */
export function mergeExtraction(existingMarkdown, { filename, source, sha256, conversion }) {
  const existing = existingMarkdown ?? "";
  const block = extractionBlock({ filename, source, sha256, conversion, verb: "Ré-extrait le" });

  const startIdx = existing.indexOf(EXTRACTION_START);
  const endIdx = existing.indexOf(EXTRACTION_END);
  if (startIdx >= 0 && endIdx > startIdx) {
    const preserved = existing.slice(endIdx + EXTRACTION_END.length).trim();
    const firstLine = existing.split("\n")[0] ?? "";
    const title = firstLine.startsWith("# ") ? firstLine : "";
    const body = [title, "", block, preserved ? `\n${preserved}` : ""].filter(Boolean).join("\n");
    return { markdown: body, preserved: preserved ? ["contenu humain après le bloc d'extraction"] : [] };
  }

  const marker = existing.indexOf("## Texte extrait");
  if (marker < 0) {
    return { markdown: appendExtraction(existing, block), preserved: ["contenu existant conservé"] };
  }

  const previous = (conversion.markdown ?? "").trim();
  const lastIdx = previous ? existing.lastIndexOf(previous) : -1;
  let preserved = "";
  if (lastIdx >= 0) {
    preserved = existing.slice(lastIdx + previous.length).trim();
  } else {
    const after = existing.slice(marker);
    const split = after.indexOf("\n\n", after.indexOf("\n\n") + 2);
    preserved = split > 0 ? after.slice(split).trim() : "";
  }
  const firstLine = existing.split("\n")[0] ?? "";
  const title = firstLine.startsWith("# ") ? firstLine : "";
  const body = [title, "", block, preserved ? `\n${preserved}` : ""].filter(Boolean).join("\n");
  return { markdown: body, preserved: preserved ? ["contenu humain après le bloc d'extraction"] : [] };
}

/** List the headings of a Markdown document, for error reporting. */
export function headingsOf(markdown) {
  return (markdown ?? "")
    .split("\n")
    .map((line) => /^(#{1,6})\s+(.*)$/.exec(line))
    .filter(Boolean)
    .map((m) => `${m[1]} ${m[2].trim()}`);
}

/**
 * Replace the body of a section identified by its heading, up to the next
 * heading of the same or higher level. The heading line itself is kept.
 */
export function replaceSection(markdown, section, content) {
  const existing = markdown ?? "";
  const lines = existing.split("\n");
  const target = String(section ?? "").trim().replace(/^#+\s*/, "").toLowerCase();
  if (!target) return { ok: false, error: "missing_section", headings: headingsOf(existing) };

  let start = -1;
  let level = 0;
  for (let i = 0; i < lines.length; i += 1) {
    const m = /^(#{1,6})\s+(.*)$/.exec(lines[i]);
    if (!m) continue;
    if (m[2].trim().toLowerCase() === target) {
      start = i;
      level = m[1].length;
      break;
    }
  }
  if (start < 0) return { ok: false, error: "section_not_found", headings: headingsOf(existing) };

  let end = lines.length;
  for (let i = start + 1; i < lines.length; i += 1) {
    const m = /^(#{1,6})\s+/.exec(lines[i]);
    if (m && m[1].length <= level) {
      end = i;
      break;
    }
  }

  const head = lines.slice(0, start + 1).join("\n");
  const tail = lines.slice(end).join("\n");
  const body = String(content ?? "").replace(/\s*$/, "");
  const parts = [head, "", body];
  if (tail.trim()) parts.push("", tail);
  return { ok: true, markdown: parts.join("\n") };
}

/** Exact single-occurrence replacement; refuses ambiguous or missing text. */
export function applyEdit(markdown, find, replacement) {
  const existing = markdown ?? "";
  const needle = String(find ?? "");
  if (!needle) return { ok: false, error: "missing_find", occurrences: 0 };
  const occurrences = existing.split(needle).length - 1;
  if (occurrences === 0) return { ok: false, error: "text_not_found", occurrences };
  if (occurrences > 1) return { ok: false, error: "ambiguous_text", occurrences };
  return { ok: true, markdown: existing.replace(needle, String(replacement ?? "")), occurrences };
}
