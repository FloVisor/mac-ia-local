# wg-admin

Instantané du 21 octobre 2026. WG-Companion tourne sur docker-01 ; son port 8765 est publié sur les adresses LAN propres au nœud (.21 et ::21), pas sur la VIP .30 dans les bindings Docker. Le socket proxy monte docker.sock en lecture seule ; cela ne prouve pas que son API Docker est inoffensive. Les backends .22/.23 refusent la connexion à cet instant, compatible avec un seul compagnon actif. Configuration de droits de proxy et authentification applicative non qualifiées.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | WG-Companion | running / sans état health | ghcr.io/aerya/gluetun-companion:latest | 0 |
| docker-01 | WG-Socket-Proxy | running / sans état health | tecnativa/docker-socket-proxy:latest | 0 |


## docker-01 — WG-Companion

ID : `aeaccf66180ed9e59638c1e9b148598d8940dc1c673491bbf3dc84f2e71aecbe`. Image effective : `sha256:0bdd62839cf14af50514431ab09ab858f09a6b08eb03c734f5707aeb1a91e8c0`. Création : 2026-09-15T18:17:37.240989726Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/wg-admin/companion | /data | True |
| bind | /srv/docker-shared/wg-router/gluetun | /gluetun | False |
| bind | /srv/docker-local/compose/wg-router | /srv/docker-local/compose/wg-router | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| WG_Internal | 172.31.204.4 |  | ["WG-Companion", "companion"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "8765/tcp": [
    {
      "HostIp": "192.168.201.21",
      "HostPort": "8765"
    },
    {
      "HostIp": "2a01:e0a:8ce:68c1::21",
      "HostPort": "8765"
    }
  ]
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "on-failure",
    "MaximumRetryCount": 5
  },
  "NetworkMode": "WG_Internal",
  "PortBindings": {
    "8765/tcp": [
      {
        "HostIp": "192.168.201.21",
        "HostPort": "8765"
      },
      {
        "HostIp": "2a01:e0a:8ce:68c1::21",
        "HostPort": "8765"
      }
    ]
  },
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

Noms de variables seulement (valeurs exclues) : `GLUETUN_PROXY_PORT`, `DATA_DIR`, `GLUETUN_CONTAINER`, `TZ`, `SECRET_KEY`, `GLUETUN_HOST`, `DOCKER_HOST`, `COMPOSE_DIR`, `PATH`, `PYTHON_VERSION`, `PYTHON_SHA256`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — WG-Socket-Proxy

ID : `11823062c54e6c24f18a97fc4090871780b485b0c7580addd8acc96629225938`. Image effective : `sha256:1f5038b54f06c3e18422902cf00ba21803d1c97805aae032e5e6673d532d3459`. Création : 2026-09-15T11:10:21.714792938Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /var/run/docker.sock | /var/run/docker.sock | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| WG_Internal | 172.31.204.3 |  | ["WG-Socket-Proxy", "socket-proxy"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "2375/tcp": null
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "on-failure",
    "MaximumRetryCount": 5
  },
  "NetworkMode": "WG_Internal",
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

Utilisateur : `root`. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `POST`, `EXEC`, `NETWORKS`, `EVENTS`, `VOLUMES`, `IMAGES`, `DELETE`, `CONTAINERS`, `PATH`, `HAPROXY_VERSION`, `HAPROXY_URL`, `HAPROXY_SHA256`, `ALLOW_RESTARTS`, `ALLOW_STOP`, `ALLOW_START`, `AUTH`, `BUILD`, `COMMIT`, `CONFIGS`, `DISABLE_IPV6`, `DISTRIBUTION`, `GRPC`, `INFO`, `LOG_LEVEL`, `NODES`, `PING`, `PLUGINS`, `SECRETS`, `SERVICES`, `SESSION`, `SOCKET_PATH`, `SWARM`, `SYSTEM`, `TASKS`, `VERSION`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/wg-admin/compose.yml`. Nœuds : docker-01, docker-02, docker-03. SHA-256 : `01bca7c7713457f89edc5376934af66778ab044a24508dfb8ad408ca48bd787b`.

```json
{
  "services": {
    "socket-proxy": {
      "image": "tecnativa/docker-socket-proxy:latest",
      "container_name": "WG-Socket-Proxy",
      "restart": "on-failure:5",
      "volumes": [
        "/var/run/docker.sock:/var/run/docker.sock:ro"
      ],
      "networks": {
        "WG_Internal": {
          "ipv4_address": "172.31.204.3"
        }
      },
      "environment_keys_only": [
        "CONTAINERS",
        "EVENTS",
        "EXEC",
        "IMAGES",
        "NETWORKS",
        "VOLUMES",
        "POST",
        "DELETE"
      ],
      "healthcheck_present": false,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "companion": {
      "image": "ghcr.io/aerya/gluetun-companion:latest",
      "container_name": "WG-Companion",
      "restart": "on-failure:5",
      "ports": [
        "${COMPANION_BIND_IPV4}:8765:8765/tcp",
        "[${COMPANION_BIND_IPV6}]:8765:8765/tcp"
      ],
      "volumes": [
        "/srv/docker-shared/wg-admin/companion:/data",
        "/srv/docker-local/compose/wg-router:/srv/docker-local/compose/wg-router:rw",
        "/srv/docker-shared/wg-router/gluetun:/gluetun:ro"
      ],
      "networks": {
        "WG_Internal": {
          "ipv4_address": "172.31.204.4"
        }
      },
      "depends_on": [
        "socket-proxy"
      ],
      "environment_keys_only": [
        "TZ",
        "SECRET_KEY",
        "DATA_DIR",
        "GLUETUN_HOST",
        "GLUETUN_PROXY_PORT",
        "GLUETUN_CONTAINER",
        "COMPOSE_DIR",
        "DOCKER_HOST"
      ],
      "healthcheck_present": false,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    }
  },
  "networks": {
    "WG_Internal": {
      "external": true,
      "name": "WG_Internal"
    }
  }
}
```
