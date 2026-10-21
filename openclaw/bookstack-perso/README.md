# BookStack Perso — plugin OpenClaw

Gestion documentaire BookStack pour l'agent **Perso** uniquement.

## Modèle

Une activité = un livre BookStack + un groupe de conversations OpenClaw.
BookStack reste la référence documentaire ; le registre local ne contient que
les associations.

## Outils

| Outil | Rôle |
|---|---|
| `bookstack_activity` | activités : list, search, create, open, rename, archive, unarchive, delete, export, status |
| `bookstack_structure` | arborescence, chapitres, pages, déplacement, suppression ; `update_page` avec `mode` append/section/edit/replace |
| `bookstack_search` | recherche dans le livre de l'activité (ou globale) |
| `bookstack_page` | lecture d'une page avec budget de caractères, pièces jointes |
| `bookstack_attachment` | ajout, téléchargement, suppression de pièces jointes |
| `bookstack_import` | import : original + extraction/OCR + page de provenance ; `targetPageId` complète une page existante ; `reextract` préserve les notes humaines |
| `bookstack_conversation` | conversations du groupe : list, create, move, bind, unbind |
| `bookstack_comment` | commentaires natifs : list, read, create, reply, update, archive, unarchive, delete, search, sync, thread |
| `bookstack_suivi` | page `Suivi` à la racine du livre : read, ensure, add_event, set_deadlines, set_situation, replace |

## Configuration

```json5
{
  plugins: {
    entries: {
      "bookstack-perso": {
        config: {
          baseUrl: "https://bookstack.gangneux.org",
          apiToken: { source: "store", provider: "default", id: "PERSO_BOOKSTACK_API_TOKEN" },
        },
      },
    },
  },
}
```

Le jeton est un **SecretRef** vers le store OpenClaw (entrée `secret`, hôte
autorisé `bookstack.gangneux.org`). Aucune valeur en clair dans ce dépôt.

## Restrictions

- Outils `bookstack_*` refusés à Pro (`main`) et Technique (`tools.deny`).
- Aucune opération sur les utilisateurs, rôles, partages ou permissions.
- L'authentification n'est envoyée qu'à l'hôte BookStack configuré ; les
  redirections ne sont pas suivies.

## État local

```text
~/.openclaw/state/bookstack-perso/registry.json        # activités + liaisons
~/.openclaw/state/bookstack-perso/watcher.json         # pièces jointes traitées
~/.openclaw/state/bookstack-perso/comments-index.json  # index lexical des commentaires
```

## Surveillance des dépôts navigateur

```sh
node bin/bookstack-watch.mjs --dry-run
node bin/bookstack-watch.mjs
```

LaunchAgent `org.gangneux.bookstack-watch` : toutes les 5 minutes, sans appel
LLM. Il traite les nouvelles pièces jointes **et** resynchronise l'index des
commentaires (détection des suppressions incluse). Journal :
`~/.openclaw/logs/bookstack-watch.log`.

## Recherche

`bookstack_search` interroge par défaut les **pages et les commentaires**
(`corpus=both`). La recherche native BookStack n'indexe pas les commentaires :
un index lexical local, reconstructible et sans moteur vectoriel, les couvre.
Pagination explicite (`page`, `commentOffset`, `nextOffset`), sans plafond
global caché.

## Suivi d'activité

Chaque activité possède une page `Suivi` à la racine du livre (hors chapitre),
créée par `bookstack_activity` `create` ou `bookstack_suivi` `ensure`. Elle
contient *Situation actuelle*, *Échéances et points en attente* et
*Chronologie*. Les événements sont identifiés par un id stable
(`gmail:<messageId>`, `bookstack:page:<id>`, `doc:<sha256>`) : rejouer une
source ne crée pas de doublon. Les ajouts humains et les sections inconnues
sont préservés. Un bilan ordinaire se répond depuis `bookstack_suivi` `read`
sans aucun accès à la messagerie.

## Retour arrière

```sh
openclaw plugins disable bookstack-perso
launchctl unload ~/Library/LaunchAgents/org.gangneux.bookstack-watch.plist
```

Les livres BookStack restent intacts ; le registre local peut être sauvegardé
ou supprimé sans perte documentaire.
