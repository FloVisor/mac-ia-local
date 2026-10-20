# Fusion de l'agent Technique dans Pro — 2026-10-20

## Décision

Supprimer l'agent `technique` et réunir son périmètre dans l'agent `main`
(Pro) : même modèle, mêmes outils MCP, mêmes skills partagés. Objectif :
un seul contexte technique, moins de duplication d'`AGENTS.md` et de skills,
moins de délégations inutiles.

État final : **2 agents** — `main` (Pro) et `perso` (Perso).

## Inventaire avant fusion

| Élément | Pro (`main`) | Technique (`technique`) |
|---|---|---|
| Workspace | `~/.openclaw/workspace` | `~/.openclaw/workspace-technique` |
| Modèle | `omlx/…Qwen3.6-35B-A3B-4bit` | idem |
| `tools.deny` | `bookstack_*` | `bookstack_*` |
| Skills allowlist | aucune (non restreint) | liste explicite de 60 skills |
| Skills locaux | 8 | 5 |
| MCP | orion, outline | orion, outline (globaux) |

Skills locaux identiques (contenu vérifié par `diff`) : `mcp-raphael`,
`tool-ids`, `recherche-web`, `coordination-agents`. Seul `diagnostic-technique`
était propre à Technique.

## Modifications appliquées

| Action | Détail |
|---|---|
| Backup | `~/.openclaw/backups-merge-technique-20261020-153637/` (config + workspace + agent dir) |
| Skill | `diagnostic-technique` copié dans `workspace/skills/`, texte adapté (plus de délégation) |
| Mémoire | `workspace-technique/memory/` → `workspace/.archive/technique-memory/` (hors contexte actif) |
| Documents | `workspace-technique/.documents/technique/` → `workspace/.documents/archive-technique/` |
| `AGENTS.md` Pro | périmètre élargi au technique, méthode technique condensée en une ligne renvoyant au skill |
| `coordination-agents` | réécrit dans `workspace` et `workspace-perso` : 2 agents, plus de route `technique` |
| Skills partagés | `document-reader`, `documents-extraction-ocr` : ligne Technique retirée du tableau des sources |
| `docread` | message d'erreur `--agent <main\|perso>` |
| Agent | `openclaw agents delete technique --force` (config + agent dir + workspace → trash) |

## Vérifications

```text
openclaw agents list                 → main, perso (technique absent)
openclaw agent --agent technique -m  → Unknown agent id "technique"
openclaw approvals get --json        → agents: main, perso
openclaw skills info --agent main diagnostic-technique → Ready, visible to model
openclaw skills list --agent main    → 36/69 ready (diagnostic-technique inclus)
docread /tmp/ocr-test.png            → ok, agent=main, artefacts dans .documents/main/
openclaw agent --agent main (session neuve) → « Pro (main) », « Perso », Technique signalé fusionné
openclaw agent --agent main exec sw_vers → 27.0.1
```

## Points d'attention

- Les sessions historiques de l'agent `technique` sont supprimées avec l'agent
  (copie conservée dans le backup). Aucune migration de session n'est possible
  entre agents.
- La mémoire « dreaming » de Technique n'est pas réinjectée dans le contexte de
  Pro : elle reste consultable dans `.archive/technique-memory/`.
- `openclaw.json` ne contient plus d'entrée `technique` ; les allowlists
  d'approbation `exec` ne concernaient que `main` et `perso`.
