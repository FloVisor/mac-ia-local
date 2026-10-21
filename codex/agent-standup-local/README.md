# Agent Standup P3-C — dérivé isolé

Base MIT Agent Standup **1.40.0**, commit fixé dans [BASE.json](BASE.json).
Identité locale `local-xithi.agent-standup-p3c`, version `1.40.0-p3c.1`.
Quatre fichiers amont adaptés ; nouveaux modules d’intégration séparés. Les
sources/ressources amont et VSIX sont sous `artifacts/agent-standup-p3c`, ignoré
par Git. Aucun fichier de l’extension officielle installée n’est modifié.

## Ouvrir la version de revue

```sh
bash codex/agent-standup-local/launch-isolated.sh
```

Le profil et le répertoire d’extensions sont isolés. Commande dans cette fenêtre :
**Agent Standup: Open** (commande technique `p3cStandup.open`), ou son icône dans
la barre d’activité. Les titres localisés restent ceux d’Agent Standup ; la fiche
Extensions précise **Agent Standup P3-C · isolé**. Les commandes, configurations et
vues ont le préfixe `p3cStandup` pour éviter toute collision.

Dans Live Call, sélectionner la session parente de Lovelace/Confucius/Harvey
ou la **Session référencée · trace absente** de la tâche P3-A. Les personnages,
le mode arbre, la sélection/épingle de session, le replay et les détails restent
ceux de la scène d’origine. Le clic d’un personnage donne les métadonnées techniques
ajoutées. Les modèles Codex sont **déclarés** ; l’exécution fournisseur n’est pas
prétendue confirmée. MCP est étiqueté **Tâche MCP · llm-router**.

Le lanceur de revue garde `P3C_OFFLINE_TEST=1` : traduction, plaisanteries et
appels LLM bloqués côté serveur. Exception audio : `/api/tts?engine=kokoro`
est autorisé uniquement lorsque le worker local est déjà prêt ; installation et
chargement initial par cette route restent bloqués. Les voix système demandées
directement restent bloquées dans ce mode. Il ne modifie pas les
préférences quotidiennes. Les fonctions correspondantes restent présentes dans
le code amont ; leurs appels réels ne font pas partie de la recette.

## Construire et comparer

```sh
python3 codex/agent-standup-local/build.py
```

Utilise les sources déjà présentes du commit fixé. Le script applique des remplacements
à contexte exact et refuse une dérive de contexte ; vérifie la syntaxe des modules
et du script navigateur, copie le collecteur partagé depuis `agent-observer` sans
recopier sa logique, puis génère le VSIX et `local-changes.patch`. Aucun serveur,
MCP ou moteur n’est démarré par la construction.

Pour reconstituer les sources sur un autre poste, télécharger l’archive GitHub du
commit BASE dans `artifacts/agent-standup-p3c/source/`. Archive initiale qualifiée :
SHA-256 `c0c36d6773ee4f7265b52f2c237898839c28213b4e6157038218b7c4abef714c`.
Conserver LICENSE amont et LICENSE.txt du VSIX.

**Mise à jour sans promotion automatique :**

```sh
python3 codex/agent-standup-local/update.py --ref COMMIT_OU_TAG_EXPLICITE
```

Télécharge une source candidate dans `update-candidate/`, compare les cinq fichiers
d’intégration avec la base, écrit `upstream.diff` et `comparison.json`, tente une
construction dans un autre dossier. Ni BASE.json, ni le VSIX actuel, ni le profil
quotidien ne sont promus. Le patch des modifications locales est produit dans le
build candidat. Examiner les différences amont ET locales ; si contexte incompatible,
arrêter et résoudre dans les scripts de patch. Changement de base/version puis
recette ciblée et visuelle obligatoires avant toute installation approuvée.
Les autres évolutions de ressources amont restent également à examiner lors de la
revue du dépôt : cette comparaison automatique porte sur les points d’intégration.

Contrôle hors réseau : `update.py --source CHEMIN_SOURCE_AMONT`. Le contrôle sur
la base 1.40.0 passe ; compatibilité avec une version future non qualifiée.

## Collecte, états et confidentialité

`p3c.js` utilise le protocole du collecteur Python partagé, avec son identité Codex
fixe et ses filtres. Cadence de lecture maximale 5 s, découverte 30 s, 200 fichiers/
14 jours, 200 tâches/20 transitions par tâche, 64 transitions natives par fichier.
Pas de nouvelle base ou de journal d’activité persistant. Cache uniquement mémoire.
Un collecteur qui échoue n’est pas redémarré en boucle ; erreur remontée dans la
chronologie technique (`p3c.error`). Python 3 doit être accessible dans PATH.

Nom technique et chemin Codex sont repris depuis thread_spawn. Les reviews
`subagent.other=guardian` sont exclues. La tâche affichée est le chemin ou le profil
connu, pas un résumé inventé du prompt. Parents manquants explicitement référencés.
Le parent MCP reste déclaré par le routeur, sans authentification runtime ajoutée.

Le journal du parent suit le chemin amont existant ; aucune copie de ses contenus
n’est créée par l’intégration. Les participants ajoutés ne recopient ni prompts,
réponses, arguments d’outil, secrets ou résultats privés. Leurs événements sont
techniques et ne sont pas envoyés à la traduction/voix distante. Pas de faux usage
ou résultat généré. Les tokens par participant sont accessibles dans les détails ;
les cumuls natifs ne sont pas ajoutés au total parent pour éviter un double compte.

Actual_model reste inconnu dans les projections actuelles du routeur ; le modèle
ou alias demandé est étiqueté comme tel. Coût absent = null. Running silencieux
Codex > 5 min = unknown ; aucun completed déduit du seul silence. Sans nouveau
journal, ni connexion ni blocage réel du processus ne peuvent être certifiés.

## Validation et rollback

Résultats : [25-agent-standup-local-p3c.md](../25-agent-standup-local-p3c.md).
Captures et preuves techniques sous `artifacts/agent-standup-p3c/` (locales privées).

Rollback de cette revue : fermer la fenêtre VS Code isolée. Aucun retour en arrière
sur le profil quotidien, l’extension officielle ou les services n’est nécessaire.
Pour enlever l’installation isolée uniquement :

```sh
"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" \
  --user-data-dir "$PWD/artifacts/agent-standup-p3c/isolated-profile" \
  --extensions-dir "$PWD/artifacts/agent-standup-p3c/isolated-extensions" \
  --uninstall-extension local-xithi.agent-standup-p3c
```

Le mode développement fonctionne depuis le répertoire généré ; ne pas le modifier
à la main. Pour un éventuel déploiement quotidien, une décision utilisateur distincte
et une procédure de bascule sont requises. Aucune bascule réalisée par P3-C.
