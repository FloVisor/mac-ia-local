# wg-router

Instantané du 21 octobre 2026. WG-Router et son sidecar de routes tournent sur docker-01. NET_ADMIN et /dev/net/tun sont présents. Le sidecar partage le namespace réseau du routeur ; sa liste Networks vide ne signifie pas absence de réseau. La clé WireGuard est un fichier local réel (0600, root), pas un lien vers docker-shared. Le Compose de docker-01 déclare le sidecar wg-router-routes ; ceux de docker-02/03 ne le déclarent pas : dérive de reconstruction à traiter séparément. Le contenu de la clé et les règles VPN ne sont pas exportés ; trafic VPN réel non qualifié.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-01 | WG-Router-Routes | running / healthy | qmcgaw/gluetun:v3.41.1 | 0 |
| docker-01 | WG-Router | running / healthy | qmcgaw/gluetun:v3.41.1 | 0 |


## docker-01 — WG-Router-Routes

ID : `b48f4333f45f70cacb4acef95c7e7b9edce131d23d727e07fa67a58db4c77b59`. Image effective : `sha256:1a5bf4b4820a879cdf8d93d7ef0d2d963af56670c9ebff8981860b6804ebc8ab`. Création : 2026-10-20T12:23:22.411804959Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-local/compose/wg-router/scripts | /scripts | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|


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
  "NetworkMode": "container:a4cc0dccb7f725c1d7aa7ecda1695bc60223e76431f9cbb6778a82d85ba12da1",
  "PortBindings": {},
  "Privileged": false,
  "ReadonlyRootfs": false,
  "CapAdd": [
    "CAP_NET_ADMIN"
  ],
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

Noms de variables seulement (valeurs exclues) : `PATH`, `VPN_SERVICE_PROVIDER`, `VPN_TYPE`, `VPN_INTERFACE`, `OPENVPN_ENDPOINT_IP`, `OPENVPN_ENDPOINT_PORT`, `OPENVPN_PROTOCOL`, `OPENVPN_USER`, `OPENVPN_PASSWORD`, `OPENVPN_USER_SECRETFILE`, `OPENVPN_PASSWORD_SECRETFILE`, `OPENVPN_VERSION`, `OPENVPN_VERBOSITY`, `OPENVPN_FLAGS`, `OPENVPN_CIPHERS`, `OPENVPN_AUTH`, `OPENVPN_PROCESS_USER`, `OPENVPN_MSSFIX`, `OPENVPN_CUSTOM_CONFIG`, `WIREGUARD_ENDPOINT_IP`, `WIREGUARD_ENDPOINT_PORT`, `WIREGUARD_CONF_SECRETFILE`, `WIREGUARD_PRIVATE_KEY`, `WIREGUARD_PRIVATE_KEY_SECRETFILE`, `WIREGUARD_PRESHARED_KEY`, `WIREGUARD_PRESHARED_KEY_SECRETFILE`, `WIREGUARD_PUBLIC_KEY`, `WIREGUARD_ALLOWED_IPS`, `WIREGUARD_PERSISTENT_KEEPALIVE_INTERVAL`, `WIREGUARD_ADDRESSES`, `WIREGUARD_ADDRESSES_SECRETFILE`, `WIREGUARD_MTU`, `WIREGUARD_IMPLEMENTATION`, `SERVER_REGIONS`, `SERVER_COUNTRIES`, `SERVER_CITIES`, `SERVER_HOSTNAMES`, `SERVER_CATEGORIES`, `ISP`, `OWNED_ONLY`, `PRIVATE_INTERNET_ACCESS_OPENVPN_ENCRYPTION_PRESET`, `VPN_PORT_FORWARDING`, `VPN_PORT_FORWARDING_LISTENING_PORT`, `VPN_PORT_FORWARDING_PROVIDER`, `VPN_PORT_FORWARDING_STATUS_FILE`, `VPN_PORT_FORWARDING_USERNAME`, `VPN_PORT_FORWARDING_PASSWORD`, `VPN_PORT_FORWARDING_UP_COMMAND`, `VPN_PORT_FORWARDING_DOWN_COMMAND`, `OPENVPN_CERT`, `OPENVPN_KEY`, `OPENVPN_CLIENTCRT_SECRETFILE`, `OPENVPN_CLIENTKEY_SECRETFILE`, `OPENVPN_ENCRYPTED_KEY`, `OPENVPN_ENCRYPTED_KEY_SECRETFILE`, `OPENVPN_KEY_PASSPHRASE`, `OPENVPN_KEY_PASSPHRASE_SECRETFILE`, `SERVER_NUMBER`, `SERVER_NAMES`, `STREAM_ONLY`, `FREE_ONLY`, `SECURE_CORE_ONLY`, `TOR_ONLY`, `MULTIHOP_ONLY`, `PREMIUM_ONLY`, `PORT_FORWARD_ONLY`, `FIREWALL_ENABLED_DISABLING_IT_SHOOTS_YOU_IN_YOUR_FOOT`, `FIREWALL_VPN_INPUT_PORTS`, `FIREWALL_INPUT_PORTS`, `FIREWALL_OUTBOUND_SUBNETS`, `FIREWALL_DEBUG`, `LOG_LEVEL`, `HEALTH_SERVER_ADDRESS`, `HEALTH_TARGET_ADDRESSES`, `HEALTH_ICMP_TARGET_IPS`, `HEALTH_SMALL_CHECK_TYPE`, `HEALTH_RESTART_VPN`, `DNS_SERVER`, `DNS_UPSTREAM_RESOLVER_TYPE`, `DNS_UPSTREAM_RESOLVERS`, `DNS_BLOCK_IPS`, `DNS_BLOCK_IP_PREFIXES`, `DNS_CACHING`, `DNS_UPSTREAM_IPV6`, `BLOCK_MALICIOUS`, `BLOCK_SURVEILLANCE`, `BLOCK_ADS`, `DNS_UNBLOCK_HOSTNAMES`, `DNS_REBINDING_PROTECTION_EXEMPT_HOSTNAMES`, `DNS_UPDATE_PERIOD`, `DNS_ADDRESS`, `DNS_KEEP_NAMESERVER`, `HTTPPROXY`, `HTTPPROXY_LOG`, `HTTPPROXY_LISTENING_ADDRESS`, `HTTPPROXY_STEALTH`, `HTTPPROXY_USER`, `HTTPPROXY_PASSWORD`, `HTTPPROXY_USER_SECRETFILE`, `HTTPPROXY_PASSWORD_SECRETFILE`, `SHADOWSOCKS`, `SHADOWSOCKS_LOG`, `SHADOWSOCKS_LISTENING_ADDRESS`, `SHADOWSOCKS_PASSWORD`, `SHADOWSOCKS_PASSWORD_SECRETFILE`, `SHADOWSOCKS_CIPHER`, `HTTP_CONTROL_SERVER_LOG`, `HTTP_CONTROL_SERVER_ADDRESS`, `HTTP_CONTROL_SERVER_AUTH_CONFIG_FILEPATH`, `HTTP_CONTROL_SERVER_AUTH_DEFAULT_ROLE`, `UPDATER_PERIOD`, `UPDATER_MIN_RATIO`, `UPDATER_VPN_SERVICE_PROVIDERS`, `UPDATER_PROTONVPN_EMAIL`, `UPDATER_PROTONVPN_PASSWORD`, `PUBLICIP_FILE`, `PUBLICIP_ENABLED`, `PUBLICIP_API`, `PUBLICIP_API_TOKEN`, `STORAGE_FILEPATH`, `PPROF_ENABLED`, `PPROF_BLOCK_PROFILE_RATE`, `PPROF_MUTEX_PROFILE_RATE`, `PPROF_HTTP_SERVER_ADDRESS`, `VERSION_INFORMATION`, `TZ`, `PUID`, `PGID`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## docker-01 — WG-Router

ID : `a4cc0dccb7f725c1d7aa7ecda1695bc60223e76431f9cbb6778a82d85ba12da1`. Image effective : `sha256:1a5bf4b4820a879cdf8d93d7ef0d2d963af56670c9ebff8981860b6804ebc8ab`. Création : 2026-10-20T12:23:10.354050906Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/wg-router/gluetun | /gluetun | True |
| bind | /srv/docker-local/compose/wg-router/iptables/post-rules.txt | /iptables/post-rules.txt | False |
| bind | /srv/docker-local/compose/wg-router/secrets/wireguard_private_key | /run/secrets/wireguard_private_key | False |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| WAN | 192.168.200.30 | 2a01:e0a:8ce:68c0::30 | ["WG-Router", "gluetun"] |
| WG_Internal | 172.31.204.2 |  | ["WG-Router", "gluetun"] |
| WG_Transit | 192.168.204.30 | 2a01:e0a:8ce:68c4::30 | ["WG-Router", "gluetun"] |


Bindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :

```json
{
  "8000/tcp": null,
  "8388/tcp": null,
  "8388/udp": null,
  "8888/tcp": null
}
```

### Exécution et isolation

```json
{
  "RestartPolicy": {
    "Name": "on-failure",
    "MaximumRetryCount": 5
  },
  "NetworkMode": "WAN",
  "PortBindings": {},
  "Privileged": false,
  "ReadonlyRootfs": false,
  "CapAdd": [
    "CAP_NET_ADMIN"
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

Utilisateur : non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié. Healthcheck : True.

Noms de variables seulement (valeurs exclues) : `WIREGUARD_ENDPOINT_PORT`, `DNS_UPSTREAM_RESOLVERS`, `BLOCK_SURVEILLANCE`, `FREE_ONLY`, `OPENVPN_USER`, `OPENVPN_CERT`, `BLOCK_MALICIOUS`, `WIREGUARD_ADDRESSES`, `VPN_PORT_FORWARDING_PORTS_COUNT`, `HTTPPROXY_LOG`, `VPN_PORT_FORWARDING_PROVIDER`, `OPENVPN_CUSTOM_CONFIG`, `WIREGUARD_PUBLIC_KEY`, `BLOCK_ADS`, `VPN_PORT_FORWARDING`, `WIREGUARD_PERSISTENT_KEEPALIVE_INTERVAL`, `WIREGUARD_PRIVATE_KEY`, `DNS_UNBLOCK_HOSTNAMES`, `WIREGUARD_PRESHARED_KEY`, `DNS_UPSTREAM_RESOLVER_TYPE`, `VPN_TYPE`, `WIREGUARD_PRIVATE_KEY_SECRETFILE`, `TZ`, `HTTPPROXY_LISTENING_ADDRESS`, `SERVER_CITIES`, `HTTP_CONTROL_SERVER_AUTH_DEFAULT_ROLE`, `SERVER_HOSTNAMES`, `WIREGUARD_ENDPOINT_IP`, `TOR_ONLY`, `OPENVPN_KEY_PASSPHRASE`, `HTTPPROXY`, `SERVER_REGIONS`, `OPENVPN_PASSWORD`, `STREAM_ONLY`, `SERVER_NAMES`, `OPENVPN_ENCRYPTED_KEY`, `OPENVPN_KEY`, `HTTP_CONTROL_SERVER_ADDRESS`, `VPN_SERVICE_PROVIDER`, `SERVER_TYPES`, `SECURE_CORE_ONLY`, `WIREGUARD_ALLOWED_IPS`, `SERVER_COUNTRIES`, `DNS_UPSTREAM_IPV6`, `PORT_FORWARD_ONLY`, `FIREWALL_OUTBOUND_SUBNETS`, `PATH`, `VPN_INTERFACE`, `OPENVPN_ENDPOINT_IP`, `OPENVPN_ENDPOINT_PORT`, `OPENVPN_PROTOCOL`, `OPENVPN_USER_SECRETFILE`, `OPENVPN_PASSWORD_SECRETFILE`, `OPENVPN_VERSION`, `OPENVPN_VERBOSITY`, `OPENVPN_FLAGS`, `OPENVPN_CIPHERS`, `OPENVPN_AUTH`, `OPENVPN_PROCESS_USER`, `OPENVPN_MSSFIX`, `WIREGUARD_CONF_SECRETFILE`, `WIREGUARD_PRESHARED_KEY_SECRETFILE`, `WIREGUARD_ADDRESSES_SECRETFILE`, `WIREGUARD_MTU`, `WIREGUARD_IMPLEMENTATION`, `SERVER_CATEGORIES`, `ISP`, `OWNED_ONLY`, `PRIVATE_INTERNET_ACCESS_OPENVPN_ENCRYPTION_PRESET`, `VPN_PORT_FORWARDING_LISTENING_PORT`, `VPN_PORT_FORWARDING_STATUS_FILE`, `VPN_PORT_FORWARDING_USERNAME`, `VPN_PORT_FORWARDING_PASSWORD`, `VPN_PORT_FORWARDING_UP_COMMAND`, `VPN_PORT_FORWARDING_DOWN_COMMAND`, `OPENVPN_CLIENTCRT_SECRETFILE`, `OPENVPN_CLIENTKEY_SECRETFILE`, `OPENVPN_ENCRYPTED_KEY_SECRETFILE`, `OPENVPN_KEY_PASSPHRASE_SECRETFILE`, `SERVER_NUMBER`, `MULTIHOP_ONLY`, `PREMIUM_ONLY`, `FIREWALL_ENABLED_DISABLING_IT_SHOOTS_YOU_IN_YOUR_FOOT`, `FIREWALL_VPN_INPUT_PORTS`, `FIREWALL_INPUT_PORTS`, `FIREWALL_DEBUG`, `LOG_LEVEL`, `HEALTH_SERVER_ADDRESS`, `HEALTH_TARGET_ADDRESSES`, `HEALTH_ICMP_TARGET_IPS`, `HEALTH_SMALL_CHECK_TYPE`, `HEALTH_RESTART_VPN`, `DNS_SERVER`, `DNS_BLOCK_IPS`, `DNS_BLOCK_IP_PREFIXES`, `DNS_CACHING`, `DNS_REBINDING_PROTECTION_EXEMPT_HOSTNAMES`, `DNS_UPDATE_PERIOD`, `DNS_ADDRESS`, `DNS_KEEP_NAMESERVER`, `HTTPPROXY_STEALTH`, `HTTPPROXY_USER`, `HTTPPROXY_PASSWORD`, `HTTPPROXY_USER_SECRETFILE`, `HTTPPROXY_PASSWORD_SECRETFILE`, `SHADOWSOCKS`, `SHADOWSOCKS_LOG`, `SHADOWSOCKS_LISTENING_ADDRESS`, `SHADOWSOCKS_PASSWORD`, `SHADOWSOCKS_PASSWORD_SECRETFILE`, `SHADOWSOCKS_CIPHER`, `HTTP_CONTROL_SERVER_LOG`, `HTTP_CONTROL_SERVER_AUTH_CONFIG_FILEPATH`, `UPDATER_PERIOD`, `UPDATER_MIN_RATIO`, `UPDATER_VPN_SERVICE_PROVIDERS`, `UPDATER_PROTONVPN_EMAIL`, `UPDATER_PROTONVPN_PASSWORD`, `PUBLICIP_FILE`, `PUBLICIP_ENABLED`, `PUBLICIP_API`, `PUBLICIP_API_TOKEN`, `STORAGE_FILEPATH`, `PPROF_ENABLED`, `PPROF_BLOCK_PROFILE_RATE`, `PPROF_MUTEX_PROFILE_RATE`, `PPROF_HTTP_SERVER_ADDRESS`, `VERSION_INFORMATION`, `PUID`, `PGID`.

Source : [capture docker-01](../evidence/2026-10-21/docker-01.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/wg-router/compose.yml`. Nœuds : docker-01. SHA-256 : `7c1c9d276ecc6217f7efefdbbb9ec4397b38fd5aa75fe3f7e29ec38b57553d1b`.

```json
{
  "services": {
    "gluetun": {
      "image": "qmcgaw/gluetun:v3.41.1",
      "container_name": "WG-Router",
      "restart": "on-failure:5",
      "volumes": [
        "/srv/docker-shared/wg-router/gluetun:/gluetun",
        "./iptables/post-rules.txt:/iptables/post-rules.txt:ro"
      ],
      "networks": {
        "WAN": {
          "interface_name": "wan0",
          "ipv4_address": "192.168.200.30",
          "ipv6_address": "2a01:e0a:8ce:68c0::30",
          "mac_address": "02:00:00:c8:00:30",
          "gw_priority": 100
        },
        "WG_Transit": {
          "interface_name": "transit0",
          "ipv4_address": "192.168.204.30",
          "ipv6_address": "2a01:e0a:8ce:68c4::30",
          "mac_address": "02:00:00:cc:00:30"
        },
        "WG_Internal": {
          "interface_name": "admin0",
          "ipv4_address": "172.31.204.2"
        }
      },
      "cap_add": [
        "NET_ADMIN"
      ],
      "devices": [
        "/dev/net/tun:/dev/net/tun"
      ],
      "secrets": [
        "wireguard_private_key"
      ],
      "environment_keys_only": [
        "TZ",
        "VPN_SERVICE_PROVIDER",
        "VPN_TYPE",
        "WIREGUARD_PRIVATE_KEY_SECRETFILE",
        "WIREGUARD_ADDRESSES",
        "WIREGUARD_ALLOWED_IPS",
        "WIREGUARD_PERSISTENT_KEEPALIVE_INTERVAL",
        "SERVER_COUNTRIES",
        "PORT_FORWARD_ONLY",
        "VPN_PORT_FORWARDING",
        "VPN_PORT_FORWARDING_PORTS_COUNT",
        "DNS_UPSTREAM_RESOLVER_TYPE",
        "DNS_UPSTREAM_RESOLVERS",
        "DNS_UPSTREAM_IPV6",
        "BLOCK_MALICIOUS",
        "BLOCK_ADS",
        "BLOCK_SURVEILLANCE",
        "FIREWALL_OUTBOUND_SUBNETS",
        "HTTP_CONTROL_SERVER_ADDRESS",
        "HTTP_CONTROL_SERVER_AUTH_DEFAULT_ROLE",
        "HTTPPROXY",
        "HTTPPROXY_LISTENING_ADDRESS",
        "HTTPPROXY_LOG"
      ],
      "healthcheck_present": false,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    },
    "wg-router-routes": {
      "image": "qmcgaw/gluetun:v3.41.1",
      "container_name": "WG-Router-Routes",
      "restart": "unless-stopped",
      "volumes": [
        "./scripts:/scripts:ro"
      ],
      "depends_on": {
        "gluetun": {
          "condition": "service_healthy",
          "restart": true
        }
      },
      "cap_add": [
        "NET_ADMIN"
      ],
      "network_mode": "service:gluetun",
      "environment_keys_only": [],
      "healthcheck_present": false,
      "command_present": false,
      "entrypoint_present": true,
      "traefik_labels": {}
    }
  },
  "networks": {
    "WAN": {
      "external": true,
      "name": "WAN"
    },
    "WG_Transit": {
      "external": true,
      "name": "WG_Transit"
    },
    "WG_Internal": {
      "external": true,
      "name": "WG_Internal"
    }
  },
  "secrets": {
    "wireguard_private_key": "[REDACTED]"
  }
}
```

Chemin : `/srv/docker-local/compose/wg-router/compose.yml`. Nœuds : docker-02, docker-03. SHA-256 : `cacfd04e4f3d3d6c7eb96e932434613681779daa9f87f52ef3d6f35106c4d12c`.

```json
{
  "services": {
    "gluetun": {
      "image": "qmcgaw/gluetun:v3.41.1",
      "container_name": "WG-Router",
      "restart": "on-failure:5",
      "volumes": [
        "/srv/docker-shared/wg-router/gluetun:/gluetun",
        "./iptables/post-rules.txt:/iptables/post-rules.txt:ro"
      ],
      "networks": {
        "WAN": {
          "interface_name": "wan0",
          "ipv4_address": "192.168.200.30",
          "ipv6_address": "2a01:e0a:8ce:68c0::30",
          "mac_address": "02:00:00:c8:00:30",
          "gw_priority": 100
        },
        "WG_Transit": {
          "interface_name": "transit0",
          "ipv4_address": "192.168.204.30",
          "ipv6_address": "2a01:e0a:8ce:68c4::30",
          "mac_address": "02:00:00:cc:00:30"
        },
        "WG_Internal": {
          "interface_name": "admin0",
          "ipv4_address": "172.31.204.2"
        }
      },
      "cap_add": [
        "NET_ADMIN"
      ],
      "devices": [
        "/dev/net/tun:/dev/net/tun"
      ],
      "secrets": [
        "wireguard_private_key"
      ],
      "environment_keys_only": [
        "TZ",
        "VPN_SERVICE_PROVIDER",
        "VPN_TYPE",
        "WIREGUARD_PRIVATE_KEY_SECRETFILE",
        "WIREGUARD_ADDRESSES",
        "WIREGUARD_ALLOWED_IPS",
        "WIREGUARD_PERSISTENT_KEEPALIVE_INTERVAL",
        "SERVER_COUNTRIES",
        "PORT_FORWARD_ONLY",
        "VPN_PORT_FORWARDING",
        "VPN_PORT_FORWARDING_PORTS_COUNT",
        "DNS_UPSTREAM_RESOLVER_TYPE",
        "DNS_UPSTREAM_RESOLVERS",
        "DNS_UPSTREAM_IPV6",
        "BLOCK_MALICIOUS",
        "BLOCK_ADS",
        "BLOCK_SURVEILLANCE",
        "FIREWALL_OUTBOUND_SUBNETS",
        "HTTP_CONTROL_SERVER_ADDRESS",
        "HTTP_CONTROL_SERVER_AUTH_DEFAULT_ROLE",
        "HTTPPROXY",
        "HTTPPROXY_LISTENING_ADDRESS",
        "HTTPPROXY_LOG"
      ],
      "healthcheck_present": false,
      "command_present": false,
      "entrypoint_present": false,
      "traefik_labels": {}
    }
  },
  "networks": {
    "WAN": {
      "external": true,
      "name": "WAN"
    },
    "WG_Transit": {
      "external": true,
      "name": "WG_Transit"
    },
    "WG_Internal": {
      "external": true,
      "name": "WG_Internal"
    }
  },
  "secrets": {
    "wireguard_private_key": "[REDACTED]"
  }
}
```
