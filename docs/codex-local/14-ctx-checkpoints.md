# Limitation des context checkpoints llama-server — LLAMA_ARG_CTX_CHECKPOINTS=4

Date : 2026-10-04 · Machine : MacBook Pro Apple Silicon 48 Go · Ollama 0.35.1 · Modèle : `qwen3.6:35b-coding` (qwen35moe, Q4_K_M)

## 1. Pourquoi ce changement

llama-server maintient des **context checkpoints** (instantanés du KV cache) pour accélérer la reprise des sessions longues. Par défaut, jusqu'à **32** checkpoints sont conservés par slot. Lors des longues sessions Codex (contexte ~111k tokens), chaque checkpoint pèse jusqu'à ~285 MiB et le serveur atteignait `created context checkpoint 31 of 32`, avec une croissance mémoire importante (RSS llama-server ~24–25 Go, swap système élevé).

Cible retenue : **`LLAMA_ARG_CTX_CHECKPOINTS=4`** (et non `0` — les checkpoints restent utiles pour la reprise de contexte).

## 2. Valeurs avant / après

| Élément | Avant | Après |
|---|---|---|
| Context checkpoints max | 32 (défaut) | **4** |
| Preuve log | `context checkpoints enabled, max = 32` (server.log ancien, l.463) ; `created context checkpoint 31 of 32` | `context checkpoints enabled, max = 4` (server.log, l.361) ; `created context checkpoint 1 of 4`, `2 of 4` |
| Contexte | 131072 | 131072 (inchangé) |
| NUM_PARALLEL | 1 | 1 (inchangé) |
| Flash Attention | actif | actif (inchangé) |
| KV cache | F16, 2560 MiB + 256 MiB | F16, 2560 MiB + 256 MiB (inchangé) |

## 3. Audit de l'existant (avant modification)

- Serveur actif : **app Ollama** (Electron) lancée au login par macOS (BTM login item `com.ollama.ollama`), qui spawn `ollama serve` puis `llama-server`.
- `OLLAMA_CONTEXT_LENGTH=131072` et `OLLAMA_NO_CLOUD=true` sont injectés par l'app elle-même (réglages `~/Library/Application Support/Ollama/db.sqlite`), `OLLAMA_NUM_PARALLEL=1` par défaut serveur.
- LaunchAgent du dépôt `org.gangneux.ollama-serve` (binaire patché v0.35.0-pr18413) : chargé mais inactif (`RunAtLoad=false`, `runs=0`) — il ne détient pas le port 11434 actuellement.
- `llama-server` 0.35.1 supporte `LLAMA_ARG_CTX_CHECKPOINTS` (vérifié dans le binaire) ; `ollama serve` transmet son environnement hérité à `llama-server` (`cmd.Env = os.Environ()` dans `llm/llama_server.go`).

## 4. Mécanisme de persistance macOS

Deux mécanismes complémentaires, tous deux dans le domaine utilisateur (`gui/UID`), idempotents :

1. **`~/Library/LaunchAgents/org.gangneux.ollama-env.plist`** (nouveau) — `RunAtLoad=true`, exécute `launchctl setenv LLAMA_ARG_CTX_CHECKPOINTS 4` à chaque ouverture de session. La variable entre dans l'environnement du domaine `gui/` **avant** que l'app Ollama (login item BTM) ne soit lancée ; l'app et son `ollama serve` en héritent, puis `llama-server` en hérite à son tour.
2. **`~/Library/LaunchAgents/org.gangneux.ollama-serve.plist`** (modifié) — ajout de `LLAMA_ARG_CTX_CHECKPOINTS=4` dans `EnvironmentVariables`, couvrant le cas où le serveur patché du dépôt reprendrait le port 11434.

Aucune dépendance à un shell interactif ; enregistré dans BTM (`sfltool dumpbtm` : `enabled, allowed`).

Sauvegardes :
- `~/Library/LaunchAgents/org.gangneux.ollama-serve.plist.bak-20261004-170503` (original du plist modifié)

## 5. Procédure de vérification

```sh
# 1. Variable dans le domaine launchd
launchctl getenv LLAMA_ARG_CTX_CHECKPOINTS        # attendu : 4

# 2. Héritage par ollama serve (PID du serveur)
ps eww $(pgrep -f "ollama serve" | head -1) | tr ' ' '\n' | grep LLAMA_ARG
# attendu : LLAMA_ARG_CTX_CHECKPOINTS=4

# 3. Héritage par llama-server + preuve comportementale
ps eww $(pgrep -f llama-server | head -1) | tr ' ' '\n' | grep LLAMA_ARG
grep "context checkpoints enabled" ~/.ollama/logs/server.log   # max = 4
grep "created context checkpoint" ~/.ollama/logs/server.log    # "N of 4", jamais "of 32"

# 4. Non-régression
grep "Flash Attention enabled" ~/.ollama/logs/server.log      # présent
grep "KV buffer size" ~/.ollama/logs/server.log                # 2560.00 MiB + 256.00 MiB
ps aux | grep '[l]lama-server'                                 # -c 131072 -np 1 --flash-attn auto
```

Après le prochain reboot, rejouer les étapes 1 à 3 : la variable doit être à `4` sans aucune commande manuelle.

## 6. Preuves (2026-10-04, après redémarrage du serveur)

- `launchctl getenv LLAMA_ARG_CTX_CHECKPOINTS` → `4`
- Env `ollama serve` (PID 8655) : `LLAMA_ARG_CTX_CHECKPOINTS=4`, `OLLAMA_CONTEXT_LENGTH=131072`, `OLLAMA_NO_CLOUD=1`
- Env `llama-server` (PID 8672) : `LLAMA_ARG_CTX_CHECKPOINTS=4`
- server.log l.361 : `srv load_model: context checkpoints enabled, max = 4, min spacing = 8192`
- 6 tours de génération avec prompts ~17k tokens : `created context checkpoint 1 of 4`, `2 of 4` — plafonnement à 4 confirmé (avant : `31 of 32`)
- server.log l.1 (`server config`) : `OLLAMA_CONTEXT_LENGTH:131072`, `OLLAMA_NUM_PARALLEL:1`, `OLLAMA_NO_CLOUD:true`
- server.log l.18 : cmdline llama-server avec `-c 131072 -np 1 --flash-attn auto`
- server.log l.251/291 : `Flash Attention enabled` ; l.244/286 : KV buffer 2560 MiB / 256 MiB, K (f16) + V (f16)
- `ollama ps` : qwen3.6:35b-coding, 22.9 Go, 100 % VRAM, `context_length: 131072`
- RSS llama-server : ~28,5 Go (28 564 384 Ko) pendant les tests longs
- Proxy Codex (`/api/codex/v1/responses`) : `status: completed`, réponse `PONG`
- Catalogue inchangé : qwen3.6:35b-coding, qwen3.6:35b-mlx, muse-glimmer:30b-mlx, qwen3-embedding:0.6b, qwen3.5:2b, qwen3-coder:30b
- Tests témoins `witness-a/` : 2/2 OK
- `vm.swapusage` : 2648 Mo utilisés ; memory free 31 %

## 7. Rollback

Retour au comportement par défaut (32 checkpoints) :

```sh
# 1. Décharger et supprimer le LaunchAgent env
launchctl bootout gui/$(id -u)/org.gangneux.ollama-env
rm ~/Library/LaunchAgents/org.gangneux.ollama-env.plist

# 2. Retirer la variable du domaine launchd
launchctl unsetenv LLAMA_ARG_CTX_CHECKPOINTS

# 3. Restaurer le plist du serveur patché (ou retirer la clé LLAMA_ARG_CTX_CHECKPOINTS)
cp -p ~/Library/LaunchAgents/org.gangneux.ollama-serve.plist.bak-20261004-170503 \
      ~/Library/LaunchAgents/org.gangneux.ollama-serve.plist
launchctl bootout gui/$(id -u)/org.gangneux.ollama-serve 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/org.gangneux.ollama-serve.plist

# 4. Redémarrer l'app Ollama (elle héritera de l'environnement nettoyé)
kill -TERM $(pgrep -f "MacOS/Ollama" | head -1)   # quit gracieux
open -a Ollama

# 5. Vérifier le retour au défaut
launchctl getenv LLAMA_ARG_CTX_CHECKPOINTS        # attendu : vide
grep "context checkpoints enabled" ~/.ollama/logs/server.log | tail -1   # max = 32
```

Les autres paramètres Ollama (`OLLAMA_CONTEXT_LENGTH`, `OLLAMA_NUM_PARALLEL`, `OLLAMA_NO_CLOUD`, KV cache, Flash Attention) ne sont pas touchés par ce rollback.
