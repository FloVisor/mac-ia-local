#!/usr/bin/env node
/**
 * Migration unique : rattache chaque dossier de conversations (session_groups)
 * à l'agent propriétaire de ses conversations.
 *
 * Idempotente : n'écrit que les lignes dont agent_id est NULL.
 * Ne supprime jamais de dossier, de conversation ni d'historique.
 *
 * Usage : node 20261020-session-groups-agent-owner.mjs [--dry-run]
 */
import { DatabaseSync } from "node:sqlite";
import { homedir } from "node:os";
import path from "node:path";

const dryRun = process.argv.includes("--dry-run");
const root = path.join(homedir(), ".openclaw");
const statePath = path.join(root, "state", "openclaw.sqlite");
const agents = ["main", "perso"];

const state = new DatabaseSync(statePath);
const columns = state.prepare("PRAGMA table_info(session_groups)").all().map((row) => row.name);
if (!columns.includes("agent_id")) {
	if (dryRun) console.log("[dry-run] ALTER TABLE session_groups ADD COLUMN agent_id TEXT");
	else state.exec("ALTER TABLE session_groups ADD COLUMN agent_id TEXT");
}

const groups = state.prepare(columns.includes("agent_id") ? "SELECT name, agent_id FROM session_groups ORDER BY position" : "SELECT name, NULL AS agent_id FROM session_groups ORDER BY position").all();

/** name -> Set(agentId) d'après les catégories des conversations. */
const owners = new Map();
for (const agentId of agents) {
	const db = new DatabaseSync(path.join(root, "agents", agentId, "agent", "openclaw-agent.sqlite"), { readOnly: true });
	for (const row of db.prepare("SELECT DISTINCT category FROM session_nodes WHERE category IS NOT NULL AND category <> ''").all()) {
		const set = owners.get(row.category) ?? new Set();
		set.add(agentId);
		owners.set(row.category, set);
	}
	db.close();
}

const summary = { main: 0, perso: 0, mixed: [], unassigned: [], already: 0 };
const update = dryRun ? null : state.prepare("UPDATE session_groups SET agent_id = ? WHERE name = ? AND agent_id IS NULL");

for (const group of groups) {
	if (group.agent_id) {
		summary.already += 1;
		continue;
	}
	const set = owners.get(group.name);
	if (!set || set.size === 0) {
		summary.unassigned.push(group.name);
		continue;
	}
	if (set.size > 1) {
		summary.mixed.push(group.name);
		continue;
	}
	const agentId = [...set][0];
	if (dryRun) console.log(`[dry-run] ${group.name} -> ${agentId}`);
	else update.run(agentId, group.name);
	summary[agentId] += 1;
}

state.close();
console.log(JSON.stringify({
	dryRun,
	pro: summary.main,
	perso: summary.perso,
	mixed: summary.mixed,
	unassigned: summary.unassigned,
	alreadyOwned: summary.already
}, null, 2));
