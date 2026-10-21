# Sauvegardes, HA et reconstruction

Audit de configuration du 21 octobre 2026. Aucun déclenchement de sauvegarde, bascule ou restauration.

## Proxmox

Tâche quotidienne 10:00, snapshot/zstd, NAS GAN-NAS-720-01, VM 100/102/103/104/105, repeat-missed=1, rétention keep-last=10. La VM 101 TEST n’est pas incluse dans cette tâche. Les tâches vzdump récentes exposées par l’API ont status=OK ; cela ne prouve pas une restauration.

```json
[
  {
    "compress": "zstd",
    "enabled": 1,
    "fleecing": {
      "enabled": 0
    },
    "id": "backup-1b405f70-afcb",
    "mailnotification": "always",
    "mailto": "florian@gangneux.org",
    "mode": "snapshot",
    "next-run": 1792569600,
    "notes-template": "{{guestname}}",
    "notification-mode": "legacy-sendmail",
    "prune-backups": {
      "keep-last": "10"
    },
    "repeat-missed": 1,
    "schedule": "10:00",
    "storage": "GAN-NAS-720-01",
    "type": "vzdump",
    "vmid": "100,102,103,104,105"
  }
]
```

Archives récentes présentes (métadonnées uniquement, aucun parcours du contenu) :

| Archive | Taille octets |
|---|---|
| vzdump-qemu-105-2026_10_20-10_17_28.vma.zst | 1259743044 |
| vzdump-qemu-104-2026_10_20-10_15_05.vma.zst | 8452826963 |
| vzdump-qemu-103-2026_10_20-10_11_30.vma.zst | 6161831332 |
| vzdump-qemu-102-2026_10_20-10_02_24.vma.zst | 27733415355 |
| vzdump-qemu-100-2026_10_20-10_00_12.vma.zst | 7267569292 |
| vzdump-qemu-105-2026_10_19-10_17_16.vma.zst | 1253356076 |
| vzdump-qemu-104-2026_10_19-10_14_52.vma.zst | 8476958937 |
| vzdump-qemu-103-2026_10_19-10_11_15.vma.zst | 5739415194 |
| vzdump-qemu-102-2026_10_19-10_02_16.vma.zst | 27715891380 |
| vzdump-qemu-100-2026_10_19-10_00_03.vma.zst | 7338521306 |


La présence de sauvegardes des disques VM ne démontre pas une sauvegarde indépendante de /srv/docker-shared exposé via VirtioFS. Aucune preuve d’une copie complète de ce volume hors hyperviseur ni de restauration applicative n’est produite. Les snapshots avantinstall des VM Docker sont sur le même stockage.

## Sauvegardes applicatives et synchronisation de certificats

### docker-01

```json
{
  "unit_last_results": {
    "super-agent-backup.service": "Result=success\nExecMainStatus=0\nActiveState=inactive\n",
    "traefik-syno-cert-sync.service": "Result=success\nExecMainStatus=0\nActiveState=inactive\n",
    "super-agent-maintenance.service": "Result=success\nExecMainStatus=0\nActiveState=inactive\n"
  },
  "backup_scripts": [
    {
      "path": "/srv/docker-local/compose/super-agent/ops/lot5h-backup.sh",
      "sha256": "3eb3ddb0b54567a972d1cf189d7377e836b0bcc93c4774599ec632d5552bc154",
      "paths_referenced": [
        "/srv/docker-local/compose/openwebui/compose.yml",
        "/srv/docker-local/compose/super-agent",
        "/srv/docker-local/compose/super-agent/compose.yml",
        "/srv/docker-shared/mcpo/config/config.json",
        "/srv/docker-shared/openwebui/data/webui.db",
        "/srv/docker-shared/super-agent",
        "/srv/docker-shared/super-agent/backup-keys",
        "/srv/docker-shared/super-agent/backups",
        "/srv/docker-shared/super-agent/linked-accounts/linked-accounts.sqlite3",
        "/srv/docker-shared/super-agent/redis/dump.rdb",
        "/srv/docker-shared/super-agent/secrets",
        "/srv/docker-shared/traefik/dynamic/super-agent-oauth.yml"
      ],
      "tools": [
        "pg_dump",
        "tar",
        "docker",
        "redis-cli"
      ]
    }
  ]
}
```

### docker-02

```json
{
  "unit_last_results": {
    "bookstack-backup.service": "Result=success\nExecMainStatus=0\nActiveState=inactive\n",
    "traefik-syno-cert-sync.service": "Result=success\nExecMainStatus=0\nActiveState=inactive\n"
  },
  "backup_scripts": [
    {
      "path": "/srv/docker-local/compose/bookstack/backup.sh",
      "sha256": "7808ddfe727fa67432161cd7f40457cc691d76ec47a05cefa88745730e646c7b",
      "paths_referenced": [
        "/srv/docker-local/compose/bookstack",
        "/srv/docker-shared/bookstack",
        "/srv/docker-shared/traefik/dynamic/bookstack.yml"
      ],
      "tools": [
        "mariadb-dump",
        "tar",
        "docker"
      ]
    }
  ]
}
```

### docker-03

```json
{
  "unit_last_results": {
    "traefik-syno-cert-sync.service": "Result=success\nExecMainStatus=0\nActiveState=inactive\n"
  },
  "backup_scripts": []
}
```

BookStack : timer quotidien 03:30, script mariadb-dump/tar. Super-agent : timer observé, script référençant pg_dump, redis-cli et tar, chemins sous /srv/docker-shared/super-agent/backups et backup-keys. Les derniers résultats systemd sont success ; ni archives applicatives, ni chiffrement effectif, ni restauration n’ont été vérifiés. Une sauvegarde sous docker-shared ne constitue pas à elle seule une protection contre perte de l’hôte.

Le timer traefik-syno-cert-sync existe sur les trois VM et son dernier résultat est success. Son script référence encore /srv/docker-local/compose/traefik/acme/acme.json, chemin local existant distinct du montage ACME actif /srv/docker-shared/traefik/acme/acme.json. Contenus non lus : identité et fraîcheur de ces états ACME non établies. Aucun secret ou certificat privé copié.

## Keepalived

| Instance | VRID | Priorités 01/02/03 | VIP déclarée |
|---|---|---|---|
| VI_WG_ROUTER | 204 | 150 / 140 / 130 | 192.168.201.30 ; 2a01:e0a:8ce:68c1::30 (excluded IPv6) |
| VI_QBITTORRENT | 205 | 130 / 140 / 150 | no_virtual_ipaddress |
| VI_RATIOMASTER | 206 | 130 / 150 / 140 | no_virtual_ipaddress |
| VI_TRAEFIK | 210 | 150 / 140 / 130 | no_virtual_ipaddress |


Trois services Keepalived actifs, unicast sur ens18, état configuré BACKUP, nopreempt. L’état BACKUP dans le fichier n’est pas le rôle runtime élu. La VIP WG est observée sur docker-01. Traefik/qBittorrent/RatioMaster sont actifs sur docker-02 ; les priorités ne décrivent pas le placement instantané. Les scripts notify master/backup/fault/stop sont référencés, ainsi que les contrôles prérequis et les interfaces suivies.

Scripts HA : check-docker.sh, check-*-prereq.sh et *-ha.sh sous /usr/local/sbin. Ils référencent docker, timeout, findmnt/curl selon les services ; les scripts HA utilisent des verrous /run/lock/*-ha.lock locaux. Aucun fencing distribué ni résistance au split-brain n’est démontré. Le résumé statique des scripts ne remplace pas une revue complète de leur logique. Les fichiers Compose WG-Router divergent : sidecar de routes présent seulement sur docker-01.

## Configurations Keepalived sans bloc d’authentification

### docker-01

```text
global_defs {
    router_id docker-01
    enable_script_security
    script_user root
}

vrrp_script chk_docker {
    script "/usr/local/sbin/check-docker.sh"
    interval 10
    timeout 4
    fall 2
    rise 2
    weight -60
}


# BEGIN WG_ROUTER_HA

vrrp_script chk_wg_router_prereq {
    script "/usr/local/sbin/check-wg-router-prereq.sh"
    interval 60
    timeout 5
    fall 3
    rise 2
}

vrrp_instance VI_WG_ROUTER {
    state BACKUP
    interface ens18

    virtual_router_id 204
    priority 150
    advert_int 1


    nopreempt
    unicast_src_ip 192.168.201.21

    unicast_peer {
        192.168.201.22
        192.168.201.23
    }


virtual_ipaddress {
        192.168.201.30/24 dev ens18
    }

    virtual_ipaddress_excluded {
        2a01:e0a:8ce:68c1::30/64 dev ens18
    }


    track_interface {
        ens21
        ens22
    }

    track_script {
        chk_docker
        chk_wg_router_prereq
    }

    notify_master "/usr/local/sbin/wg-router-ha.sh master"
    notify_backup "/usr/local/sbin/wg-router-ha.sh backup"
    notify_fault  "/usr/local/sbin/wg-router-ha.sh fault"
    notify_stop   "/usr/local/sbin/wg-router-ha.sh stop"
}

# END WG_ROUTER_HA

# BEGIN QBITTORRENT_HA

vrrp_script chk_qbittorrent_prereq {
    script "/usr/local/sbin/check-qbittorrent-prereq.sh"
    interval 60
    timeout 4
    fall 2
    rise 2
}

vrrp_instance VI_QBITTORRENT {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 205
    priority 130
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.21

    unicast_peer {
        192.168.201.22
        192.168.201.23
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_qbittorrent_prereq
    }

    notify_master "/usr/local/sbin/qbittorrent-ha.sh master"
    notify_backup "/usr/local/sbin/qbittorrent-ha.sh backup"
    notify_fault  "/usr/local/sbin/qbittorrent-ha.sh fault"
    notify_stop   "/usr/local/sbin/qbittorrent-ha.sh stop"
}

# END QBITTORRENT_HA

# BEGIN RATIOMASTER_HA

vrrp_script chk_ratiomaster_prereq {
    script "/usr/local/sbin/check-ratiomaster-prereq.sh"
    interval 60
    timeout 4
    fall 2
    rise 2
}

vrrp_instance VI_RATIOMASTER {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 206
    priority 130
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.21

    unicast_peer {
        192.168.201.22
        192.168.201.23
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_ratiomaster_prereq
    }

    notify_master "/usr/local/sbin/ratiomaster-ha.sh master"
    notify_backup "/usr/local/sbin/ratiomaster-ha.sh backup"
    notify_fault  "/usr/local/sbin/ratiomaster-ha.sh fault"
    notify_stop   "/usr/local/sbin/ratiomaster-ha.sh stop"
}

# END RATIOMASTER_HA

# BEGIN TRAEFIK_HA

vrrp_script chk_traefik_prereq {
    script "/usr/local/sbin/check-traefik-prereq.sh"
    interval 30
    timeout 5
    fall 2
    rise 2
}

vrrp_instance VI_TRAEFIK {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 210
    priority 150
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.21

    unicast_peer {
        192.168.201.22
        192.168.201.23
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_traefik_prereq
    }

    notify_master "/usr/local/sbin/traefik-ha.sh master"
    notify_backup "/usr/local/sbin/traefik-ha.sh backup"
    notify_fault  "/usr/local/sbin/traefik-ha.sh fault"
    notify_stop   "/usr/local/sbin/traefik-ha.sh stop"
}

# END TRAEFIK_HA
```

### docker-02

```text
global_defs {
    router_id docker-02
    enable_script_security
    script_user root
}

vrrp_script chk_docker {
    script "/usr/local/sbin/check-docker.sh"
    interval 10
    timeout 4
    fall 2
    rise 2
    weight -60
}


# BEGIN WG_ROUTER_HA

vrrp_script chk_wg_router_prereq {
    script "/usr/local/sbin/check-wg-router-prereq.sh"
    interval 60
    timeout 5
    fall 3
    rise 2
}

vrrp_instance VI_WG_ROUTER {
    state BACKUP
    interface ens18

    virtual_router_id 204
    priority 140
    advert_int 1


    nopreempt
    unicast_src_ip 192.168.201.22

    unicast_peer {
        192.168.201.21
        192.168.201.23
    }


virtual_ipaddress {
        192.168.201.30/24 dev ens18
    }

    virtual_ipaddress_excluded {
        2a01:e0a:8ce:68c1::30/64 dev ens18
    }


    track_interface {
        ens21
        ens22
    }

    track_script {
        chk_docker
        chk_wg_router_prereq
    }

    notify_master "/usr/local/sbin/wg-router-ha.sh master"
    notify_backup "/usr/local/sbin/wg-router-ha.sh backup"
    notify_fault  "/usr/local/sbin/wg-router-ha.sh fault"
    notify_stop   "/usr/local/sbin/wg-router-ha.sh stop"
}

# END WG_ROUTER_HA

# BEGIN QBITTORRENT_HA

vrrp_script chk_qbittorrent_prereq {
    script "/usr/local/sbin/check-qbittorrent-prereq.sh"
    interval 60
    timeout 4
    fall 2
    rise 2
}

vrrp_instance VI_QBITTORRENT {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 205
    priority 140
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.22

    unicast_peer {
        192.168.201.21
        192.168.201.23
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_qbittorrent_prereq
    }

    notify_master "/usr/local/sbin/qbittorrent-ha.sh master"
    notify_backup "/usr/local/sbin/qbittorrent-ha.sh backup"
    notify_fault  "/usr/local/sbin/qbittorrent-ha.sh fault"
    notify_stop   "/usr/local/sbin/qbittorrent-ha.sh stop"
}

# END QBITTORRENT_HA

# BEGIN RATIOMASTER_HA

vrrp_script chk_ratiomaster_prereq {
    script "/usr/local/sbin/check-ratiomaster-prereq.sh"
    interval 60
    timeout 4
    fall 2
    rise 2
}

vrrp_instance VI_RATIOMASTER {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 206
    priority 150
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.22

    unicast_peer {
        192.168.201.21
        192.168.201.23
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_ratiomaster_prereq
    }

    notify_master "/usr/local/sbin/ratiomaster-ha.sh master"
    notify_backup "/usr/local/sbin/ratiomaster-ha.sh backup"
    notify_fault  "/usr/local/sbin/ratiomaster-ha.sh fault"
    notify_stop   "/usr/local/sbin/ratiomaster-ha.sh stop"
}

# END RATIOMASTER_HA

# BEGIN TRAEFIK_HA

vrrp_script chk_traefik_prereq {
    script "/usr/local/sbin/check-traefik-prereq.sh"
    interval 30
    timeout 5
    fall 2
    rise 2
}

vrrp_instance VI_TRAEFIK {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 210
    priority 140
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.22

    unicast_peer {
        192.168.201.21
        192.168.201.23
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_traefik_prereq
    }

    notify_master "/usr/local/sbin/traefik-ha.sh master"
    notify_backup "/usr/local/sbin/traefik-ha.sh backup"
    notify_fault  "/usr/local/sbin/traefik-ha.sh fault"
    notify_stop   "/usr/local/sbin/traefik-ha.sh stop"
}

# END TRAEFIK_HA
```

### docker-03

```text
global_defs {
    router_id docker-03
    enable_script_security
    script_user root
}

vrrp_script chk_docker {
    script "/usr/local/sbin/check-docker.sh"
    interval 10
    timeout 4
    fall 2
    rise 2
    weight -60
}


# BEGIN WG_ROUTER_HA

vrrp_script chk_wg_router_prereq {
    script "/usr/local/sbin/check-wg-router-prereq.sh"
    interval 60
    timeout 5
    fall 3
    rise 2
}

vrrp_instance VI_WG_ROUTER {
    state BACKUP
    interface ens18

    virtual_router_id 204
    priority 130
    advert_int 1


    nopreempt
    unicast_src_ip 192.168.201.23

    unicast_peer {
        192.168.201.21
        192.168.201.22
    }


virtual_ipaddress {
        192.168.201.30/24 dev ens18
    }

    virtual_ipaddress_excluded {
        2a01:e0a:8ce:68c1::30/64 dev ens18
    }


    track_interface {
        ens21
        ens22
    }

    track_script {
        chk_docker
        chk_wg_router_prereq
    }

    notify_master "/usr/local/sbin/wg-router-ha.sh master"
    notify_backup "/usr/local/sbin/wg-router-ha.sh backup"
    notify_fault  "/usr/local/sbin/wg-router-ha.sh fault"
    notify_stop   "/usr/local/sbin/wg-router-ha.sh stop"
}

# END WG_ROUTER_HA

# BEGIN QBITTORRENT_HA

vrrp_script chk_qbittorrent_prereq {
    script "/usr/local/sbin/check-qbittorrent-prereq.sh"
    interval 60
    timeout 4
    fall 2
    rise 2
}

vrrp_instance VI_QBITTORRENT {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 205
    priority 150
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.23

    unicast_peer {
        192.168.201.21
        192.168.201.22
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_qbittorrent_prereq
    }

    notify_master "/usr/local/sbin/qbittorrent-ha.sh master"
    notify_backup "/usr/local/sbin/qbittorrent-ha.sh backup"
    notify_fault  "/usr/local/sbin/qbittorrent-ha.sh fault"
    notify_stop   "/usr/local/sbin/qbittorrent-ha.sh stop"
}

# END QBITTORRENT_HA

# BEGIN RATIOMASTER_HA

vrrp_script chk_ratiomaster_prereq {
    script "/usr/local/sbin/check-ratiomaster-prereq.sh"
    interval 60
    timeout 4
    fall 2
    rise 2
}

vrrp_instance VI_RATIOMASTER {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 206
    priority 140
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.23

    unicast_peer {
        192.168.201.21
        192.168.201.22
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_ratiomaster_prereq
    }

    notify_master "/usr/local/sbin/ratiomaster-ha.sh master"
    notify_backup "/usr/local/sbin/ratiomaster-ha.sh backup"
    notify_fault  "/usr/local/sbin/ratiomaster-ha.sh fault"
    notify_stop   "/usr/local/sbin/ratiomaster-ha.sh stop"
}

# END RATIOMASTER_HA

# BEGIN TRAEFIK_HA

vrrp_script chk_traefik_prereq {
    script "/usr/local/sbin/check-traefik-prereq.sh"
    interval 30
    timeout 5
    fall 2
    rise 2
}

vrrp_instance VI_TRAEFIK {
    state BACKUP
    interface ens18

    version 3
    virtual_router_id 210
    priority 130
    advert_int 1

    nopreempt
    no_virtual_ipaddress

    unicast_src_ip 192.168.201.23

    unicast_peer {
        192.168.201.21
        192.168.201.22
    }

    check_unicast_src

    track_interface {
        ens20
    }

    track_script {
        chk_traefik_prereq
    }

    notify_master "/usr/local/sbin/traefik-ha.sh master"
    notify_backup "/usr/local/sbin/traefik-ha.sh backup"
    notify_fault  "/usr/local/sbin/traefik-ha.sh fault"
    notify_stop   "/usr/local/sbin/traefik-ha.sh stop"
}

# END TRAEFIK_HA
```

## Limites de qualification

NOT_RUN : redémarrage réseau, perte d’un manager, bascule de chaque application, perte du stockage/NAS, panne d’hyperviseur, double maître, fencing, reprise sur nœud reconstruit, restauration de sauvegarde, test de génération IA, exécution n8n, OAuth, trafic VPN et session Minecraft. Aucun de ces effets n’est déduit de healthy, success, de trois managers ou de la présence d’un montage partagé.
