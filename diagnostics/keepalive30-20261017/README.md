# Validation keep_alive 30m + dropdown Codex — 2026-10-17

## Changements
- `~/Library/LaunchAgents/org.gangneux.ollama-serve.plist` : `OLLAMA_KEEP_ALIVE` 10m → **30m**
- `~/Library/LaunchAgents/org.gangneux.ollama-env.plist` : ajoute `launchctl setenv OLLAMA_KEEP_ALIVE 30m`
  (wrapper `sh -c`, car setenv n'accepte qu'un couple) — s'applique à l'app Ollama (serveur actif)
- Backups : `*.bak-keepalive30-20261017-192207`

## Découverte importante
Le serveur qui écoute sur 11434 est l'**app Ollama** (GUI), pas le LaunchAgent
`org.gangneux.ollama-serve` (état `not running`). Sans `OLLAMA_KEEP_ALIVE` dans
l'env launchd, l'app utilisait le défaut **5 min** (TTL mesuré 300 s), pas 10 m.
Le setenv launchd corrige les deux chemins.

## Validation (2026-10-17 ~19:30)
- `launchctl getenv OLLAMA_KEEP_ALIVE` → `30m`
- Env du serveur (PID nouveau) : `OLLAMA_KEEP_ALIVE=30m`
- TTL mesuré via `/api/ps` après génération : **1800 s** (30 min) — PASS
- Wire Codex `/api/codex/v1/responses` (qwen3.6:35b-coding) : HTTP 200, status completed — PASS
- MCP `local_llm` delegate (muse-glimmer:30b-mlx, effort high) : `DELEGUE_OK` — PASS
- Tests témoins `witness-a/` : 2/2 OK

## Dropdown Codex (inchangé, vérifié)
`qwen3.6:35b-coding` déjà présent (visibility=list) avec muse-glimmer:30b-mlx,
qwen3.6:35b-mlx, qwen3-coder:30b. Aucune modification du catalogue — conf
glimmer/MCP intacte.

## Efforts raisonnement (vérifiés sur le wire)
- muse-glimmer:30b-mlx : none/low/**medium**/high/max natifs — medium ≈ moitié du
  raisonnement de high (mesuré : 761 vs 1616 chars sur prompt test)
- qwen3.6:35b-coding : thinking binaire (none/high). Le proxy mappe medium→high
  proprement (`normalizeThinkingEffort`), donc l'effort medium est accepté mais
  équivaut à high pour ce modèle.

## Correctif efforts qwen3.6:35b-coding (2026-10-17 ~19:35)

Problème : dans le dropdown Codex, le sélecteur d'effort de qwen3.6:35b-coding
affichait un défaut « none » avec des descriptions FR non standard, alors que le
modèle est thinking ON par défaut (natif `/api/show` : values [false, true],
default true).

Corrections (catalogue + routing + script de re-patch) :
- `default_reasoning_level` : none → **high** (= Thinking ON)
- `supported_reasoning_levels` : descriptions standard (« Turn thinking off » /
  « Greater thinking depth for complex tasks »)
- routing `controls.default` : false → **true**
- `apply-qwen-codex-fix.sh` : re-patch idempotent mis à jour avec ces valeurs

Validation wire `/api/codex/v1/responses` (qwen3.6:35b-coding) :
- effort=high → item `reasoning` présent (Thinking ON) — PASS
- effort=none → aucun item `reasoning` (Thinking OFF) — PASS
- Script re-patch : idempotence vérifiée — PASS
- glimmer/MCP/routing auto_review : inchangés — PASS
- Témoins `witness-a/` : 2/2 OK

Backups : `ollama-launch-models.json.bak-coding-default-20261017-193407`

## Correctif sélecteur d'effort qwen3.6:35b-coding (2026-10-17 ~19:45)

Problème : aucun sélecteur d'effort dans l'UI Codex pour qwen3.6:35b-coding
(chip figé « High »), alors que muse-glimmer:30b-mlx l'affiche.

Cause racine (analyse du webview VS Code `app-initial-fee819fe4f22.js`) :
l'initialisation du power picker exige **≥3 niveaux** de raisonnement
(`canInitializePowerPicker: g.length>=3`). coding n'en exposait que 2
(none/high) → pas de sélecteur. glimmer en expose 5 → sélecteur visible.

Correctif : catalogue coding aligné sur le contrat glimmer (5 niveaux
none/low/medium/high/max, défaut high). Le routing reste binaire
(false/true) — le proxy normalise : none → thinking OFF, low/medium/high/max
→ thinking ON (vérifié dans internal/proxy/codex_desktop_normalize.go).

Validation :
- app-server `model/list` : coding expose ['none','low','medium','high','max'],
  défaut high — PASS
- wire `/api/codex/v1/responses` : none→OFF, low/medium/high/max→ON (5/5 HTTP 200) — PASS
- script re-patch idempotent mis à jour — PASS
- glimmer/MCP/config intacts — PASS
- témoins witness-a/ 2/2 OK

Backups : ollama-launch-models.json.bak-coding-5levels-*
