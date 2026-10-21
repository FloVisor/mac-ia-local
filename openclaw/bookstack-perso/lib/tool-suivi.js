import { str, num, bool, obj } from "./schema.js";
import { resolveConfig } from "./config.js";
import { ConfigError, BookStackError } from "./errors.js";
import { BookStackClient } from "./http.js";
import { makeRegistry, findActivity, resolveActivityForSession, ensureSuiviPage, pageUrl } from "./activities.js";
import * as gw from "./gateway.js";
import {
  SUIVI_PAGE,
  parseSuivi,
  renderSuivi,
  upsertEvent,
  setDeadlines,
  setSituation,
  todayParis,
} from "./suivi.js";

const text = (value) => ({
  content: [{ type: "text", text: typeof value === "string" ? value : JSON.stringify(value, null, 2) }],
  details: value,
});

function fail(code, message, extra = {}) {
  const payload = { ok: false, error: code, message, ...extra };
  return { content: [{ type: "text", text: JSON.stringify(payload, null, 2) }], details: payload };
}

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

function parseJsonArg(value, name) {
  if (value === undefined || value === null) return undefined;
  if (typeof value === "object") return value;
  try {
    return JSON.parse(String(value));
  } catch {
    const error = new Error(`${name} doit être un tableau JSON valide.`);
    error.code = "invalid_json";
    throw error;
  }
}

export function buildSuiviTool(api) {
  return {
    name: "bookstack_suivi",
    label: "BookStack suivi d'activité",
    description:
      "Lit et met à jour la page « Suivi » d'une activité (racine du livre) : situation actuelle, échéances, chronologie. Actions: read (défaut), ensure, add_event, set_deadlines, set_situation, replace. Idempotent : un événement déjà présent (même id) n'est pas dupliqué. Ne consulte jamais la messagerie.",
    parameters: obj({
      action: str("read (défaut) | ensure | add_event | set_deadlines | set_situation | replace"),
      activityId: str("Identifiant interne de l'activité (défaut : activité de la conversation)."),
      name: str("Nom de l'activité si activityId est absent."),
      bookId: num("Identifiant du livre BookStack."),
      event: obj({
        id: str("Identifiant stable de la source (ex. gmail:<messageId>). Obligatoire."),
        date: str("Date réelle de l'événement (AAAA-MM-JJ, ou texte tel que connu)."),
        kind: str("Nature : demande, échange reçu, réponse envoyée, décision, document reçu, opération confirmée…"),
        people: str("Personnes concernées."),
        summary: str("Résumé factuel de l'étape."),
        outcome: str("Résultat ou conséquence établie."),
        reference: str("Référence courte vers la source (expéditeur, date, objet, identifiant)."),
        correction: str("Correction significative explicite."),
      }),      deadlines: {
        type: "array",
        description: "Échéances : [{date, label, person, state, reference}].",
        items: obj({
          date: str("Date ou période (AAAA-MM-JJ si connue, sinon texte)."),
          label: str("Objet de l'échéance."),
          person: str("Personne concernée."),
          state: str("État (à venir, en attente, réalisée, dépassée…)."),
          reference: str("Référence permettant de retrouver l'origine."),
        }),
      },
      situation: str("Synthèse « Situation actuelle » (Markdown court)."),
      lastEventAt: str("Date du dernier événement connu (AAAA-MM-JJ)."),
      markdown: str("Contenu complet (action=replace uniquement)."),
      expectedRevision: num("Révision lue avant modification : si la page a changé entre-temps, l'écriture est refusée (conflit)."),
      confirm: bool("Confirme une réécriture totale (action=replace)."),
    }, ["action"]),
    async run(params, ctx) {
      try {
        const config = await resolveConfig(api);
        const client = new BookStackClient(config);
        const stateDir = api.runtime?.stateDir ?? process.env.OPENCLAW_STATE_DIR ?? `${process.env.HOME}/.openclaw`;
        const registry = makeRegistry(stateDir);
        const action = params.action ?? "read";

        let activity = null;
        if (params.activityId) activity = await findActivity(registry, { id: params.activityId });
        else if (params.bookId) activity = await findActivity(registry, { bookId: params.bookId });
        else if (params.name) activity = await findActivity(registry, { name: params.name });
        else activity = (await currentActivity({ registry, ctx })).activity;
        if (!activity) {
          return fail("no_activity", "Aucune activité liée à cette conversation. Préciser activityId, name ou bookId.");
        }

        const ensured = await ensureSuiviPage({
          client,
          registry,
          activity,
          baseUrl: config.baseUrl,
          create: action !== "read",
        });
        activity = ensured.activity;
        if (!ensured.page) {
          return text({
            ok: true,
            activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
            suivi: { exists: false, pageId: null },
            note: "Aucune page Suivi. Utiliser action=ensure pour la créer.",
          });
        }

        const page = ensured.page;
        const url = pageUrl(config.baseUrl, page);
        const today = todayParis();

        if (action === "read") {
          const state = parseSuivi(page.markdown ?? "");
          return text({
            ok: true,
            activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
            suivi: {
              pageId: page.id,
              name: page.name,
              url,
              revision: page.revision_count,
              updatedAt: page.updated_at,
              pageUpdatedAt: state.meta?.updatedAt ?? null,
              lastEventAt: state.meta?.lastEventAt ?? null,
              situation: state.situation,
              deadlines: state.deadlines,
              events: state.events.map((e) => ({
                id: e.id,
                date: e.date,
                kind: e.kind,
                people: e.people ?? null,
                summary: e.summary ?? null,
                outcome: e.outcome ?? null,
                reference: e.reference ?? null,
                correction: e.correction ?? null,
              })),
            },
            note: "Répondre à partir de ce contenu. Aucun accès à la messagerie n'est nécessaire pour un bilan.",
          });
        }

        if (action === "ensure") {
          return text({
            ok: true,
            activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
            suivi: { pageId: page.id, name: page.name, url, created: ensured.created, source: ensured.source },
            ...(ensured.warning ? { warning: ensured.warning } : {}),
          });
        }

        if (action === "replace") {
          if (params.confirm !== true) {
            return fail("confirmation_required", "Réécriture totale de la page Suivi : renvoyer avec confirm=true.", {
              pageId: page.id,
              preview: String(params.markdown ?? "").slice(0, 200),
            });
          }
          if (params.markdown === undefined) return fail("missing_markdown", "markdown requis pour action=replace.");
          const updated = await client.put(`/pages/${page.id}`, {
            markdown: params.markdown,
            changelog: `Suivi réécrit (révision ${page.revision_count ?? "?"})`,
          });
          return text({ ok: true, action: "replace", suivi: { pageId: updated.id, url, revision: updated.revision_count } });
        }

        let state = parseSuivi(page.markdown ?? "");
        if (!state.activityName) state.activityName = activity.name;
        const changes = [];
        const baseRevision = params.expectedRevision ?? page.revision_count ?? null;

        if (action === "add_event") {
          const event = parseJsonArg(params.event, "event");
          if (!event || !event.id) return fail("missing_event_id", "event.id est requis (identifiant stable de la source).");
          const result = upsertEvent(state, event);
          state = result.state;
          if (result.duplicate) {
            return text({
              ok: true,
              action: "add_event",
              duplicate: true,
              suivi: { pageId: page.id, url, revision: page.revision_count },
              event: result.event,
              note: "Événement déjà présent : aucune écriture.",
            });
          }
          changes.push(result.updated ? "événement mis à jour" : "événement ajouté");
        } else if (action === "set_deadlines") {
          const deadlines = parseJsonArg(params.deadlines, "deadlines");
          if (!Array.isArray(deadlines)) return fail("missing_deadlines", "deadlines doit être un tableau.");
          state = setDeadlines(state, deadlines);
          changes.push("échéances remplacées");
        } else if (action === "set_situation") {
          if (params.situation === undefined) return fail("missing_situation", "situation requise.");
          state = setSituation(state, params.situation, { lastEventAt: params.lastEventAt });
          changes.push("situation mise à jour");
        } else {
          return fail("unknown_action", `Action inconnue: ${action}`);
        }

        const markdown = renderSuivi(state, { today });
        if (markdown.trim() === String(page.markdown ?? "").trim()) {
          return text({
            ok: true,
            action,
            duplicate: true,
            suivi: { pageId: page.id, url, revision: page.revision_count },
            note: "Aucun changement : page inchangée.",
          });
        }
        const fresh = await client.get(`/pages/${page.id}`);
        if (baseRevision !== null && fresh.revision_count !== baseRevision) {
          return fail(
            "revision_conflict",
            "La page Suivi a été modifiée entre la lecture et l'écriture. Relire puis réappliquer.",
            { pageId: page.id, expectedRevision: baseRevision, currentRevision: fresh.revision_count },
          );
        }
        const updated = await client.put(`/pages/${page.id}`, {
          markdown,
          changelog: `Suivi OpenClaw : ${changes.join(", ")} (révision ${page.revision_count ?? "?"})`,
        });
        return text({
          ok: true,
          action,
          activity: { id: activity.id, name: activity.name, bookId: activity.bookId },
          suivi: {
            pageId: updated.id,
            name: updated.name,
            url,
            revision: updated.revision_count,
            pageUpdatedAt: today,
            lastEventAt: state.meta?.lastEventAt ?? null,
            events: state.events.length,
            deadlines: state.deadlines.length,
          },
          changes,
        });
      } catch (error) {
        if (error instanceof ConfigError) return fail(error.code, error.message);
        if (error instanceof BookStackError) return fail(error.code, error.message, { status: error.status });
        if (error.code === "ambiguous_activity") return fail("ambiguous_activity", error.message, { candidates: error.candidates });
        if (error.code === "invalid_json") return fail("invalid_json", error.message);
        return fail("unexpected_error", `${error.name}: ${error.message}`);
      }
    },
  };
}

export { SUIVI_PAGE };
