# Perso — contexte familial, Contacts Apple et socle professionnel

Paquet de préparation (Phase A). **Rien n'est déployé** : aucun workspace actif,
aucune configuration, aucun service, aucune autorisation macOS n'a été modifié.

## Contenu

| Chemin | Rôle |
| --- | --- |
| `contacts-tool/` | Outil Swift `perso-contacts` (CNContactStore, lecture seule) |
| `workspace-perso/` | Annuaire familial, fiches, skill, patches USER/AGENTS |
| `workspace-pro/` | Socle professionnel partagé, patches USER/AGENTS |
| `config/openclaw.patch.json` | Patch de configuration (validé en dry-run) |
| `tests/` | Tests unitaires, simulation de résolution, scénarios |
| `deploy.sh` / `rollback.sh` | Application et retour arrière idempotents |

## Démarrage rapide

```sh
./contacts-tool/build.sh          # compile dans contacts-tool/build/
./tests/run-tests.sh              # 13 contrôles, lecture seule
./tests/simulate.sh               # chaîne de résolution, aucun envoi
```

## Documentation

- [DIAGNOSTIC.md](DIAGNOSTIC.md) — état réel constaté de l'installation
- [ARCHITECTURE.md](ARCHITECTURE.md) — conception, isolation, limites
- [DEPLOIEMENT.md](DEPLOIEMENT.md) — procédure Phase B et retour arrière
- [DEPLOIEMENT-REALISE.md](DEPLOIEMENT-REALISE.md) — ce qui a été appliqué le 2026-10-20
- [RECETTE.md](RECETTE.md) — tests exécutés depuis le Gateway
- [osascript-safeBins.md](osascript-safeBins.md) — constat et correction envisageable
