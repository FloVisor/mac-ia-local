# Stabilisation de l'installation habituelle - 2026-10-02

## Binaire et serveur habituel

- Artefact qualifie conserve, sans reconstruction :
  `/Users/fngux2/codex-ollama-maintenance/artifacts/ollama-v0.35.0-pr18413-release`
- Copie installee :
  `/Users/fngux2/.local/lib/ollama-codex-patched/v0.35.0-pr18413/ollama`
- SHA-256 observe :
  `b2c89a64969dd7ddf23be36c442d2d93a65f80bb0cd94b874caba2d93ac1e9a8`
- LaunchAgent : `org.gangneux.ollama-serve`
- Configuration : `RunAtLoad=true`, `KeepAlive=true`, `OLLAMA_HOST=127.0.0.1:11434`.
- Redemarrage cible le 2026-10-02 a 22:39:30 +0200 : ancien PID 29262, nouveau PID 43292.
- Apres le redemarrage, le PID 43292 ecoute sur 127.0.0.1:11434, l'API annonce 0.35.0 et le modele `qwen3.6:35b-coding` est catalogue.
- Controle differe de 10 secondes : meme PID, job `running`, `last exit code=0`, port toujours ouvert.
- Controle final apres la tentative VS Code : PID 43292 et meme SHA.

## Concurrence avec Ollama.app

- Le processus principal `/Applications/Ollama.app/Contents/MacOS/Ollama` n'etait pas actif pendant et apres le redemarrage cible.
- Le job `com.ollama.ollama` encore enregistre est le composant Squirrel de mise a jour ; il etait `not running`, avec `last exit code=0`.
- Aucun reglage utilisateur documente n'a ete trouve pour interdire seulement le serveur de l'application tout en conservant son mecanisme de mise a jour.
- Ce job n'a donc pas ete desactive et l'application n'a pas ete supprimee.
- Conclusion : la concurrence est resolue dans l'etat courant et le LaunchAgent reprend correctement 11434 apres redemarrage cible, mais le risque de recurrence lors d'une relance future de l'application ou apres une mise a jour n'est pas elimine par une politique persistante distincte.

## Temoin isole termine

- Conversation : `01a0fe46-2917-7843-b184-5f33f8875833`.
- Preuves : `diagnostics/reconciliation-20261002/isolated-high-mcp/`.
- Premier tour : un seul `n8n_health_check` reussi, reponse finale `OLLAMA_0351_MCP_OK`, `agent_message`, fichier final et fin de tour coherents.
- Suivi dans la meme conversation : `OLLAMA_0351_FOLLOWUP_OK: OLLAMA_0351_MCP_OK`, sans second appel MCP.
- Duree mesuree du premier tour, de `task_started` a `task_complete` : **410,236 secondes**, soit **6 min 50,236 s**.
- Le port 11435 est ferme et la session de lancement n'existe plus.
- Les deux cles temporaires creees dans `isolated-home/.ollama/` le 2026-10-02 a 22:19:35 +0200 ont ete supprimees.

## Validation VS Code

### Observe dans `witness-a`

- Le panneau Codex utilise la configuration utilisateur commune et le mode `Work locally`.
- Le selecteur contient `qwen3.6:35b-coding` ainsi que les modeles cloud.
- `qwen3.6:35b-coding` a pu etre selectionne.
- Le bouton a toutefois conserve l'affichage `Medium`.
- Les actions d'accessibilite puis un acces direct a la zone d'effort n'ont pas affiche le choix attendu `None`/`High`.

### Non valide

- `None` et `High` uniquement dans VS Code.
- `None` par defaut dans un nouveau fil.
- Tour High avec MCP puis reponse finale dans VS Code.
- Suivi dans le meme fil VS Code.
- Bascule locale vers cloud puis retour local.
- Deuxieme workspace distinct.

La tentative UI a ete arretee apres absence de progression, conformement a la consigne. Aucune configuration metier de workspace n'a ete modifiee.

## Geste manuel restant

1. Dans la fenetre VS Code `witness-a`, ouvrir la palette de commandes et executer `Developer: Reload Window`.
2. Creer un nouveau chat Codex.
3. Ouvrir le selecteur, choisir `qwen3.6:35b-coding`, puis verifier que l'effort propose uniquement `None` et `High` et que `None` est actif sans choix explicite.
4. Selectionner `High`, lancer exactement un `n8n_health_check`, verifier la reponse finale, puis envoyer un suivi dans le meme fil.
5. Basculer vers un modele cloud, effectuer un tour court, puis revenir a `qwen3.6:35b-coding` et effectuer un tour court.
6. Refaire la verification dans `/Users/fngux2/codex-ollama-maintenance/witness-none`.

Si `Medium` reste affiche apres `Developer: Reload Window`, ne pas poursuivre les tests : capturer le selecteur et reexaminer le rafraichissement du catalogue commun avant toute autre modification.

## Sauvegarde et retour arriere

- Le binaire source qualifie reste conserve dans `artifacts/`.
- Le binaire installe est isole dans un repertoire versionne.
- Sauvegardes de LaunchAgent presentes :
  - `~/Library/LaunchAgents/org.gangneux.ollama-serve.plist.bak-20260922T111626`
  - `~/Library/LaunchAgents/org.gangneux.ollama-serve.plist.bak-20261002-103613`
  - `~/Library/LaunchAgents/org.gangneux.ollama-serve.plist.bak-before-origins-20260920-231114`
- Retour arriere : restaurer la sauvegarde de plist retenue, recharger le job utilisateur, puis verifier explicitement le chemin, le SHA et le proprietaire du port 11434.
