# Interfaces préparées pour la phase 3 — aucune intégration effectuée

## Arbre d'activité

Le client futur conserve son identifiant de session et le transmet comme
`parent_session` de chaque tâche. `task_id` est produit par le worker.
`activity(after, limit)` alimente un arbre client/session → tâche → modèle ;
`status` reconstruit l'état courant, `result` récupère le contenu à la demande.
Aucune copie des prompts dans les événements. Le client gère un curseur et
resynchronise quand `history_truncated=true`. Polling compatible stdio, pas de
promesse de push ni d'événements MCP Tasks natifs non qualifiés avec les clients.
Une session parente déclarée sert à la corrélation, jamais à l'authentification.
Agent Standup et les extensions VS Code restent inchangés.

## DIRECT

Sélection explicite dans le catalogue natif Codex/OpenClaw, identité authentifiée
et habilitée au modèle/pool, clé dédiée à droits et budget contrôlés.
**Pas de confirmation supplémentaire à chaque appel.** Le client/catalogue de
confiance doit produire la sélection, le serveur vérifier l'identité et les droits.
Ni prompt ni champ `mode=DIRECT` envoyé au MCP ordinaire ne constituent une preuve.
`direct_selection()` décrit la validation attendue de données déjà authentifiées ;
elle ne les authentifie pas. Elle n'est pas exposée par MCP.

Identités/permissions DIRECT payantes distinctes des identités d'escalade MCP.
Plafond partagé existant **40 USD/mois**, équipe `paid-openrouter-shared`, inchangé.
Ne pas ajouter une confirmation globale LiteLLM qui intercepterait ce chemin.
Les éventuelles clés permanentes DIRECT appartiennent au client habilité et à
son stockage sécurisé, jamais au worker MCP ordinaire.

## DELEGATED

Une proposition payante est un refus d'exécution tant que le courtier et une
confirmation native ne sont pas raccordés. La tâche expose modèle exact,
identifiant, motif, empreinte du périmètre de données, coût estimé/plafond et
budget restant ; les montants inconnus sont `null`, jamais considérés approuvés.
Dans l'implémentation actuelle le motif est structurel (`explicit_paid_candidate`),
pas une évaluation automatique fiable de qualité complexe.

Le futur adaptateur natif doit obtenir un accord humain pour tâche + modèle +
périmètre + plafond + expiration, puis appeler le courtier de confiance.
`Authorizations.issue/consume/revoke` sont des primitives internes : accord
obligatoire, liaison exacte, consommation atomique une seule fois avant appel,
refus de réutilisation, concurrence bornée à un gagnant. Aucun grant émis par
une déclaration du modèle. Refus/expiration/révocation ne donnent pas d'inférence.

La réserve `budget_remaining` passée à la primitive de test n'est **pas** une
preuve bancaire ni une réservation globale de budget. Le courtier réel devra
faire appliquer permissions, plafond de l'opération et budget partagé côté serveur
LiteLLM, et empêcher l'accès de son credential au worker. La procédure exacte
(credential éphémère ou inférence mandatée par un courtier privilégié) doit être
qualifiée sur les API réellement disponibles avant activation. Aucun contrôle
non démontré n'est présenté comme existant.

Un crash après consommation ne permet pas de réutiliser le grant ; résultat
incertain à réconcilier. Le courtier transmet uniquement métadonnées et résultat
au moteur de tâches existant. Pas de clé payante permanente dans son environnement
ordinaire. Les confirmations d'envoi Gmail/SMS/iMessage et plugins OpenClaw
ne sont ni modifiés ni concurrencés ; leur réutilisation native reste NOT_TESTED.

## Conditions de raccordement encore nécessaires

1. **VERIFIED le 21 octobre 2026 :** identité existante `mcp-delegate`, clé dédiée
   `llm-router-local-free`, 13 alias LOCAL/FREE explicites, aucun wildcard/PAID,
   catalogue exact et refus serveur 403 PAID/Muse-Glimmer/gestion. Lecture par
   `key_file` privé, aucun enregistrement client changé. Chemin réel local/gratuit
   et récupération asynchrone vérifiés ; les contrôles stricts des deux réponses
   gratuites ont échoué et restent enregistrés (voir VALIDATION.md).
2. Métadonnées actualisées, fenêtres et capacités vérifiées des routes individuelles.
   Pools autorisés seulement si tous leurs membres sont compatibles ; pas de
   copie d'un catalogue administratif comme permission.
3. Adaptateur natif de sélection DIRECTE authentifiée et de confirmation ponctuelle.
4. Courtier privilégié séparé, enforcement serveur du plafond opérationnel,
   dépenses et identité, testé sans coût puis éventuel test payant autorisé séparément.
5. Vérification de bout en bout des clients après nouvelle décision utilisateur.

Aucune de ces étapes n'autorise à changer maintenant Codex, OpenClaw, leurs
catalogues, les extensions, les budgets ou les fournisseurs.


## Précisions issues de la finalisation réelle

La clé ordinaire reste limitée à LOCAL/FREE, type `llm_api`, sans appartenance
à l'équipe payante. Sa possession ne confère ni sélection DIRECTE payante ni
permission d'escalade DELEGATED. Les permissions PAID exigent toujours des
identités/credentials distincts et un contrôle serveur ; pas de confirmation
LiteLLM globale ajoutée, pas de changement au plafond partagé de 40 USD/mois.
Les primitives d'accord restent préparées, aucune activation PAID réalisée.

Pour la supervision, `response_model` peut être un alias LiteLLM. Afficher
`actual_model=null` comme provenance non confirmée, puis permettre la corrélation
par `request_id` de complétion, `x-litellm-call-id` et `x-litellm-model-id`.
Le journal LiteLLM est recherché par le premier identifiant, pas par le call-id.
Le modèle fournisseur est confirmé séparément par les traces natives de routage ;
les pools exigent aussi la trace du membre effectivement choisi. Ne pas donner
au worker une clé de gestion pour alimenter cette interface : prévoir une lecture
opérateur autorisée ou une interface de métadonnées à droits minimaux.

Un résultat refusé par un contrôle objectif reste `failed`. Son contenu peut
être récupéré dans le stockage privé pour diagnostic, sans apparaître dans
`activity`. Les contrôles stricts ne sont pas assouplis pour faire passer un test.
La conformité des sorties gratuites observées n'est pas garantie par le succès
des API et restera un critère de recette des usages choisis ultérieurement.

## P3-B — état du 21 octobre 2026

Raccordement LOCAL/FREE OpenClaw par adaptateur à identité runtime, deux instances
privées et deux clés distinctes. Sélections DIRECT préparées séparément avec
credentials dédiés ; trois clés PAID rattachées au même budget existant.
DELEGATED PAID reste désactivé faute de courtier/plafond opérationnel démontré.
L'API native OpenClaw exécute et récupère une tâche locale ; la découverte et
l'appel autonomes dans le catalogue différé du modèle restent BLOCKED.
Voir [rapport P3-B](../../codex/21-llm-router-p3b.md) : il actualise les mentions
antérieures « aucune intégration » sans réécrire les preuves des phases précédentes.
Agent Standup inchangé ; P3-C non commencé.
