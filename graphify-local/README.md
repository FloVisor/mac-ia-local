# Graphify local — déploiement du 21 octobre 2026

Graphify **0.9.93**, paquet officiel `graphifyy`, installé une seule fois par
`uv tool install graphifyy` dans `~/.local/share/uv/tools/graphifyy/`.
Exécutables : `~/.local/bin/graphify`, `graphify-mcp` (non configuré) et notre
commande de cadrage `~/.local/bin/graphify-local` ; source dans ce dossier.
Aucun commit ni push.

## Périmètre et inventaire

Découverte ciblée dans Workspaces, Projects, AI, super-agent,
super-agent-migration-private, hue-audit et nodectra. Ni scan intégral du Mac,
ni suivi des liens symboliques ; dépendances/caches écartés. Neuf dépôts et
un worktree lié identifié par `git worktree list`. Aucun dépôt imbriqué trouvé
dans le périmètre exploré. Les tailles portent sur les fichiers suivis présents,
hors historique Git, dépendances ignorées et fichiers non suivis.
Aucun graphe préexistant dans les emplacements recherchés.

| Racine | Branche observée | Mio suivis | Langages/formats |
|---|---|---:|---|
| `/Users/fngux2/Workspaces/mac-ia-local` | `main` | 47.6 | Go, Python, JS/TS, Swift |
| `/Users/fngux2/Workspaces/m3-si-xithi` | `main` | 8.3 | JSON, Markdown, JavaScript |
| `/Users/fngux2/Workspaces/Plateforme-SD-WAN-XITHI` | `chore/altiwan-branding` | 4.4 | Go, Python, JS/TS |
| `/Users/fngux2/Workspaces/Plateforme-CaaS-XITHI` | `main` | 0.2 | Shell, YAML, Markdown |
| `/Users/fngux2/Workspaces/XITHI-Infrastructure-Ops` | `main` | 11.9 | Python, Ansible/YAML, PowerShell |
| `/Users/fngux2/Projects/m3-si-mixtrio-kit` | `main` | 8.8 | JavaScript, JSON, Markdown |
| `/Users/fngux2/super-agent` | `migration/candidate-0.8.0-no-deploy` | 4.0 | Python, Shell |
| `/Users/fngux2/super-agent-migration-private/20261002T-migration.4ewvdU/recovery-clone` | `(detached)` | 4.0 | Python, Shell |
| `/Users/fngux2/nodectra` | `main` | 1.6 | Python |
| `/Users/fngux2/Workspaces/.codex-worktrees/XITHI-xansible-decisions-0.5.16` | `codex/xansible-decisions-0.5.16` | 4.6 | Python, Ansible/YAML, PowerShell |

Inventaire détaillé : [inventory.json](inventory.json). Les branches sont un
instantané, pas une configuration imposée.

## Installation Codex et usage

Sources vérifiées : [README officiel](https://github.com/Graphify-Labs/graphify),
[installation officielle](https://docs.graphify.com/installation),
[site Graphify](https://graphify.com/),
[skills Codex](https://developers.openai.com/codex/skills/).
Le code officiel `graphify/install.py` distingue `graphify codex install`,
qui écrit AGENTS.md et un hook, de `graphify install --platform agents`,
qui installe uniquement le skill global et ses références.
C'est cette seconde commande qui a été exécutée, sans modification du produit.

Skill : `~/.agents/skills/graphify/SKILL.md` et `references/`.
Consignes ajoutées uniquement en fin de `~/.codex/AGENTS.md` entre
`BEGIN GRAPHIFY LOCAL` et `END GRAPHIFY LOCAL` ; copie versionnable dans
[global-instructions.md](global-instructions.md). Consignes RTK conservées.
Leur priorité limite le skill générique : aucun LLM, Cloud, fusion multi-dépôts,
hook, extraction documentaire ou MCP supplémentaire. Aucun réglage modèle changé.
Le skill doit être disponible aux prochains tours/sessions ; le démarrage réel
d'une nouvelle session Desktop ou CLI avec appel modèle n'a pas été testé.

Depuis un dépôt Git (si le terminal est dans `~`, entrer d'abord dans le dépôt) :

```sh
cd ~/Workspaces/mac-ia-local
~/.local/bin/graphify-local refresh
~/.local/bin/graphify-local query "symbole module"
~/.local/bin/graphify-local explain "symbole"
~/.local/bin/graphify-local path "A" "B"
```

Initialiser les autres dépôts uniquement à leur première utilisation utile,
après lecture de leurs AGENTS.md et vérification de leurs exclusions.
Ajouter `/graphify-out/` à leur .gitignore. Pas de réinstallation globale.
Utiliser Graphify pour architecture, dépendances et impact ; garder les lectures
directes pour les tâches simples. Lire les sources avant modification sensible.

## Graphes, confidentialité et actualisation

Seul dépôt réel indexé : `/Users/fngux2/Workspaces/mac-ia-local` (dépôt courant,
donc aucune seconde initialisation du même dépôt).
Graphe persistant : `graphify-out/graph.json` dans cette racine, exclu de Git.
16 699 nœuds, 64 192 relations à la création ; après actualisation finale :
16 693 nœuds, 64 183 relations (1 220 fichiers en cache, 119 réextraits,
0 supprimé ; l’extracteur peut reprendre des dépendances et dédupliquer). Les fichiers d'analyse et de cache
incrémental restent à côté. Aucun HTML/rapport généré : inutiles à la CLI.

La commande fixe `GRAPHIFY_BACKEND=none`, `GRAPHIFY_OUT=graphify-out`,
utilise `extract --code-only --max-workers 2` et respecte .gitignore,
.graphifyignore et les exclusions explicites. Attention : `--backend none`
est refusé par 0.9.93 ; seul le réglage d'environnement est utilisé.
Les dépendances ont été téléchargées lors de l'installation ; l'extraction et
les requêtes de validation ont tourné sous `sandbox-exec` avec réseau interdit.
Les usages suivants reposent sur le mode sans backend ; aucun sandbox permanent
ni réglage système global ajouté.

Chaque worktree a son propre dossier et son verrou `.local.lock` (fcntl).
Les dépôts imbriqués sont exclus explicitement. Les graphes d'une autre racine
sont refusés grâce au marqueur de propriété `.local-owner.json`.
Les changements de branche/HEAD imposent refresh avant interrogation.
Les changements non committés nécessitent un refresh à la demande lorsque
pertinents : la commande n'effectue pas une inspection complète à chaque query.
Graphify compare ses empreintes et réextrait seulement les fichiers modifiés ;
aucun --force, watcher ou hook Git. Les requêtes ont un budget de 1 500 tokens.
Le verrou protège les appels via graphify-local, pas les appels directs à graphify.

## Validation et limites

[validation.json](validation.json) contient les résultats.
Requête réelle `paid_broker Approval` : classe `Approval` dans
`mcp/llm-router/paid_broker.py:65`, tests dans `test_paid_broker.py`.
Relation `calls` EXTRACTED de `NativeAuthority.allow` vers `Approval`,
confirmée dans le source du test à la ligne 28.
[Sortie de requête](query-validation.txt), limitée à 1 500 tokens ;
53 des 162 nœuds trouvés affichés, troncature explicitement signalée.

Dépôt temporaire indépendant : graphe limité à sample.py, relation
isolated_caller → isolated_leaf ; aucun symbole mélangé avec le pilote.
Secrets/dépendances exclus ; réutilisation sans changement : 1 fichier en cache,
0 réextrait ; ajout non committé repris ; verrou concurrent et mauvaise racine
refusés. Dépôt temporaire supprimé après contrôle.

39 fichiers P3-C/Standup/router/adaptateur contrôlés par SHA-256 inchangés.
config.toml et AGENTS.md du projet inchangés ; aucun hooks.json Codex créé.
Instructions globales originales conservées octet pour octet avant l'ajout.
RTK git status utilisable. Aucune déclaration MCP, trace, supervision ou paramètre
LiteLLM/oMLX modifié. Ces contrôles de préservation ne sont pas une nouvelle
recette fonctionnelle complète de P3-C.

Limites Graphify observées : 40 fichiers sans symboles modélisés, collisions de
noms Swift (`Contacts`, `Foundation`) avec nœuds abandonnés et avertissement PDF
sans extra pypdf (PDF volontairement hors périmètre). Les relations inférées et
la couverture restent des indications statiques, jamais une preuve d'exécution.

MCP : l'exécutable est livré par le paquet mais aucun serveur n'est déclaré.
Skill + CLI permettent déjà de choisir explicitement la racine locale ; aucun
avantage nécessaire ne justifie un serveur supplémentaire. La sélection
simultanée de plusieurs graphes via MCP n'a pas été qualifiée ni déployée.

## Désinstallation ciblée

1. Retirer uniquement le bloc délimité GRAPHIFY LOCAL de ~/.codex/AGENTS.md ;
   préserver les changements concurrents. Sauvegarde antérieure disponible dans
   `~/.local/state/graphify-local/AGENTS.before-20261021.md` ; ne pas restaurer
   aveuglément tout le fichier.
2. Supprimer uniquement `~/.local/bin/graphify-local` et
   `~/.agents/skills/graphify/` (skill installé pour cette mission).
3. Exécuter `uv tool uninstall graphifyy`.
4. Conserver les graphes utiles par défaut. Leur suppression est facultative et
   doit viser uniquement le graphify-out du dépôt choisi. Retirer les seuls
   ajouts Graphify de .gitignore/.graphifyignore si souhaité.
5. Ce dossier contient documentation et source de déploiement ; aucun autre
   dossier, MCP ou réglage Codex ne fait partie du rollback.
