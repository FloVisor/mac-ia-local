# AGENTS.md — openclaw/

## Objectif

Intégration d'outils dans **OpenClaw** : pièges connus (TCC, `tools.allow`, politique Graph, saturation de session) et checklist pour les prochaines intégrations.

## Structure

- `integration-pitfalls.md` — pièges d'intégration (iMessage) + checklist

## Règles

- Toute intégration OpenClaw doit passer par la checklist de [integration-pitfalls.md](integration-pitfalls.md).
- Les captures de validation vont dans `diagnostics/` (préfixe `openclaw-*` ou `mcp-*`), jamais ici.
- Contexte : alléger les AGENTS.md des workspaces OpenClaw (procédures → skills), voir `diagnostics/openclaw-ctx-allege-20261018/`.

## Lecteur documentaire (PDF / OCR)

- Skill partagé `document-reader` + convertisseur `docread` (Docling local),
  installés dans `~/.openclaw/skills/document-reader/` (managé, visible des 3 agents).
- Recette et pièges : [integration-pitfalls.md](integration-pitfalls.md#lecteur-documentaire-commun-pdf--ocr--2026-10-19)
  et [diagnostics/openclaw-document-reader-20261019](../diagnostics/openclaw-document-reader-20261019/VALIDATION.md).
- Toute modification du convertisseur doit être revalidée depuis les **trois**
  agents (Pro/Perso/Technique), pas seulement en terminal.
