# Observateur P3-C

Complément indépendant d’Agent Standup, sans dépendance npm. Vue **Explorateur →
Codex · agents et délégations**. Python 3 requis dans PATH. Clic sur une ligne :
métadonnées JSON ; boutons de titre : filtre (session/modèle/fournisseur/profil),
actualisation ; chevrons : arborescence. Les tokens, erreurs, transitions et coûts
connus figurent dans les détails. Les descriptions ne reprennent aucun prompt.

Le panneau affiche les sessions, sous-agents natifs et délégations llm-router dans
un arbre. Un parent absent reste une référence explicitement étiquetée ; aucune
session active n’est inventée. Le fournisseur Codex est déclaré par sa session,
pas prouvé au niveau de l’inférence. Le modèle exécuté et le fournisseur du routeur
restent inconnus : aucune jointure approximative par heure ni par alias. Le champ
`response_model` est informatif. Un coût inconnu reste null. Le marqueur historique
`legacy_mcp_observed` identifie local_llm séparément ; il ne prouve ni task ID ni
état de tâche récupérable. Connexion runtime : inconnue (lecture de journaux).

## Activation

```sh
python3 codex/agent-observer/package.py
"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" --install-extension artifacts/p3c-agent-observer-0.1.0.vsix
```

Ouvrir la vue depuis l’Explorateur, ou via **Affichage : Ouvrir la vue…**.
Si l’hôte ne recharge pas la nouvelle extension, **Developer: Reload Window**.
Développement sans installation : lancer VS Code avec
`--extensionDevelopmentPath=/chemin/absolu/codex/agent-observer`.

## Sources et limites

- `$CODEX_HOME/sessions`, sinon `~/.codex/sessions` : session_meta, turn_context,
  événements de tours et de tokens ; noms d’outils uniquement. Aucun titre utilisateur,
  prompt, réponse, argument d’outil, résultat ou clé affiché/conservé.
- Seul `~/.local/state/llm-router/codex/tasks.sqlite`, `mode=ro`, `query_only=ON` :
  projection de colonnes techniques et événements, sans request/output. Aucun
  Engine initialisé, worker lancé, API interrogée ou écriture au stockage applicatif.
  Ce format interne est une dépendance de compatibilité : schéma inconnu → erreur
  visible, aucune réparation. Pas une interface d’intégration officiellement stable.
- Jusqu’à 200 fichiers, 14 jours ; découverte toutes les 30 s, rafraîchissement
  toutes les 5 s lorsque la vue est visible. Lectures synchrones dans un processus
  Python indépendant ; fichiers inchangés servis par cache. Première ligne bornée
  à 2 Mio, début de corps 2 Mio et fin 512 Kio ; historique tronqué signalé.
- Historique routeur : 20 transitions par tâche, 200 tâches au plus. Reconstruction
  par identifiant au démarrage, sans journal parallèle ni fichier de supervision.
  Cache mémoire évincé automatiquement ; aucun historique exporté automatiquement.
- Un tour sans activité depuis cinq minutes devient unknown. Cela ne prouve pas
  un blocage ou un arrêt. États de tâche conservés : queued/running/completed/
  failed/cancelled/unknown ; cancel_requested est affiché unknown. La durée Codex
  porte sur le dernier tour observé, pas sur toute la conversation. Les tokens
  Codex sont le cumul déclaré, non attribués à une seule délégation.
- Un grand journal peut ne pas contenir le dernier turn_context dans la portion
  lue : `history_partial=true` impose de traiter le modèle comme une déclaration
  observée, non une preuve d’exécution actuelle. Les fichiers archivés/compressés
  et les sessions sans journal local sont hors fenêtre.
- Les erreurs libres sont masquées ; seuls quelques codes serveur connus passent.
  Aucun abonnement réseau, télémétrie, LLM ou coût d’inférence.

## Validation et rollback

`python3 -m unittest discover -s codex/agent-observer/test -v`.
Le test d’hôte `test/integration.js` utilise uniquement des traces existantes.
Rapport de mission : [23-agent-observer-p3c.md](../23-agent-observer-p3c.md).

Rollback par interface supportée :

```sh
"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" --uninstall-extension local-xithi.p3c-agent-observer
```

La désactivation depuis le panneau Extensions arrête le collecteur à la fermeture
de l’hôte concerné. Aucune restauration de configuration moteur/MCP/Standup.
Le VSIX est reconstruit depuis les sources ; ne pas éditer la copie installée.

OpenClaw futur : instances de collecte et vues séparées par identité authentifiée,
chemins explicites par agent, aucun accès partagé aux historiques Pro/Perso.
Aucun raccordement OpenClaw dans P3-C.

Historique MCP : les tâches du stockage source sont conservées sans filtre d’âge ni limite de 200 tâches ; les 20 dernières transitions sont exposées. Parent absent : corrélation uniquement par résultat structuré submit/delegate dans une session Codex unique, sinon tâche non rattachée. Voir `../28-agent-standup-p3c-delegation-history.md`.
