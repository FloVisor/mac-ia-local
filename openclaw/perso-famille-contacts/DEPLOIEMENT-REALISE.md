# Déploiement réalisé — 2026-10-20

Sauvegarde : `~/.openclaw/backups-perso-famille-20261020-1555/`

## Fichiers modifiés

| Fichier | Nature |
| --- | --- |
| `~/.openclaw/openclaw.json` | `tools.sessions.visibility=agent`, `tools.agentToAgent{enabled,allow}`, `send` par agent, `read` ajouté à `tools.allow` |
| `~/.openclaw/state/openclaw.sqlite` (`exec_approvals_config`) | `perso-contacts` ajouté à l'allowlist exec de **perso** uniquement |
| `~/.openclaw/workspace-perso/USER.md` | Directives (identité, famille, confidentialité, style) |
| `~/.openclaw/workspace-perso/AGENTS.md` | Bloc « Famille et contacts Apple » + règle patronyme + règle demande entrante |
| `~/.openclaw/workspace-perso/famille/` | `index.md` + 21 fiches (nouveau) |
| `~/.openclaw/workspace-perso/skills/famille-contacts/` | Skill (nouveau) |
| `~/.openclaw/workspace-perso/skills/imessage/SKILL.md` | Syntaxe `imsg` corrigée |
| `~/.openclaw/workspace/AGENTS.md` | Bloc « Périmètre personnel — séparation avec Perso » |
| `~/.openclaw/workspace/skills/imessage/SKILL.md` | Syntaxe `imsg` corrigée |
| `~/.openclaw/workspace/skills/macos-contacts/` | **Archivé** vers `.archive/macos-contacts-20261020/` |
| `~/.local/bin/perso-contacts` | Binaire installé |

## Non modifié (volontairement)

- `tools.exec.safeBins` (`osascript` conservé) — voir `osascript-safeBins.md`.
- Socle professionnel de Pro : aucune réécriture, seulement la règle de périmètre.
- `USER.md` de Pro : inchangé.
- Fenêtre de contexte du modèle : inchangée.
- Aucun contact, aucun envoi, aucun document publié.

## Coût du contexte permanent

| Agent | Avant | Après | Delta |
| --- | --- | --- | --- |
| Perso `USER.md` | 1 137 | 2 410 | +1 273 car. |
| Perso `AGENTS.md` | 7 479 | 8 936 | +1 457 car. |
| Pro `AGENTS.md` | 6 648 | 7 242 | +594 car. |

Total ajouté : **+3 324 caractères**, soit ≈ **830 tokens** (≈ 4 car./token).

Note : `AGENTS.md` de Perso contient aussi les sections préexistantes ; seul le
delta ci-dessus est imputable à cette mission.
Annuaire, fiches, skill et socle pro restent hors contexte permanent.

## Retour arrière

```sh
cd openclaw/perso-famille-contacts
./rollback.sh ~/.openclaw/backups-perso-famille-20261020-1555
~/.openclaw/bin/openclaw approvals allowlist remove --agent perso "/Users/fngux2/.local/bin/perso-contacts"
~/.openclaw/bin/openclaw gateway restart
```

Le skill `macos-contacts` archivé se restaure par
`mv ~/.openclaw/workspace/.archive/macos-contacts-20261020/macos-contacts ~/.openclaw/workspace/skills/`.
