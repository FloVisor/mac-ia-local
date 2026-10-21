# Accès SSH directs depuis le Mac

Vérifications du 21 octobre 2026. Aucun rebond nécessaire. Aucun secret enregistré dans le dépôt, aucune configuration SSH modifiée.

| Cible | Chemin retenu | État |
|---|---|---|
| docker-01 / 192.168.201.21 | Mac → root@docker-01 | PASS (vérification précédente) |
| docker-02 / 192.168.201.22 | Mac → root@docker-02 | PASS : publickey seule, hostname docker-02 |
| docker-03 / 192.168.201.23 | Mac → root@docker-03 | PASS : publickey seule, hostname docker-03 |
| Proxmox / 192.168.201.39 | Mac → root@192.168.201.39 | PASS : publickey seule (vérification précédente) |

Commandes pour les accès directs :

```bash
ssh root@docker-01
ssh root@docker-02
ssh root@docker-03
ssh root@192.168.201.39
```

Pour docker-02 et docker-03, test réellement exécuté avec BatchMode=yes, StrictHostKeyChecking=yes, PreferredAuthentications=publickey et ConnectTimeout=8, commande distante hostname : exit 0 pour chacun. Aucun mot de passe ou ajout de clé hôte demandé.

ssh -G confirme respectivement hostname 192.168.201.22 et 192.168.201.23, user root, sans ProxyJump ni ProxyCommand configuré : les accès testés sont bien directs.

L'accès Proxmox par clé depuis le Mac a été validé après installation de la clé par l'utilisateur. Le refus historique depuis docker-01 n'est plus un blocage du chemin retenu ; aucun rebond à mettre en place.
