# Sélecteur d'effort Codex — pièges et procédure (modèles Ollama locaux)

Date : 2026-10-17 · Suite à deux corrections successives sur `qwen3.6:35b-coding`
(capture complète : [diagnostics/keepalive30-20261017/](../../diagnostics/keepalive30-20261017/README.md))

## Règle d'or

**Un modèle Ollama local n'affiche le sélecteur d'effort dans l'UI Codex
(VS Code / Desktop) que s'il expose ≥3 niveaux de raisonnement.**

Le webview (`app-initial-*.js` de l'extension) initialise le power picker avec
`canInitializePowerPicker: g.length >= 3`. Avec 2 niveaux (ex. none/high), le
chip reste figé sur le défaut — pas de menu cliquable.

## Contrats par modèle (2026-10-17)

| Modèle | Thinking natif (`/api/show`) | Niveaux catalogue | Sélecteur UI |
|---|---|---|---|
| muse-glimmer:30b-mlx | `[false, low, medium, high, max]` | 5 (none/low/medium/high/max) | ✅ visible |
| qwen3.6:35b-coding | `[false, true]` (binaire) | **5** (alignés sur glimmer) | ✅ visible |
| qwen3.6:35b-mlx | `[false, true]` (binaire) | 2 (none/high) | ❌ figé |
| qwen3-coder:30b | pas de thinking | 0 | ❌ aucun |

## Pour un modèle binaire (thinking on/off)

Le modèle ne supporte que ON/OFF, mais on lui déclare quand même les 5 niveaux
au catalogue. C'est le **proxy Ollama** qui normalise
(`internal/proxy/codex_desktop_normalize.go`) :

- `none` → thinking OFF (`think: false`)
- `low` / `medium` / `high` / `max` → thinking ON (`think: true`)

Les efforts intermédiaires sont donc cosmétiques pour un modèle binaire, mais
indispensables pour débloquer le sélecteur UI.

## Procédure pour ajouter/corriger un modèle

1. **Vérifier le thinking natif** :
   `curl -s http://127.0.0.1:11434/api/show -d '{"model":"<slug>"}' | jq .thinking`
2. **Sauvegarder le catalogue** :
   `cp ~/.codex/ollama-launch-models.json ~/.codex/ollama-launch-models.json.bak-<tag>-$(date +%Y%m%d-%H%M%S)`
3. **Patcher le catalogue** (`~/.codex/ollama-launch-models.json`, entrée du slug) :
   - `default_reasoning_level` = niveau par défaut voulu (ex. `high` = Thinking ON)
   - `supported_reasoning_levels` = **au moins 3 niveaux** (idéalement les 5
     standard : none/low/medium/high/max avec les descriptions EN standard)
4. **Patcher le routing** (`~/.codex/ollama-launch-codex-routing.json`) :
   `controls.default` = `true` (ON) ou `false` (OFF)
5. **Mettre à jour le re-patch idempotent** `~/.codex/apply-qwen-codex-fix.sh`
   (sinon la prochaine régénération par l'app Ollama écrase le correctif)
6. **Valider AVANT d'annoncer « fait »** :
   - app-server : `model/list` doit exposer les niveaux voulus
     ```sh
     (echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"probe","version":"1.0"}}}';
      sleep 2; echo '{"jsonrpc":"2.0","id":2,"method":"model/list","params":{}}'; sleep 3) \
       | ~/.vscode/extensions/openai.chatgpt-*/bin/macos-aarch64/codex app-server
     ```
   - wire : chaque effort doit donner le comportement attendu
     (`/api/codex/v1/responses` avec `reasoning.effort` → item `reasoning`
     présent = ON, absent = OFF)
   - UI : **recharger la fenêtre VS Code** et vérifier visuellement le
     sélecteur — le wire seul ne prouve PAS que l'UI l'affiche
7. **Ne jamais toucher** : bloc `[mcp_servers.local_llm]` de `~/.codex/config.toml`,
   entrées glimmer du catalogue/routing (modèle de référence fonctionnel).

## Descriptions standard (à réutiliser telles quelles)

```json
[
  {"effort": "none",   "description": "Turn thinking off"},
  {"effort": "low",    "description": "Fast responses with lighter thinking"},
  {"effort": "medium", "description": "Balances speed and thinking depth for everyday tasks"},
  {"effort": "high",   "description": "Greater thinking depth for complex tasks"},
  {"effort": "max",    "description": "Maximum thinking depth for the hardest tasks"}
]
```

## Erreurs commises le 2026-10-17 (à ne pas reproduire)

1. Annoncer « corrigé » après validation wire seulement — l'UI exige ≥3 niveaux,
   invisible sur le wire.
2. Descriptions FR non standard dans le catalogue (peut perturber l'UI).
3. `default_reasoning_level: "none"` alors que le modèle est thinking ON par
   défaut natif.
