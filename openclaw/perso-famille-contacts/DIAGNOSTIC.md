# Diagnostic factuel — 2026-10-20

Constats vérifiés sur l'installation réelle. Aucune supposition de chemin,
de binaire ou de clé de configuration.

## Installation

| Élément | Valeur constatée |
| --- | --- |
| Version | OpenClaw 2026.10.5 (`1b58cb9`) |
| Runtime | `~/.openclaw/runtime/2026.10.5-release-1b58cb9a1b4f-…` |
| App | `/Applications/OpenClaw.app` (`ai.openclaw.mac`, Team `FWJYW4S8P8`) |
| Config | `~/.openclaw/openclaw.json` |
| Gateway | PID enfant de `OpenClaw.app` (processus responsable = l'app) |
| État partagé | `~/.openclaw/state/openclaw.sqlite` |

## Agents

| id | Nom | Workspace | Modèle |
| --- | --- | --- | --- |
| `main` | Pro | `~/.openclaw/workspace` | `omlx/…Qwen3.6-35B-A3B-4bit` |
| `perso` | Perso | `~/.openclaw/workspace-perso` | idem |

`technique` a été fusionné dans Pro pendant la préparation (2026-10-20) : le
paquet ne cible plus que deux agents.

## Fichiers de workspace existants

- Perso : `AGENTS.md`, `USER.md` (placeholder), `SOUL.md`, `IDENTITY.md`, `DREAMS.md`, `memory/`, `skills/`.
- Skills Perso : `coordination-agents`, `gmail-perso`, `imessage`, `perso-bookstack`, `recherche-web`.
- Pro : mêmes fichiers de base ; `USER.md` également en placeholder.

## Outils Contacts existants

- **Aucun outil Contacts côté agent.** Le plugin stock `apple-fm` ne concerne pas Contacts.
- Le nœud macOS appairé (`openclaw-macos/node`) déclare `contacts.search` dans sa
  politique de plateforme, mais l'invocation réelle échoue :
  `node command not allowed: the platform macOS 27.0.1 does not support "contacts.search"`.
  → **non réutilisable**.
- `imsg` 0.17.0 ne fournit pas de résolution de contacts exploitable en CLI.
- Aucune commande système `contacts` n'existe sur ce Mac.

## Accès Contacts réel

| Contexte | Résultat |
| --- | --- |
| Terminal / VS Code (processus responsable = VS Code) | `authorized` |
| Binaire nu lancé par `launchd` | `notDetermined` |
| Binaire dans un bundle **sans** `NSContactsUsageDescription` | `denied` (CNError 100) |
| Helper `.app` signé ad-hoc **avec** `NSContactsUsageDescription`, lancé via LaunchServices | `authorized` |

Conclusion : l'autorisation TCC suit le **bundle responsable**. Un binaire nu
hérite de l'autorité du terminal, ce qui ne prouve rien pour le Gateway.

Carnet accessible : **1 conteneur**, `iCloud` (type `carddav`), 226 fiches.

## SMS / iMessage

- Canal `imessage` activé, `cliPath=/opt/homebrew/bin/imsg`, `dmPolicy=disabled` (sortant seul).
- `imsg send` accepte `--to`, `--text`, `--service imessage|sms|auto`, `--json`.
- **`--message` n'existe pas** (le skill `imessage` du workspace Perso l'indique à tort).
- Allowlist exec de Perso : `/opt/homebrew/bin/imsg` et `/opt/homebrew/Cellar/imsg/*/bin/imsg` déjà présents.
- Lecture de `chat.db` refusée depuis VS Code (FDA manquant) : sans effet sur l'envoi.

## Mail personnel

- `gog` 0.45.0, compte `florian@gangneux.org`, allowlist exec Perso déjà présente.
- `gog gmail send` dispose de `--dry-run`, `--attach`, `--body-file` : envoi et
  pièces jointes réellement possibles.

## Documents

- Plugin `bookstack-perso` activé (outils `bookstack_*`), skill `perso-bookstack`.
- `bookstack_*` est refusé à Pro (`tools.deny`) : isolation déjà en place.

## Isolation constatée (avant modification)

| Point | État |
| --- | --- |
| `tools.sessions.visibility` | `all` (défaut) → **chaque agent peut lister/lire les sessions des autres** |
| `tools.agentToAgent` | activé, sans `allow` → **tous les agents peuvent se solliciter** |
| `sessions_send` / `sessions_list` / `session_status` | autorisés aux deux agents |
| `exec` | allowlist par agent, mais `osascript` en `safeBins` global |
| Lecture de `workspace-perso` depuis un contexte type Gateway | **possible** (`osascript` → `do shell script` → `head`) |

Conséquence : un dossier séparé et des permissions 600/700 **ne constituent pas**
une isolation contre un agent disposant d'`exec`. Voir [ARCHITECTURE.md](ARCHITECTURE.md#limites-disolation).
