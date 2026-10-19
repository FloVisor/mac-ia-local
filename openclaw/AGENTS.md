# AGENTS.md — openclaw/

## Objectif

Intégration d'outils dans **OpenClaw** : pièges connus (TCC, `tools.allow`, politique Graph, saturation de session) et checklist pour les prochaines intégrations.

## Structure

- `integration-pitfalls.md` — pièges d'intégration (iMessage) + checklist

## Règles

- Toute intégration OpenClaw doit passer par la checklist de [integration-pitfalls.md](integration-pitfalls.md).
- Les captures de validation vont dans `diagnostics/` (préfixe `openclaw-*` ou `mcp-*`), jamais ici.
- Contexte : alléger les AGENTS.md des workspaces OpenClaw (procédures → skills), voir `diagnostics/openclaw-ctx-allege-20261018/`.