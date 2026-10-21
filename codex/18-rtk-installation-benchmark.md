# RTK — installation et qualification du 21 octobre 2026

État global : **NON ACTIVE**. RTK reste disponible manuellement.

## Installation et audit

- RTK 1.0.1 installé par `HOMEBREW_NO_AUTO_UPDATE=1 brew install rtk`, formule `homebrew/core`, source officielle `rtk-ai/rtk` tag v1.0.1 ; bottle Apple Silicon.
- Binaire : `/opt/homebrew/bin/rtk` → `/opt/homebrew/Cellar/rtk/1.0.1/bin/rtk`.
- Codex CLI 0.160.0 ; fonctionnalité `hooks` stable et activée dans le CLI.
- Aucun service ni dépendance d'exécution ajouté. Télémétrie RTK désactivée par défaut ; historique local RTK créé par les commandes de benchmark via l'interface officielle.
- Configuration globale Codex inspectée sans afficher ses secrets ; MCP déclarés : n8n-mcp, local_llm, node_repl. Politique de délégation préservée.
- Aucun changement de modèle, raisonnement, contexte, backend, MCP, OpenClaw ou projet métier.
- Nombreuses modifications préexistantes dans le dépôt : préservées, aucun commit ni staging effectué.

## Benchmark borné

Dépôt mac-ia-local consulté en lecture seule. Les tests `unittest` du témoin ont été lancés avec `-B` ; aucun test d'infrastructure ou de base de données. Captures et mesures : `artifacts/rtk-20261021/` (ignoré par Git). Les commandes exactes et leurs codes de sortie sont dans `benchmark.json` ; copie versionnable adjacente au rapport.

Tokenizer absent de Python système : estimation uniforme **octets UTF-8 / 4**, sans installation supplémentaire. Ce n'est pas un comptage exact des tokens Codex. Les pourcentages sont donc des réductions d'octets, identiques à celles de cette estimation. Une mesure de temps par commande : indication locale, pas statistique de performance.

| Cas | Octets natifs | Octets RTK | Tokens estimés natifs → RTK | Gain | Temps natif → RTK |
|---|---:|---:|---:|---:|---:|
| status | 5952 | 4584 | 1488.0 → 1146.0 | 22.98 % | 16.08 → 35.23 ms |
| diff | 699 | 679 | 174.8 → 169.8 | 2.86 % | 8.63 → 20.22 ms |
| log | 2866 | 1229 | 716.5 → 307.2 | 57.12 % | 8.18 → 12.77 ms |
| rg | 409 | 409 | 102.2 → 102.2 | 0.00 % | 8.35 → 11.82 ms |
| ls | 1938 | 802 | 484.5 → 200.5 | 58.62 % | 9.86 → 11.62 ms |
| tests | 230 | 125 | 57.5 → 31.2 | 45.65 % | 37.69 → 38.41 ms |
| logs | 2232 | 387 | 558.0 → 96.8 | 82.66 % | 2.48 → 6.55 ms |

Moyenne arithmétique : **38,56 %** ; réduction pondérée par volume : **42,66 %**. Surcoût observé : environ 0,7 à 19,2 ms par commande. Pas de dégradation sensible sur cet échantillon, sans preuve sur gros volumes. Aucune économie de session Codex complète mesurée.

## Qualité et compatibilité

- `git status` : états et chemins de l'échantillon visibles, dont états mixtes index/travail.
- Diff borné AGENTS.md : ajout et contexte présents ; ce contrôle ne qualifie pas les gros diffs ni la fidélité patch. Pour un diff exact, utiliser Git natif ou bypass.
- `git log -5` : commits et sujets présents ; corps de messages partiellement omis, avec indication du nombre de lignes.
- `rg` : sortie identique sur le petit témoin ; aucun gain. Les limites documentées ne sont pas qualifiées sur de gros résultats.
- `ls -la codex` : noms et permissions numériques présents ; propriétaire, groupe et dates retirés. Adapté à l'exploration simple, insuffisant pour certains audits.
- Témoin : 2 tests réussis dans les deux parcours ; RTK retire les noms des tests.
- Journal existant de tests : `rtk log` tronque `TEST_HOOK_FAILURE` et `SIMULATED_TRANSPORT_ERROR`, classe un test réussi contenant « error » comme erreur et omet le bilan `24 pass / 0 fail`. Aucun chemin de récupération annoncé dans cette sortie. **Perte de contexte diagnostique constatée.**
- Test d'échec isolé et temporaire : code 1 conservé, assertion et stack trace absentes de la sortie initiale ; chemin `rtk recall` présent. Récupération intégrale vérifiée, incluant `RTK_DIAGNOSTIC_SENTINEL`. Fichier de test temporaire supprimé automatiquement.
- `rtk bypass git diff -- AGENTS.md` comparé octet par octet au diff natif : identique.
- Hook officiel appelé avec payload Codex et `permission_mode=default` : `git status` devient `rtk git status` via `updatedInput`. Commande incompatible et bypass : aucune réécriture. Premier essai sans permission_mode : sortie vide attendue selon la documentation ; ce n'était pas une preuve d'incompatibilité.
- Aucun accès MCP exécuté : aucun fichier MCP modifié et aucun hook installé ; disponibilité fonctionnelle des services **non retestée**, car aucune activation n'a eu lieu.

## Décision

Les gains dépassent la cible de 25 %, mais sont variables (0 à 82,66 %) et la qualité diagnostique n'est pas préservée uniformément. Le texte d'awareness par défaut proposé par RTK demande de traiter la sortie condensée comme complète et de ne contourner qu'en cas de résultat inutilisable ; cela ne répond pas à l'exigence de détail natif préventif pour les investigations complexes. Pas d'activation globale.

Méthode officielle évaluée uniquement : `rtk init -g --codex`, hook natif `PreToolUse` matcher `Bash`. Dry-run exécuté, aucune écriture d'intégration. Codex impose la confiance explicite des nouveaux hooks via `/hooks` ; aucune confiance interne manipulée, aucun contournement utilisé. Pas de nouvelle session de validation d'activation, puisque l'activation est rejetée.

## Utilisation et retour arrière

- Usage manuel : `rtk git status`, `rtk git log -5`, `rtk ls codex`.
- Diagnostic complet : commande native ou `rtk bypass <commande>`.
- Économies : `rtk gain`, détails `rtk gain --history`, export `rtk gain --format json`.
- Premier relevé RTK après les 7 cas : 3444 tokens estimés en entrée, 2056 en sortie, 1388 économisés (40,30 %). Estimateur interne distinct ; cohérence d'ordre de grandeur avec 42,66 % d'octets. Les contrôles ultérieurs ajoutent leur historique. Aucune économie financière ou de quota démontrée.
- **Fichiers de configuration modifiés : aucun.** Aucun backup nécessaire, aucune restauration de config à effectuer. `~/.codex/hooks.json` et `~/.codex/RTK.md` absents au contrôle final. Empreintes finales dans `artifacts/rtk-20261021/final-state.json`.
- Désinstallation de l'installation actuelle : `brew uninstall rtk`. L'historique local peut être conservé ; sa remise à zéro, si souhaitée, passe par `rtk gain --reset` avant désinstallation.
- Si une intégration officielle est installée ultérieurement, désactivation documentée : `rtk init -g --codex --uninstall`, puis redémarrage de Codex. Ce chemin n'a pas été exercé ici et ne constitue pas une restauration testée.

## Sources officielles

- [RTK v1.0.1 : intégration Codex, limites de classification et modes de permission](https://github.com/rtk-ai/rtk/blob/v1.0.1/hooks/codex/README.md)
- [RTK v1.0.1 : agents supportés](https://github.com/rtk-ai/rtk/blob/v1.0.1/docs/guide/getting-started/supported-agents.md)
- [Documentation OpenAI : hooks et confiance](https://learn.chatgpt.com/docs/hooks)
