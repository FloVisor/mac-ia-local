# Capture de validation — Ponytail skill, 2026-10-21

- Installation native utilisateur : `/Users/fngux2/.codex/skills/ponytail`.
- Skill Creator : PASS ; découverte native 18 → 19, une occurrence active.
- Captures API factice, sans inférence : métadonnées seules au démarrage, +469 octets de texte ; corps principal injecté sur invocation explicite.
- Recette CLI réelle : deux déclenchements implicites ; contrôle DNS sans activation ; invocation explicite avec lecture de référence.
- Quatre sorties sur copies du collecteur : suites complètes PASS (20, 21, 19, 20 tests) ; 26 assertions indépendantes PASS ; autres définitions AST inchangées.
- Témoins : 2 tests PASS.
- Configurations protégées et collecteur réel inchangés ; aucun hook/plugin/routage direct ajouté.
- 401 : ancienne sonde urllib sans Authorization, aucun nouvel appel HTTP à oMLX ni essai d'authentification pendant la reprise. Aucune mauvaise configuration MCP démontrée.
- Desktop : NOT_RUN, interface non accessible ; aucun redémarrage.
- Pilote : mêmes +7 lignes de code ; B −6,35 % sortie, +16,82 % entrée cumulée et +13,67 % latence. Aucune économie globale démontrée.

Rapport : [34-ponytail-skill-integration.md](../../codex/34-ponytail-skill-integration.md).
Preuves locales : `artifacts/ponytail-skill-20261021/`, notamment `install-manifest.json`, `preservation.json`, `routing-evidence.json`, `activation.json`, `aggregate.json` et les événements/diffs A/B. Les captures existantes sont laissées intactes.
