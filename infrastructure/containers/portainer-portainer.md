# portainer_portainer

Instantané du 21 octobre 2026. Serveur Swarm, une réplique, contrainte node.role == manager. Volume portainer_data : driver local, mais Options type=nfs vers 192.168.201.39:/srv/docker-shared/portainer. Le montage NFS est confirmé sur docker-03 ; le constat initial de stockage local seul est corrigé. Port 9443 publié par ingress ; frontend 200. Traefik désactive la validation du certificat backend.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-03 | portainer_portainer.1.na8qxtnuocqhnbimb3jeokesl | running / sans état health | portainer/portainer-ce:lts@sha256:511f3f06c96fe3b993ebeaafde311c1959cae73a7ef825dba6397d51b450dffa | 0 |


## docker-03 — portainer_portainer.1.na8qxtnuocqhnbimb3jeokesl

ID : `de74c385d705deec72354b9b89e5e37643d1d0eabadf8e8fa44719482e9420bd`. Image effective : `sha256:511f3f06c96fe3b993ebeaafde311c1959cae73a7ef825dba6397d51b450dffa`. Création : 2026-09-15T11:39:01.149326533Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| volume | /srv/docker-local/docker/volumes/portainer_data/_data | /data | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| ingress | 172.29.0.9 |  | None |
| portainer_agent_network | 172.29.1.17 |  | None |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "8000/tcp": null,
  "9000/tcp": null,
  "9443/tcp": null
}
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

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-03](../evidence/2026-10-21/docker-03.json). Aucun log applicatif ni contenu de base exporté.

## Déclaration Swarm filtrée

```json
{
  "ID": "zbb79x37m0dz3jt5gabi89wkk",
  "name": "portainer_portainer",
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
    "Placement": {
      "Constraints": [
        "node.role == manager"
      ],
      "Platforms": [
        {
          "Architecture": "amd64",
          "OS": "linux"
        },
        {
          "Architecture": "arm64",
          "OS": "linux"
        },
        {
          "OS": "linux"
        },
        {
          "Architecture": "ppc64le",
          "OS": "linux"
        },
        {
          "Architecture": "amd64",
          "OS": "windows"
        }
      ]
    },
    "Networks": [
      {
        "Target": "d3a6rlxzytuu0cv4w5i2lck79",
        "Aliases": [
          "portainer"
        ]
      }
    ],
    "container": {
      "Image": "portainer/portainer-ce:lts@sha256:511f3f06c96fe3b993ebeaafde311c1959cae73a7ef825dba6397d51b450dffa",
      "Mounts": [
        {
          "Type": "volume",
          "Source": "portainer_data",
          "Target": "/data",
          "VolumeOptions": {
            "NoCopy": true
          }
        }
      ]
    }
  },
  "endpoint": {
    "Spec": {
      "Mode": "vip",
      "Ports": [
        {
          "Protocol": "tcp",
          "TargetPort": 9443,
          "PublishedPort": 9443,
          "PublishMode": "ingress"
        }
      ]
    },
    "Ports": [
      {
        "Protocol": "tcp",
        "TargetPort": 9443,
        "PublishedPort": 9443,
        "PublishMode": "ingress"
      }
    ],
    "VirtualIPs": [
      {
        "NetworkID": "m09xcte0rhe2k1e1qk355nksx",
        "Addr": "172.29.0.2/24"
      },
      {
        "NetworkID": "d3a6rlxzytuu0cv4w5i2lck79",
        "Addr": "172.29.1.2/24"
      }
    ]
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
  "tasks": "{\"CurrentState\":\"Running 3 weeks ago\",\"DesiredState\":\"Running\",\"Error\":\"\",\"ID\":\"na8qxtnuocqhnbimb3jeokesl\",\"Image\":\"portainer/portainer-ce:lts@sha256:511f3f06c96fe3b993ebeaafde311c1959cae73a7ef825dba6397d51b450dffa\",\"Name\":\"portainer_portainer.1\",\"Node\":\"docker-03\",\"Ports\":\"\"}"
}
```
