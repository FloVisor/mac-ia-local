# Intégration iMessage OpenClaw — Retour d'expérience (2026-10-18)

Ce document capitalise les pièges rencontrés lors de l'intégration du canal
iMessage dans OpenClaw, pour éviter de les reproduire sur les prochains
outils/canaux à intégrer.

## Environnement de référence

- OpenClaw 2026.10.4 (CLI + app `/Applications/OpenClaw.app`)
- macOS 27.0.1, Apple Silicon, SIP activé
- Modèle unique : `omlx/mlx-community--Qwen3.6-35B-A3B-4bit` (32k ctx)
- Config : `~/.openclaw/openclaw.json`

## Pièges rencontrés et résolutions

### 1. TCC / Full Disk Access — l'attribution suit le processus responsable

**Symptôme** : `imsg rpc not ready (Database unavailable: code=-32002)` —
accès refusé à `~/Library/Messages/chat.db`.

**Cause** : macOS attribue l'autorisation TCC au *processus responsable*
(responsible process), pas au binaire enfant. Le Gateway est un enfant de
`OpenClaw.app` ; c'est donc **OpenClaw.app** qui doit avoir l'Accès complet au
disque, pas nécessairement `imsg` ou `bun`.

**Règle** : identifier le processus responsable avec
`ps -o ppid= -p <pid_gateway>` en remontant la chaîne, et accorder FDA à
l'app parent. Un Gateway lancé depuis un terminal hérite de l'autorité du
terminal (VS Code), pas d'OpenClaw.app — d'où des comportements différents
selon le mode de lancement.

**Non-documenté mais important** : `/opt/homebrew/bin/imsg` est un symlink ;
le sélecteur de fichiers macOS ne le suit pas. Utiliser le chemin réel dans
`Cellar/`.

### 2. `tools.allow` restrictif — l'outil `message` n'était pas autorisé

**Symptôme** : l'agent répond « aucun outil de messagerie iMessage n'est
disponible » alors que le canal est `connected, works`.

**Cause** : `tools.allow` global était une allowlist restrictive
(`["exec", "microsoft-graph", "orion__*", "outline__*"]`) sans `message`.
Le canal fonctionne (envoi CLI OK) mais l'**agent** n'a pas l'outil.

**Règle** : à chaque intégration d'un canal (iMessage, Telegram, etc.),
vérifier **les deux niveaux** :
1. Le canal : `openclaw channels status --probe` → `connected, works`
2. L'outil agent : `openclaw doctor` → ne doit PAS contenir
   « message tool is unavailable for that agent »

Le doctor est le vérificateur systématique après toute modification.

### 3. Politique Microsoft Graph — refus locaux vs OAuth

**Symptôme** : `outlook_calendar_read` échoue avec `access_denied` en
1-2 ms (durée ≈ 0 = refus de politique **locale**, pas un problème OAuth).

**Cause** : le modèle passe parfois des paramètres inventés (ex.
`calendarId: "default"`) non présents dans
`plugins.entries.microsoft-graph.config.policy.services.calendar.agents.main.resources`.

**Règle** : un refus < 5 ms = politique locale. Un refus lent/401 = OAuth.
Ajouter les valeurs que le modèle utilise naturellement aux `resources`
autorisées, ou instruire l'agent (prompt) de ne pas préciser le paramètre.

### 4. Saturation de session — le modèle ne répond plus

**Symptôme** : `Context window exceeded: estimated input 49121 leaves only
0 output tokens within the 32768-token context`. L'agent ne répond plus,
les tours restent bloqués 10+ min, et le rechargement de config est différé
(`reload deferred while active work finishes`).

**Cause** : la session `agent:main:main` accumule l'historique au-delà de la
fenêtre de contexte du modèle local (32k).

**Règles** :
- Compacter par troncature (pas LLM — le modèle saturé ne peut pas se
  résumer lui-même) :
  `openclaw sessions compact agent:main:main --agent main --max-lines 40`
- Surveiller : `openclaw sessions --agent main --active 120` (colonne
  Tokens ctx %)
- Un reload différé persistant signale souvent un tour d'agent bloqué.

### 5. Utility model / titres de session — fallback crustacé

**Symptôme** : titres de session aléatoires (`salty-lobster`) au lieu de
résumés ; log `dashboard session title generation exhausted`.

**Cause** : la génération de titre passe par le modèle utilitaire = modèle
principal par défaut. Sur un modèle local 35B en 32k, ces micro-requêtes
échouent souvent (timeout/abort).

**Attention** : ne PAS ajouter un provider supplémentaire (ex. Ollama) sans
mesurer l'impact — un second modèle 30B chargé en VRAM sature un Mac 48 Go
avec le modèle principal. Si un utility model léger est voulu, vérifier
l'empreinte mémoire cumulée et décharger après test
(`curl /api/generate -d '{"model":"X","keep_alive":0}'`).

### 6. `dmPolicy` — sens exact

- `pairing` : les expéditeurs inconnus reçoivent un code d'appairage ;
  une fois approuvés (`openclaw pairing approve imessage <code>`), ils
  peuvent **discuter avec l'agent** (réponses automatiques).
- `disabled` : les DM entrants sont ignorés — **l'envoi sortant fonctionne
  toujours**. C'est le bon choix si on ne veut que du sortant.

## Checklist d'intégration d'un nouvel outil/canal

1. **Audit** : `openclaw plugins list`, `openclaw agents list`,
   `openclaw channels status --probe`, sauvegarde config
   (`cp ~/.openclaw/openclaw.json ~/.openclaw/backups-<date>/`).
2. **Permissions macOS** : identifier le processus responsable du Gateway
   (`ps -o ppid=`), accorder FDA au parent, pas aux enfants.
3. **Config ciblée** : modifier uniquement les clés nécessaires (jamais de
   remplacement complet du fichier). Valider : `openclaw config validate`.
4. **Vérifier l'outil agent** : `openclaw doctor` — l'outil doit être
   disponible pour l'agent routé (allowlist `tools.allow`).
5. **Redémarrer** : `openclaw gateway restart`, puis re-probe.
6. **Diagnostic des échecs** : durée de l'erreur (ms = politique locale,
   lente = réseau/OAuth), `openclaw sessions tail --agent main`,
   `/tmp/openclaw/openclaw-gateway.log`.
7. **Surveiller la saturation** : tokens de session vs fenêtre de contexte
   du modèle local.

## État final (2026-10-18)

- Canal iMessage : `connected, works`, envoi sortant validé par test réel
- `dmPolicy=disabled` (pas de réponses automatiques entrantes)
- `tools.allow` inclut `message`
- Calendrier Graph : `default` ajouté aux ressources autorisées
- Modèle unique : Qwen omlx (aucun provider parasite)
- `commands.ownerAllowFrom` vidé : les réponses dashboard ne fuient plus
  vers iMessage (effet de bord de l'approbation d'appairage à surveiller)
- `tools.exec.safeBinProfiles.osascript` : permet la résolution de contacts
  via AppleScript sans approbation manuelle

## Limite connue : comportement du modèle local

Le modèle Qwen 35B (32k contexte, 55 outils catalogués) est **inconstant**
sur les enchaînements d'outils autonomes : il peut exécuter correctement
osascript un tour, puis affirmer « exec non configuré » au tour suivant sans
même essayer. Ce n'est pas un problème de configuration — la chaîne complète
(résolution contact → envoi iMessage) est prouvée fonctionnelle en CLI.

**Parade** : relancer la demande en cas d'échec de l'agent. Ne pas « corriger »
la config sur la base des affirmations du modèle — vérifier les logs
(`grep -E "exec|tool" /tmp/openclaw/openclaw-gateway.log`) pour distinguer
un vrai refus d'une hallucination du modèle.
