# Docker Swarm et systèmes invités

Instantané du 21 octobre 2026, accès SSH directs depuis le Mac.

| Nœud | Version Docker | Conteneurs actifs / total | Manager | État networking.service |
|---|---|---|---|---|
| docker-01 | 29.8.0 | 17/21 | Reachable | Result=exit-code ; ExecMainStatus=1 ; ActiveState=failed ; SubState=failed |
| docker-02 | 29.8.0 | 9/9 | Reachable | Result=success ; ExecMainStatus=0 ; ActiveState=active ; SubState=exited |
| docker-03 | 29.8.0 | 5/5 | Leader | Result=exit-code ; ExecMainStatus=1 ; ActiveState=failed ; SubState=failed |


Trois managers Ready/Active, Debian 13, racine Docker /srv/docker-local/docker. AutoLockManagers=false. Aucun test de perte de quorum ou rotation de certificat.

Voir [tous les conteneurs](containers/README.md) pour images, états, ressources, montages et configurations par application.

## Services Swarm

| Service | Mode | Placement | Image |
|---|---|---|---|
| avahi_reflector | {"Replicated": {"Replicas": 1}} | {} | local/avahi-reflector:1.0 |
| portainer_agent | {"Global": {}} | {"Constraints": ["node.platform.os == linux"], "Platforms": [{"Architecture": "amd64", "OS": "linux"}, {"Architecture": "arm64", "OS": "linux"}, {"OS": "linux"}, {"Architecture": "ppc64le", "OS": "linux"}, {"Architecture": "amd64", "OS": "windows"}]} | portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba |
| portainer_portainer | {"Replicated": {"Replicas": 1}} | {"Constraints": ["node.role == manager"], "Platforms": [{"Architecture": "amd64", "OS": "linux"}, {"Architecture": "arm64", "OS": "linux"}, {"OS": "linux"}, {"Architecture": "ppc64le", "OS": "linux"}, {"Architecture": "amd64", "OS": "windows"}]} | portainer/portainer-ce:lts@sha256:511f3f06c96fe3b993ebeaafde311c1959cae73a7ef825dba6397d51b450dffa |


Réplicas constatés : avahi 1/1, agent Portainer global 3/3, serveur Portainer 1/1. Les conteneurs Compose autonomes ne sont pas gérés par l’ordonnanceur Swarm.

## Système et surface d’accès

networking.service est failed, Result=exit-code, ExecMainStatus=1 sur docker-01 et docker-03 ; docker-02 est active/exited avec résultat success. Cela n’annule pas les interfaces actives, mais la configuration au prochain cycle réseau reste à diagnostiquer. Aucun restart effectué.

Sur les trois VM, sshd -T indique permitrootlogin=yes et passwordauthentication=yes, en plus de pubkeyauthentication=yes. L’authentification par clé est validée, mais l’authentification par mot de passe n’est pas désactivée. Règles nft, listeners, interfaces, routes et timers sont dans les captures filtrées ; aucune preuve d’isolement depuis un réseau externe non autorisé.

## docker-01

Capture : [système, Docker et réseaux](evidence/2026-10-21/docker-01.json), [unités, scripts et permissions](evidence/2026-10-21/docker-01.details.json).

Timers observés :
```text
NEXT                             LEFT LAST                               PASSED UNIT                          ACTIVATES
Wed 2026-10-21 08:29:14 CEST 2min 46s Wed 2026-10-21 08:24:14 CEST 2min 13s ago super-agent-monitor.timer     super-agent-monitor.service
Wed 2026-10-21 09:01:05 CEST    34min Wed 2026-10-21 08:00:12 CEST    26min ago traefik-syno-cert-sync.timer  traefik-syno-cert-sync.service
Wed 2026-10-21 12:04:41 CEST 3h 38min Tue 2026-10-20 12:04:41 CEST      20h ago systemd-tmpfiles-clean.timer  systemd-tmpfiles-clean.service
Wed 2026-10-21 12:49:59 CEST 4h 23min Wed 2026-10-21 02:31:41 CEST 5h 54min ago apt-daily.timer               apt-daily.service
Thu 2026-10-22 00:00:00 CEST      15h Wed 2026-10-21 00:00:03 CEST       8h ago dpkg-db-backup.timer          dpkg-db-backup.service
Thu 2026-10-22 00:02:36 CEST      15h Wed 2026-10-21 00:48:41 CEST       7h ago logrotate.timer               logrotate.service
Thu 2026-10-22 00:22:19 CEST      15h Wed 2026-10-21 04:02:10 CEST 4h 24min ago man-db.timer                  man-db.service
Thu 2026-10-22 02:23:59 CEST      17h Wed 2026-10-21 02:17:41 CEST       6h ago super-agent-backup.timer      super-agent-backup.service
Thu 2026-10-22 03:31:18 CEST      19h Wed 2026-10-21 03:38:12 CEST 4h 48min ago super-agent-maintenance.timer super-agent-maintenance.service
Thu 2026-10-22 06:36:14 CEST      22h Wed 2026-10-21 06:46:41 CEST 1h 39min ago apt-daily-upgrade.timer       apt-daily-upgrade.service
Sun 2026-10-25 03:10:11 CET    3 days Sun 2026-10-18 03:10:12 CEST   3 days ago e2scrub_all.timer             e2scrub_all.service
Mon 2026-10-26 01:30:57 CET    4 days Mon 2026-10-19 01:14:03 CEST   2 days ago fstrim.timer                  fstrim.service

12 timers listed.
```

## docker-02

Capture : [système, Docker et réseaux](evidence/2026-10-21/docker-02.json), [unités, scripts et permissions](evidence/2026-10-21/docker-02.details.json).

Timers observés :
```text
NEXT                             LEFT LAST                               PASSED UNIT                         ACTIVATES
Wed 2026-10-21 09:01:25 CEST    34min Wed 2026-10-21 08:01:34 CEST    24min ago traefik-syno-cert-sync.timer traefik-syno-cert-sync.service
Wed 2026-10-21 11:08:43 CEST 2h 42min Wed 2026-10-21 01:26:30 CEST       6h ago apt-daily.timer              apt-daily.service
Wed 2026-10-21 12:06:33 CEST 3h 40min Tue 2026-10-20 12:06:33 CEST      20h ago systemd-tmpfiles-clean.timer systemd-tmpfiles-clean.service
Thu 2026-10-22 00:00:00 CEST      15h Wed 2026-10-21 00:00:00 CEST       8h ago dpkg-db-backup.timer         dpkg-db-backup.service
Thu 2026-10-22 00:02:24 CEST      15h Wed 2026-10-21 00:47:34 CEST       7h ago logrotate.timer              logrotate.service
Thu 2026-10-22 03:30:00 CEST      19h Wed 2026-10-21 03:30:00 CEST 4h 56min ago bookstack-backup.timer       bookstack-backup.service
Thu 2026-10-22 03:43:12 CEST      19h Wed 2026-10-21 04:21:10 CEST  4h 5min ago man-db.timer                 man-db.service
Thu 2026-10-22 06:52:12 CEST      22h Wed 2026-10-21 06:57:34 CEST 1h 28min ago apt-daily-upgrade.timer      apt-daily-upgrade.service
Sun 2026-10-25 03:10:08 CET    3 days Sun 2026-10-18 03:10:50 CEST   3 days ago e2scrub_all.timer            e2scrub_all.service
Mon 2026-10-26 00:02:41 CET    4 days Mon 2026-10-19 00:46:10 CEST   2 days ago fstrim.timer                 fstrim.service

10 timers listed.
```

## docker-03

Capture : [système, Docker et réseaux](evidence/2026-10-21/docker-03.json), [unités, scripts et permissions](evidence/2026-10-21/docker-03.details.json).

Timers observés :
```text
NEXT                             LEFT LAST                               PASSED UNIT                         ACTIVATES
Wed 2026-10-21 09:00:56 CEST    34min Wed 2026-10-21 08:01:35 CEST    24min ago traefik-syno-cert-sync.timer traefik-syno-cert-sync.service
Wed 2026-10-21 09:32:44 CEST  1h 6min Tue 2026-10-20 22:57:36 CEST       9h ago apt-daily.timer              apt-daily.service
Wed 2026-10-21 12:06:36 CEST 3h 40min Tue 2026-10-20 12:06:36 CEST      20h ago systemd-tmpfiles-clean.timer systemd-tmpfiles-clean.service
Thu 2026-10-22 00:00:00 CEST      15h Wed 2026-10-21 00:00:05 CEST       8h ago dpkg-db-backup.timer         dpkg-db-backup.service
Thu 2026-10-22 00:50:27 CEST      16h Wed 2026-10-21 00:37:37 CEST       7h ago logrotate.timer              logrotate.service
Thu 2026-10-22 06:25:00 CEST      21h Wed 2026-10-21 06:48:37 CEST 1h 37min ago apt-daily-upgrade.timer      apt-daily-upgrade.service
Thu 2026-10-22 06:42:26 CEST      22h Wed 2026-10-21 00:36:52 CEST       7h ago man-db.timer                 man-db.service
Sun 2026-10-25 03:10:38 CET    3 days Sun 2026-10-18 03:11:05 CEST   3 days ago e2scrub_all.timer            e2scrub_all.service
Mon 2026-10-26 01:17:55 CET    4 days Mon 2026-10-19 01:26:05 CEST   2 days ago fstrim.timer                 fstrim.service

9 timers listed.
```
