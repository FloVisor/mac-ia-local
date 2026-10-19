# Lecteur documentaire commun (PDF / extraction / OCR) — 2026-10-19

## Périmètre

Étendre la capacité « récupérer un document → extraire texte/Markdown → OCR si
nécessaire » aux **trois** agents OpenClaw, en remplacement de la restriction
« Perso uniquement ». Un convertisseur commun et un skill partagé, pas trois
implémentations.

## Identifiants réels (vérifiés, pas déduits du nom affiché)

| Agent | ID OpenClaw | Workspace | Agent dir | Modèle |
|---|---|---|---|---|
| Pro | `main` | `~/.openclaw/workspace` | `~/.openclaw/agents/main/agent` | `omlx/…Qwen3.6-35B-A3B-4bit` |
| Perso | `perso` | `~/.openclaw/workspace-perso` | `~/.openclaw/agents/perso/agent` | idem |
| Technique | `technique` | `~/.openclaw/workspace-technique` | `~/.openclaw/agents/technique/agent` | idem |

Aucun agent créé ni renommé. Modèles et fournisseurs inchangés.

## Emplacement partagé des skills (version installée 2026.10.4)

Ordre de précédence documenté : `<workspace>/skills` > `<workspace>/.agents/skills`
> `~/.agents/skills` > **`<state-dir>/skills`** (managé) > workshop > bundled.

Skill installé dans le répertoire managé `~/.openclaw/skills/document-reader/`
(visible par tous les agents, filtré ensuite par allowlist).

**Contrôle des copies locales masquantes** : aucun `document-reader` dans
`workspace*/skills`, `workspace*/.agents/skills`, `~/.agents/skills`, ni
`agents/*/agent/workshop-skills`. Aucune collision de nom.

## Convertisseur

- Docling 2.140.0 installé via `uv tool install docling --python 3.12`
  (`~/.local/share/uv/tools/docling/`), OCR **RapidOCR** (CPU, PP-OCRv6).
- Wrapper `docread` → `~/.openclaw/skills/document-reader/scripts/docread`
  (résout son vrai chemin même via symlink `~/.local/bin/docread`).
- Script `convert_document.py` : sortie JSON une ligne, `--ocr auto` (OCR si
  < 40 caractères natifs/page), `--ocr full_page`, `--tables`, `--max-pages`.
- Réutilise l'existant : `document-extract` (clawpdf) reste le fallback du tool
  `pdf` natif ; Docling est ajouté pour l'extraction durable + OCR.

## Isolation des artefacts

```text
<workspace-agent>/.documents/<agent>/<conversation>/<nom>-<hash>/
```

- `--agent` déduit du **répertoire de travail réel** (`workspace` → `main`,
  `workspace-<id>` → `<id>`), jamais d'une valeur par défaut `main` : hors
  workspace → `agent_not_determined` (échec explicite, pas de collision).
- `media://inbound/<id>` (pièces Outlook/OneDrive) copié dans `originals/` du
  dossier de l'agent avant conversion — le store média OpenClaw est partagé.
- Hash SHA-256 du contenu : deux versions d'un même nom ne s'écrasent pas.

## Politique exec (suppression des popups)

`tools.exec.mode` : `ask` → **`allowlist`**. Entrées par agent (le wildcard
`--agent "*"` n'est pas hérité par les agents nommés) :

| Agent | Allowlist ajoutée |
|---|---|
| `main` | `docread`, `docling`, `imsg`, `openclaw` |
| `perso` | `docread`, `docling`, `gog`, `imsg`, `openclaw` |
| `technique` | `docread`, `docling`, `openclaw` |

- `gog` **volontairement absent** de `main` et `technique` : pas d'accès Gmail.
- `imsg` absent de `technique` (pas de périmètre iMessage).
- Vérifié : `curl` reste refusé (`exec denied: allowlist miss`) ; `gog` refusé
  pour `main`.
- Les commandes composées (`&&`, pipes) ne sont pas liables par l'approbation :
  d'où l'allowlist plutôt que l'approbation à la volée.

## Périmètre des connexions (inchangé)

| Agent | Récupération autorisée | Messagerie |
|---|---|---|
| Pro | `microsoft-graph` : `outlook_mail_read` → `list_attachments` → `download_attachment`, `onedrive_download` | Outlook uniquement |
| Perso | `gog gmail attachment <messageId> <attachmentId> --out <dir>` | Gmail uniquement |
| Technique | fichiers fournis, URL via `web_fetch` | aucune |

Aucun identifiant Gmail copié vers Pro/Technique. Le convertisseur ne reçoit
qu'un fichier : il n'accède à aucune messagerie.

## BookStack

Aucune occurrence de BookStack dans la configuration, les workspaces ou les
skills de cet environnement (recherche exhaustive `~/.openclaw`, keychain,
`~/.config`, transcripts SQLite décompressés). Rien n'a été modifié ni déplacé :
le périmètre BookStack de Perso reste intact par construction. Pro et Technique
lisent leurs documents sans dépendre de BookStack.

## Validation réelle (appels depuis chaque agent, pas seulement terminal)

| Test | Pro (`main`) | Perso (`perso`) | Technique (`technique`) |
|---|---|---|---|
| Skill visible modèle | ✅ | ✅ | ✅ (ajouté à l'allowlist) |
| PDF texte converti | ✅ `DOC-2026-1019` | ✅ `DOC-2026-1019` | ✅ `DOC-2026-1019` |
| PDF scanné + OCR | ✅ `SCAN-7788` / `ZEBULON42` | ✅ `SCAN-7788` | ✅ `SCAN-7788` |
| Pièce jointe récupérée | ✅ Outlook PDF 2 pages (scan, OCR) | ✅ Gmail PDF 4 pages (texte natif) | ⛔ non disponible (pas de messagerie) |
| Isolation artefacts | `.documents/main/…` | `.documents/perso/…` | `.documents/technique/…` |

Détails :

- **Pro** : `outlook_mail_read` `search_messages` → `list_attachments` →
  `download_attachment` → `media://inbound/Non_renouvellement_licence_VMWare---db1fb420-….pdf`
  → `docread` → 2 pages, `ocr_executed: true`, 2 180 caractères.
- **Perso** : `gog gmail attachment 1a13a78fcf38d6e2 … --out …` → PDF 4 pages
  (devis MAAF) → `docread` → `ocr_executed: false` (texte natif suffisant).
- **Technique** : fichiers fournis directement ; pas de connecteur de
  messagerie, comportement attendu.

## Limites restantes

1. **OCR** : RapidOCR CPU, bon sur imprimé latin ; manuscrit et scans très
   dégradés incertains. Pas de `--ocr-lang` par défaut (auto).
2. **Premier appel** : téléchargement des poids Docling (~1 Go) — déjà fait sur
   ce poste, à refaire sur une nouvelle machine.
3. **PDF chiffrés** : non pris en charge par le wrapper.
4. **Commandes composées** : toujours refusées en mode `allowlist` ; utiliser
   des appels simples ou une entrée d'allowlist dédiée.
5. **`media://inbound`** : store partagé entre agents ; la copie dans
   `originals/` rattache l'original à l'agent, mais la purge du store reste
   globale à OpenClaw.
6. **BookStack** : non présent dans cet environnement ; si une intégration
   existe ailleurs, elle n'a pas été touchée par ce chantier.

## Fichiers modifiés

- `~/.openclaw/skills/document-reader/SKILL.md` (nouveau, managé)
- `~/.openclaw/skills/document-reader/scripts/{docread,convert_document.py}` (nouveaux)
- `~/.local/bin/docread` (symlink)
- `~/.openclaw/openclaw.json` : `tools.exec.mode`, `agents.entries.technique.skills`
  (sauvegarde `openclaw.json.bak-pre-docreader-20261019`)
- `~/.openclaw/workspace{,-perso,-technique}/AGENTS.md` : section « Documents »
  (sauvegardes `AGENTS.md.bak-pre-docreader-20261019`)
- Approbations exec (SQLite `state/openclaw.sqlite#exec_approvals_config`)
