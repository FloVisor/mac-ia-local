# homepage

Instantané du 21 octobre 2026. Homepage healthy sur docker-03. Frontend HTTP 307 ; backend interrogé avec son nom Docker brut répond 400. Le Host utilisé diffère du frontend : ce résultat ne démontre pas une indisponibilité du service publié. Image versionnée ; config partagée.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-03 | Homepage | running / healthy | ghcr.io/gethomepage/homepage:v2.3.0 | 0 |


## docker-03 — Homepage

ID : `5685c0d3ab9c3753f9cbec1ee6261016295b9407a557154ef93f8f137b700140`. Image effective : `sha256:f820276654539cdc2cf0169f28188d135919a7984fad76d83d8d5ff1383f3705`. Création : 2026-09-16T19:42:23.032791486Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/homepage/config | /app/config | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.24 |  | ["Homepage", "homepage", "homepage"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "3000/tcp": null
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

Utilisateur : `root`. Healthcheck : True.

Noms de variables seulement (valeurs exclues) : `HOMEPAGE_AUTH_ENABLED`, `HOMEPAGE_AUTH_SECRET`, `HOMEPAGE_AUTH_PASSWORD`, `HOMEPAGE_EXTERNAL_URL`, `HOMEPAGE_ALLOWED_HOSTS`, `PATH`, `NODE_VERSION`, `YARN_VERSION`, `NODE_ENV`, `HOSTNAME`, `PORT`.

Source : [capture docker-03](../evidence/2026-10-21/docker-03.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/homepage/compose.yml`. Nœuds : docker-03. SHA-256 : `4f2fb8e3f2e5eab7a7d6eea35b80175e10675646228cd10a098db37c358e63a2`.

```json
{
  "services": {
    "homepage": {
      "image": "ghcr.io/gethomepage/homepage:v2.3.0",
      "container_name": "Homepage",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/homepage/config:/app/config"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "homepage"
          ]
        }
      },
      "env_file": [
        "/srv/docker-shared/homepage/.env"
      ],
      "environment_keys_only": [
        "HOMEPAGE_ALLOWED_HOSTS"
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
    }
  }
}
```
