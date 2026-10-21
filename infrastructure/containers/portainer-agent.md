# portainer_agent

Instantané du 21 octobre 2026. Service global, trois tâches actives. Monte docker.sock RW et le répertoire des volumes Docker ; accès administratif attendu pour ce composant, à réserver au périmètre de confiance. Trois anciennes tâches arrêtées restent sur docker-01, sans suppression. Données de socket et identifiants Portainer non lus.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | portainer_agent.9koqx4hnjemcqzhf2amsn104m.r01ccrq6arylc59btgouvnkd7 | running / sans état health | portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba | 0 |
| docker-01 | portainer_agent.9koqx4hnjemcqzhf2amsn104m.b1gt9gt686hcudatmvqycpinn | exited / sans état health | portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba | 0 |
| docker-01 | portainer_agent.9koqx4hnjemcqzhf2amsn104m.94tlk4iba01tc27q3w1eifm8u | exited / sans état health | portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba | 0 |
| docker-01 | portainer_agent.9koqx4hnjemcqzhf2amsn104m.nbwfh45ub4zz3dhci04dwdvl6 | exited / sans état health | portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba | 0 |
| docker-02 | portainer_agent.r91yes4cho1ppyerywtmrr170.is9ubmw5xaab84xxphve3exhz | running / sans état health | portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba | 0 |
| docker-03 | portainer_agent.xcxurj56mv1u238bnskyjlld9.twbarixu8071jjjq507e8xbvu | running / sans état health | portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba | 0 |


## docker-01 — portainer_agent.9koqx4hnjemcqzhf2amsn104m.r01ccrq6arylc59btgouvnkd7

ID : `abd8efa34bc06ca2d2dbccc0dbae66d8cdd1427bec4f49028e536d3fccc3ab56`. Image effective : `sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba`. Création : 2026-09-27T14:16:24.70627763Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /var/run/docker.sock | /var/run/docker.sock | True |
| bind | /srv/docker-local/docker/volumes | /var/lib/docker/volumes | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| portainer_agent_network | 172.29.1.4 |  | None |


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

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — portainer_agent.9koqx4hnjemcqzhf2amsn104m.b1gt9gt686hcudatmvqycpinn

ID : `39415c50cc5df79842f9e55a6a9d088afa035844c286d20bd4f37ba34f62e34d`. Image effective : `sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba`. Création : 2026-09-27T14:13:57.529641524Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /var/run/docker.sock | /var/run/docker.sock | True |
| bind | /srv/docker-local/docker/volumes | /var/lib/docker/volumes | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| portainer_agent_network |  |  | None |


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

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — portainer_agent.9koqx4hnjemcqzhf2amsn104m.94tlk4iba01tc27q3w1eifm8u

ID : `ea6848e3fc4eebc678b3b6b66141d395bb8adacb0592cfa6f4e5d517513462a9`. Image effective : `sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba`. Création : 2026-09-15T09:49:18.841047604Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /var/run/docker.sock | /var/run/docker.sock | True |
| bind | /srv/docker-local/docker/volumes | /var/lib/docker/volumes | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| portainer_agent_network |  |  | None |


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

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — portainer_agent.9koqx4hnjemcqzhf2amsn104m.nbwfh45ub4zz3dhci04dwdvl6

ID : `b1b748e32da296a2faa68f32ba388156e091fefcebe9af29d679034dd2da1c80`. Image effective : `sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba`. Création : 2026-09-09T21:03:06.18690941Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /var/run/docker.sock | /var/run/docker.sock | True |
| bind | /srv/docker-local/docker/volumes | /var/lib/docker/volumes | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| portainer_agent_network |  |  | None |


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
  "Dns": [],
  "ExtraHosts": null
}
```

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-02 — portainer_agent.r91yes4cho1ppyerywtmrr170.is9ubmw5xaab84xxphve3exhz

ID : `eec387c0ce43f11b1f06af62fc62f6db62df8e9343cc34a73747e88f6132e3e2`. Image effective : `sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba`. Création : 2026-09-15T09:50:48.555969078Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /var/run/docker.sock | /var/run/docker.sock | True |
| bind | /srv/docker-local/docker/volumes | /var/lib/docker/volumes | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| portainer_agent_network | 172.29.1.6 |  | None |


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

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## docker-03 — portainer_agent.xcxurj56mv1u238bnskyjlld9.twbarixu8071jjjq507e8xbvu

ID : `209439b0362c546e5a0419774e55ebf148b72c311451bf598dd0544ea4c7dce8`. Image effective : `sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba`. Création : 2026-09-15T09:51:32.447106586Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /var/run/docker.sock | /var/run/docker.sock | True |
| bind | /srv/docker-local/docker/volumes | /var/lib/docker/volumes | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| portainer_agent_network | 172.29.1.12 |  | None |


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

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`.

Source : [capture docker-03](../evidence/2026-10-21/docker-03.json). Aucun log applicatif ni contenu de base exporté.

## Déclaration Swarm filtrée

```json
{
  "ID": "vwfaeqb7fvkritamdexvzx7y7",
  "name": "portainer_agent",
  "mode": {
    "Global": {}
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
        "node.platform.os == linux"
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
          "agent"
        ]
      }
    ],
    "container": {
      "Image": "portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba",
      "Mounts": [
        {
          "Type": "bind",
          "Source": "/var/run/docker.sock",
          "Target": "/var/run/docker.sock"
        },
        {
          "Type": "bind",
          "Source": "/srv/docker-local/docker/volumes",
          "Target": "/var/lib/docker/volumes"
        }
      ]
    }
  },
  "endpoint": {
    "Spec": {
      "Mode": "vip"
    },
    "VirtualIPs": [
      {
        "NetworkID": "d3a6rlxzytuu0cv4w5i2lck79",
        "Addr": "172.29.1.5/24"
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
  "tasks": "{\"CurrentState\":\"Running 3 weeks ago\",\"DesiredState\":\"Running\",\"Error\":\"\",\"ID\":\"r01ccrq6arylc59btgouvnkd7\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.9koqx4hnjemcqzhf2amsn104m\",\"Node\":\"docker-01\",\"Ports\":\"\"}\n{\"CurrentState\":\"Shutdown 3 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\",\"ID\":\"b1gt9gt686hcudatmvqycpinn\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.9koqx4hnjemcqzhf2amsn104m\",\"Node\":\"docker-01\",\"Ports\":\"\"}\n{\"CurrentState\":\"Shutdown 3 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\",\"ID\":\"94tlk4iba01tc27q3w1eifm8u\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.9koqx4hnjemcqzhf2amsn104m\",\"Node\":\"docker-01\",\"Ports\":\"\"}\n{\"CurrentState\":\"Rejected 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\\\"cannot create a swarm scoped network when swarm is not active\\\"\",\"ID\":\"op6mpd8vi57gig6q9vrgq0zee\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.9koqx4hnjemcqzhf2amsn104m\",\"Node\":\"docker-01\",\"Ports\":\"\"}\n{\"CurrentState\":\"Shutdown 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\",\"ID\":\"nbwfh45ub4zz3dhci04dwdvl6\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.9koqx4hnjemcqzhf2amsn104m\",\"Node\":\"docker-01\",\"Ports\":\"\"}\n{\"CurrentState\":\"Running 3 weeks ago\",\"DesiredState\":\"Running\",\"Error\":\"\",\"ID\":\"is9ubmw5xaab84xxphve3exhz\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.r91yes4cho1ppyerywtmrr170\",\"Node\":\"docker-02\",\"Ports\":\"\"}\n{\"CurrentState\":\"Rejected 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\\\"cannot create a swarm scoped network when swarm is not active\\\"\",\"ID\":\"zoosjkuv3bz7g1kljm3qurjyi\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.r91yes4cho1ppyerywtmrr170\",\"Node\":\"docker-02\",\"Ports\":\"\"}\n{\"CurrentState\":\"Rejected 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\\\"cannot create a swarm scoped network when swarm is not active\\\"\",\"ID\":\"lpeqwikzs1rivfnbt64qdqjrv\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.r91yes4cho1ppyerywtmrr170\",\"Node\":\"docker-02\",\"Ports\":\"\"}\n{\"CurrentState\":\"Shutdown 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\",\"ID\":\"qzqosveri3ilqgmmk3rxhacin\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.r91yes4cho1ppyerywtmrr170\",\"Node\":\"docker-02\",\"Ports\":\"\"}\n{\"CurrentState\":\"Running 3 weeks ago\",\"DesiredState\":\"Running\",\"Error\":\"\",\"ID\":\"twbarixu8071jjjq507e8xbvu\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.xcxurj56mv1u238bnskyjlld9\",\"Node\":\"docker-03\",\"Ports\":\"\"}\n{\"CurrentState\":\"Rejected 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\\\"cannot create a swarm scoped network when swarm is not active\\\"\",\"ID\":\"ok3vgqqjngaoptckqs5t04adk\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.xcxurj56mv1u238bnskyjlld9\",\"Node\":\"docker-03\",\"Ports\":\"\"}\n{\"CurrentState\":\"Rejected 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\\\"cannot create a swarm scoped network when swarm is not active\\\"\",\"ID\":\"7unka95k4iqep6sublw8qics6\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.xcxurj56mv1u238bnskyjlld9\",\"Node\":\"docker-03\",\"Ports\":\"\"}\n{\"CurrentState\":\"Shutdown 5 weeks ago\",\"DesiredState\":\"Shutdown\",\"Error\":\"\",\"ID\":\"cr5gowiksa9bwiv4vcwcl0oks\",\"Image\":\"portainer/agent:lts@sha256:d63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba\",\"Name\":\"portainer_agent.xcxurj56mv1u238bnskyjlld9\",\"Node\":\"docker-03\",\"Ports\":\"\"}"
}
```
