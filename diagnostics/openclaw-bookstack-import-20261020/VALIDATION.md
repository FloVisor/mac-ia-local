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
