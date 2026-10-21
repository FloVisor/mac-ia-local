# bookstack

Instantané du 21 octobre 2026. BookStack et MariaDB sur docker-02 ; application sur TRAEFIK_BACKEND et réseau privé bookstack_bookstack_private, base sur réseau privé. Données et secrets sous docker-shared. Métadonnées vérifiées : app_key/db_password/db_root_password en 0444, mais répertoires bookstack et secrets en 0700 root ; ne pas conclure à une lecture possible par tous les utilisateurs du nœud à partir des seuls droits des fichiers. Contenus jamais lus. HTTP 302 frontend et 200 après redirection backend. Sauvegarde BookStack déclarée et dernier résultat systemd success, sans restauration testée.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-02 | BookStack | running / sans état health | lscr.io/linuxserver/bookstack:v26.09.1-ls288 | 0 |
| docker-02 | BookStackDB | running / healthy | mariadb:11.8.9 | 0 |


## docker-02 — BookStack

ID : `6e6f6c565d6ffb3c254145ee8f6de9f0282607ae4ae0070d49ab1125d1ac1a84`. Image effective : `sha256:0d66f65417fa667085849bf9b32b412ec9a90420773c4f47a95138c4711876b7`. Création : 2026-10-19T20:19:07.723599991Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/bookstack/app | /config | True |
| bind | /srv/docker-shared/bookstack/secrets/app_key | /run/secrets/app_key | False |
| bind | /srv/docker-shared/bookstack/secrets/db_password | /run/secrets/db_password | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.9 |  | ["BookStack", "bookstack", "bookstack"] |
| bookstack_bookstack_private | 172.19.0.3 |  | ["BookStack", "bookstack"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "443/tcp": null,
  "80/tcp": null
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "unless-stopped",
    "MaximumRetryCount": 0
  },
  "NetworkMode": "TRAEFIK_BACKEND",
  "PortBindings": {},
  "Privileged": false,
  "ReadonlyRootfs": false,
  "CapAdd": null,
  "CapDrop": null,
  "SecurityOpt": null,
  "Devices": null,
  "DeviceRequests": null,
  "PidMode": "",
  "IpcMode": "private",
  "Memory": 0,
  "MemorySwap": 0,
  "NanoCpus": 0,
  "CpuShares": 0,
  "PidsLimit": null,
  "Ulimits": null,
  "LogConfig": {
    "Type": "json-file",
    "Config": {}
  },
  "Dns": null,
  "ExtraHosts": []
}
```

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `FILE__DB_PASSWORD`, `DB_HOST`, `FILE__APP_KEY`, `APP_LANG`, `APP_URL`, `DB_PORT`, `DB_DATABASE`, `APP_DEBUG`, `PGID`, `SESSION_SECURE_COOKIE`, `PUID`, `DB_USERNAME`, `STORAGE_TYPE`, `TZ`, `PATH`, `PS1`, `HOME`, `TERM`, `S6_CMD_WAIT_FOR_SERVICES_MAXTIME`, `S6_VERBOSITY`, `S6_STAGE2_HOOK`, `VIRTUAL_ENV`, `PHP_INI_SCAN_DIR`, `LSIO_FIRST_PARTY`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## docker-02 — BookStackDB

ID : `41f36f10a085fdb0639b79c5bf5bc3e0f2bc43129712bcf9c7d5bc512e83982b`. Image effective : `sha256:f16d7a344413e519dff518f27bdb221388f84b0d274c97c4fb5f2cb0dc1b34fa`. Création : 2026-10-19T20:06:12.569276683Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/bookstack/secrets/db_password | /run/secrets/db_password | False |
| bind | /srv/docker-shared/bookstack/secrets/db_root_password | /run/secrets/db_root_password | False |
| bind | /srv/docker-shared/bookstack/mariadb | /var/lib/mysql | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| bookstack_bookstack_private | 172.19.0.2 |  | ["BookStackDB", "database", "bookstack-db"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "3306/tcp": null
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "unless-stopped",
    "MaximumRetryCount": 0
  },
  "NetworkMode": "bookstack_bookstack_private",
  "PortBindings": {},
  "Privileged": false,
  "ReadonlyRootfs": false,
  "CapAdd": null,
  "CapDrop": null,
  "SecurityOpt": null,
  "Devices": null,
  "DeviceRequests": null,
  "PidMode": "",
  "IpcMode": "private",
  "Memory": 0,
  "MemorySwap": 0,
  "NanoCpus": 0,
  "CpuShares": 0,
  "PidsLimit": null,
  "Ulimits": null,
  "LogConfig": {
    "Type": "json-file",
    "Config": {}
  },
  "Dns": null,
  "ExtraHosts": []
}
```

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : True.

Noms de variables seulement (valeurs exclues) : `MARIADB_PASSWORD_FILE`, `MARIADB_ROOT_PASSWORD_FILE`, `TZ`, `MARIADB_DATABASE`, `MARIADB_USER`, `PATH`, `GOSU_VERSION`, `LANG`, `MARIADB_VERSION`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/bookstack/compose.yml`. Nœuds : docker-02. SHA-256 : `bf8af59e14193c6a5456bd5556af45f33a8f73e2370d26c3b892672f34b5f9e1`.

```json
{
  "services": {
    "database": {
      "image": "mariadb:11.8.9",
      "container_name": "BookStackDB",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/bookstack/mariadb:/var/lib/mysql"
      ],
      "networks": {
        "bookstack_private": {
          "aliases": [
            "bookstack-db"
          ]
        }
      },
      "secrets": [
        "db_password",
        "db_root_password"
      ],
      "environment_keys_only": [
        "TZ",
        "MARIADB_DATABASE",
        "MARIADB_USER",
        "MARIADB_PASSWORD_FILE",
        "MARIADB_ROOT_PASSWORD_FILE"
      ],
      "healthcheck_present": true,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "bookstack": {
      "image": "lscr.io/linuxserver/bookstack:v26.09.1-ls288",
      "container_name": "BookStack",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/bookstack/app:/config"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "bookstack"
          ]
        },
        "bookstack_private": null
      },
      "depends_on": {
        "database": {
          "condition": "service_healthy"
        }
      },
      "secrets": [
        "app_key",
        "db_password"
      ],
      "environment_keys_only": [
        "PUID",
        "PGID",
        "TZ",
        "APP_URL",
        "APP_LANG",
        "APP_DEBUG",
        "SESSION_SECURE_COOKIE",
        "FILE__APP_KEY",
        "DB_HOST",
        "DB_PORT",
        "DB_DATABASE",
        "DB_USERNAME",
        "FILE__DB_PASSWORD",
        "STORAGE_TYPE"
      ],
      "healthcheck_present": false,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    }
  },
  "networks": {
    "TRAEFIK_BACKEND": {
      "external": true,
      "name": "TRAEFIK_BACKEND"
    },
    "bookstack_private": {
      "driver": "bridge",
      "internal": true
    }
  },
  "secrets": {
    "app_key": {
      "file": "/srv/docker-shared/bookstack/secrets/app_key"
    },
    "db_password": "[REDACTED]",
    "db_root_password": "[REDACTED]"
  }
}
```
