# traefik

Instantané du 21 octobre 2026. Voir aussi ../traefik.md pour tous les fichiers dynamiques, les paramètres statiques, ACL, transports TLS et sondes. Service actif sur docker-02, restart=no dans le Compose ; les notifications Keepalived pilotent son cycle de vie. Aucun test de bascule effectué.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-02 | Traefik | running / sans état health | traefik:v3.7.13 | 0 |


## docker-02 — Traefik

ID : `1beed98094263d786de4e08ad6308250b21c21bbb25e117715f1a31bb8e5a2de`. Image effective : `sha256:f86a2cab1b5c649070c49f883c743dd32d8485a56e3368c5f93b9e91f1e91259`. Création : 2026-09-27T14:12:11.681725028Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/traefik/acme/acme.json | /acme/acme.json | True |
| bind | /srv/docker-shared/traefik/dynamic | /etc/traefik/dynamic | False |
| bind | /srv/docker-shared/traefik/secrets/ovh_application_key | /run/secrets/ovh_application_key | False |
| bind | /srv/docker-shared/traefik/secrets/ovh_application_secret | /run/secrets/ovh_application_secret | False |
| bind | /srv/docker-shared/traefik/secrets/ovh_consumer_key | /run/secrets/ovh_consumer_key | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| DMZ | 192.168.205.10 | 2a01:e0a:8ce:68c5::10 | ["Traefik", "traefik"] |
| TRAEFIK_BACKEND | 172.29.2.2 |  | ["Traefik", "traefik", "traefik"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "80/tcp": null
}
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

Noms de variables seulement (valeurs exclues) : `OVH_APPLICATION_KEY_FILE`, `OVH_APPLICATION_SECRET_FILE`, `OVH_CONSUMER_KEY_FILE`, `OVH_ENDPOINT`, `PATH`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/traefik/compose.yml`. Nœuds : docker-01, docker-02, docker-03. SHA-256 : `28c5f54141f3fcf8e35f868be5e0539e9c1a4bc4086b057f8110248d7d3449c4`.

```json
{
  "services": {
    "traefik": {
      "image": "traefik:v3.7.13",
      "container_name": "Traefik",
      "restart": "no",
      "volumes": [
        "/srv/docker-shared/traefik/dynamic:/etc/traefik/dynamic:ro",
        "/srv/docker-shared/traefik/acme/acme.json:/acme/acme.json",
        "/srv/docker-shared/traefik/secrets/ovh_application_key:/run/secrets/ovh_application_key:ro",
        "/srv/docker-shared/traefik/secrets/ovh_application_secret:/run/secrets/ovh_application_secret:ro",
        "/srv/docker-shared/traefik/secrets/ovh_consumer_key:/run/secrets/ovh_consumer_key:ro"
      ],
      "networks": {
        "DMZ": {
          "ipv4_address": "192.168.205.10",
          "ipv6_address": "2a01:e0a:8ce:68c5::10",
          "gw_priority": 1
        },
        "TRAEFIK_BACKEND": {
          "aliases": [
            "traefik"
          ],
          "gw_priority": 0
        }
      },
      "environment_keys_only": [
        "OVH_ENDPOINT",
        "OVH_APPLICATION_KEY_FILE",
        "OVH_APPLICATION_SECRET_FILE",
        "OVH_CONSUMER_KEY_FILE"
      ],
      "healthcheck_present": false,
      "command_present": true,
      "entrypoint_present": false,
      "traefik_labels": {}
    }
  },
  "networks": {
    "DMZ": {
      "external": true,
      "name": "DMZ"
    },
    "TRAEFIK_BACKEND": {
      "name": "TRAEFIK_BACKEND",
      "external": true
    }
  }
}
```
