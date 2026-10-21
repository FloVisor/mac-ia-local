# homeassistant

Instantané du 21 octobre 2026. Conteneur privilégié, avec /run/dbus et /etc/localtime montés ; configuration sur docker-shared. Connecté à TRAEFIK_BACKEND et homeassistant_default, à justifier selon les besoins réels. Frontend HEAD / : 405 ; backend depuis Traefik : 200. Pas de panne déduite du refus de méthode HEAD. Aucune session authentifiée ou automation exécutée.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | HomeAssistant | running / sans état health | ghcr.io/home-assistant/home-assistant:2026.9.2 | 0 |


## docker-01 — HomeAssistant

ID : `246a8d73389f86f92803b0e14864468f14c24b85b08d89bcaecd1a4ca6817295`. Image effective : `sha256:a1bc133af84ee6505fe2c266d9805b7c75b780dfdc188edfee3b11e8f3cd8efe`. Création : 2026-09-15T19:36:09.056476189Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/homeassistant/config | /config | True |
| bind | /etc/localtime | /etc/localtime | False |
| bind | /run/dbus | /run/dbus | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.10 |  | ["homeassistant"] |
| homeassistant_default | 172.19.0.2 |  | ["HomeAssistant", "homeassistant"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{}
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
  "Privileged": true,
  "ReadonlyRootfs": false,
  "CapAdd": null,
  "CapDrop": null,
  "SecurityOpt": [
    "label=disable"
  ],
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

Noms de variables seulement (valeurs exclues) : `TZ`, `PATH`, `LANG`, `S6_BEHAVIOUR_IF_STAGE2_FAILS`, `S6_CMD_WAIT_FOR_SERVICES_MAXTIME`, `S6_CMD_WAIT_FOR_SERVICES`, `S6_SERVICES_READYTIME`, `PIP_EXTRA_INDEX_URL`, `UV_EXTRA_INDEX_URL`, `S6_SERVICES_GRACETIME`, `UV_SYSTEM_PYTHON`, `UV_NO_CACHE`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/homeassistant/compose.yml`. Nœuds : docker-01, docker-02, docker-03. SHA-256 : `6e47141d2944e88571bff0d98aa0f5bfc65923002aca02d6b6f7ecc81c1c8400`.

```json
{
  "services": {
    "homeassistant": {
      "image": "ghcr.io/home-assistant/home-assistant:2026.9.2",
      "container_name": "HomeAssistant",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/homeassistant/config:/config",
        "/etc/localtime:/etc/localtime:ro",
        "/run/dbus:/run/dbus:ro"
      ],
      "networks": {
        "default": {},
        "TRAEFIK_BACKEND": {
          "aliases": [
            "homeassistant"
          ]
        }
      },
      "privileged": true,
      "environment_keys_only": [
        "TZ"
      ],
      "healthcheck_present": false,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    }
  },
  "networks": {
    "default": {
      "driver": "bridge"
    },
    "TRAEFIK_BACKEND": {
      "name": "TRAEFIK_BACKEND",
      "external": true
    }
  }
}
```
