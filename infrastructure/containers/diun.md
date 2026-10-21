# diun

Instantané du 21 octobre 2026. DIUN healthy sur docker-03, image latest et socket Docker monté RW. / sur le frontend et le backend répond 404 ; le conteneur peut fournir des métriques ou une autre route, non assimilées à une WebUI fonctionnelle. Nom diun.gangneux.org non résolu depuis le Mac au moment de l’audit. Notifications et mises à jour d’image non déclenchées.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-03 | DIUN | running / healthy | crazymax/diun:latest | 0 |


## docker-03 — DIUN

ID : `2b64448f9290bd7fbd58c1fdcbabdc58bd9de7b44cdc84f0688bf20d8da90e1b`. Image effective : `sha256:e324b793eb32dfb7f74d3a39421ebf090141caaadee69b8f78da63112408ee25`. Création : 2026-09-16T19:15:08.499671519Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/diun/data | /data | True |
| bind | /srv/docker-shared/diun/config/custom-images.yml | /config/custom-images.yml | False |
| bind | /srv/docker-shared/diun/config/diun.yml | /config/diun.yml | False |
| bind | /var/run/docker.sock | /var/run/docker.sock | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.17 |  | ["DIUN", "diun", "diun"] |


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

Noms de variables seulement (valeurs exclues) : `TZ`, `CONFIG`, `LOG_LEVEL`, `LOG_JSON`, `GRPC_AUTHORITY`, `PATH`, `PROFILER_PATH`, `DIUN_DB_PATH`.

Source : [capture docker-03](../evidence/2026-10-21/docker-03.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/diun/compose.yml`. Nœuds : docker-03. SHA-256 : `fd37659f7c519a852f640275cfeb59817a488fd69bd6f019c941aea04bf3fe1d`.

```json
{
  "services": {
    "diun": {
      "image": "crazymax/diun:latest",
      "container_name": "DIUN",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/diun/data:/data",
        "/srv/docker-shared/diun/config/diun.yml:/config/diun.yml:ro",
        "/srv/docker-shared/diun/config/custom-images.yml:/config/custom-images.yml:ro",
        "/var/run/docker.sock:/var/run/docker.sock"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "diun"
          ]
        }
      },
      "environment_keys_only": [
        "TZ",
        "CONFIG",
        "LOG_LEVEL",
        "LOG_JSON",
        "GRPC_AUTHORITY"
      ],
      "healthcheck_present": true,
      "command_present": true,
      "entrypoint_present": false,
      "traefik_labels": {}
    }
  },
  "networks": {
    "TRAEFIK_BACKEND": {
      "external": true,
      "name": "TRAEFIK_BACKEND"
    }
  }
}
```
