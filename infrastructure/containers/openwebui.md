# openwebui

Instantané du 21 octobre 2026. OpenWebUI, MCPO et Tailscale-Ollama sont présents. OpenWebUI et MCPO healthy ; Tailscale a NET_ADMIN et NET_RAW. Configurations et données persistantes sont sous docker-shared. Frontend owui : 200 via VIP privée IPv4 et IPv6. Échec du chemin IPv4 public depuis le Mac. Aucun test OAuth, MCP métier ou modèle avec identifiants utilisateur.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | OpenWebUI | running / healthy | local/open-webui:0.11.3-fr | 0 |
| docker-01 | MCPO | running / healthy | ghcr.io/open-webui/mcpo:main | 0 |
| docker-01 | Tailscale-Ollama | running / sans état health | tailscale/tailscale:v1.102.4 | 0 |


## docker-01 — OpenWebUI

ID : `6fbb75cf6bcc8bceb73182138a1faf8dd1b9d27ef8056bab29ed98f5de43f272`. Image effective : `sha256:d89678caf7934d8059f250e8afd770f37b6c34e67e782b7fc9b6ce089a8df466`. Création : 2026-09-24T14:47:44.110013414Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/openwebui/data | /app/backend/data | True |
| bind | /srv/docker-shared/super-agent/secrets/oauth-openwebui-microsoft-client-id | /run/secrets/oauth-openwebui-microsoft-client-id | False |
| bind | /srv/docker-shared/super-agent/secrets/oauth-openwebui-microsoft-client-secret | /run/secrets/oauth-openwebui-microsoft-client-secret | False |
| bind | /srv/docker-shared/super-agent/secrets/openwebui.env | /run/secrets/super-agent-auth.env | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.14 |  | ["OpenWebUI", "openwebui", "openwebui"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "8080/tcp": null
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
  "CapDrop": [
    "ALL"
  ],
  "SecurityOpt": [
    "no-new-privileges:true"
  ],
  "Devices": null,
  "DeviceRequests": null,
  "PidMode": "",
  "IpcMode": "private",
  "Memory": 2147483648,
  "MemorySwap": 4294967296,
  "NanoCpus": 2000000000,
  "CpuShares": 0,
  "PidsLimit": 512,
  "Ulimits": null,
  "LogConfig": {
    "Type": "json-file",
    "Config": {}
  },
  "Dns": null,
  "ExtraHosts": []
}
```

Utilisateur : `0:0`. Healthcheck : True.

Noms de variables seulement (valeurs exclues) : `MICROSOFT_CLIENT_ID_FILE`, `WEBUI_ADMIN_NAME`, `MICROSOFT_CLIENT_SECRET_FILE`, `CORS_ALLOW_ORIGIN`, `WEBUI_AUTH_COOKIE_SECURE`, `WEBUI_ADMIN_PASSWORD`, `ENABLE_OAUTH_ID_TOKEN_COOKIE`, `OAUTH_UPDATE_PICTURE_ON_LOGIN`, `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS`, `ENABLE_SIGNUP`, `OAUTH_SUB_CLAIM`, `ENABLE_OAUTH_GROUP_MANAGEMENT`, `MICROSOFT_CLIENT_TENANT_ID`, `ENABLE_LOGIN_FORM`, `ENABLE_OAUTH_SIGNUP`, `ENABLE_OAUTH_ROLE_MANAGEMENT`, `WEBUI_SESSION_COOKIE_SAME_SITE`, `OAUTH_UPDATE_EMAIL_ON_LOGIN`, `OAUTH_MERGE_ACCOUNTS_BY_EMAIL`, `WEBUI_AUTH_COOKIE_SAME_SITE`, `WEBUI_SESSION_COOKIE_SECURE`, `WEBUI_ADMIN_EMAIL`, `AUDIT_UVICORN_LOGGER_NAMES`, `OAUTH_UPDATE_NAME_ON_LOGIN`, `MICROSOFT_OAUTH_SCOPE`, `ENABLE_OAUTH`, `WEBUI_SECRET_KEY`, `ENABLE_OAUTH_GROUP_CREATION`, `WEBUI_URL`, `ENABLE_OAUTH_PERSISTENT_CONFIG`, `ENABLE_OAUTH_EMAIL_FALLBACK`, `OPENID_PROVIDER_URL`, `MICROSOFT_REDIRECT_URI`, `PATH`, `LANG`, `GPG_KEY`, `PYTHON_VERSION`, `PYTHON_SHA256`, `PYTHONUNBUFFERED`, `ENV`, `PORT`, `USE_OLLAMA_DOCKER`, `USE_CUDA_DOCKER`, `USE_SLIM_DOCKER`, `USE_CUDA_DOCKER_VER`, `USE_EMBEDDING_MODEL_DOCKER`, `USE_RERANKING_MODEL_DOCKER`, `USE_AUXILIARY_EMBEDDING_MODEL_DOCKER`, `OLLAMA_BASE_URL`, `OPENAI_API_BASE_URL`, `OPENAI_API_KEY`, `SCARF_NO_ANALYTICS`, `DO_NOT_TRACK`, `ANONYMIZED_TELEMETRY`, `WHISPER_MODEL`, `WHISPER_MODEL_DIR`, `RAG_EMBEDDING_MODEL`, `RAG_RERANKING_MODEL`, `AUXILIARY_EMBEDDING_MODEL`, `SENTENCE_TRANSFORMERS_HOME`, `TIKTOKEN_ENCODING_NAME`, `TIKTOKEN_CACHE_DIR`, `HF_HOME`, `HOME`, `UV_LINK_MODE`, `WEBUI_BUILD_VERSION`, `DOCKER`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — MCPO

ID : `e6d3d546589ae929eac327d01f99c419b0db9274468a2d619d096c2996b7cb77`. Image effective : `sha256:1e82c9555c19e50b80745705f32b47a2647589f35279527b5118ecd3a71bd467`. Création : 2026-09-24T14:46:08.623326075Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/mcpo/config | /app/config | False |
| bind | /srv/docker-shared/mcpo/glpi/mcp-glpi-3.2.0 | /app/glpi | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.12 |  | ["MCPO", "mcpo", "mcpo"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "8000/tcp": null
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
  "ReadonlyRootfs": true,
  "CapAdd": null,
  "CapDrop": [
    "ALL"
  ],
  "SecurityOpt": [
    "no-new-privileges:true"
  ],
  "Devices": null,
  "DeviceRequests": null,
  "PidMode": "",
  "IpcMode": "private",
  "Memory": 805306368,
  "MemorySwap": 1610612736,
  "NanoCpus": 1000000000,
  "CpuShares": 0,
  "PidsLimit": 256,
  "Ulimits": null,
  "LogConfig": {
    "Type": "json-file",
    "Config": {}
  },
  "Dns": null,
  "ExtraHosts": []
}
```

Utilisateur : `65532:65532`. Healthcheck : True.

Noms de variables seulement (valeurs exclues) : `GLPI_URL`, `GLPI_APP_TOKEN`, `GLPI_USER_TOKEN`, `NODE_OPTIONS`, `MCPO_API_KEY`, `PATH`, `LANG`, `GPG_KEY`, `PYTHON_VERSION`, `PYTHON_SHA256`, `VIRTUAL_ENV`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — Tailscale-Ollama

ID : `7f018788d72fce2396dee265bc5116e85f266e625a21144e175868d4bb1143c0`. Image effective : `sha256:2667499ed87ae29218f292556ba062918402dd5e92e93637af14867e4df12dd3`. Création : 2026-09-20T16:47:46.744327101Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/openwebui/tailscale-ollama/state | /var/lib/tailscale | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.27 |  | ["Tailscale-Ollama", "tailscale-ollama", "ollama-tailscale"] |


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
  "CapAdd": [
    "CAP_NET_ADMIN",
    "CAP_NET_RAW"
  ],
  "CapDrop": null,
  "SecurityOpt": null,
  "Devices": [
    {
      "PathOnHost": "/dev/net/tun",
      "PathInContainer": "/dev/net/tun",
      "CgroupPermissions": "rwm"
    }
  ],
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

Noms de variables seulement (valeurs exclues) : `TS_TAILNET_TARGET_FQDN`, `TS_HOSTNAME`, `TS_STATE_DIR`, `TS_AUTH_ONCE`, `TS_ACCEPT_DNS`, `TS_USERSPACE`, `PATH`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/openwebui/compose.yml`. Nœuds : docker-01. SHA-256 : `ef922a30673750a5f5c7da142272a0321f6a60450182995318dd433e13b7d8b3`.

```json
{
  "services": {
    "openwebui": {
      "image": "local/open-webui:0.11.3-fr",
      "container_name": "OpenWebUI",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/openwebui/data:/app/backend/data",
        "/srv/docker-shared/super-agent/secrets/openwebui.env:/run/secrets/super-agent-auth.env:ro",
        "/srv/docker-shared/super-agent/secrets/oauth-openwebui-microsoft-client-id:/run/secrets/oauth-openwebui-microsoft-client-id:ro",
        "/srv/docker-shared/super-agent/secrets/oauth-openwebui-microsoft-client-secret:/run/secrets/oauth-openwebui-microsoft-client-secret:ro"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "openwebui"
          ]
        }
      },
      "cap_drop": [
        "ALL"
      ],
      "security_opt": [
        "no-new-privileges:true"
      ],
      "mem_limit": "2g",
      "cpus": 2.0,
      "env_file": [
        "/srv/docker-shared/openwebui/runtime.env"
      ],
      "environment_keys_only": [
        "WEBUI_URL",
        "CORS_ALLOW_ORIGIN",
        "WEBUI_SESSION_COOKIE_SECURE",
        "WEBUI_AUTH_COOKIE_SECURE",
        "WEBUI_SESSION_COOKIE_SAME_SITE",
        "WEBUI_AUTH_COOKIE_SAME_SITE",
        "ENABLE_SIGNUP",
        "ENABLE_LOGIN_FORM",
        "ENABLE_OAUTH",
        "ENABLE_OAUTH_SIGNUP",
        "ENABLE_OAUTH_PERSISTENT_CONFIG",
        "OAUTH_MERGE_ACCOUNTS_BY_EMAIL",
        "OAUTH_SUB_CLAIM",
        "MICROSOFT_CLIENT_ID_FILE",
        "MICROSOFT_CLIENT_SECRET_FILE",
        "MICROSOFT_CLIENT_TENANT_ID",
        "MICROSOFT_REDIRECT_URI",
        "MICROSOFT_OAUTH_SCOPE",
        "OPENID_PROVIDER_URL",
        "ENABLE_OAUTH_EMAIL_FALLBACK",
        "ENABLE_OAUTH_ID_TOKEN_COOKIE",
        "ENABLE_OAUTH_ROLE_MANAGEMENT",
        "ENABLE_OAUTH_GROUP_MANAGEMENT",
        "ENABLE_OAUTH_GROUP_CREATION",
        "OAUTH_UPDATE_NAME_ON_LOGIN",
        "OAUTH_UPDATE_EMAIL_ON_LOGIN",
        "OAUTH_UPDATE_PICTURE_ON_LOGIN",
        "AUDIT_UVICORN_LOGGER_NAMES",
        "WEBUI_ADMIN_EMAIL",
        "WEBUI_ADMIN_PASSWORD",
        "WEBUI_ADMIN_NAME"
      ],
      "healthcheck_present": false,
      "command_present": true,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "mcpo": {
      "image": "ghcr.io/open-webui/mcpo:main",
      "container_name": "MCPO",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/mcpo/config:/app/config:ro",
        "/srv/docker-shared/mcpo/glpi/mcp-glpi-3.2.0:/app/glpi:ro"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "mcpo"
          ]
        }
      },
      "read_only": true,
      "cap_drop": [
        "ALL"
      ],
      "security_opt": [
        "no-new-privileges:true"
      ],
      "user": "65532:65532",
      "mem_limit": "768m",
      "cpus": 1.0,
      "env_file": [
        "/srv/docker-shared/mcpo/runtime.env",
        "/srv/docker-shared/mcpo/secrets/glpi.env"
      ],
      "environment_keys_only": [],
      "healthcheck_present": true,
      "command_present": true,
      "entrypoint_present": true,
      "traefik_labels": {}
    },
    "tailscale-ollama": {
      "image": "tailscale/tailscale:v1.102.4",
      "container_name": "Tailscale-Ollama",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/openwebui/tailscale-ollama/state:/var/lib/tailscale"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "ollama-tailscale"
          ]
        }
      },
      "cap_add": [
        "NET_ADMIN",
        "NET_RAW"
      ],
      "security_opt": [
        "no-new-privileges:true"
      ],
      "devices": [
        "/dev/net/tun:/dev/net/tun"
      ],
      "mem_limit": "512m",
      "cpus": 1.0,
      "env_file": [
        "/srv/docker-shared/openwebui/tailscale-ollama/tailscale.env"
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
