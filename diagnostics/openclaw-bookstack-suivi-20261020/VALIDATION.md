# Suivi d'activité BookStack — 2026-10-20

## 1. Implémentation

| Élément | Fichier |
|---|---|
| Rendu/parsing de la page Suivi, idempotence, tri des échéances | `openclaw/bookstack-perso/lib/suivi.js` |
| Outil `bookstack_suivi` (read, ensure, add_event, set_deadlines, set_situation, replace) | `openclaw/bookstack-perso/lib/tool-suivi.js` |
| `ensureSuiviPage()` + création dans `createActivity` | `openclaw/bookstack-perso/lib/activities.js` |
| Enregistrement de l'outil + contrat | `index.js`, `openclaw.plugin.json` |
| Tests | `test/suivi.test.mjs`, `test/suivi-page.test.mjs` (30/30) |
| Consignes | `~/.openclaw/workspace-perso/AGENTS.md`, skill `perso-bookstack` (`SKILL.md`, `references/suivi.md`, `references/operations.md`) |

Format : `# Suivi — <activité>`, métadonnées `<!-- openclaw:suivi:meta {…} -->`,
sections `Situation actuelle`, `Échéances et points en attente` (tableau),
`Chronologie` (entrées `### date — nature` + marqueur `<!-- evt:<id> -->`).

## 2. Activation

- `openclaw plugins enable bookstack-perso --accept-capabilities` (consentement
  de capacité requis après ajout d'un outil au contrat).
- Redémarrage franc : `openclaw gateway stop --force`, attente de la sortie du
  processus, puis `openclaw gateway start`. `plugins info` ne remonte plus de
  diagnostic.

## 3. Rattrapage des deux activités

| Activité | Livre | Page Suivi |
|---|---|---|
| Appartement VARS | 36 | 65 — https://bookstack.gangneux.org/books/36/page/suivi |
| Projet Jardin 2026 | 61 | 66 — https://bookstack.gangneux.org/books/61/page/suivi |

Sources : pages documentaires du livre (offre de prêt, devis ACM/MAAF, appels de
fonds, PV d'AG), commentaires indexés, et mails ciblés (`gog gmail read|thread`)
pour les échanges non présents dans BookStack.

Lacunes signalées dans les pages : réalisation des appels de fonds 2026 non
confirmée ; tenue du rendez-vous Jardins du Perquoi du 14/10 non documentée ;
aucun devis jardin reçu.

## 4. Tests

| Scénario | Résultat |
|---|---|
| Création d'activité → une seule page Suivi à la racine | OK (livre de test 67 : `Présentation`, `Suivi`) |
| Nouvelle tentative de création | OK : livre réutilisé, aucune étape rejouée, aucun doublon |
| `add_event` rejoué | `duplicate: true`, révision inchangée |
| `set_deadlines` / `set_situation` rejoués | aucune écriture (rendu identique) |
| Tri des échéances | de la plus récente à la plus ancienne, sans date en fin |
| Conflit de révision | `revision_conflict` |
| Document ordinaire créé dans le livre | page Suivi inchangée (même révision) |
| Correction humaine du texte | conservée après mise à jour |
| Section humaine inconnue | conservée en fin de page |
| Doublon de page Suivi | page existante réutilisée, aucune suppression |
| Bilan ordinaire (agent réel) | `bookstack_activity status` + `bookstack_suivi read` uniquement — **0 appel mail** |
| Bilan par nom d'activité | idem, 0 appel mail |
| Question précise (frais de dossier) | `bookstack_search` + `bookstack_page` ciblés, réponse 819,00 € |
| Vérification explicite (« le notaire a-t-il répondu ? ») | recherche Gmail ciblée `after:2026-10-16`, 1 message, puis mise à jour de Suivi |
| Agents Pro / Technique | `bookstack_*` refusé (`tools.deny`), aucun accès |

Preuve « zéro mail » : `audit_events` (session `agent:perso:suivi-test-20261020`)
ne contient que `bookstack_activity` et `bookstack_suivi` pour les deux bilans.

## 5. Limites

- Le modèle local tente parfois `exec` avec `2>&1` (refusé par l'allowlist) ;
  consigne ajoutée dans le skill (commande simple, sans redirection).
- Une absence de trace n'est pas une preuve d'échec : consigne ajoutée pour ne
  pas conclure « rendez-vous non tenu » depuis un simple silence documentaire.
