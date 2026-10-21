# Validation de cohérence — 21 octobre 2026

Rapport : [codex/30-routing-coherence.md](../../codex/30-routing-coherence.md).
Les captures antérieures restent intactes. Aucun secret publié.

- MCP existant : 87 tests PASS ; nouveaux tests contexte : 7 PASS.
- Adaptateur : 24 tests PASS. Témoins : 2 PASS.
- OpenClaw : capture du transport installé PASS pour main/perso et six niveaux,
  sans réseau. Minimal désactivé. Rechargement natif ok, sans redémarrage requis.
- Santé OpenClaw après rechargement : ok, `plugins.errors=[]`, reload actif.
  Ancienne instance occupée : avertissement de nettoyage différé conservé.
- DIRECT réel local : HTTP200 completed, exact OK, entrée20, sortie1,
  reasoning0. Appel LiteLLM `0984b3e1-0be8-4dc9-bc46-d5708148e259`, déploiement
  `17720d29-9da3-4888-aef8-f6db0cc5bd96`, retries0/fallbacks0.
- DIRECT trop grand : HTTP400 `context_budget_exceeded_return_to_codex`,
  aucune donnée tronquée ni appel amont dans cette branche du handler.
- MCP réel : catalogue et récupération d'une délégation locale effectués.
  Tâche completed `f2d075e8-a7a3-4984-a1fb-0bfee9db948d` ; résultat métier
  incorrect rejeté. Ne pas assimiler completed à une validation de qualité.
- LiteLLM distant : SHA256 config
  `2e582383979656e6dc82468e58dd7999c53c2bcb4b723db2a68e24ced9bccf5b`,
  callback `00769a6e6959219570edd81c75ce0ba9556a9ba374ae39ed7425a9ede31132d3` ;
  correspondent aux sources du dépôt. Aucun déploiement distant.
- FreeLLMAPI : source de boucle native lue en SSH, limite par défaut20,
  budget par défaut45000ms, cooldowns et Retry-After ; configuration runtime
  du budget et chaîne multi-échec NOT_RUN.
- CLI : construction de la commande PASS, génération CLI NOT_RUN.
- Grands contextes réels, stress, quota distant et paiement NOT_RUN.

Préimages, résultats JSON et contrôles de préservation privés :
`artifacts/routing-coherence-20261021/`. Aucun commit/push.
