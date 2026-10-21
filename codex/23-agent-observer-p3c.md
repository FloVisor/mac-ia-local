# P3-C — Agent Standup, sous-agents et observabilité LLM

21 octobre 2026. **Résultat global : PARTIAL.** Complément indépendant installé
et validé dans un véritable hôte VS Code. Aucune génération, aucun commit/push.
Arrêt après P3-C. Aucune modification des moteurs, proxy, adaptateur, noms,
modèles, budgets, permissions, hooks, agents OpenClaw ou configuration MCP.

## Capacités et choix vérifiés

Agent Standup actif : **doublegeste.agent-standup 1.40.0**, registre
`~/.vscode/extensions/extensions.json` et liste native VS Code concordants.
1.39.0/1.39.2 sont aussi présentes sur disque, sans être les versions sélectionnées.
Dépôt déclaré : [Atoll92/agent-standup](https://github.com/Atoll92/agent-standup).
Licence MIT, fichier installé `LICENSE.txt`, copyright Arthur 2026.
Le `codex.js` installé est identique octet pour octet au main amont consulté.
Cela vérifie ce module ; le commit exact de construction du VSIX reste inconnu.

SHA-256 installés avant intervention :

- codex.js : `e0428bc73d24f5b5ab19439f5e149c28b32de8d5790b4e75bcb3592f1b22a46f`
- extension.js : `7fcd813b2aea70c5b970864b751d0f850e18c2b5a71ccfc61cb0ec5aa23152a7`
- server.js : `78ee743673d9fb9cd53027b01230faa9ef646f98a19e3fa820eb2b512854e0c7`

L’extension lit sessions JSONL et session_index depuis CODEX_HOME ou ~/.codex ;
scan mémorisé deux secondes, lecture bornée de la fin des fichiers, suivi de
plusieurs sessions et filtrage par dossier. Les états sont déduits des événements
de tours et de leur ancienneté, pas d’un abonnement au runtime.
Le parser lit turn_context.model et token_count. La liste `sessions()` exclut
explicitement `head.child` ; `boardRow()` renvoie subActive=0/subTotal=0.
Son README installé annonce également l’absence de sous-agents Codex.
Les personnages animés ne démontrent donc pas ce support.

**Option A non disponible dans la surface examinée** : manifeste, exports
activate/deactivate et routes serveur examinés ; aucun contrat d’enregistrement
externe ou d’injection de tâches. Les routes HTTP internes ne sont pas une API
plugin documentée. **Option B retenue** : extension complémentaire indépendante.
Aucun fork, patch de copie installée ou remplacement d’Agent Standup.

La [documentation OpenAI sur les sous-agents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
décrit les agents natifs ; les relations affichées ici viennent exclusivement des
métadonnées locales effectivement observées, sans assimiler un outil MCP à un agent.

## Versions réellement observées

| Composant | Version / preuve |
|---|---|
| VS Code | 1.142.0 arm64, CLI natif |
| Extension Codex VS Code | openai.chatgpt 26.51007.21434 |
| Journaux récents VS Code | originator=codex_vscode, cli_version=0.162.0-alpha.17.2 |
| CLI PATH | codex-cli 0.160.0 |
| Application bundle com.openai.codex | /Applications/ChatGPT.app ; 26.1013.40934, build 20770 |
| CLI embarqué Desktop | 0.163.0-alpha.10.2, Resources/codex-cli/bin/codex --version |

Le nom du bundle est ChatGPT.app malgré son identifiant com.openai.codex.
Compatibilité des formats de journaux observée ; aucune nouvelle conversation
Desktop, CLI ou inférence de recette. Formats futurs, sessions sans JSONL et
statuts natifs via app-server restent NOT_TESTED. Pas de lecteur SQLite Codex.

## Implémentation et vue

Sources : [agent-observer/](agent-observer/README.md). Extension locale
`local-xithi.p3c-agent-observer@0.1.0`, installée par `code --install-extension`.
VSIX : `artifacts/p3c-agent-observer-0.1.0.vsix` (non versionné).

Vue Explorateur **Codex · agents et délégations** : arbre repliable, modèle déclaré
ou alias, état et durée, filtre session/modèle/fournisseur/profil, détails JSON au
clic. Les détails exposent dates, identifiants, tokens, coût nullable, transitions,
code d’erreur filtré et disponibilité d’un résultat. Aucun contenu de résultat
n’est récupéré. Modèle fournisseur inconnu explicitement, connexion inconnue.

Extrait réel, sans titre utilisateur ni texte de tâche :

```text
Codex · vscode — parent 01a13a9b-ac78-7b00-86eb-a1a8ca464d78
  Sous-agent natif 01a13a9c-fae5-7b72-8f2e-e867f83f49af · gpt-6-astra · completed
  Sous-agent natif 01a13a9c-d5ca-7332-a1f1-cb2d34bccd92 · gpt-6-astra · completed
  Sous-agent natif 01a13a9c-ab14-7142-8b88-bfab2b8e2b7c · gpt-6-astra · completed
Session référencée · trace absente — 01a15de3-b087-75d2-bc09-b064732582a0
  llm-router / testing — 1e595a8e-9e9d-4553-8d18-7d38fee4949f
    failed · local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit
    10 796 ms · 37 tokens · coût null · objective_quality_failed
```

Les trois liens natifs sont présents dans session_meta.parent_thread_id ET
source.subagent.thread_spawn.parent_thread_id. Le modèle déclaré vient de
turn_context. Les noms personnels et prompts de rôle ne sont pas affichés.
La parenté routeur est **déclarative** (`meta.parent_session`), pas une identité
authentifiée du runtime. La session de recette P3-A n’a pas de journal dans la
fenêtre lue : référence explicite, aucun état/model/session réelle inventé.
Le MCP historique local_llm reste un marqueur distinct dans les métadonnées de
session si son nom d’outil est observé. Son état persistant est PARTIAL/non exposé.

## Lecture seule, provenance et confidentialité

Un processus Python séparé lit des portions bornées des JSONL, garde uniquement
la projection technique en mémoire et interroge le stockage Codex llm-router en
SQLite mode=ro + query_only=ON. Aucun Engine/worker initialisé. Aucune requête
LiteLLM/OpenClaw/FreeLLMAPI, aucun fichier de credentials lu, aucun deuxième journal créé.
Cette lecture non destructive est une dépendance au schéma interne actuel,
explicitement assumée et limitée ; ce n’est pas une API fournisseur stable.
Toute erreur de lecture devient visible, sans réparation de base ni écriture.

Le coût absent reste null. Alias et response_model ne prouvent pas le modèle
fournisseur ; actual_model et provider routeur restent inconnus. Les request IDs
sont visibles pour une future corrélation autorisée. Aucun accès administratif
ajouté. Pour Codex, provider est le fournisseur **déclaré de la session**, pas une
preuve du chemin réseau ou de l’inférence. Aucune déduction par timestamps.

Pas de prompts/réponses/arguments/outils complets, emails, contacts, clés ou tokens
d’authentification en sortie. Les messages d’erreur libres sont masqués ; seuls
quelques codes connus sont affichés. Les métadonnées au clic sont un document
VS Code non enregistré, aucune sauvegarde automatique par le collecteur.
Pas de serveur HTTP, fichier public, base supplémentaire, télémétrie ou LLM.
Protection des données : processus du même compte macOS, stockage source existant
privé ; ce dispositif n’est pas une frontière OS contre un processus du même UID.

## Actualisation et ressources

- Polling 5 s uniquement lorsque la vue est visible ; scan de découverte 30 s.
- Aucun abonnement natif aux sessions préexistantes établi ; polling borné retenu.
- 200 fichiers/14 jours, cache évincé, 200 tâches/20 transitions ; aucun historique
  persistant du superviseur à nettoyer. Conservation source inchangée.
- Lecture initiale de métadonnées 2 Mio max, corps initial 2 Mio + fin 512 Kio.
  Les journaux partiels sont signalés ; un modèle observé peut être ancien.
- Mesure ponctuelle sur 89 objets : 256,2 ms à froid, 3,6 ms à chaud,
  max RSS Python 37 601 280 octets (~36 Mio). Après ajout d’une référence parente,
  la recette d’hôte présente 90 objets. Pas un benchmark de charge ni une mesure
  du CPU total VS Code. Consommation prolongée/macOS globale NOT_TESTED.
- Un running sans écriture depuis cinq minutes est unknown. Les journaux ne
  permettent pas de certifier une connexion, un blocage ou une annulation active.

## Recette et preuves

| Vérification | Statut | Résultat |
|---|---|---|
| Sessions principales | VERIFIED | 85 sessions réelles projetées depuis session_meta |
| Sous-agents natifs | VERIFIED | 3 traces réelles, parents explicites, modèles gpt-6-astra |
| Parenté routeur | PARTIAL | ID parent déclaré conservé ; référence sans trace de session |
| Modèle demandé/alias | VERIFIED | Champs distincts, inconnus conservés null |
| Provenance exécutée | PARTIAL | Inconnue ; aucune provenance inférée ou inventée |
| États/transitions | VERIFIED | 6 événements réels queued→running→failed ; tests de fin/annulation structurelle |
| Tâche asynchrone récupérée | VERIFIED | Tâche P3-A reconstruite sans submit/inférence ; résultat disponible indiqué |
| Erreurs sans secrets | VERIFIED | Code connu affiché ; erreur libre synthétique masquée |
| Redémarrage/doublons | VERIFIED | Reconstruction testée, identifiants uniques dans l’hôte |
| Agent Standup | VERIFIED portée bornée | Activation 1.40.0 et commande enregistrée dans le même hôte ; sources contrôlées inchangées |
| Interface VS Code réelle | VERIFIED | Vue focus, TreeItems, arbre, filtre et document de détails exécutés dans Extension Host |
| Contrôle visuel humain/animations Standup | NOT_TESTED | Pas de capture visuelle ni interaction humaine qualifiée |
| Installation | VERIFIED | CLI confirme installation ; liste native ; sources exécutables identiques au dépôt |
| Rollback | IMPLEMENTED / NOT_TESTED réel | Désinstallation documentée, non exécutée pour conserver la livraison |

Huit tests unittest ciblés PASS après correction du cache temporel et des parents
absents ; node --check PASS. Test d’hôte VS Code PASS : 90 objets, 3 enfants,
arbre/filtre/détails/Standup. La première recette hôte a échoué sur l’hypothèse
erronée d’une trace de parent présente pour P3-A ; hypothèse invalidée, parent
référencé explicitement, seconde recette réussie. Aucun échec maquillé.

Preuves : [agent-observer/VALIDATION.json](agent-observer/VALIDATION.json),
`artifacts/p3c-host-validation.json`, logs du profil de recette v2. Le manifeste
installé ajoute uniquement __metadata de VS Code ; ses champs déclarés concordent.
Comparaisons SHA-256 finales : config.toml, catalogue harmonisé, router.py,
codex.js et extension.js de Standup inchangés depuis le contrôle de préinstallation.
Aucun test historique P3-A/P3-B ou witness d’inférence relancé.

## Activation, rollback et suites

Activation et désinstallation via les interfaces natives documentées dans le
[README](agent-observer/README.md). Vue prête dans l’Explorateur ; un rechargement
de la fenêtre existante peut être nécessaire. Aucun patch d’extension installée.
Les copies installées se régénèrent depuis les sources et le script de packaging.

Limites matérielles : modèle effectif des pools non confirmé, liaison de session
routeur déclarative, source de lecture SQLite non contractuelle, fenêtres bornées,
état réseau inconnu, historique legacy local_llm partiel. Décrire une tâche par son
profil technique protège les données mais ne résume pas son prompt.

OpenClaw futur uniquement : collecteurs/vues distincts par identité runtime,
aucun agrégateur Pro/Perso ni accès croisé aux résultats, interfaces de métadonnées
à droits minimaux à qualifier. Aucun agent/Gateway/config OpenClaw touché.
**P3-C s’arrête ici avec ces réserves ; aucune phase supplémentaire engagée.**
