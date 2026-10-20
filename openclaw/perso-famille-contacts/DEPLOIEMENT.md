# Déploiement (Phase B) et retour arrière

**Ne rien exécuter avant le message « VALIDE LE DÉPLOIEMENT ».**

## Prérequis

- Gateway arrêté ou redémarrage accepté (`openclaw gateway restart`).
- Accès physique au Mac pour la boîte de dialogue Contacts.

## 1. Sauvegarde

`deploy.sh` crée `~/.openclaw/backups-perso-famille-<horodatage>/` contenant
`openclaw.json`, les `AGENTS.md`/`USER.md` de Perso et de Pro.

## 2. Application

```sh
cd openclaw/perso-famille-contacts
./deploy.sh
```

Étapes : sauvegarde → compilation et installation de `perso-contacts` dans
`~/.local/bin` → copie de `famille/`, du skill et de `pro/index.md` → patch de
configuration validé → `config validate` → `doctor` → tests.

Idempotent : une relance réécrit les mêmes fichiers et réapplique le même patch.

## 3. Fusion manuelle des blocs

`deploy.sh` **ne touche pas** `USER.md` / `AGENTS.md` (risque d'écrasement).
Fusionner à la main :

| Fichier | Action |
| --- | --- |
| `workspace-perso/USER.md` | Remplacer la section `## Directives` par le bloc de `USER.md.patch.md` |
| `workspace-perso/AGENTS.md` | Insérer le bloc de `AGENTS.md.patch.md` avant `## Règles communes` |
| `workspace/AGENTS.md` (Pro) | Insérer le bloc de `workspace-pro/AGENTS.md.patch.md` avant `## Règles communes` |
| `workspace/USER.md` (Pro) | Remplacer la section `## Directives` par le bloc de `workspace-pro/USER.md.patch.md` |

## 4. Autorisation Contacts (intervention macOS)

Option recommandée — helper dédié :

```sh
mkdir -p ~/Applications/PersoContacts.app/Contents/MacOS
cp ~/.local/bin/perso-contacts ~/Applications/PersoContacts.app/Contents/MacOS/perso-contacts
cat > ~/Applications/PersoContacts.app/Contents/Info.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>org.gangneux.perso-contacts</string>
<key>CFBundleName</key><string>PersoContacts</string>
<key>CFBundleExecutable</key><string>perso-contacts</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
<key>NSContactsUsageDescription</key><string>Lecture des contacts pour l'agent Perso.</string>
</dict></plist>
PLIST
codesign -s - --force ~/Applications/PersoContacts.app
open -n -a ~/Applications/PersoContacts.app --args request-access
```

La boîte de dialogue macOS doit être acceptée **une fois**. Vérifier ensuite :

```sh
open -n -a ~/Applications/PersoContacts.app --args status
```

Attendu : `"authorization":"authorized"`.

## 5. Vérifications après redémarrage

```sh
openclaw gateway restart
openclaw doctor
openclaw agents list
```

Puis, depuis une **nouvelle session** de chaque agent :

| Contrôle | Attendu |
| --- | --- |
| Perso : « Qui est ma femme ? » | Anaïs, sans lecture du carnet |
| Perso : « Anniversaire de ma femme ? » | 1991-06-21 avec provenance |
| Perso : `/tools` | `perso_contacts` présent |
| Pro : `/tools` | `perso_contacts` **absent** |
| Pro : demande de données familiales | refus, aucune délégation sortante de Perso |
| Perso : `sessions_list` | uniquement ses propres sessions |

## 6. Retour arrière

```sh
./rollback.sh ~/.openclaw/backups-perso-famille-<horodatage>
openclaw gateway restart
```

Restaure `openclaw.json`, les quatre fichiers de workspace, supprime `famille/`,
le skill, `pro/index.md` et le binaire installé.

## Points non vérifiés avant déploiement

- Autorisation Contacts du helper **depuis le processus Gateway réel** (vérifiée
  depuis un contexte `launchd` équivalent, pas depuis le Gateway lui-même).
- Comportement de `perso_contacts` dans le catalogue d'outils de Perso après
  rechargement (le patch est validé en dry-run, pas encore appliqué).
- Envoi réel SMS/mail : **aucun test d'envoi** n'a été effectué.
