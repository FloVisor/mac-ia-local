# Limite Ollama — 2026-10-20

- PASS : LaunchAgent persistant `/Users/fngux2/Library/LaunchAgents/org.gangneux.ollama-serve.plist` : OLLAMA_MAX_LOADED_MODELS=2.
- PASS : RunAtLoad=true (démarrage à ouverture de session après reboot).
- KeepAlive=false conservé ; autres variables inchangées.
- PASS : bootout/bootstrap effectué ; service running avec limite 2.
- PASS : API /api/version : 0.35.0-pr18413-upstream.
- BLOCKED : test témoin pytest witness-a/ : No module named pytest dans .venv et Python système. Aucun paquet installé.
- NOT_RUN : reboot réel et essai de chargement simultané de deux modèles.
- Sauvegardes avant/après dans ce dossier. Captures antérieures non modifiées.
