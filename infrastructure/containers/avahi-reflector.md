# avahi_reflector

Instantané du 21 octobre 2026. Service Swarm une réplique sur docker-02, réseaux MACVLAN FAMILLE_SWARM et PRO_SWARM. Une ancienne tâche arrêtée sur docker-01 conserve un état unhealthy historique. La tâche active est healthy. Réflexion mDNS réelle et absence de fuite inter-réseaux non testées.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | avahi_reflector.1.sr8xasobsqrkoue6wsseqdfmk | exited / unhealthy | local/avahi-reflector:1.0 | 0 |
| docker-02 | avahi_reflector.1.qhh4btwznq4zz0pt5s1ot2hxi | running / healthy | local/avahi-reflector:1.0 | 0 |


## docker-01 — avahi_reflector.1.sr8xasobsqrkoue6wsseqdfmk

ID : `4b4ef1db1d0457f3468c53acc85030ae969aba9bf9ecb7f17d012c8b1522166a`. Image effective : `sha256:8b6c99b6ca50c84843c3029ca15ff09f7e4781214659f7b54f3be288906a68fb`. Création : 2026-09-15T09:49:57.620290604Z.

### Stockage réel

Aucun montage déclaré ; la couche writable reste locale. Cela ne prouve pas que l’application n’y écrit aucune donnée importante.

### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| FAMILLE_SWARM |  |  | None |
| PRO_SWARM |  |  | None |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "no",
    "MaximumRetryCount": 0
  },
  "NetworkMode": "bridge",
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
  "Ulimits": [],
  "LogConfig": {
    "Type": "json-file",
    "Config": {}
  },
  "Dns": null,
  "ExtraHosts": null
}
```

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : True.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-02 — avahi_reflector.1.qhh4btwznq4zz0pt5s1ot2hxi

ID : `b9741248bb0ab9755eab8de960a14c79c79cb599e25906f374cece7f97fdd75e`. Image effective : `sha256:8b6c99b6ca50c84843c3029ca15ff09f7e4781214659f7b54f3be288906a68fb`. Création : 2026-09-27T14:11:40.681870748Z.

### Stockage réel

Aucun montage déclaré ; la couche writable reste locale. Cela ne prouve pas que l’application n’y écrit aucune donnée importante.

### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| FAMILLE_SWARM | 192.168.201.80 | 2a01:e0a:8ce:68c1::80 | None |
| PRO_SWARM | 192.168.202.80 | 2a01:e0a:8ce:68c2::80 | None |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "no",
    "MaximumRetryCount": 0
  },
  "NetworkMode": "bridge",
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
  "Ulimits": [],
  "LogConfig": {
    "Type": "json-file",
    "Config": {}
  },
  "Dns": null,
  "ExtraHosts": null
}
```

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : True.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## Déclaration Swarm filtrée

```json
{
  "ID": "l8fgcur6mr7qydnrlzp79vi92",
  "name": "avahi_reflector",
  "mode": {
    "Replicated": {
      "Replicas": 1
    }
  },
  "task": {
    "Resources": {},
    "RestartPolicy": {
      "Condition": "any",
      "Delay": 5000000000,
      "MaxAttempts": 0
    },
    "Placement": {},
    "Networks": [
      {
        "Target": "k7fu7vlpyya62typb30ul3487",
        "Aliases": [
          "reflector"
        ]
      },
      {
        "Target": "pcjgm48848c046ig5kogljnu8",
        "Aliases": [
          "reflector"
        ]
      }
    ],
    "container": {
      "Image": "local/avahi-reflector:1.0"
    }
  },
  "endpoint": {
    "Spec": {}
  },
  "update": {
    "UpdateConfig": {
      "Parallelism": 1,
      "FailureAction": "pause",
      "Monitor": 5000000000,
      "MaxFailureRatio": 0,
      "Order": "stop-first"
    },
    "RollbackConfig": {
      "Parallelism": 1,
      "FailureAction": "pause",
      "Monitor": 5000000000,
      "MaxFailureRatio": 0,
      "Order": "stop-first"
    }
  },
  "tasks": "{\"CurrentState\":\"Running 3 weeks ago\",\"DesiredState\":\"Running\",\"Error\":\"\",\"ID\":\"qhh4btwznq4zz0pt5s1ot2hxi\",\"Image\":\"local/avahi-reflector:1.0\",\"Name\":\"avahi_reflector.1\",\"Node\":\"docker-02\",\"Ports\":\"\"}\n{\"CurrentState\":\"Shutdown 3 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\",\"ID\":\"sr8xasobsqrkoue6wsseqdfmk\",\"Image\":\"local/avahi-reflector:1.0\",\"Name\":\"avahi_reflector.1\",\"Node\":\"docker-01\",\"Ports\":\"\"}\n{\"CurrentState\":\"Shutdown 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\",\"ID\":\"o9s93z3bad6ijnjesybfa6j8k\",\"Image\":\"local/avahi-reflector:1.0\",\"Name\":\"avahi_reflector.1\",\"Node\":\"docker-02\",\"Ports\":\"\"}"
}
```
