# `osascript` dans `tools.exec.safeBins` — constat et correction envisageable

## Constat

`tools.exec.safeBins` contient `osascript` avec un profil autorisant `-e` et un
argument positionnel. Conséquence vérifiée le 2026-10-20 : depuis un contexte
équivalent au Gateway, `osascript -e 'do shell script "head -c 60 ~/.openclaw/workspace-perso/USER.md"'`
lit un fichier du workspace de Perso.

`safeBins` est conçu pour des binaires **stdin-only** (filtres de flux). La
documentation OpenClaw déconseille explicitement d'y placer un interpréteur :
« If a command can evaluate code, execute subcommands, or read files by design,
prefer explicit allowlist entries and keep approval prompts enabled. »

`osascript` peut exécuter du code arbitraire (`do shell script`) : il ne relève
pas de cette catégorie.

## Correction envisageable

1. Retirer `osascript` de `tools.exec.safeBins` et de `safeBinProfiles`.
2. Si un usage AppleScript reste nécessaire, l'ajouter comme entrée d'allowlist
   explicite **par agent**, avec approbation, plutôt qu'en `safeBins` global.
3. Vérifier ensuite qu'aucun skill existant ne dépend de `osascript` implicite
   (`macos-contacts` archivé le 2026-10-20 était le principal consommateur).

## Ce que cette correction ne ferait pas

Retirer `osascript` **ne réalise pas** une isolation système :

- `exec` reste autorisé aux deux agents avec d'autres binaires ;
- un interpréteur présent dans l'allowlist (`openclaw`, `gog`, `docread`) peut
  avoir ses propres chemins de lecture ;
- les deux agents partagent le même compte macOS, sans sandbox.

Une isolation forte exigerait un sandbox par agent, un compte macOS distinct ou
un Gateway séparé — hors périmètre de cette mission.

## Décision

Non appliqué : la mission exclut explicitement de retirer `osascript` de Pro
« pour cette raison ». Le présent document sert de base à une décision ultérieure.
