/**
 * Page « Suivi » d'une activité : rendu et parsing Markdown.
 *
 * Format stable, lisible dans l'éditeur BookStack :
 *   # Suivi — <activité>
 *   <!-- openclaw:suivi:meta {json} -->
 *   ## Situation actuelle
 *   ## Échéances et points en attente   (tableau)
 *   ## Chronologie                      (entrées ### + marqueur <!-- evt:<id> -->)
 *
 * Les marqueurs `<!-- evt:<id> -->` assurent l'idempotence : rejouer le même
 * événement ne crée pas de doublon. Aucune donnée n'est supprimée par le rendu.
 */

export const SUIVI_PAGE = "Suivi";
export const META_START = "<!-- openclaw:suivi:meta";
export const META_END = "-->";
export const EVENT_MARKER = /<!--\s*evt:([^\s>]+)\s*-->/;

export const SECTION_SITUATION = "Situation actuelle";
export const SECTION_DEADLINES = "Échéances et points en attente";
export const SECTION_TIMELINE = "Chronologie";

const DEADLINE_HEADER = ["Date / période", "Objet", "Personne", "État", "Référence"];
const DONE_STATE = /réalis|realis|confirm|fait|termin|annul|clos|sold/i;

/** Date du jour en Europe/Paris, au format AAAA-MM-JJ. */
export function todayParis(now = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Paris",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

export function emptySuivi({ activityName, today = todayParis() }) {
  return {
    meta: { version: 1, createdAt: today, updatedAt: today, lastEventAt: null },
    activityName,
    situation: "",
    deadlines: [],
    events: [],
  };
}

function escapeCell(value) {
  return String(value ?? "").replace(/\|/g, "\\|").replace(/\r?\n/g, " ").trim();
}

function unescapeCell(value) {
  return String(value ?? "").replace(/\\\|/g, "|").trim();
}

/** Normalise une date libre : garde la valeur telle quelle, sans invention. */
export function normalizeDate(value) {
  const raw = String(value ?? "").trim();
  if (!raw) return "Sans échéance connue";
  return raw;
}

function isOverdue(date, today) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(date ?? "").trim());
  if (!m) return false;
  return `${m[1]}-${m[2]}-${m[3]}` < today;
}

function sortDeadlines(deadlines) {
  const dated = (d) => /^\d{4}-\d{2}-\d{2}$/.test(String(d.date ?? "").trim());
  return [...deadlines].sort((a, b) => {
    const da = dated(a);
    const db = dated(b);
    if (da !== db) return da ? -1 : 1;
    if (!da) return 0;
    return String(b.date).localeCompare(String(a.date));
  });
}

function sortEvents(events) {
  return [...events].sort((a, b) => String(b.date ?? "").localeCompare(String(a.date ?? "")));
}

export function renderSuivi(state, { today = todayParis() } = {}) {
  const meta = {
    version: 1,
    createdAt: state.meta?.createdAt ?? today,
    updatedAt: today,
    lastEventAt: state.meta?.lastEventAt ?? null,
  };
  const lines = [];
  lines.push(`# Suivi — ${state.activityName ?? ""}`.trim());
  lines.push("");
  lines.push(`${META_START} ${JSON.stringify(meta)} ${META_END}`);
  lines.push("");
  lines.push(`## ${SECTION_SITUATION}`);
  lines.push("");
  const situation = String(state.situation ?? "").trim();
  lines.push(situation || "_Aucune synthèse enregistrée._");
  lines.push("");
  lines.push(`- **Page mise à jour le** : ${today}`);
  lines.push(`- **Dernier événement connu** : ${meta.lastEventAt ?? "non établi"}`);
  lines.push("");
  lines.push(`## ${SECTION_DEADLINES}`);
  lines.push("");
  lines.push(`| ${DEADLINE_HEADER.join(" | ")} |`);
  lines.push(`| ${DEADLINE_HEADER.map(() => "---").join(" | ")} |`);
  const deadlines = sortDeadlines(state.deadlines ?? []);
  if (deadlines.length === 0) {
    lines.push(`| Sans échéance connue | — | — | — | — |`);
  } else {
    for (const d of deadlines) {
      const date = normalizeDate(d.date);
      const overdue = isOverdue(date, today) && !DONE_STATE.test(String(d.state ?? ""));
      const stateText = overdue ? `⚠️ Dépassée — ${d.state ?? "réalisation non confirmée"}` : (d.state ?? "À confirmer");
      lines.push(
        `| ${escapeCell(date)} | ${escapeCell(d.label)} | ${escapeCell(d.person ?? "—")} | ${escapeCell(stateText)} | ${escapeCell(d.reference ?? "—")} |`,
      );
    }
  }
  lines.push("");
  lines.push(`## ${SECTION_TIMELINE}`);
  lines.push("");
  const events = sortEvents(state.events ?? []);
  if (events.length === 0) {
    lines.push("_Aucune étape enregistrée._");
  } else {
    for (const e of events) {
      if (e.raw) {
        lines.push(e.raw.trim());
        lines.push("");
        continue;
      }
      lines.push(`### ${normalizeDate(e.date)} — ${e.kind ?? "Étape"}`);
      if (e.people) lines.push(`- **Personnes** : ${e.people}`);
      lines.push(`- **Résumé** : ${String(e.summary ?? "").trim()}`);
      if (e.outcome) lines.push(`- **Suite** : ${String(e.outcome).trim()}`);
      if (e.reference) lines.push(`- **Source** : ${String(e.reference).trim()}`);
      if (e.correction) lines.push(`- **Correction** : ${String(e.correction).trim()}`);
      lines.push(`<!-- evt:${e.id} -->`);
      lines.push("");
    }
  }
  for (const section of state.extraSections ?? []) {
    lines.push(`## ${section.title}`);
    lines.push("");
    if (section.body.trim()) lines.push(section.body.trim());
    lines.push("");
  }
  return `${lines.join("\n").replace(/\n{3,}/g, "\n\n").trim()}\n`;
}

function splitSections(markdown) {
  const out = { preamble: [], sections: {} };
  let current = null;
  for (const line of String(markdown ?? "").split("\n")) {
    const m = /^##\s+(.*)$/.exec(line);
    if (m) {
      current = m[1].trim();
      out.sections[current] = [];
      continue;
    }
    if (current) out.sections[current].push(line);
    else out.preamble.push(line);
  }
  return out;
}

function parseMeta(preamble) {
  const text = preamble.join("\n");
  const start = text.indexOf(META_START);
  if (start < 0) return null;
  const end = text.indexOf(META_END, start);
  if (end < 0) return null;
  const json = text.slice(start + META_START.length, end).trim();
  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function parseDeadlines(lines) {
  const rows = lines.filter((l) => l.trim().startsWith("|"));
  if (rows.length < 2) return [];
  const cells = (row) =>
    row
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split(/(?<!\\)\|/)
      .map(unescapeCell);
  const header = cells(rows[0]);
  if (header[0] !== DEADLINE_HEADER[0]) return [];
  const out = [];
  for (const row of rows.slice(2)) {
    const c = cells(row);
    if (c.length < 5) continue;
    if (c[0] === "Sans échéance connue" && c[1] === "—") continue;
    out.push({ date: c[0], label: c[1], person: c[2], state: c[3], reference: c[4] });
  }
  return out;
}

function parseTimeline(lines) {
  const events = [];
  let current = null;
  const flush = () => {
    if (!current) return;
    const body = current.lines.join("\n");
    const marker = EVENT_MARKER.exec(body);
    const field = (name) => {
      const m = new RegExp(`^- \\*\\*${name}\\*\\*\\s*:\\s*(.*)$`, "m").exec(body);
      return m ? m[1].trim() : null;
    };
    if (!marker) {
      // Entrée humaine sans marqueur : conservée telle quelle, jamais réécrite.
      events.push({
        id: `legacy:${current.date}:${current.kind}:${events.length}`,
        date: current.date,
        kind: current.kind,
        raw: `### ${current.date} — ${current.kind}\n${body}`.trim(),
      });
      current = null;
      return;
    }
    events.push({
      id: marker[1],
      date: current.date,
      kind: current.kind,
      people: field("Personnes"),
      summary: field("Résumé") ?? "",
      outcome: field("Suite"),
      reference: field("Source"),
      correction: field("Correction"),
    });
    current = null;
  };
  for (const line of lines) {
    const m = /^###\s+(.*)$/.exec(line);
    if (m) {
      flush();
      const title = m[1].trim();
      const sep = title.indexOf(" — ");
      current = sep >= 0
        ? { date: title.slice(0, sep).trim(), kind: title.slice(sep + 3).trim(), lines: [] }
        : { date: title, kind: "Étape", lines: [] };
      continue;
    }
    if (current) current.lines.push(line);
  }
  flush();
  return events;
}

const KNOWN_SECTIONS = new Set([SECTION_SITUATION, SECTION_DEADLINES, SECTION_TIMELINE]);

export function parseSuivi(markdown) {
  const { preamble, sections } = splitSections(markdown);
  const meta = parseMeta(preamble) ?? {};
  const titleLine = preamble.find((l) => l.startsWith("# ")) ?? "";
  const activityName = titleLine.replace(/^#\s*Suivi\s*—\s*/, "").replace(/^#\s*/, "").trim();
  const situationLines = (sections[SECTION_SITUATION] ?? [])
    .filter((l) => !/^- \*\*(Page mise à jour le|Dernier événement connu)\*\*/.test(l.trim()))
    .join("\n")
    .trim();
  const extraSections = Object.entries(sections)
    .filter(([title]) => !KNOWN_SECTIONS.has(title))
    .map(([title, body]) => ({ title, body: body.join("\n").trim() }));
  return {
    meta,
    activityName,
    situation: situationLines === "_Aucune synthèse enregistrée._" ? "" : situationLines,
    deadlines: parseDeadlines(sections[SECTION_DEADLINES] ?? []),
    events: parseTimeline(sections[SECTION_TIMELINE] ?? []),
    extraSections,
  };
}

/** Ajoute ou met à jour un événement. Idempotent par `id`. */
export function upsertEvent(state, event) {
  const id = String(event.id ?? "").trim();
  if (!id) throw new Error("event.id requis (identifiant stable de la source).");
  const events = [...(state.events ?? [])];
  const index = events.findIndex((e) => e.id === id);
  const next = {
    id,
    date: normalizeDate(event.date),
    kind: event.kind ?? "Étape",
    people: event.people ?? null,
    summary: event.summary ?? "",
    outcome: event.outcome ?? null,
    reference: event.reference ?? null,
    correction: event.correction ?? null,
  };
  if (index >= 0) {
    const previous = events[index];
    const same = ["date", "kind", "people", "summary", "outcome", "reference"].every(
      (k) => String(previous[k] ?? "") === String(next[k] ?? ""),
    );
    if (same) return { state, duplicate: true, event: previous };
    events[index] = { ...next, correction: next.correction ?? `mise à jour du ${todayParis()}` };
    return { state: { ...state, events }, duplicate: false, updated: true, event: events[index] };
  }
  events.push(next);
  const lastEventAt = [state.meta?.lastEventAt, next.date]
    .filter((d) => d && /^\d{4}/.test(d))
    .sort()
    .pop() ?? state.meta?.lastEventAt ?? null;
  return {
    state: { ...state, events, meta: { ...(state.meta ?? {}), lastEventAt } },
    duplicate: false,
    created: true,
    event: next,
  };
}

/** Remplace la liste des échéances (le rendu trie et marque les dépassées). */
export function setDeadlines(state, deadlines) {
  return {
    ...state,
    deadlines: (deadlines ?? []).map((d) => ({
      date: normalizeDate(d.date),
      label: d.label ?? "",
      person: d.person ?? "—",
      state: d.state ?? "À confirmer",
      reference: d.reference ?? "—",
    })),
  };
}

export function setSituation(state, situation, { lastEventAt } = {}) {
  return {
    ...state,
    situation: String(situation ?? "").trim(),
    meta: { ...(state.meta ?? {}), ...(lastEventAt ? { lastEventAt } : {}) },
  };
}
