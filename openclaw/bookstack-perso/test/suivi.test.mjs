import test from "node:test";
import assert from "node:assert/strict";
import {
  emptySuivi,
  renderSuivi,
  parseSuivi,
  upsertEvent,
  setDeadlines,
  setSituation,
  todayParis,
} from "../lib/suivi.js";

const TODAY = "2026-10-20";

test("renderSuivi produit les trois sections et les dates distinctes", () => {
  const state = emptySuivi({ activityName: "Appartement VARS", today: TODAY });
  const md = renderSuivi(state, { today: TODAY });
  assert.match(md, /^# Suivi — Appartement VARS/);
  assert.match(md, /## Situation actuelle/);
  assert.match(md, /## Échéances et points en attente/);
  assert.match(md, /## Chronologie/);
  assert.match(md, /\*\*Page mise à jour le\*\* : 2026-10-20/);
  assert.match(md, /\*\*Dernier événement connu\*\* : non établi/);
});

test("parseSuivi relit ce que renderSuivi a écrit", () => {
  let state = emptySuivi({ activityName: "A", today: TODAY });
  state = setSituation(state, "Situation connue.", { lastEventAt: "2026-09-30" });
  state = setDeadlines(state, [
    { date: "2026-11-05", label: "Réponse banque", person: "Natacha", state: "En attente", reference: "mail 1" },
  ]);
  state = upsertEvent(state, {
    id: "gmail:abc",
    date: "2026-09-30",
    kind: "échange reçu",
    people: "Guillaume",
    summary: "Refus de se positionner sur l'enrobé.",
    outcome: "Relance envoyée.",
    reference: "mail du 30/09/2026",
  }).state;
  const md = renderSuivi(state, { today: TODAY });
  const parsed = parseSuivi(md);
  assert.equal(parsed.activityName, "A");
  assert.equal(parsed.situation, "Situation connue.");
  assert.equal(parsed.deadlines.length, 1);
  assert.equal(parsed.deadlines[0].label, "Réponse banque");
  assert.equal(parsed.events.length, 1);
  assert.equal(parsed.events[0].id, "gmail:abc");
  assert.equal(parsed.events[0].summary, "Refus de se positionner sur l'enrobé.");
  assert.equal(parsed.meta.lastEventAt, "2026-09-30");
});

test("upsertEvent est idempotent sur le même identifiant", () => {
  let state = emptySuivi({ activityName: "A", today: TODAY });
  const event = { id: "gmail:1", date: "2026-09-01", kind: "demande", summary: "Demande initiale." };
  const first = upsertEvent(state, event);
  assert.equal(first.created, true);
  const second = upsertEvent(first.state, event);
  assert.equal(second.duplicate, true);
  assert.equal(second.state.events.length, 1);
});

test("upsertEvent met à jour un événement modifié et laisse une trace", () => {
  let state = emptySuivi({ activityName: "A", today: TODAY });
  state = upsertEvent(state, { id: "gmail:1", date: "2026-09-01", kind: "demande", summary: "v1" }).state;
  const updated = upsertEvent(state, { id: "gmail:1", date: "2026-09-01", kind: "demande", summary: "v2" });
  assert.equal(updated.updated, true);
  assert.equal(updated.state.events.length, 1);
  assert.equal(updated.state.events[0].summary, "v2");
  assert.match(updated.state.events[0].correction, /mise à jour du/);
});

test("les échéances dépassées restent visibles et signalées", () => {
  let state = emptySuivi({ activityName: "A", today: TODAY });
  state = setDeadlines(state, [
    { date: "2026-01-01", label: "Appel de fonds", state: "En attente" },
    { date: "2026-12-01", label: "Échéance future", state: "À venir" },
  ]);
  const md = renderSuivi(state, { today: TODAY });
  assert.match(md, /⚠️ Dépassée/);
  const parsed = parseSuivi(md);
  assert.equal(parsed.deadlines.length, 2);
  // Tri : de la plus récente à la plus ancienne.
  assert.match(parsed.deadlines[0].date, /2026-12-01/);
  assert.match(parsed.deadlines[1].date, /2026-01-01/);
});

test("les échéances sans date passent en fin de tableau", () => {
  let state = emptySuivi({ activityName: "A", today: TODAY });
  state = setDeadlines(state, [
    { label: "Sans date", state: "En attente" },
    { date: "2026-05-01", label: "Datée", state: "À venir" },
  ]);
  const parsed = parseSuivi(renderSuivi(state, { today: TODAY }));
  assert.equal(parsed.deadlines[0].date, "2026-05-01");
  assert.equal(parsed.deadlines[1].date, "Sans échéance connue");
});

test("une échéance réalisée n'est pas marquée dépassée", () => {
  let state = emptySuivi({ activityName: "A", today: TODAY });
  state = setDeadlines(state, [{ date: "2026-01-01", label: "Payé", state: "Réalisée" }]);
  const md = renderSuivi(state, { today: TODAY });
  assert.doesNotMatch(md, /⚠️ Dépassée/);
});

test("une démarche sans date reste « Sans échéance connue »", () => {
  let state = emptySuivi({ activityName: "A", today: TODAY });
  state = setDeadlines(state, [{ label: "Attente retour notaire", state: "En attente" }]);
  const md = renderSuivi(state, { today: TODAY });
  assert.match(md, /Sans échéance connue/);
});

test("les entrées humaines sans marqueur sont conservées telles quelles", () => {
  const md = [
    "# Suivi — A",
    "",
    "## Chronologie",
    "",
    "### 2026-05-01 — note manuelle",
    "- **Résumé** : ajouté à la main.",
    "",
  ].join("\n");
  const parsed = parseSuivi(md);
  assert.equal(parsed.events.length, 1);
  assert.match(parsed.events[0].raw, /ajouté à la main/);
  const rerendered = renderSuivi(parsed, { today: TODAY });
  assert.match(rerendered, /ajouté à la main/);
});

test("les sections humaines inconnues sont préservées", () => {
  const md = [
    "# Suivi — A",
    "",
    "## Situation actuelle",
    "",
    "RAS",
    "",
    "## Notes personnelles",
    "",
    "À vérifier avec le notaire.",
    "",
  ].join("\n");
  const parsed = parseSuivi(md);
  assert.equal(parsed.extraSections.length, 1);
  const rerendered = renderSuivi(parsed, { today: TODAY });
  assert.match(rerendered, /## Notes personnelles/);
  assert.match(rerendered, /À vérifier avec le notaire/);
});

test("todayParis renvoie une date AAAA-MM-JJ", () => {
  assert.match(todayParis(new Date("2026-10-20T22:30:00Z")), /^\d{4}-\d{2}-\d{2}$/);
});
