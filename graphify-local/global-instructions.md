
<!-- BEGIN GRAPHIFY LOCAL -->
## Graphify local — navigation multi-dépôts sans hook

- Skill officiel : `~/.agents/skills/graphify/SKILL.md`. Utiliser Graphify pour architecture, appelants, dépendances, impact et tests associés quand cela évite des lectures ; ignorer pour tâches simples, fichier connu, git status ou quelques lignes.
- Ces restrictions priment sur les usages génériques du skill : code uniquement, aucun LLM ni Cloud, aucun graphe global/fusion entre projets, aucun hook Git/PreToolUse, aucun MCP supplémentaire. Ne pas lancer la pipeline sémantique du skill.
- Depuis le dépôt concerné, `~/.local/bin/graphify-local refresh` crée/actualise incrémentalement son `graphify-out/` via l'installation uv unique. Premier usage d'un autre dépôt : lire ses instructions, vérifier ses exclusions puis initialiser ce dépôt uniquement ; ne jamais indexer le parent commun. Ajouter `/graphify-out/` à son .gitignore si nécessaire.
- Chaque worktree conserve son propre graphe ; la commande verrouille les accès, refuse un graphe copié d'une autre racine, exclut dépôts imbriqués, secrets, caches et dépendances. Respecter .gitignore et .graphifyignore ; compléter les exclusions spécifiques avant indexation.
- Réutiliser le graphe ; actualiser après changement de branche/HEAD et lorsque les sources pertinentes ont changé, y compris modifications non committées. Pas de reconstruction intégrale ni d'indexation à chaque demande. Aucun --force.
- Interroger avec `graphify-local query "question"` (budget 1500), `graphify-local explain "symbole"` ou `graphify-local path "A" "B"`. La commande fixe GRAPHIFY_BACKEND=none et le graphe du dépôt courant. Ne pas utiliser --global, merge, add URL, push ou extraction sémantique.
- Les relations statiques (EXTRACTED/INFERRED) orientent l'analyse ; vérifier fichiers/lignes et lire les sources pertinentes avant toute modification sensible. Le graphe ne prouve pas le comportement réel et ne remplace pas les tests.
- RTK reste réservé aux commandes prévues par sa section. Ne modifier ni llm-router/LiteLLM/oMLX, ni les paramètres Codex, ni P3-C/Standup pour Graphify.
<!-- END GRAPHIFY LOCAL -->
