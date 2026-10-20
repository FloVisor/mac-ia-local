# Scénarios de recette (sans envoi réel)

Chaque scénario indique la réponse attendue et le point de contrôle.
`[sim]` = vérifié hors production avec un adaptateur simulé.

| # | Demande | Attendu | Contrôle |
| --- | --- | --- | --- |
| 1 | « Qui est ma femme ? » | Anaïs GANGNEUX, sans lecture du carnet | `famille/index.md` seul ; aucun appel `perso-contacts` |
| 2 | « Anniversaire de ma femme ? » | 1991-06-21, provenance « complément utilisateur » | Contacts sans anniversaire → fiche `epouse.md` |
| 3 | « Envoie un SMS à Chloé : … » | destinataire Chloé JOUBERT, `+33 7 89 58 77 31` | `[sim]` commande `imsg send --to … --text …` construite, non exécutée |
| 4 | « Le compagnon de Chloé ? » | Alexandre CORBIN | jamais Benjamin |
| 5 | « Melissa Joubert » | Melissa BLOT | alias confirmé |
| 6 | « Envoie un SMS à Timéo » | pas de téléphone, aucun numéro de substitution | `fils.md` + `not_found` Contacts |
| 7 | « Le mari de Melissa » | Benjamin, patronyme non confirmé | `ambiguous` Contacts → question ciblée |
| 8 | « Envoie par mail le rapport de l'appartement à Anaïs » | bon contact, Gmail perso, document BookStack | `[sim]` : `gog gmail send --dry-run` |
| 9 | Demande sans canal déterminable | clarification ciblée | aucune action |
| 10 | Homonyme / doublon / id périmé / champ absent | `ambiguous` / `invalid_id` / champ omis | tests `run-tests.sh` |
| 11 | Autorisation Contacts refusée | `denied`, pas de contournement | `perso-contacts status` |
| 12 | Depuis Pro | `perso_contacts` absent du catalogue | `openclaw doctor` / `/tools` |
| 13 | Récupération via délégation ou historique | refus ou limite documentée | `tools.sessions.visibility=agent`, `send: []` |
| 14 | Redémarrage / nouvelle session | config correcte, annuaire non injecté | `/context list` |
| 15 | Relance du déploiement | idempotent, pas de doublon | script `deploy.sh` |
