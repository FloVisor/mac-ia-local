# n8n

Instantané du 21 octobre 2026. Persistance /srv/docker-shared/n8n/data, réseau TRAEFIK_BACKEND. Frontend protégé par CORP@file ; HTTP 200 depuis le Mac sur les deux familles. Aucun workflow lancé et aucun credential consulté.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | n8n | running / sans état health | docker.n8n.io/n8nio/n8n:2.40.7 | 0 |


## docker-01 — n8n

ID : `762acdbcec6e89299e8c62d521adaccbfc6cc9dec892cd265acf23a03c21d379`. Image effective : `sha256:ffeb52485f78b1b06c9a832205853cf75da72a07a514c9a27724df85979d6c34`. Création : 2026-09-27T08:34:30.203613779Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/n8n/data | /home/node/.n8n | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.4 |  | ["n8n", "n8n", "n8n"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "5678/tcp": null
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

Utilisateur : `node`. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `N8N_EDITOR_BASE_URL`, `CENTREON_API_TOKEN`, `PROVIDER_GATEWAY_URL`, `N8N_HOST`, `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS`, `GLPI_USER_TOKEN`, `GLPI_APP_TOKEN`, `N8N_PORT`, `N8N_ENCRYPTION_KEY`, `N8N_BLOCK_ENV_ACCESS_IN_NODE`, `SUPER_AGENT_LINKED_ACCOUNTS_DB`, `N8N_DIAGNOSTICS_ENABLED`, `GLPI_URL`, `N8N_PROTOCOL`, `GENERIC_TIMEZONE`, `CENTREON_URL`, `SUPER_AGENT_PROVIDER_PORT`, `TZ`, `NODE_ENV`, `N8N_RUNNERS_ENABLED`, `N8N_WEBHOOK_URL`, `CENTREON_API_VERSION`, `N8N_PROXY_HOPS`, `PROVIDER_GATEWAY_SERVICE_SECRET`, `NODE_VERSION`, `NPM_CONFIG_UPDATE_NOTIFIER`, `PATH`, `NODE_PATH`, `N8N_RELEASE_TYPE`, `SHELL`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/n8n/compose.yml`. Nœuds : docker-01. SHA-256 : `11357be6ebe6f4c790c936f491a08a943f5cb662ec3e398c37825f9fb5f6f3c1`.

```json
{
  "services": {
    "n8n": {
      "image": "docker.n8n.io/n8nio/n8n:2.40.7",
      "container_name": "n8n",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/n8n/data:/home/node/.n8n"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "n8n"
          ]
        }
      },
      "env_file": [
        "/srv/docker-shared/n8n/.env",
        "/srv/docker-shared/shared-secrets/integrations.env"
      ],
      "environment_keys_only": [],
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
