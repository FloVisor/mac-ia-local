# super-agent

Instantané du 21 octobre 2026. Cinq composants : application, provider-gateway, entra-sync, PostgreSQL et Redis, tous healthy à la collecte. Limites CPU/RAM explicites ; réseaux privés distincts pour état, fournisseur et sortie. Les routes OAuth sont inventoriées mais leurs endpoints de connexion et callback ne sont pas appelés. Le backend racine du provider-gateway répond 404 : cela ne teste pas les routes OAuth. Sauvegarde applicative déclarée ; voir ../sauvegardes-ha.md.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | super-agent-postgres | running / healthy | postgres:17.6-bookworm@sha256:f3bd19c606e442c3d7bdfa8002e03fe260a1023351e0ea4598032022b68dd6e3 | 1 |
| docker-01 | super-agent-provider-gateway-1 | running / healthy | local/super-agent:0.7.0 | 0 |
| docker-01 | super-agent | running / healthy | local/super-agent:0.7.0 | 0 |
| docker-01 | super-agent-entra-sync-1 | running / healthy | local/super-agent:0.7.0 | 0 |
| docker-01 | super-agent-redis | running / healthy | redis/redis-stack-server:7.4.0-v8@sha256:798ab84d9f266936b034ab11c4d04a2b8e4b441884c5aa7d17ac951eefdf742a | 0 |


## docker-01 — super-agent-postgres

ID : `419d2f19bba0f47dc59b451d34a23bb6cf6e2a23b722763e2d44be65a02921a4`. Image effective : `sha256:f3bd19c606e442c3d7bdfa8002e03fe260a1023351e0ea4598032022b68dd6e3`. Création : 2026-09-25T11:47:13.303380008Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/super-agent/secrets/postgres-admin-password | /run/secrets/postgres-admin-password | False |
| bind | /srv/docker-shared/super-agent/postgres | /var/lib/postgresql/data | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| super-agent_SUPER_AGENT_STATE | 172.21.0.2 |  | ["super-agent-postgres", "super-agent-postgres", "super-agent-postgres"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "5432/tcp": null
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "unless-stopped",
    "MaximumRetryCount": 0
  },
  "NetworkMode": "super-agent_SUPER_AGENT_STATE",
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
  "Memory": 805306368,
  "MemorySwap": 1610612736,
  "NanoCpus": 1500000000,
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

Noms de variables seulement (valeurs exclues) : `POSTGRES_INITDB_ARGS`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD_FILE`, `PATH`, `GOSU_VERSION`, `LANG`, `PG_MAJOR`, `PG_VERSION`, `PGDATA`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — super-agent-provider-gateway-1

ID : `001c3d89afbb657f7cb4a3c7d385c51c8fe768dddf6fc648bfaa514a1e47a24f`. Image effective : `sha256:249b0c3f01801e9bf4590358e824bbfd50787d1181f2c02d9111cb80fa773645`. Création : 2026-09-24T14:59:53.985993029Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/super-agent/linked-accounts | /data | True |
| bind | /srv/docker-shared/super-agent/secrets/oauth-google-client-id | /run/secrets/oauth-google-client-id | False |
| bind | /srv/docker-shared/super-agent/secrets/oauth-google-client-secret | /run/secrets/oauth-google-client-secret | False |
| bind | /srv/docker-shared/super-agent/secrets/oauth-master-key-v2 | /run/secrets/oauth-master-key-v2 | False |
| bind | /srv/docker-shared/super-agent/secrets/oauth-microsoft-client-id | /run/secrets/oauth-microsoft-client-id | False |
| bind | /srv/docker-shared/super-agent/secrets/oauth-microsoft-client-secret | /run/secrets/oauth-microsoft-client-secret | False |
| bind | /srv/docker-shared/super-agent/secrets/provider-gateway-service | /run/secrets/provider-gateway-service | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.26 |  | ["super-agent-provider-gateway-1", "provider-gateway"] |
| super-agent_SUPER_AGENT_EGRESS | 172.20.0.2 |  | ["super-agent-provider-gateway-1", "provider-gateway"] |
| super-agent_SUPER_AGENT_PROVIDER | 172.22.0.3 |  | ["super-agent-provider-gateway-1", "provider-gateway"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "8080/tcp": null,
  "8081/tcp": null
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "unless-stopped",
    "MaximumRetryCount": 0
  },
  "NetworkMode": "super-agent_SUPER_AGENT_EGRESS",
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
  "Memory": 268435456,
  "MemorySwap": 536870912,
  "NanoCpus": 500000000,
  "CpuShares": 0,
  "PidsLimit": 128,
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

Noms de variables seulement (valeurs exclues) : `PROVIDER_GATEWAY_GOOGLE_REDIRECT_URI`, `PROVIDER_GATEWAY_M365_LINKED_READ_ENABLED`, `PROVIDER_GATEWAY_M365_LINKED_WRITE_ENABLED`, `PROVIDER_GATEWAY_DB_FILE`, `PROVIDER_GATEWAY_MASTER_KEY_FILE`, `PROVIDER_GATEWAY_MICROSOFT_CLIENT_ID_FILE`, `PROVIDER_GATEWAY_GOOGLE_CLIENT_SECRET_FILE`, `PROVIDER_GATEWAY_MICROSOFT_REDIRECT_URI`, `PROVIDER_GATEWAY_MICROSOFT_CLIENT_SECRET_FILE`, `PROVIDER_GATEWAY_PUBLIC_URL`, `PROVIDER_GATEWAY_SERVICE_SECRET_FILE`, `PROVIDER_GATEWAY_MASTER_KEY_VERSION`, `PROVIDER_GATEWAY_GMAIL_LINKED_READ_ENABLED`, `PROVIDER_GATEWAY_MICROSOFT_TENANT_ID`, `PROVIDER_GATEWAY_GOOGLE_CLIENT_ID_FILE`, `PROVIDER_GATEWAY_OAUTH_ENABLED`, `PROVIDER_GATEWAY_RUNTIME`, `PROVIDER_GATEWAY_MICROSOFT_SCOPES`, `PROVIDER_GATEWAY_GOOGLE_SCOPES`, `PROVIDER_GATEWAY_GMAIL_LINKED_WRITE_ENABLED`, `PROVIDER_GATEWAY_STATUS_ENABLED`, `PATH`, `GPG_KEY`, `PYTHON_VERSION`, `PYTHON_SHA256`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — super-agent

ID : `ad3ab46f334102ede5b315bf50fe95024a1e8c2e89668b54f1b788e1779dd4e4`. Image effective : `sha256:249b0c3f01801e9bf4590358e824bbfd50787d1181f2c02d9111cb80fa773645`. Création : 2026-09-24T14:59:53.89810413Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/super-agent/signatures | /data/signatures | False |
| bind | /srv/docker-shared/super-agent/models/fastembed | /data/models/fastembed | False |
| bind | /srv/docker-shared/mcpo/runtime.env | /run/secrets/mcpo-runtime.env | False |
| bind | /srv/docker-shared/super-agent/secrets/provider-gateway-service | /run/secrets/provider-gateway-service | False |
| bind | /srv/docker-shared/super-agent/secrets/redis-password | /run/secrets/redis-password | False |
| bind | /srv/docker-shared/super-agent/secrets/openwebui.env | /run/secrets/super-agent-auth.env | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.25 |  | ["super-agent", "super-agent", "super-agent"] |
| super-agent_SUPER_AGENT_PROVIDER | 172.22.0.2 |  | ["super-agent", "super-agent"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "8080/tcp": null,
  "8081/tcp": null
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "unless-stopped",
    "MaximumRetryCount": 0
  },
  "NetworkMode": "super-agent_SUPER_AGENT_PROVIDER",
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
  "NanoCpus": 2000000000,
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

Noms de variables seulement (valeurs exclues) : `SUPER_AGENT_EXTERNAL_EXECUTION_ENABLED`, `SUPER_AGENT_M365_LINKED_WRITE_ENABLED`, `SUPER_AGENT_GMAIL_LINKED_READ_ENABLED`, `SUPER_AGENT_GLPI_EMBEDDING_URL`, `SUPER_AGENT_GLPI_CATALOG_PROVIDER`, `SUPER_AGENT_REGISTRY_PROVIDER`, `SUPER_AGENT_MODEL_PROFILES_PROVIDER`, `SUPER_AGENT_M365_LINKED_READ_ENABLED`, `SUPER_AGENT_SUPER_CONTEXT_PROVIDER`, `SUPER_AGENT_PROVIDER_GATEWAY_URL`, `SUPER_AGENT_PRESENTATION_PROVIDER`, `SUPER_AGENT_FCONTEXT_PROVIDER`, `SUPER_AGENT_EXTERNAL_INFERENCE_ENABLED`, `SUPER_AGENT_REGISTRY_DIR`, `SUPER_AGENT_MCPO_BASE_URL`, `SUPER_AGENT_GMAIL_LINKED_WRITE_ENABLED`, `SUPER_AGENT_SIGNATURE_ROOT`, `SUPER_AGENT_REDIS_PASSWORD_FILE`, `SUPER_AGENT_SEMANTIC_PROVIDER`, `SUPER_AGENT_RESOLUTION_PROFILES_PROVIDER`, `SUPER_AGENT_MCPO_RUNTIME_ENV_FILE`, `SUPER_AGENT_PROVIDER_GATEWAY_SECRET_FILE`, `SUPER_AGENT_REDIS_URL`, `PATH`, `GPG_KEY`, `PYTHON_VERSION`, `PYTHON_SHA256`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — super-agent-entra-sync-1

ID : `8f42e5a7548b0dcaa347f3ef8eac52508b9cc680954a92ead967e4e71c3c4f94`. Image effective : `sha256:249b0c3f01801e9bf4590358e824bbfd50787d1181f2c02d9111cb80fa773645`. Création : 2026-09-24T14:58:55.294462825Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/super-agent/secrets/entra-sync-certificate.p12 | /run/secrets/entra-sync-certificate.p12 | False |
| bind | /srv/docker-shared/super-agent/secrets/entra-sync-client-id | /run/secrets/entra-sync-client-id | False |
| bind | /srv/docker-shared/super-agent/secrets/redis-password | /run/secrets/redis-password | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.21 |  | ["super-agent-entra-sync-1", "entra-sync"] |
| super-agent_SUPER_AGENT_EGRESS | 172.20.0.3 |  | ["super-agent-entra-sync-1", "entra-sync"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "8080/tcp": null,
  "8081/tcp": null
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "unless-stopped",
    "MaximumRetryCount": 0
  },
  "NetworkMode": "super-agent_SUPER_AGENT_EGRESS",
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
  "Memory": 402653184,
  "MemorySwap": 805306368,
  "NanoCpus": 750000000,
  "CpuShares": 0,
  "PidsLimit": 128,
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

Noms de variables seulement (valeurs exclues) : `SUPER_AGENT_ENTRA_READ_RETRIES`, `SUPER_AGENT_ENTRA_RETAIN_SNAPSHOTS`, `SUPER_AGENT_ENTRA_TIMEOUT_SECONDS`, `SUPER_AGENT_REDIS_PASSWORD_FILE`, `SUPER_AGENT_ENTRA_SYNC_INTERVAL_SECONDS`, `SUPER_AGENT_ENTRA_TENANT_ID`, `SUPER_AGENT_ENTRA_CLIENT_ID_FILE`, `SUPER_AGENT_ENTRA_CERTIFICATE_P12_FILE`, `SUPER_AGENT_ENTRA_MAX_CHANGE_RATIO`, `SUPER_AGENT_ENTRA_STALE_AFTER_SECONDS`, `SUPER_AGENT_REDIS_URL`, `PATH`, `GPG_KEY`, `PYTHON_VERSION`, `PYTHON_SHA256`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — super-agent-redis

ID : `271120df35694b5c5872d5603c2a2487c5805f6c893f561811010eb83b39fe4c`. Image effective : `sha256:798ab84d9f266936b034ab11c4d04a2b8e4b441884c5aa7d17ac951eefdf742a`. Création : 2026-09-24T14:45:54.644687694Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/super-agent/redis | /data | True |
| bind | /srv/docker-shared/super-agent/secrets/redis-password | /run/secrets/redis-password | False |
| bind | /srv/docker-shared/super-agent/secrets/redis-users.acl | /run/secrets/redis-users.acl | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.6 |  | ["super-agent-redis", "super-agent-redis", "super-agent-redis"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "6379/tcp": null
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
  "Memory": 671088640,
  "MemorySwap": 1342177280,
  "NanoCpus": 1000000000,
  "CpuShares": 0,
  "PidsLimit": 128,
  "Ulimits": null,
  "LogConfig": {
    "Type": "json-file",
    "Config": {}
  },
  "Dns": null,
  "ExtraHosts": []
}
```

Utilisateur : `999:65532`. Healthcheck : True.

Noms de variables seulement (valeurs exclues) : `REDIS_ARGS`, `PATH`, `REDISBLOOM_ARGS`, `REDISEARCH_ARGS`, `REDISJSON_ARGS`, `REDISTIMESERIES_ARGS`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/super-agent/compose.yml`. Nœuds : docker-01. SHA-256 : `4d3c13e13e32226c27af520de61fd74cbb5884d50a355382403d3054b3e7958f`.

```json
{
  "services": {
    "super-agent-postgres": {
      "image": "postgres:17.6-bookworm@sha256:f3bd19c606e442c3d7bdfa8002e03fe260a1023351e0ea4598032022b68dd6e3",
      "container_name": "super-agent-postgres",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/super-agent/postgres:/var/lib/postgresql/data",
        "/srv/docker-shared/super-agent/secrets/postgres-admin-password:/run/secrets/postgres-admin-password:ro"
      ],
      "networks": {
        "SUPER_AGENT_STATE": {
          "aliases": [
            "super-agent-postgres"
          ]
        }
      },
      "mem_limit": "768m",
      "cpus": 1.5,
      "environment_keys_only": [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD_FILE",
        "POSTGRES_INITDB_ARGS"
      ],
      "healthcheck_present": true,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "super-agent-redis": {
      "image": "redis/redis-stack-server:7.4.0-v8@sha256:798ab84d9f266936b034ab11c4d04a2b8e4b441884c5aa7d17ac951eefdf742a",
      "container_name": "super-agent-redis",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/super-agent/redis:/data",
        "/srv/docker-shared/super-agent/secrets/redis-password:/run/secrets/redis-password:ro",
        "/srv/docker-shared/super-agent/secrets/redis-users.acl:/run/secrets/redis-users.acl:ro"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "super-agent-redis"
          ]
        }
      },
      "cap_drop": [
        "ALL"
      ],
      "security_opt": [
        "no-new-privileges:true"
      ],
      "user": "999:65532",
      "mem_limit": "640m",
      "cpus": 1.0,
      "environment_keys_only": [
        "REDIS_ARGS"
      ],
      "healthcheck_present": true,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "super-agent": {
      "image": "local/super-agent:0.8.0",
      "container_name": "super-agent",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/mcpo/runtime.env:/run/secrets/mcpo-runtime.env:ro",
        "/srv/docker-shared/super-agent/secrets/openwebui.env:/run/secrets/super-agent-auth.env:ro",
        "/srv/docker-shared/super-agent/secrets/provider-gateway-service:/run/secrets/provider-gateway-service:ro",
        "/srv/docker-shared/super-agent/secrets/redis-password:/run/secrets/redis-password:ro",
        "/srv/docker-shared/super-agent/secrets/postgres-runtime-dsn:/run/secrets/postgres-runtime-dsn:ro",
        "/srv/docker-shared/super-agent/config/closure-policy.json:/config/closure-policy.json:ro",
        "/srv/docker-shared/super-agent/config/turn-entitlements.json:/config/turn-entitlements.json:ro",
        "/srv/docker-shared/super-agent/config/super-context/identity-mappings.json:/config/identity-mappings.json:ro",
        "./config/model-manifest-production.json:/config/model-manifest-production.json:ro",
        "./config/model-routing-production.json:/config/model-routing-production.json:ro",
        "./config/model-manifest-qualification.json:/config/model-manifest-qualification.json:ro",
        "./config/model-routing-qualification.json:/config/model-routing-qualification.json:ro",
        "./catalog/production-repository:/data/turn-catalog:ro",
        "/srv/docker-shared/super-agent/models/fastembed:/data/models/fastembed:ro",
        "/srv/docker-shared/super-agent/signatures:/data/signatures:ro"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "aliases": [
            "super-agent"
          ]
        },
        "SUPER_AGENT_PROVIDER": {},
        "SUPER_AGENT_STATE": {}
      },
      "depends_on": {
        "super-agent-redis": {
          "condition": "service_healthy"
        },
        "super-agent-postgres": {
          "condition": "service_healthy"
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
      "cpus": 2.0,
      "environment_keys_only": [
        "SUPER_AGENT_REGISTRY_DIR",
        "SUPER_AGENT_REGISTRY_PROVIDER",
        "SUPER_AGENT_REDIS_URL",
        "SUPER_AGENT_REDIS_PASSWORD_FILE",
        "SUPER_AGENT_GLPI_CATALOG_PROVIDER",
        "SUPER_AGENT_SEMANTIC_PROVIDER",
        "SUPER_AGENT_PRESENTATION_PROVIDER",
        "SUPER_AGENT_MODEL_PROFILES_PROVIDER",
        "SUPER_AGENT_RESOLUTION_PROFILES_PROVIDER",
        "SUPER_AGENT_FCONTEXT_PROVIDER",
        "SUPER_AGENT_SUPER_CONTEXT_PROVIDER",
        "SUPER_AGENT_EXTERNAL_INFERENCE_ENABLED",
        "SUPER_AGENT_TURN_SERVICE_ENABLED",
        "SUPER_AGENT_TURN_POSTGRES_DSN_FILE",
        "SUPER_AGENT_TURN_CATALOG_REPOSITORY",
        "SUPER_AGENT_TURN_MODEL_URL",
        "SUPER_AGENT_TURN_MODEL",
        "SUPER_AGENT_TURN_MODEL_REVISION",
        "SUPER_AGENT_TURN_ENGINE_VERSION",
        "SUPER_AGENT_TURN_MODEL_BACKEND_REF",
        "SUPER_AGENT_TURN_MODEL_CONFIGURATION_DIGEST",
        "SUPER_AGENT_TURN_MODEL_MANIFEST_FILE",
        "SUPER_AGENT_TURN_ROUTING_POLICY_FILE",
        "SUPER_AGENT_QUALIFICATION_MODEL_MANIFEST_FILE",
        "SUPER_AGENT_QUALIFICATION_ROUTING_POLICY_FILE",
        "SUPER_AGENT_TURN_POLICY_REVISION",
        "SUPER_AGENT_TURN_ROUTING_POLICY_REVISION",
        "SUPER_AGENT_TURN_QUOTA_POLICY_REVISION",
        "SUPER_AGENT_TURN_AUTHORIZATION_REF",
        "SUPER_AGENT_TURN_ORGANIZATION",
        "SUPER_AGENT_TURN_INFERENCE_ACTOR",
        "SUPER_AGENT_TURN_PROFILES",
        "SUPER_AGENT_TURN_COHORT",
        "SUPER_AGENT_TURN_CAPABILITIES",
        "SUPER_AGENT_TURN_BINDINGS_JSON",
        "SUPER_AGENT_TURN_ENTITLEMENTS_FILE",
        "SUPER_AGENT_TURN_IDENTITY_MAPPINGS_FILE",
        "SUPER_AGENT_TURN_LEXICAL_FALLBACK",
        "SUPER_AGENT_TURN_EMBEDDING_MODEL",
        "SUPER_AGENT_TURN_EMBEDDING_REVISION",
        "SUPER_AGENT_TURN_EMBEDDING_DIMENSION",
        "SUPER_AGENT_TURN_EMBEDDING_CACHE",
        "SUPER_AGENT_TURN_EMBEDDING_REVISION_MARKER",
        "SUPER_AGENT_TURN_EMBEDDING_ARTIFACT",
        "SUPER_AGENT_TURN_EMBEDDING_ARTIFACT_DIGEST",
        "SUPER_AGENT_JOURNAL_MIRROR_ENABLED",
        "SUPER_AGENT_JOURNAL_ENVIRONMENT",
        "SUPER_AGENT_JOURNAL_DSN_FILE",
        "SUPER_AGENT_CLOSURE_POLICY_FILE",
        "SUPER_AGENT_JOURNAL_QUEUE_SIZE",
        "SUPER_AGENT_JOURNAL_CONNECT_TIMEOUT",
        "SUPER_AGENT_JOURNAL_STATEMENT_TIMEOUT_MS",
        "SUPER_AGENT_MCPO_BASE_URL",
        "SUPER_AGENT_MCPO_RUNTIME_ENV_FILE",
        "SUPER_AGENT_SIGNATURE_ROOT",
        "SUPER_AGENT_EXTERNAL_EXECUTION_ENABLED",
        "SUPER_AGENT_GLPI_EMBEDDING_URL",
        "SUPER_AGENT_PROVIDER_GATEWAY_URL",
        "SUPER_AGENT_PROVIDER_GATEWAY_SECRET_FILE",
        "SUPER_AGENT_M365_LINKED_READ_ENABLED",
        "SUPER_AGENT_M365_LINKED_WRITE_ENABLED",
        "SUPER_AGENT_GMAIL_LINKED_READ_ENABLED",
        "SUPER_AGENT_GMAIL_LINKED_WRITE_ENABLED"
      ],
      "healthcheck_present": true,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "provider-gateway": {
      "image": "local/super-agent:0.7.0",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/super-agent/linked-accounts:/data",
        "/srv/docker-shared/super-agent/secrets/provider-gateway-service:/run/secrets/provider-gateway-service:ro",
        "/srv/docker-shared/super-agent/secrets/oauth-master-key-v2:/run/secrets/oauth-master-key-v2:ro",
        "/srv/docker-shared/super-agent/secrets/oauth-microsoft-client-id:/run/secrets/oauth-microsoft-client-id:ro",
        "/srv/docker-shared/super-agent/secrets/oauth-microsoft-client-secret:/run/secrets/oauth-microsoft-client-secret:ro",
        "/srv/docker-shared/super-agent/secrets/oauth-google-client-id:/run/secrets/oauth-google-client-id:ro",
        "/srv/docker-shared/super-agent/secrets/oauth-google-client-secret:/run/secrets/oauth-google-client-secret:ro"
      ],
      "networks": {
        "SUPER_AGENT_PROVIDER": {},
        "SUPER_AGENT_EGRESS": {},
        "TRAEFIK_BACKEND": {}
      },
      "read_only": true,
      "cap_drop": [
        "ALL"
      ],
      "security_opt": [
        "no-new-privileges:true"
      ],
      "user": "65532:65532",
      "mem_limit": "256m",
      "cpus": 0.5,
      "environment_keys_only": [
        "PROVIDER_GATEWAY_RUNTIME",
        "PROVIDER_GATEWAY_STATUS_ENABLED",
        "PROVIDER_GATEWAY_OAUTH_ENABLED",
        "PROVIDER_GATEWAY_M365_LINKED_READ_ENABLED",
        "PROVIDER_GATEWAY_M365_LINKED_WRITE_ENABLED",
        "PROVIDER_GATEWAY_GMAIL_LINKED_READ_ENABLED",
        "PROVIDER_GATEWAY_GMAIL_LINKED_WRITE_ENABLED",
        "PROVIDER_GATEWAY_DB_FILE",
        "PROVIDER_GATEWAY_SERVICE_SECRET_FILE",
        "PROVIDER_GATEWAY_MASTER_KEY_FILE",
        "PROVIDER_GATEWAY_MASTER_KEY_VERSION",
        "PROVIDER_GATEWAY_MICROSOFT_TENANT_ID",
        "PROVIDER_GATEWAY_MICROSOFT_CLIENT_ID_FILE",
        "PROVIDER_GATEWAY_MICROSOFT_CLIENT_SECRET_FILE",
        "PROVIDER_GATEWAY_MICROSOFT_REDIRECT_URI",
        "PROVIDER_GATEWAY_MICROSOFT_SCOPES",
        "PROVIDER_GATEWAY_GOOGLE_CLIENT_ID_FILE",
        "PROVIDER_GATEWAY_GOOGLE_CLIENT_SECRET_FILE",
        "PROVIDER_GATEWAY_GOOGLE_REDIRECT_URI",
        "PROVIDER_GATEWAY_GOOGLE_SCOPES",
        "PROVIDER_GATEWAY_PUBLIC_URL"
      ],
      "healthcheck_present": true,
      "command_present": true,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "catalog-publisher": {
      "image": "local/super-agent:0.7.0",
      "volumes": [
        "/srv/docker-shared/super-agent/registry:/publisher/registry:ro",
        "/srv/docker-shared/super-agent/catalog:/publisher/catalog:ro",
        "/srv/docker-shared/super-agent/config:/publisher/config:ro",
        "/srv/docker-shared/super-agent/secrets/redis-password:/run/secrets/redis-password:ro",
        "/srv/docker-shared/super-agent/models/fastembed:/data/models/fastembed:ro"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {}
      },
      "depends_on": {
        "super-agent-redis": {
          "condition": "service_healthy"
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
      "environment_keys_only": [
        "SUPER_AGENT_REDIS_URL",
        "SUPER_AGENT_REDIS_PASSWORD_FILE"
      ],
      "healthcheck_present": false,
      "command_present": true,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "calendar-sync": {
      "image": "local/super-agent:0.7.0",
      "volumes": [
        "/srv/docker-shared/mcpo/runtime.env:/run/secrets/mcpo-runtime.env:ro",
        "/srv/docker-shared/super-agent/registry:/publisher/registry:ro",
        "/srv/docker-shared/super-agent/catalog:/publisher/catalog:ro",
        "/srv/docker-shared/super-agent/config:/publisher/config",
        "/srv/docker-shared/super-agent/secrets/redis-password:/run/secrets/redis-password:ro",
        "/srv/docker-shared/super-agent/models/fastembed:/data/models/fastembed"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {}
      },
      "depends_on": {
        "super-agent-redis": {
          "condition": "service_healthy"
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
      "environment_keys_only": [
        "SUPER_AGENT_REDIS_URL",
        "SUPER_AGENT_REDIS_PASSWORD_FILE",
        "SUPER_AGENT_MCPO_BASE_URL",
        "SUPER_AGENT_MCPO_RUNTIME_ENV_FILE"
      ],
      "healthcheck_present": false,
      "command_present": true,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "entra-sync": {
      "image": "local/super-agent:0.7.0",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/super-agent/secrets/entra-sync-client-id:/run/secrets/entra-sync-client-id:ro",
        "/srv/docker-shared/super-agent/secrets/entra-sync-certificate.p12:/run/secrets/entra-sync-certificate.p12:ro",
        "/srv/docker-shared/super-agent/secrets/redis-password:/run/secrets/redis-password:ro"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {},
        "SUPER_AGENT_EGRESS": {}
      },
      "depends_on": {
        "super-agent-redis": {
          "condition": "service_healthy"
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
      "mem_limit": "384m",
      "cpus": 0.75,
      "environment_keys_only": [
        "SUPER_AGENT_REDIS_URL",
        "SUPER_AGENT_REDIS_PASSWORD_FILE",
        "SUPER_AGENT_ENTRA_TENANT_ID",
        "SUPER_AGENT_ENTRA_CLIENT_ID_FILE",
        "SUPER_AGENT_ENTRA_CERTIFICATE_P12_FILE",
        "SUPER_AGENT_ENTRA_TIMEOUT_SECONDS",
        "SUPER_AGENT_ENTRA_READ_RETRIES",
        "SUPER_AGENT_ENTRA_MAX_CHANGE_RATIO",
        "SUPER_AGENT_ENTRA_SYNC_INTERVAL_SECONDS",
        "SUPER_AGENT_ENTRA_RETAIN_SNAPSHOTS",
        "SUPER_AGENT_ENTRA_STALE_AFTER_SECONDS"
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
    },
    "SUPER_AGENT_PROVIDER": {
      "internal": true
    },
    "SUPER_AGENT_EGRESS": {
      "driver": "bridge",
      "internal": false
    },
    "SUPER_AGENT_STATE": {
      "internal": true
    }
  }
}
```
