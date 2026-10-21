# ratiomaster

Instantané du 21 octobre 2026. Placement actif docker-02, image locale local/ratiomaster:1.1.0, réseau DMZ, configuration et torrents sur docker-shared. Aucun routeur Web RatioMaster trouvé dans les fichiers Traefik collectés. Fonction métier non testée ; reproductibilité de l’image locale non qualifiée.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-02 | RatioMaster | running / sans état health | local/ratiomaster:1.1.0 | 0 |


## docker-02 — RatioMaster

ID : `38197dcb73ce77f4430f4a30065868ebaf8c70597e7237598b5a3b8e1e11531c`. Image effective : `sha256:6c2087ad7a4780691a985346c100e4a148f8c43e882afc349ede10d9ae589d21`. Création : 2026-09-15T10:52:13.830180721Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/ratiomaster/torrents | /torrents | False |
| bind | /srv/docker-shared/ratiomaster/config | /root/.config/RatioMaster.NET | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| DMZ | 192.168.205.41 | 2a01:e0a:8ce:68c5::41 | ["RatioMaster", "ratiomaster"] |


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
  "NetworkMode": "DMZ",
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

Noms de variables seulement (valeurs exclues) : `DISPLAY`, `TZ`, `HOME`, `PATH`, `DEBIAN_FRONTEND`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/ratiomaster/compose.yml`. Nœuds : docker-01, docker-02, docker-03. SHA-256 : `98143909ead313980f225069f18a8b711f4a29a1cc822106161ead2d0635dbad`.

```json
{
  "services": {
    "ratiomaster": {
      "image": "local/ratiomaster:1.1.0",
      "container_name": "RatioMaster",
      "volumes": [
        "/srv/docker-shared/ratiomaster/config:/root/.config/RatioMaster.NET",
        "/srv/docker-shared/ratiomaster/torrents:/torrents:ro"
      ],
      "networks": {
        "DMZ": {
          "ipv4_address": "192.168.205.41",
          "ipv6_address": "2a01:e0a:8ce:68c5::41"
        }
      },
      "environment_keys_only": [
        "TZ",
        "HOME",
        "DISPLAY"
      ],
      "healthcheck_present": false,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    }
  },
  "networks": {
    "DMZ": {
      "external": true,
      "name": "DMZ"
    }
  }
}
```
