# Harmonisation des libellés Codex et OpenClaw — 21 octobre 2026

Mission exclusivement de présentation. P3-A/P3-B restent PARTIAL ; aucune reprise
P3-A, P3-B ou P3-C, aucun commit/push, aucune génération de test.

## Application

- Codex : `litellm-adapter/manage.py` génère les noms courts avec `display_name`.
  Exemples : `oMLX · Qwen3.6 35B`, `Ollama · Qwen3 4B`,
  `Free · Groq GPT-OSS 120B`, `Free · Mistral Codestral`, `Free · Task Coding`,
  `Paid · DeepSeek V4.1 Flash`, `Paid · GLM-5.3`.
  Les quinze alias actifs restent distincts ; l'ancien alias masqué est nommé
  `oMLX · Qwen3.6 35B (ancien)`. Les dix entrées GPT/Codex sont inchangées.
- OpenClaw : patch natif des seuls champs `models.providers.*.models[].name`.
  Noms courts, fournisseur amont conservé pour les six gratuits individuels ;
  les quatre pools gratuits portent `· pool`, sans leur inventer un fournisseur
  unique. Noms des modèles natifs : `Qwen3.6 35B` et `Qwen3 4B`.
- Aucun changement de plugin ou de `llm-router`/`local_llm`. Le générateur
  OpenClaw `openclaw/llm-router/catalogue.py` est un outil de prévisualisation
  uniquement ; il ne réécrit jamais les définitions existantes. Il reste inchangé.
  Les catalogues OpenClaw générés sont laissés à la gestion native de l'application.

## Regroupements et limites

Le contrat installé Codex ne propose pas de catégorie/section personnalisée
pour les entrées ; aucun support de regroupement personnalisé n'est établi.
La convention de noms demandée est donc appliquée sans patch du Desktop.
La [référence officielle](https://learn.chatgpt.com/docs/config-file/config-reference)
décrit `model_catalog_json`, chargé au démarrage ; le rendu à chaud n'est pas garanti.

OpenClaw regroupe nativement par identifiant fournisseur ; le composant installé
utilise `groupByProvider` et le nom obtenu par `fm(provider)`. Son schéma strict
`ModelProviderSchema` ne possède aucun champ fournisseur `name` ou `displayName`.
Les groupes restent donc `omlx`, `ollama`, `litellm-free-pro/perso` et
`litellm-paid-pro/perso`, avec la présentation native des fournisseurs connus.
Les alias LOCAL de LiteLLM restent dans leur fournisseur `litellm-free-*`.

Obtenir exactement quatre groupes oMLX/Ollama/Free/Paid imposerait de renommer
ou déplacer les identifiants fournisseurs/modèles et leurs références de
credentials, politiques et sessions, ou de modifier l'interface. **Non appliqué.**
L'alternative conservant tous les identifiants est celle livrée : groupes natifs
existants et noms courts précisant oMLX/Ollama pour les alias locaux du routeur.
Aucun fournisseur ni clé recréé.

## Contrôles

- Rapports P3-A/P3-B lus ; derniers tours des sessions correspondantes terminés.
  Aucun handle ouvert identifié sur les fichiers ciblés ; comparaison des
  préimages avant écriture. Le synchroniseur périodique utilise son verrou normal.
- Candidat de synchronisation comparé avant application : seules les valeurs
  `display_name` diffèrent ; routes et configuration adaptateur identiques.
- Après application : **26 entrées Codex, mêmes identifiants**, 16 libellés
  changés ; **32 définitions OpenClaw**, 32 noms changés, **17 modèles par agent**.
  Comparaison exhaustive OpenClaw : aucun autre champ changé.
- Défaut Codex `gpt-6.1-sol`, défaut Pro/Perso Qwen oMLX et référence de profil
  existante, utility model `ollama/qwen3:4b-instruct` identiques.
  Permissions, catégories, paramètres de raisonnement/contexte, routes et plugins
  identiques par comparaison structurelle ou empreinte.
- Sources/credentials/configurations protégés inchangés par empreinte ; budget
  et routes serveur non écrits. Pas de nouvelle qualification fonctionnelle.
- `openclaw config patch --dry-run` et `openclaw config validate` PASS.
  Deux tests `python3 -m unittest discover -s witness-a -q` PASS.
  Compilation Python PASS. Pas de délégation LLM : aucune génération autorisée.
- `model/list` du binaire Desktop lit les 26 entrées et leurs nouveaux noms ;
  `openclaw models list --agent main/perso --json` lit les noms courts.
  Aucun `turn/start`, aucune génération, aucun redémarrage de service.
- Gateway `health.ok=true`, aucune erreur de plugin ; adaptateur `/health=ok`.
- **NOT_RUN graphique** : inventaire d'interface vide (aucune app/navigateur).
  La fenêtre Desktop déjà ouverte peut garder son ancien catalogue jusqu'au
  prochain démarrage choisi par l'utilisateur ; aucun redémarrage forcé.

**VERIFIED : cycle automatique suivant observé**, timestamp postérieur au cycle
manuel, même révision et mêmes identifiants ; catalogue strictement identique au
candidat avec les nouveaux noms. LaunchAgent : dernier exit 0.
Le LaunchAgent conserve `StartInterval=300`, son programme et son enregistrement.

## Sauvegardes et rollback limité aux libellés

Préimages privées des seules configurations/sources concernées sous
`artifacts/selector-ux-20261021/` (ignoré par Git). Les captures existantes de
`diagnostics/` ne sont pas modifiées. Les configurations sauvegardées peuvent
contenir des données privées et restent locales.

`rollback-labels.py` dans ce répertoire : contrôle sans écriture PASS ;
`python3 artifacts/selector-ux-20261021/rollback-labels.py --apply` restaure les
libellés uniquement. Il refuse une source ou définition modifiée concurremment,
restaure la source des noms Codex sous le verrou existant, exécute le synchroniseur
normal (qui tient son manifeste), puis applique les noms OpenClaw par la CLI
native. Aucune restauration globale de configuration, aucune écriture directe
dans les états internes, aucune modification de route ou de credential.
Rollback réel NOT_RUN pour conserver les nouveaux noms. Après rollback, relire
les catalogues, les défauts et la santé comme après application.
