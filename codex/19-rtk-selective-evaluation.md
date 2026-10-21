# RTK — politique sélective, 21 octobre 2026

**Activation globale : NON ACTIVE.** Essai natif non concluant, configuration initiale restaurée et vérifiée.

## Périmètre et résultats réutilisés

RTK 1.0.1, Codex CLI 0.160.0. Benchmark du [rapport 18](18-rtk-installation-benchmark.md) réutilisé sans relancer ses commandes, tests ou logs. Gains antérieurs : status 22,98 %, log 57,12 %, ls 58,62 % ; moyenne de ces trois cas 46,24 % (estimation octets/4), sans mesure d'économie d'une session entière. Le gain historique global de 38,56 % inclut les commandes désormais exclues de la politique souhaitée.

## Politique évaluée

- Automatique souhaité : commandes simples `git status`, `git log`, `ls`.
- Natif par défaut : toute autre commande, notamment diff, rg, tests, logs et diagnostics ; commandes composées et redirections également natives.
- Logs : aucun automatisme ; une synthèse peut être demandée explicitement, en conservant le journal brut comme référence. Le filtre `rtk log` n'est pas qualifié pour garantir les détails critiques.
- `rtk bypass`, `rtk recall`, `RTK_DISABLED=1` : rester accessibles.

## Mécanismes examinés et essai court

La documentation de RTK 1.0.1 expose `[hooks].exclude_commands`, mais signale des exceptions pour certaines formes head/tail : une liste noire serait insuffisante pour une liste d'autorisation stricte et durable.

Le mécanisme pipeline natif expose `command_matches`, `action = "rewrite"` et `action = "passthrough"`, avec première règle correspondante gagnante. Un unique pipeline utilisateur macOS a été essayé, autorisant uniquement les trois familles ci-dessus par regex ancrée, puis imposant passthrough à tout le reste. `rtk pipeline validate` le reconnaît ; l'affichage résolu place bien les règles utilisateur avant le rewrite par défaut. Avertissement W001 attendu : rewrite hérité inatteignable selon cet affichage.

**Mais `rtk hook codex` ne respecte pas cette sélection dans le test direct.** Payload conforme avec `hook_event_name=PreToolUse`, `tool_name=Bash`, `permission_mode=default` et `tool_input.command`. Le résultat observé est :

| Commande demandée | Politique attendue | Résultat du hook |
|---|---|---|
| `git status` | RTK | `rtk git status` |
| `git log -5` | RTK | `rtk git log -5` |
| `ls -la codex` | RTK | `rtk ls -la codex` |
| `git diff` | Natif | `rtk git diff` |
| `rg error .` | Natif | `rtk rg error .` |
| `python3 -m pytest` | Natif | `rtk pytest` |
| `tail -n 20 app.log` | Natif | `rtk read app.log --tail-lines 20` |
| `cat app.log` | Natif | `rtk read app.log` |
| `git status && python3 -m pytest` | Natif | `rtk git status && rtk pytest` |
| `ls; git diff` | Natif | `rtk ls; rtk git diff` |
| `rtk bypass git status` | Natif | `native / aucune réécriture` |
| `rtk recall d06e82f6cf1e` | Natif | `native / aucune réécriture` |
| `RTK_DISABLED=1 git status` | Natif | `native / aucune réécriture` |

La sortie du hook contient `updatedInput` pour les commandes sensibles : cela suffit à invalider la politique avant toute installation dans Codex. Les commandes de tests/diagnostics du tableau n'ont pas été exécutées ; seuls leurs payloads ont été présentés au hook. La conservation des diagnostics par ce candidat est donc **non validée**. Les preuves de bypass et recall du rapport 18 restent réutilisées ; absence de réécriture de ces deux commandes confirmée ici.

Le code tagué v1.0.1 de `src/hooks/hook_cmd.rs`, `process_codex_payload`, appelle directement `decide_hook_action(... Host::Codex)`. Le constat déterminant reste le résultat du binaire installé ; aucune correction RTK ni wrapper ajouté.

L'installateur refuse aussi `rtk init -g --codex --hook-only` avec `--codex cannot be combined with --hook-only`. L'activation complète de l'installateur aurait ajouté sa référence d'awareness à AGENTS.md. Aucun changement de ces instructions n'a été appliqué. Les hooks Codex natifs sont connus du rapport 18 ; leur confiance doit passer par le mécanisme officiel, aucune confiance contournée ici.

## État effectivement livré et retour arrière

- Automatisation : **aucune**. Toutes les commandes restent natives sauf préfixe RTK explicite.
- Usage manuel pertinent : `rtk git status`, `rtk git log -5`, `rtk ls codex`.
- Détail intégral : commande native ou `rtk bypass <commande>` ; récupération existante : `rtk recall <hash> --full`.
- Statistiques manuelles : `rtk gain`. Aucun gain automatique nouveau constaté.
- Pipeline d'essai retiré ; sa copie et les résultats sont dans `artifacts/rtk-selective-20261021/`, ignoré par Git.
- Vérification SHA-256 avant/après : `~/.codex/config.toml` et `~/.codex/AGENTS.md` inchangés ; `~/.codex/hooks.json`, `~/.codex/RTK.md` et le pipeline utilisateur restent absents comme au départ. Les MCP et délégations n'ont pas été modifiés ni réinitialisés.
- Aucun hook installé, aucun proxy, service ou wrapper créé ; aucune désactivation supplémentaire nécessaire. Pour cesser l'usage manuel, utiliser simplement les commandes natives. Désinstallation optionnelle : `brew uninstall rtk`.
- Aucun commit, staging ou modification de projet métier.

## Conclusion et prochaine étape minimale

La politique demandée ne peut pas être déclarée appliquée avec le parcours natif testé dans RTK 1.0.1. Une version corrigeant la prise en compte de passthrough dans le hook Codex, ou une liste d'autorisation native explicitement supportée sur ce parcours, permettrait un nouveau test ciblé. Aucun remplacement par une interception personnalisée n'est effectué.

Sources : [configuration RTK 1.0.1](https://github.com/rtk-ai/rtk/blob/v1.0.1/docs/guide/getting-started/configuration.md), [pipelines natifs](https://github.com/rtk-ai/rtk/blob/v1.0.1/docs/guide/pipelines/writing-pipelines.md), [hook Codex](https://github.com/rtk-ai/rtk/blob/v1.0.1/src/hooks/hook_cmd.rs), [hooks OpenAI](https://learn.chatgpt.com/docs/hooks).
