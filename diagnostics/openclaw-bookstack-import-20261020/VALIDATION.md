# Import PDF/OCR BookStack et échecs d'outils — 2026-10-20

Session analysée : « Général — Appartement VARS »
(`0866b8a0-7212-40e7-99de-3d43f34685fe`, agent `perso`, origine
`7f2a31b6-a255-443d-b665-bb6120a08383`).

## 1. Import PDF → BookStack en Markdown : cause racine

`document-extract` (seul fournisseur du contrat `documentExtractors`,
`enabledByDefault: true`) avait été passé à `enabled: false` lors du nettoyage
de plugins du 2026-10-18. Sans lui, `extractPdfContent` lève
`PDF extraction disabled or unavailable` → `read-failure` →
`[Attachment could not be read]` dans le prompt.

Aggravant : `chat-attachments-CGf2bW4A.mjs` pose `hydrationSuppressed: true`
sur toute pièce jointe non-image. Le PDF est offloadé vers
`media://inbound/<id>` sans chemin ni texte, donc le modèle n'a aucun
`filePath` à passer à `bookstack_import`.

### Correctifs

| Correctif | Emplacement |
|---|---|
| `document-extract.enabled = true` (global, aucun override par agent) | `~/.openclaw/openclaw.json` |
| Limites PDF relevées : 60 pages, 40 Mo, 200 k car., 40 Mpx | idem |
| `resolveSourcePath()` : `media://inbound/<id>` → chemin réel, rejet de traversée | `openclaw/bookstack-perso/lib/extract.js` |
| `slug()` : préserve l'extension lors de la troncature à 80 car. | idem |
| `bookstack_import` / `bookstack_attachment` utilisent `resolveSourcePath` | `openclaw/bookstack-perso/lib/tools.js` |
| `bookstack_structure` : résolution par `targetBookId`, `name` = titre si `activityId` fourni | idem |
| Consigne `media://inbound/<id>` | `~/.openclaw/workspace-perso/AGENTS.md` + skill `perso-bookstack` |

Sauvegarde config : `~/.openclaw/openclaw.json.bak-pre-pdf-pages-20261020`.

### Validation

- Extraction native : **37/37 pages**, `truncated: false`, 216 339 caractères.
- Import end-to-end : page BookStack **id 41** « Offre de prêt — Crédit
  Immobilier », chapitre 40, pièce jointe id 9, Markdown complet.
- `bookstack_structure` : `tree` par `targetBookId` OK ; `create_chapter` avec
  `name` OK (chapitre 42 créé puis supprimé).
- Résolution du SecretRef `store:default:PERSO_BOOKSTACK_API_TOKEN` OK
  (`GET /books` → `36:Appartement VARS`).

## 2. `invalid connect params` (~5 140 occurrences)

Symptôme : `gateway connect failed: GatewayClientRequestError: invalid connect
params: at /client/id: must be equal to one of the allowed values`, 2 par cycle
de 15–25 s, à partir de `2026-10-19T23:08:51`.

### Diagnostic

`tcpdump -A` ne montre pas les frames client→serveur (masquage XOR WebSocket).
Capture binaire `pcap` + démasquage Python : le client fautif envoie
`client.id = "bookstack-perso"`, `version = "0.1.0"`, `mode = "backend"`.

Le runtime valide `client.id` contre `GatewayClientIdSchema =
Type.Enum(GATEWAY_CLIENT_IDS)` (17 valeurs canoniques, cf.
`dist/client-info-C8RatpKO.mjs`). `bookstack-perso` n'en fait pas partie.

Le client synthétique légitime du SDK (`createSyntheticPluginRuntimeClient`,
`dist/server-plugin-runtime-client-Bn0mfXdW.mjs`) envoie
`id = GATEWAY_CLIENT_IDS.GATEWAY_CLIENT` et `version = "internal"` : ce n'est
donc pas lui. L'identité fautive reprend exactement `manifest.id` et
`manifest.version` du plugin.

### Résolution

Un **vrai** redémarrage du gateway (`openclaw gateway stop --force` puis
relance) fait cesser les erreurs : `delta = 0` sur 90 s, puis `delta = 0` après
un cycle désactivation/réactivation du plugin à chaud.

Point important : `openclaw gateway restart` ne redémarre pas réellement le
processus (même PID) et `openclaw plugins disable` ne décharge pas le plugin du
gateway en cours. Seul `gateway stop --force` garantit un état propre.

Conclusion : le plugin n'est pas la cause reproductible ; l'état corrompu du
processus gateway (accumulation de `Plugin replacement applied` — 34 en une
nuit) l'était. Parade durable : redémarrer franchement le gateway après toute
modification de `plugins.entries.*`.

## 3. `tool_search` : `limit` au niveau batch

Validateur explicite dans `dist/tool-search-DhM6ilxL.mjs` :

```js
if (singleQuery === void 0 && (params.limit != null || params.options !== undefined))
  throw new ToolInputError("set limit on each batch query, not on the batch request.");
```

Erreur de formatage du modèle (Qwen3.6-35B), pas un bug runtime. Parade
appliquée dans les trois `AGENTS.md` (`workspace`, `workspace-perso`,
`workspace-technique`) : `limit` **dans chaque query**, jamais au niveau batch,
et retry immédiat au bon format.

## 4. Autres anomalies observées (non traitées)

- `[prompt-cache] message 0 (user) differs from the previous request`
- `terminal upload staging is busy`
- `microsoft-graph` : provenance-invalid (plugin non vérifiable)
- `session observer disabled after consecutive failures`

## 5. Régression `missing_token` (2026-10-20, après import)

Tous les outils `bookstack_*` renvoyaient `missing_token` alors que le secret
était présent. Cause : le runtime matérialise les `secretInputs` déclarés au
manifeste et passe la **chaîne** résolue dans `api.pluginConfig.apiToken` ; le
plugin exigeait un objet SecretRef.

Correctif : `resolveApiToken()` accepte chaîne (matérialisée) ou SecretRef
(lecture froide), schémas en `["string","object"]`, watcher aligné.
Vérifié : `bookstack_activity list` → `ok: true`, livre 36 « Appartement VARS ».
Détail : [openclaw/integration-pitfalls.md](../../openclaw/integration-pitfalls.md).

## 6. Import depuis une pièce jointe Gmail (2026-10-20, après correctifs)

Cause : l'`attachmentId` Gmail (jeton base64 ~350 car.) était passé comme
`filePath` → `ENAMETOOLONG`, puis repli sur une page de synthèse « PDF non lu ».

Correctifs : `assertImportPath()` (`lib/extract.js`) + `invalid_file_path` dans
`bookstack_import` ; validation `scope`/`corpus` de `bookstack_search` ;
`id` alias de `pageId` dans `bookstack_page` ; consignes
`workspace-perso/AGENTS.md`, skills `perso-bookstack` et
`documents-extraction-ocr`.

Rejeu réel (agent `perso`, gateway redémarré) :

| Mail | PDF | Page | Pièce jointe |
|---|---|---|---|
| `1a13a78fcf38d6e2` | `Devis habitation_2.pdf` (Confort + mobilier, 229,60 €) | 46 | 10 |
| `1a13a78fcf38d6e2` | `Devis habitation_3.pdf` (Essentielle, 143,67 €) | 47 | 11 |
| `1a13a78fcf38d6e2` | `Devis habitation_4.pdf` (Confort, 165,13 €) | 48 | 12 |
| `1a11c434dabf30df` | `Devis.pdf` (ACM PNO, 14,31 €/mois) | 49 | 13 |

Chapitre 43 « Assurance » : 4 pages Markdown + 4 originaux. Pages 44/45
(synthèses erronées) supprimées.

Validation des garde-fous : `scope=book` → `invalid_scope` ; `corpus=bad` →
`invalid_corpus` ; `attachmentId` comme `filePath` → `invalid_file_path` ;
`bookstack_page {id:47}` → OK. Tests : `node --test test/extract.test.mjs`
(3/3), `python3 -m unittest test_calcul` (2/2).

## 7. `pageId` ignoré en mode import (2026-10-20)

Session « Fiche d'appartement présentation stockée »
(`2c4b157b-51e9-4d7f-bb6e-f316277c6cec`, agent `perso`).

Demande : « Ajoute la fiche de l'appartement dans l'activité Vars dans la page
présentation stocké en MD ». Le modèle a correctement résolu l'activité
(`7f13522c…`, livre 36) et la page cible (`bookstack_search` → page 37
« Présentation »), puis appelé :

```json
bookstack_import { activityId, pageId: 37, filePath: "media://inbound/…", title: "…" }
```

Résultat : **page 50 créée dans le chapitre 38 « Documents »**, page 37 intacte
(révision 1). Le modèle a ensuite rationalisé (« comme prévu par le protocole
d'import ») au lieu de signaler l'écart.

### Cause

`pageId` était déclaré dans le schéma de `bookstack_import` mais lu uniquement
dans la branche `action === "reextract"`. En mode `import`, la destination était
forcée à `params.chapterId ?? activity.documentsChapterId` puis `POST /pages`.
Paramètre accepté, validé, puis silencieusement ignoré — cas n°4 de la règle
d'or du dépôt (bug outil, pas bug modèle). Aucun outil ne permettait d'écrire
dans une page existante : `update_page` remplaçait le Markdown sans fusion.

### Correctifs

| Correctif | Emplacement |
|---|---|
| `pageId` hors `reextract` → `pageId_requires_reextract` | `lib/tools.js` |
| `targetPageId` : extraction ajoutée dans une page existante, sans suppression | `lib/tools.js` |
| `confirm=true` exigé si la cible n'est pas une page d'extraction | `lib/tools.js` |
| `target_outside_activity` si la cible est hors du livre | `lib/tools.js` |
| `destination: { pageId, chapterId, created }` dans le retour | `lib/tools.js` |
| `update_page` : `mode` `append` / `section` / `edit` / `replace` | `lib/tools.js` |
| Helpers Markdown purs (`appendExtraction`, `mergeExtraction`, `replaceSection`, `applyEdit`, `headingsOf`) | `lib/markdown.js` |
| Règle document vs synthèse + modes d'édition | `workspace-perso/AGENTS.md`, skill `perso-bookstack` |

`mergeExtraction` ne détruit plus une page sans marqueurs : il ajoute le bloc à
la suite au lieu de reconstruire la page.

### Validation réelle (livre 36, page de test supprimée après coup)

| Cas | Résultat |
|---|---|
| `bookstack_import { pageId: 37 }` | `pageId_requires_reextract` |
| `targetPageId` sur page non-extraction, sans `confirm` | `confirmation_required` + aperçu + titres |
| `targetPageId` + `confirm=true` | `created: false`, contenu humain conservé, 1 bloc |
| Second import sur la même page | idempotent : 1 bloc, contenu humain intact |
| `update_page mode=append` | ajout sans suppression |
| `update_page mode=section` (section absente) | `section_not_found` + titres disponibles |
| `update_page mode=section` (section présente) | corps remplacé, suite intacte |
| `update_page mode=edit` (texte ambigu) | `ambiguous_text` + nombre d'occurrences |
| `update_page mode=edit` (texte unique) | remplacement exact |

Tests : `node --test test/*.test.mjs` → 15/15 (dont 12 nouveaux sur
`lib/markdown.js`).

### Reste à faire

- Remise en état du livre 36 : la page 50 reste dans `Documents`. Fusion dans la
  page 37 ou conservation comme page dédiée = décision utilisateur.
- Redémarrer franchement le gateway (`openclaw gateway stop --force`) pour
  charger le plugin modifié.

## 8. Remise en état du livre 36 (2026-10-20)

Décision utilisateur : fusionner la fiche dans `Présentation` et supprimer le
chapitre `Documents`.

| Action | Résultat |
|---|---|
| `bookstack_import { targetPageId: 37, confirm: true }` | `created: false`, page 37 révision 2 |
| Contenu humain de la page 37 | conservé (`# Appartement VARS` + phrase de synthèse) |
| Bloc d'extraction | 1 seul, 4 771 caractères OCR (14 pages) |
| Pièce jointe | id 22 sur la page 37 |
| Page 50 supprimée | 404 (pièce jointe 14 supprimée avec elle) |
| Chapitre 38 `Documents` supprimé | 404 |

Registre local : `documentsChapterId` passé à `null` (sauvegarde
`registry.json.bak-pre-docs-chapter-20261020`). `createActivity` respecte
désormais `documentsChapterId: null` comme « chapitre supprimé volontairement »
et ne le recrée plus — vérifié par un `bookstack_activity create` idempotent
(aucun chapitre recréé).

État final du livre 36 : `Présentation` (page racine), `Notes`, `Financement`,
`Assurance`, `Co propriété`.

### Incident annexe : 404 globale sur l'API

Entre 14:20 et 14:30, tous les endpoints de lecture renvoyaient `data: []` /
404 alors que les écritures fonctionnaient. Cause : autorisations BookStack
révoquées côté interface (corrigées par l'utilisateur). Aucune perte de données.
Le watcher a enregistré `totalPages: 0` pendant l'intervalle, sans conséquence.
