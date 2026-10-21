# Compatibilité LiteLLM — reset long

Extension locale limitée à `litellm-free-pro` et `litellm-free-perso`, API
`openai-completions`, endpoint exact `https://litellm.gangneux.org/v1`.
Elle conserve le message amont et annote seulement la combinaison
`All models exhausted` + `rate-limited or on cooldown` + `Soonest reset` en
heures/jours. Le filtre natif OpenClaw reconnaît alors une limite longue.
L'estimation est attribuée à l'amont, jamais certifiée comme quota fournisseur.
Les erreurs temporaires ordinaires, les réponses et les autres providers restent
inchangés. Aucun retry, fallback, accès à un credential ni journal de prompt ajouté.

Cette adaptation compense le vocabulaire FreeLLMAPI non reconnu par OpenClaw
2026.10.5. Elle ne répare pas son estimation trompeuse de reset : les traces du
21 octobre montrent des refus locaux à 2 RPM, avec des succès intercalés, malgré
un reset annoncé à 17h. Un utilisateur peut réessayer après la fenêtre RPM ;
aucun polling automatique n'est ajouté.

Validation : `node openclaw/litellm-compat/verify.mjs`, hors réseau, avec le
classificateur natif de la version installée. Après mise à jour OpenClaw,
requalifier l'import de validation et retirer l'extension si le moteur reconnaît
nativement le message. Les imports versionnés concernent le test uniquement.

Installation : `openclaw plugins install CHEMIN --force --accept-capabilities`
après revue locale des sources ; activation native, sans patch du runtime.
Rollback : `openclaw plugins disable litellm-compat`.
