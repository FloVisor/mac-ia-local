# RTK — déploiement sélectif parallèle à P3-C, 21 octobre 2026

## État livré

**Hook global installé, Trusted et Active dans Codex CLI 0.160.0.** RTK 1.0.1 conservé. Aucun changement de modèle, raisonnement, contexte, MCP, lanceur Codex ou composant P3-C. Aucun commit ni push.

État initial : rapports 18/19 existants ; aucun hooks.json ni configuration RTK utilisateur. Le MCP llm-router était déjà présent dans config.toml avec local_llm et node_repl. Le défaut du pipeline natif constaté au rapport 19 n'a pas été retesté.

La reprise autorise les hooks propres à RTK. Le déploiement utilise un sélecteur déterministe court, sans wrapper shell ni service : hook natif Codex PreToolUse/Bash, puis processeur officiel `rtk hook codex` seulement sur liste autorisée. Il s'agit d'une intégration locale, **pas du seul installateur RTK officiel**. Le sélecteur est maintenu dans ce dépôt ; toute extension exige un contrôle ciblé. Aucune délégation LLM pour la compression.

## Politique effective

- `git status` et seulement options `-s`, `--short`, `-b`, `--branch`.
- `git log`, compte court type `-5`, options `--oneline`, `--all`, `--graph`, `--decorate`.
- `ls`, options simples combinées `a/l/h`, chemins simples ; noms évoquant traces, sessions, Standup, llm-router, JSON ou logs exclus.
- Tout le reste reste natif : diff, rg, tests, logs, compilation, commandes système, formats machine, commandes composées, redirections, substitutions, wrappers, quoting et formes non reconnues.
- Les chaînes contenant shell ou données structurées ne sont pas interprétées par le sélecteur. Les appels MCP n'entrent jamais dans ce hook ; aucun PostToolUse ou hook de session n'est ajouté.
- Bypass : commande native non éligible, `rtk bypass <commande>` ou préfixe `RTK_DISABLED=1`. `rtk recall` reste disponible. Le stockage de récupération RTK reste dans sa configuration existante.
- La compression conserve les limites déjà documentées au rapport 18 : log Git abrégé, ls sans propriétaire/dates. Pour un audit exigeant ces détails, utiliser bypass.

## Fichiers

Sources : `codex/scripts/rtk-selective-hook.py`, `codex/scripts/rtk-manage.py`.

Déployés : `~/.codex/hooks/rtk-selective.py`, entrée RTK dans `~/.codex/hooks.json` (fichier absent initialement). Aucune configuration RTK globale modifiée.

`~/.codex/config.toml` : **entrée de confiance ajoutée par Codex via l'interface officielle `/hooks`**, non par édition interne. Vérification du SHA-256 du contenu antérieur hors section ajoutée : identique. AGENTS.md global inchangé. La fusion install/uninstall relit hooks.json et compare avant écriture ; conflit détecté = arrêt de cette écriture. Ne pas restaurer intégralement config.toml depuis une ancienne copie en présence de P3-C.

Preuves locales privées/non versionnées : `artifacts/rtk-deploy-20261021/` (baseline d'empreintes, tests, validation et copie originale vérifiée de config.toml, permissions 0600).

## Validation bornée

- **A — partiel :** vraie ouverture de Codex sans prompt modèle ; `/hooks` affiche PreToolUse Installed=1, Active=1, détail Trusted. Sélection testée par appel réel du hook installé : autorisés réécrits ; exclus/bypass/recall non réécrits. Pas de tour de modèle exécutant automatiquement une commande : **NOT_RUN**, aucune inférence payante.
- **B — technique PASS, boucle modèle NOT_RUN :** parcours déterministe hook → commande RTK retournée → exécution ; `ls` sur chemin absent restitue exactement le message natif et exit=1. Diagnostic Python exclu : traceback et marqueur complets, exit=1. Douze cas de sélection testés ; aucun benchmark antérieur relancé.
- **Rollback PASS isolé :** installation puis retrait préservent un hook tiers SessionStart et les autres clés JSON. Source déployée contrôlée dans les tests.
- **C — NOT_RUN :** aucune recette commune Agent Standup / délégation / sous-agents / provenance des traces. Coexistence **partielle**, limitée à la séparation des périmètres et à la préservation de config. Aucun code P3-C modifié ; aucune inférence ni sous-agent créé pour cette recette. Ne pas interpréter la session CLI de contrôle comme une détection Standup validée.

Gains : réutilisation du benchmark 18, environ 46,24 % de réduction moyenne estimée sur status/log/ls, selon octets UTF-8/4. Aucun gain de session complète ni nouveau gain automatique mesuré. `rtk gain` consulte les statistiques locales ; les commandes techniques de recette peuvent y figurer.

## Désactivation / rollback limité à RTK

1. Immédiat dans Codex : `/hooks` → PreToolUse → entrée `/usr/bin/python3 /Users/fngux2/.codex/hooks/rtk-selective.py` → désactiver. Ne pas désactiver d'autres entrées.
2. Retrait persistant : `python3 /Users/fngux2/Workspaces/mac-ia-local/codex/scripts/rtk-manage.py uninstall`.
3. Redémarrer les sessions qui avaient déjà chargé le hook. Le retrait supprime uniquement la commande RTK et son script ; conserve les hooks tiers et toutes les autres configurations. L'entrée de confiance historique éventuellement conservée par Codex est inerte sans hook enregistré ; ne pas modifier son stockage interne manuellement.
4. Aucun besoin de désinstaller RTK. Réinstallation : même script, argument `install`, puis revue dans `/hooks` si demandée.

Sources : [hooks officiels Codex](https://learn.chatgpt.com/docs/hooks), documentation et limites RTK référencées dans les rapports 18/19.
