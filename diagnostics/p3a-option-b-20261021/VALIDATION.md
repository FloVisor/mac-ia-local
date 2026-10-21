# P3-A option B — capture du 21 octobre 2026

Option B autorisée puis activée : adaptateur DIRECT loopback derrière le proxy
existant, synchronisation du catalogue LiteLLM toutes les cinq minutes.

- Desktop embarqué 0.163.0-alpha.10.2 accepte les quinze alias exacts.
- GPT-6.1-Sol défaut, GPT-6-Sol masqué, entrées GPT identiques.
- Six efforts Qwen : générations réelles et transmission des contrôles vérifiées ;
  Off/Minimal zéro token de pensée, quatre budgets capturés sur le trafic oMLX.
  Saturation des budgets : preuve de composant antérieure, pas de génération longue.
- Appel d'outil réel avec sortie P3A_TOOL_OK, code 0 et reprise du modèle.
- Mistral gratuit : génération Desktop réussie. Aucun appel PAID.
- Identité codex-direct, PAID équipe partagée 40 USD/1mo, spend 0, API native.
- Ollama : deux HTTP 400, dont un après correction de parallel_tool_calls.
  Arrêt de cette branche ; aucune troisième inférence.
- 9 tests nouveaux d'adaptateur, 2 de rollback et 2 témoins witness-a : PASS.
- Rollback actif testé, puis réactivation et synchronisation réussies.
- Config/auth Codex, local_llm, services moteurs et mapping OpenClaw inchangés.

**PARTIAL** : Ollama, rafraîchissement graphique à chaud, efforts cloud et
générations payantes non qualifiés ; référence Muse-Glimmer historique inchangée
dans l'auto-review pour préserver son comportement GPT.

Preuves filtrées sans secrets : `artifacts/llm-router-p3a/option-b/` (ignoré Git).
Rapport et procédure de retour arrière :
[codex/20-llm-router-p3a.md](../../codex/20-llm-router-p3a.md).
Aucun commit/push, aucune opération P3-C.
