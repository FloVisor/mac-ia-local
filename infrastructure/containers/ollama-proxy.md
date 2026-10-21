# ollama-proxy

Instantané du 21 octobre 2026. Ollama-Proxy est running/unhealthy. Nginx écoute 11434 et vise http://ollama-tailscale:11434 ; DNS interne 127.0.0.11, IPv6 off pour ce resolver. Healthcheck sur /api/version toutes les 30 s, timeout 5 s, retries 3 ; cinq derniers ExitCode=-1. proxy_connect_timeout=10 s et lecture/envoi 3600 s. La cause initiale et l’accès au modèle distant ne sont pas établis ; aucun appel de génération réalisé.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | Ollama-Proxy | running / unhealthy | nginx:alpine | 0 |


## docker-01 — Ollama-Proxy

ID : `102fd90a52b7f30aa7e62a91c6639e26045d999c10550db3c8008bce416fc3da`. Image effective : `sha256:62ff2089abf5a9ed33bd232895bef5e22f7bb4b200675cec49a5ebc48e3d4ac8`. Création : 2026-09-20T21:13:48.782420092Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/ollama-proxy/nginx.conf | /etc/nginx/nginx.conf | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.36 |  | ["Ollama-Proxy", "ollama-proxy", "ollama-proxy"] |


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

Noms de variables seulement (valeurs exclues) : `PATH`, `NGINX_VERSION`, `PKG_RELEASE`, `DYNPKG_RELEASE`, `NJS_VERSION`, `NJS_RELEASE`, `ACME_VERSION`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/ollama-proxy/compose.yml`. Nœuds : docker-01. SHA-256 : `a9eb43282ebdfd3d4afe7ba0e6b07daa1c1fc7ba537ef21d101ed7a21089b63b`.

```json
{
  "services": {
    "ollama-proxy": {
      "image": "nginx:alpine",
      "container_name": "Ollama-Proxy",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/ollama-proxy/nginx.conf:/etc/nginx/nginx.conf:ro"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "ollama-proxy"
          ]
        }
      },
      "environment_keys_only": [],
      "healthcheck_present": true,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    }
  },
  "networks": {
    "TRAEFIK_BACKEND": {
      "external": true
    }
  }
}
```
