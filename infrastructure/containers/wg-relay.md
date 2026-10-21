# wg-relay

Instantané du 21 octobre 2026. Un relais par nœud sur le bridge local WG_Internal. La présence de trois conteneurs ne rend pas le bridge inter-nœuds. Les arguments de redirection ne sont pas exportés par le filtre général de commande ; leur exécution de bout en bout n’a pas été testée.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | WG-Companion-Relay | running / sans état health | alpine/socat:1.8.1.3 | 0 |
| docker-02 | WG-Companion-Relay | running / sans état health | alpine/socat:1.8.1.3 | 0 |
| docker-03 | WG-Companion-Relay | running / sans état health | alpine/socat:1.8.1.3 | 0 |


## docker-01 — WG-Companion-Relay

ID : `00a8ee1a1a3e742dc2d2c60d28a0617b3d4c26882585d1a3935f6788a6c59cbb`. Image effective : `sha256:c5a091e1e735a90aa941a5828529dbe6c6157407a8047a9aa473faa133361b82`. Création : 2026-09-13T11:51:33.98891431Z.

### Stockage réel

Aucun montage déclaré ; la couche writable reste locale. Cela ne prouve pas que l’application n’y écrit aucune donnée importante.

### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| WG_Internal | 172.31.204.5 |  | ["WG-Companion-Relay", "relay"] |


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
  "Dns": [],
  "ExtraHosts": []
}
```

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-02 — WG-Companion-Relay

ID : `d41d2aa26b50e748b53283759e23165f7dd8587058edc88917a6cd875f3f8b14`. Image effective : `sha256:c5a091e1e735a90aa941a5828529dbe6c6157407a8047a9aa473faa133361b82`. Création : 2026-09-15T09:19:44.434369593Z.

### Stockage réel

Aucun montage déclaré ; la couche writable reste locale. Cela ne prouve pas que l’application n’y écrit aucune donnée importante.

### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| WG_Internal | 172.31.204.5 |  | ["WG-Companion-Relay", "relay"] |


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
  "Dns": [],
  "ExtraHosts": []
}
```

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## docker-03 — WG-Companion-Relay

ID : `6d145cb9c49adf24a45d269ece581eea31db88dca8420dcb492a72d9b4813a95`. Image effective : `sha256:c5a091e1e735a90aa941a5828529dbe6c6157407a8047a9aa473faa133361b82`. Création : 2026-09-15T15:02:32.121794199Z.

### Stockage réel

Aucun montage déclaré ; la couche writable reste locale. Cela ne prouve pas que l’application n’y écrit aucune donnée importante.

### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| WG_Internal | 172.31.204.5 |  | ["WG-Companion-Relay", "relay"] |


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

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-03](../evidence/2026-10-21/docker-03.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/wg-relay/compose.yml`. Nœuds : docker-01, docker-02, docker-03. SHA-256 : `0d075324697c668c0d9128ae469e1dd87d00beb6eb53a56c79b080dd3c6c439a`.

```json
{
  "services": {
    "relay": {
      "image": "alpine/socat:1.8.1.3",
      "container_name": "WG-Companion-Relay",
      "restart": "unless-stopped",
      "networks": {
        "WG_Internal": {
          "ipv4_address": "172.31.204.5"
        }
      },
      "environment_keys_only": [],
      "healthcheck_present": false,
      "command_present": true,
      "entrypoint_present": true,
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
