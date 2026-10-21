# Budgets Qwen pour OpenClaw

Extension fournisseur native `wrapStreamFn`, validée avec OpenClaw 2026.10.5.
Portée exacte : fournisseur `omlx`, modèle `mlx-community--Qwen3.6-35B-A3B-4bit`,
API `openai-completions`, endpoint `http://127.0.0.1:8000/v1`.

| Sélection | enable_thinking | thinking_budget |
|---|---|---|
| Off | false | absent |
| Minimal | false | absent |
| Low | true | 512 |
| Medium | true | 2048 |
| High | true | 8192 |
| Ultra | true | 8192 |

Ultra garde son mode orchestration OpenClaw et arrive au fournisseur comme High.
Les budgets sont des plafonds ; aucune longueur minimale de réflexion n'est imposée.
Le plafond total de sortie existant (8192 tokens) reste inchangé et peut limiter la
réponse avant l'épuisement du budget de réflexion High/Ultra.
Sans niveau explicite ou reconnu, l'extension conserve le comportement natif.
Aucun catalogue, réglage d'agent ou mécanisme d'authentification n'est remplacé.

L'extension préserve les autres chat-template kwargs et le callback de payload
existant. Elle retire `reasoning_effort` pour les seules requêtes ciblées, puisque
Qwen applique le couple interrupteur/budget à la place.

## Installation locale et validation

`plugins.load.paths` référence ce dossier ; `plugins.entries.omlx-thinking.enabled`
vaut true. Le lien local ignoré par Git `node_modules/openclaw` pointe sur
`~/.openclaw/runtime/current/lib/node_modules/openclaw`, pour résoudre le SDK public.
Rechargement natif : `openclaw plugins reload omlx-thinking --json`.

`~/.openclaw/runtime/current/bin/bun openclaw/omlx-thinking/verify.mjs` capture les
payloads du transport installé pour les deux agents. Le callback interrompt la
requête avant le réseau ; `fetch` est également interdit. Aucun modèle n'est invoqué.
Le test vérifie les six niveaux, le rabattement Ultra, les exclusions de portée et
la composition du callback. Il ne qualifie pas la qualité des générations.

## Retour arrière

Sauvegarde préalable : `~/.openclaw/backups-omlx-thinking-20261020-224748/openclaw.json`.
Elle contient les secrets existants et reste locale avec permissions 0600.

```sh
python3 openclaw/omlx-thinking/rollback.py ~/.openclaw/backups-omlx-thinking-20261020-224748
~/.openclaw/bin/openclaw config validate
```

Le script retire uniquement les ajouts de cette extension et préserve les autres
changements de configuration. Le watcher applique le retrait ; le source reste disponible.

## Mises à jour

Le source reste hors du runtime distribué et ne référence aucun fichier interne.
Le SDK `definePluginEntry` et le hook `wrapStreamFn` restent des interfaces dont la
compatibilité doit être vérifiée après mise à jour. Le script de vérification utilise
deux imports internes propres à la version 2026.10.5 : les actualiser si nécessaire
pour refaire le contrôle hors réseau, sans changer l'extension.

## Résultat du 20 octobre 2026

- Capture réelle du transport installé : PASS pour les six niveaux et les deux
  agents, sans réseau ni génération. Off omet le budget, Ultra arrive comme High.
- `openclaw config validate` : PASS. Rechargement natif : `ok=true`,
  `restartRequired=false`, génération 4, entrée sélectionnée dans ce dossier.
- Santé Gateway après publication : `ok=true`, extension chargée, aucune erreur
  de plugin, rechargement actif. Aucun redémarrage demandé.
- Configurations agents et modèles strictement identiques à la sauvegarde.
  Empreintes protégées (Codex, MCP, réglages oMLX, binaire proxy, mapping et
  transport du cœur OpenClaw) inchangées.
- Le reçu de rechargement signale le nettoyage différé d'une ancienne instance
  Microsoft Graph (un appel encore actif). La santé suivante montre Graph chargé
  et aucune erreur de plugin ; elle ne prouve pas la fin de cet ancien nettoyage.
- La provenance du plugin reste locale (`plugins.load.paths`) : l'avertissement
  de provenance non certifiée d'OpenClaw est attendu. Aucun contrôle contourné.
