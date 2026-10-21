---
name: serena
description: Analyse sémantique en lecture seule des dépôts Git autorisés sur docker-02 avec Serena (symboles, fonctions, classes et références). Codex et OpenClaw Pro uniquement ; exclu du profil Perso.
---

# Serena — dépôts centralisés

Utiliser Serena pour retrouver précisément des symboles et leurs références via les serveurs de langage. Utiliser Graphify local pour une vue d'architecture, des dépendances ou chemins entre composants ; utiliser Git/rg natifs pour état, différences, historique, fichiers connus et recherches textuelles simples. Serena n'est pas un moteur de recherche vectorielle ni une preuve de comportement à l'exécution.

## Sélection et révision

Lire l'inventaire autorisé : `/Users/fngux2/Workspaces/mac-ia-local/infrastructure/deployments/serena/repositories.json`.
Chaque appel indique le nom complet `owner/repository`. Aucun projet actif implicite : l'adaptateur active le clone choisi au lancement d'un processus Serena dédié en contexte single-project ; les autres sessions ne peuvent pas changer son projet. Processus arrêté à la fin de l'appel, métadonnées conservées. Une seule analyse simultanée pour préserver docker-02.

Découvrir les noms exacts par le catalogue MCP. Codex : serveur `docker-mcp-gateway`. OpenClaw Pro : `tool_search` puis `tool_call`, identifiants `docker_gateway_pro__serena_*`, arguments sous `args`. Ne pas appeler le Skill comme un outil.

1. Appeler `serena_repository_status(repository="FloVisor/mac-ia-local")`. Relever branche, SHA et état propre.
2. `serena_find_symbol` : `repository`, `name_path_pattern` (ex. `Classe/methode`), `relative_path` si connu, `include_body` si nécessaire, `depth` pour les enfants.
3. `serena_symbols_overview` : `repository`, `relative_path`, `depth` pour les symboles d'un fichier.
4. `serena_find_references` : `repository`, `name_path`, `relative_path` pour les appelants/références sémantiques.
5. `serena_search_pattern` : `repository`, `substring_pattern`, `relative_path` pour une recherche textuelle ciblée ; ne pas la présenter comme une résolution sémantique.

Chaque résultat d'analyse porte le SHA réellement lu, vérifié avant/après. Vérifier les chemins et extraits dans le clone avant une conclusion importante. Résultat vide, erreur ou limite de langage = preuve insuffisante, pas absence certaine de code.

**Le clone distant ne contient pas les modifications non poussées du Mac**, ni ses modifications non committées. Comparer SHA local et distant ainsi que `git status` si l'analyse porte sur le travail actuel ; signaler explicitement la divergence et utiliser les outils locaux pour ce travail. Ne jamais demander un push pour contourner cette limite.

## Clonage et actualisation

Clones sous `/srv/docker-local/serena/repositories/{primary,secondary}/owner/repository`. Sept prioritaires prévus initialement, secondaires uniquement à la demande et si les droits existants permettent la lecture. Un dépôt vide ne peut pas être analysé.

Pour provisionner ou actualiser un dépôt autorisé, utiliser par SSH vérifié sur docker-02 le script `/srv/docker-local/serena/repository.py owner/repository [--update]`. Il interroge la branche par défaut GitHub réelle ; `--update` refuse modifications locales, commits locaux et divergence et n'autorise qu'un fast-forward. Actualiser seulement le dépôt utile avant analyse si une révision plus récente est nécessaire. Ne pas lancer de synchronisation globale ni de cron. Ne pas actualiser pendant une analyse.

Serena ne clone pas automatiquement et ne reçoit aucun identifiant GitHub. **Aucune modification de code sur les clones centralisés**. Aucun commit, push, `git reset --hard` ou `git clean`. Les sources sont montées en lecture seule, seuls caches et métadonnées dédiés sont inscriptibles.

Pour ajout hors des 13 dépôts, obtenir d'abord l'autorisation utilisateur puis suivre le rapport d'exploitation du déploiement. Ne jamais élargir les droits GitHub.
