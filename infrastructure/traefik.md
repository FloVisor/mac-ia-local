# Traefik — configuration et contrôles

Audit du 21 octobre 2026. Conteneur Traefik v3.7.13 sur docker-02. Compose identique par SHA-256 sur les trois nœuds. Configuration dynamique sous /srv/docker-shared/traefik/dynamic, ACME sous /srv/docker-shared/traefik/acme/acme.json ; secrets OVH référencés par fichiers, jamais lus ou exportés.

## Configuration statique active

```json
[
  "--log.level=INFO",
  "--entryPoints.web.address=:80",
  "--entryPoints.websecure.address=:443",
  "--entryPoints.minecraft.address=:25565/tcp",
  "--entryPoints.health.address=:8082",
  "--ping=true",
  "--ping.entryPoint=health",
  "--providers.file.directory=/etc/traefik/dynamic",
  "--providers.file.watch=true",
  "--certificatesresolvers.le.acme.email=florian@gangneux.org",
  "--certificatesresolvers.le.acme.storage=/acme/acme.json",
  "--certificatesresolvers.le.acme.dnschallenge=true",
  "--certificatesresolvers.le.acme.dnschallenge.provider=ovh",
  "--certificatesresolvers.le.acme.dnschallenge.resolvers=1.1.1.1:53,8.8.8.8:53"
]
```

Le provider actif déclaré est file avec watch=true. Entrypoints : web :80, websecure :443, minecraft :25565/tcp, health :8082 avec ping. Aucun argument de redirection globale HTTP→HTTPS ou provider Docker n’est présent dans cette liste ; règles réseau et listeners seuls ne constituent pas une preuve d’accès externe.

## Routage et politiques

| Protocole | Routeur | Règle | Entrypoints | Middlewares | Service | Backends |
|---|---|---|---|---|---|---|
| http | acme-bootstrap | Host(`acme-bootstrap.gangneux.org`) | ["websecure"] | [] | acme-bootstrap | [{"url": "http://127.0.0.1:65535"}] |
| http | bookstack | Host(`bookstack.gangneux.org`) | ["websecure"] | [] | bookstack | [{"url": "http://bookstack:80"}] |
| http | diun | Host(`diun.gangneux.org`) | ["websecure"] | ["private-networks@file"] | diun | [{"url": "http://diun:9090"}] |
| http | dns | Host(`dns.gangneux.org`) | ["websecure"] | ["private-networks@file"] | technitium-dns | [{"url": "http://192.168.201.33:5380"}] |
| http | gluetun | Host(`gluetun.gangneux.org`) | ["websecure"] | ["private-networks@file"] | gluetun | [{"url": "http://192.168.201.21:8765"}, {"url": "http://[2a01:e0a:8ce:68c1::21]:8765"}, {"url": "http://192.168.201.22:8765"}, {"url": "http://[2a01:e0a:8ce:68c1::22]:8765"}, {"url": "http://192.168.201.23:8765"}, {"url": "http://[2a01:e0a:8ce:68c1::23]:8765"}] |
| http | homeassistant | Host(`homeassistant.gangneux.org`) | ["websecure"] | ["private-networks@file"] | homeassistant | [{"url": "http://homeassistant:8123"}] |
| http | homepage | Host(`home.gangneux.org`) | ["websecure"] | [] | homepage | [{"url": "http://homepage:3000"}] |
| tcp | minecraft | HostSNI(`*`) | ["minecraft"] | [] | minecraft | [{"address": "172.29.2.11:25565"}] |
| http | n8n | Host(`n8n.gangneux.org`) | ["websecure"] | ["CORP@file"] | n8n | [{"url": "http://n8n:5678"}] |
| http | nas | Host(`nas.gangneux.org`) | ["websecure"] | [] | nas | [{"url": "https://192.168.201.61:5001"}, {"url": "https://[2a01:e0a:8ce:68c1::61]:5001"}] |
| http | openwebui | Host(`owui.gangneux.org`) | ["websecure"] | [] | openwebui | [{"url": "http://openwebui:8080"}] |
| http | portainer | Host(`portainer.gangneux.org`) | ["websecure"] | ["private-networks@file"] | portainer | [{"url": "https://192.168.201.21:9443"}, {"url": "https://[2a01:e0a:8ce:68c1::21]:9443"}, {"url": "https://192.168.201.22:9443"}, {"url": "https://[2a01:e0a:8ce:68c1::22]:9443"}, {"url": "https://192.168.201.23:9443"}, {"url": "https://[2a01:e0a:8ce:68c1::23]:9443"}] |
| http | qbittorrent | Host(`qbittorrent.gangneux.org`) | ["websecure"] | ["private-networks@file"] | qbittorrent | [{"url": "http://192.168.205.40:8080"}, {"url": "http://[2a01:e0a:8ce:68c5::40]:8080"}] |
| http | super-agent-oauth | Host(`auth.gangneux.org`) && (PathPrefix(`/oauth/microsoft/authorize/`) &#124;&#124; Path(`/oauth/microsoft/callback`) &#124;&#124; PathPrefix(`/oauth/google/authorize/`) &#124;&#124; Path(`/oauth/google/callback`)) | ["websecure"] | [] | super-agent-oauth | [{"url": "http://provider-gateway:8081"}] |


Les routeurs sans ipAllowList explicite ne sont pas déclarés privés par Traefik dans ces fichiers ; une authentification applicative ou un filtrage amont peuvent exister, non qualifiés ici. acme-bootstrap est une route technique vers 127.0.0.1:65535 pour demander gangneux.org et *.gangneux.org ; son backend n’est pas un service métier et n’a pas été sondé. Aucun endpoint authorize/callback OAuth appelé.

Portainer utilise insecureSkipVerify=true côté backend. Le transport NAS spécifie serverName=gan-nas-720-01.gangneux.org et ne déclare pas ce contournement. Minecraft utilise une adresse overlay numérique plutôt qu’un alias DNS.

## Résultats réseau

22 HEAD depuis le Mac en forçant la VIP privée, sans redirection et avec validation TLS normale :

| Domaine | Famille | HTTP | TLS curl | Sortie |
|---|---|---|---|---|
| bookstack.gangneux.org | 4 | 302 | 0 | 0 |
| bookstack.gangneux.org | 6 | 302 | 0 | 0 |
| diun.gangneux.org | 4 | 404 | 0 | 0 |
| diun.gangneux.org | 6 | 404 | 0 | 0 |
| dns.gangneux.org | 4 | 200 | 0 | 0 |
| dns.gangneux.org | 6 | 200 | 0 | 0 |
| gluetun.gangneux.org | 4 | 302 | 0 | 0 |
| gluetun.gangneux.org | 6 | 302 | 0 | 0 |
| home.gangneux.org | 4 | 307 | 0 | 0 |
| home.gangneux.org | 6 | 307 | 0 | 0 |
| homeassistant.gangneux.org | 4 | 405 | 0 | 0 |
| homeassistant.gangneux.org | 6 | 405 | 0 | 0 |
| n8n.gangneux.org | 4 | 200 | 0 | 0 |
| n8n.gangneux.org | 6 | 200 | 0 | 0 |
| nas.gangneux.org | 4 | 200 | 0 | 0 |
| nas.gangneux.org | 6 | 200 | 0 | 0 |
| owui.gangneux.org | 4 | 200 | 0 | 0 |
| owui.gangneux.org | 6 | 200 | 0 | 0 |
| portainer.gangneux.org | 4 | 200 | 0 | 0 |
| portainer.gangneux.org | 6 | 200 | 0 | 0 |
| qbittorrent.gangneux.org | 4 | 200 | 0 | 0 |
| qbittorrent.gangneux.org | 6 | 200 | 0 | 0 |


TLS public observé : TLSv1.3, certificat Let’s Encrypt YR2, SAN gangneux.org et *.gangneux.org, validité du 14 septembre au 13 décembre 2026. Toutes les sondes forcées ont validé le certificat. Aucun contenu ACME ni clé privée lu.

## DNS réellement vu depuis le Mac

| Domaine | Adresses / erreur |
|---|---|
| bookstack.gangneux.org | ["2a01:e0a:8ce:68c5::10", "82.67.206.214"] |
| diun.gangneux.org | {"error": "[Errno 8] nodename nor servname provided, or not known"} |
| dns.gangneux.org | ["192.168.205.10"] |
| gluetun.gangneux.org | {"error": "[Errno 8] nodename nor servname provided, or not known"} |
| home.gangneux.org | ["2a01:e0a:8ce:68c5::10", "82.67.206.214"] |
| homeassistant.gangneux.org | ["2a01:e0a:8ce:68c5::10", "82.67.206.214"] |
| n8n.gangneux.org | ["192.168.205.10", "2a01:e0a:8ce:68c5::10"] |
| nas.gangneux.org | ["2a01:e0a:8ce:68c5::10", "82.67.206.214"] |
| owui.gangneux.org | ["2a01:e0a:8ce:68c5::10", "82.67.206.214"] |
| portainer.gangneux.org | ["82.67.206.214"] |
| qbittorrent.gangneux.org | ["192.168.205.10"] |


DIUN et Gluetun ne se résolvent pas depuis le Mac à cet instant. Pour les six noms résolvant vers 82.67.206.214, le HEAD IPv4 via DNS normal a expiré après environ 8 s :

| Domaine | Code curl | HTTP | Erreur |
|---|---|---|---|
| bookstack.gangneux.org | 28 | 0 | curl: (28) Connection timed out after 8005 milliseconds |
| home.gangneux.org | 28 | 0 | curl: (28) Connection timed out after 8002 milliseconds |
| homeassistant.gangneux.org | 28 | 0 | curl: (28) Connection timed out after 8004 milliseconds |
| nas.gangneux.org | 28 | 0 | curl: (28) Connection timed out after 8005 milliseconds |
| owui.gangneux.org | 28 | 0 | curl: (28) Connection timed out after 8006 milliseconds |
| portainer.gangneux.org | 28 | 0 | curl: (28) Connection timed out after 8006 milliseconds |


Ces échecs concernent le chemin IPv4 public **depuis le Mac**. Ils ne prouvent ni une panne depuis Internet, ni une cause NAT/hairpin précise. Pas de nouvelle tentative équivalente.

## Backends depuis le conteneur Traefik

| URL | Code sonde | HTTP observés | Diagnostic |
|---|---|---|---|
| http://192.168.201.21:8765/ | 0 | ["302", "200"] | [] |
| http://192.168.201.22:8765/ | 1 | [] | ["Connection refused"] |
| http://192.168.201.23:8765/ | 1 | [] | ["Connection refused"] |
| http://192.168.201.33:5380/ | 0 | ["200"] | [] |
| http://192.168.205.40:8080/ | 0 | ["200"] | [] |
| http://[2a01:e0a:8ce:68c1::21]:8765/ | 0 | ["302", "200"] | [] |
| http://[2a01:e0a:8ce:68c1::22]:8765/ | 1 | [] | ["Connection refused"] |
| http://[2a01:e0a:8ce:68c1::23]:8765/ | 1 | [] | ["Connection refused"] |
| http://[2a01:e0a:8ce:68c5::40]:8080/ | 0 | ["200"] | [] |
| http://bookstack:80/ | 0 | ["302", "200"] | [] |
| http://diun:9090/ | 1 | ["404", "404"] | [] |
| http://homeassistant:8123/ | 0 | ["200"] | [] |
| http://homepage:3000/ | 1 | ["400", "400"] | [] |
| http://n8n:5678/ | 0 | ["200"] | [] |
| http://openwebui:8080/ | 0 | ["200"] | [] |
| http://provider-gateway:8081/ | 1 | ["404", "404"] | [] |
| https://192.168.201.21:9443/api/status | 1 | [] | ["Connection reset by peer"] |
| https://192.168.201.22:9443/api/status | 1 | [] | ["Connection reset by peer"] |
| https://192.168.201.23:9443/api/status | 1 | [] | ["Connection reset by peer"] |
| https://192.168.201.61:5001/ | 1 | [] | ["Connection reset by peer"] |
| https://[2a01:e0a:8ce:68c1::21]:9443/api/status | 1 | [] | ["Connection reset by peer"] |
| https://[2a01:e0a:8ce:68c1::22]:9443/api/status | 1 | [] | ["Connection reset by peer"] |
| https://[2a01:e0a:8ce:68c1::23]:9443/api/status | 1 | [] | ["Connection reset by peer"] |
| https://[2a01:e0a:8ce:68c1::61]:5001/ | 1 | [] | ["Connection reset by peer"] |


Les sondes backend utilisent wget --spider, qui peut suivre une redirection ; aucun corps, cookie ou en-tête brut n’est conservé. Les resets HTTPS avec ce client ne prouvent pas une indisponibilité du NAS ou de Portainer, dont les frontends répondent 200. Le Host brut homepage produit 400 alors que home.gangneux.org produit 307. Les backends Gluetun .22/.23 refusés sont compatibles avec le placement actif sur .21. DIUN / produit 404. HomeAssistant / répond 200 côté backend, donc HEAD frontend 405 n’est pas interprété comme panne.

## Fichiers dynamiques complets, filtrés

Les fichiers sont identiques par hash sur les trois nœuds. Les valeurs de credentials et d’en-têtes personnalisés sont retirées ; la section suivante couvre tous les YAML trouvés au premier niveau du répertoire déclaré.

### access-policies.yml

Source : `/srv/docker-shared/traefik/dynamic/access-policies.yml`. SHA-256 : `a0eedeffcce230ee229fd81fce8d4d2cf80a5ff2af92180f58c85f87cc0a856a`.

```json
{
  "http": {
    "middlewares": {
      "private-networks": {
        "ipAllowList": {
          "sourceRange": [
            "192.168.200.0/21",
            "2a01:e0a:8ce:68c0::/61",
            "fd72:6a3c:9e10:100::/64"
          ]
        }
      },
      "CORP": {
        "ipAllowList": {
          "sourceRange": [
            "192.168.200.0/21",
            "2a01:e0a:8ce:68c0::/61",
            "fd72:6a3c:9e10:100::/64",
            "2001:41d0:35c:d600::217/128",
            "51.178.1.217/32",
            "91.216.22.0/24",
            "185.133.83.0/24",
            "2001:67c:11c8::/48",
            "88.218.14.80/28"
          ]
        }
      }
    }
  }
}
```

### acme-bootstrap.yml

Source : `/srv/docker-shared/traefik/dynamic/acme-bootstrap.yml`. SHA-256 : `94b5d27e7474fc63796d43d1b81016e6b2a36ea242500e13866f3bc1fa1f7d13`.

```json
{
  "http": {
    "routers": {
      "acme-bootstrap": {
        "rule": "Host(`acme-bootstrap.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "service": "acme-bootstrap",
        "tls": {
          "certResolver": "le",
          "domains": [
            {
              "main": "gangneux.org",
              "sans": [
                "*.gangneux.org"
              ]
            }
          ]
        }
      }
    },
    "services": {
      "acme-bootstrap": {
        "loadBalancer": {
          "servers": [
            {
              "url": "http://127.0.0.1:65535"
            }
          ]
        }
      }
    }
  }
}
```

### bookstack.yml

Source : `/srv/docker-shared/traefik/dynamic/bookstack.yml`. SHA-256 : `9e870c8432527e7cfd2a9ba033065701acd73bf54e8f9c4011222f4238f942af`.

```json
{
  "http": {
    "routers": {
      "bookstack": {
        "rule": "Host(`bookstack.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "service": "bookstack",
        "tls": {}
      }
    },
    "services": {
      "bookstack": {
        "loadBalancer": {
          "servers": [
            {
              "url": "http://bookstack:80"
            }
          ]
        }
      }
    }
  }
}
```

### diun.yml

Source : `/srv/docker-shared/traefik/dynamic/diun.yml`. SHA-256 : `e257deff8df579b2f0eff4d3c1611f63fc14ddaf9d4351dbf38b28d6c06ad288`.

```json
{
  "http": {
    "routers": {
      "diun": {
        "rule": "Host(`diun.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "middlewares": [
          "private-networks@file"
        ],
        "service": "diun",
        "tls": {}
      }
    },
    "services": {
      "diun": {
        "loadBalancer": {
          "servers": [
            {
              "url": "http://diun:9090"
            }
          ]
        }
      }
    }
  }
}
```

### dns.yml

Source : `/srv/docker-shared/traefik/dynamic/dns.yml`. SHA-256 : `974f5c18457966fea68c095c2e685895a6b0f4ddc7f7de5f0a94c1fa114072b8`.

```json
{
  "http": {
    "routers": {
      "dns": {
        "rule": "Host(`dns.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "middlewares": [
          "private-networks@file"
        ],
        "service": "technitium-dns",
        "tls": {}
      }
    },
    "services": {
      "technitium-dns": {
        "loadBalancer": {
          "passHostHeader": true,
          "healthCheck": {
            "path": "/",
            "interval": "10s",
            "timeout": "3s"
          },
          "servers": [
            {
              "url": "http://192.168.201.33:5380"
            }
          ]
        }
      }
    }
  }
}
```

### gluetun.yml

Source : `/srv/docker-shared/traefik/dynamic/gluetun.yml`. SHA-256 : `aa129163b5e5f197d5282cf1eecd3786b0e92fa4a1b194fb610fb4ccab4da247`.

```json
{
  "http": {
    "routers": {
      "gluetun": {
        "rule": "Host(`gluetun.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "middlewares": [
          "private-networks@file"
        ],
        "service": "gluetun",
        "tls": {}
      }
    },
    "services": {
      "gluetun": {
        "loadBalancer": {
          "passHostHeader": true,
          "healthCheck": {
            "path": "/",
            "interval": "5s",
            "timeout": "2s",
            "followRedirects": false
          },
          "servers": [
            {
              "url": "http://192.168.201.21:8765"
            },
            {
              "url": "http://[2a01:e0a:8ce:68c1::21]:8765"
            },
            {
              "url": "http://192.168.201.22:8765"
            },
            {
              "url": "http://[2a01:e0a:8ce:68c1::22]:8765"
            },
            {
              "url": "http://192.168.201.23:8765"
            },
            {
              "url": "http://[2a01:e0a:8ce:68c1::23]:8765"
            }
          ]
        }
      }
    }
  }
}
```

### homeassistant.yml

Source : `/srv/docker-shared/traefik/dynamic/homeassistant.yml`. SHA-256 : `3d5b60b6c073b29109ef39106c3a71491b5df0d549a35648dafaa4daf0a5b847`.

```json
{
  "http": {
    "routers": {
      "homeassistant": {
        "rule": "Host(`homeassistant.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "middlewares": [
          "private-networks@file"
        ],
        "service": "homeassistant",
        "tls": {}
      }
    },
    "services": {
      "homeassistant": {
        "loadBalancer": {
          "passHostHeader": true,
          "servers": [
            {
              "url": "http://homeassistant:8123"
            }
          ],
          "healthCheck": {
            "path": "/",
            "interval": "10s",
            "timeout": "3s"
          }
        }
      }
    }
  }
}
```

### homepage.yml

Source : `/srv/docker-shared/traefik/dynamic/homepage.yml`. SHA-256 : `ddafcfe95dc54b7f45123f71507ae424d083a7eb599b6cab36a62d4e24e137ec`.

```json
{
  "http": {
    "routers": {
      "homepage": {
        "rule": "Host(`home.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "service": "homepage",
        "tls": {}
      }
    },
    "services": {
      "homepage": {
        "loadBalancer": {
          "servers": [
            {
              "url": "http://homepage:3000"
            }
          ]
        }
      }
    }
  }
}
```

### minecraft.yml

Source : `/srv/docker-shared/traefik/dynamic/minecraft.yml`. SHA-256 : `72be492457805b4530d2d879e3def80a404b10cd0cb68a4f4761b7fb5536f049`.

```json
{
  "tcp": {
    "routers": {
      "minecraft": {
        "entryPoints": [
          "minecraft"
        ],
        "rule": "HostSNI(`*`)",
        "service": "minecraft"
      }
    },
    "services": {
      "minecraft": {
        "loadBalancer": {
          "servers": [
            {
              "address": "172.29.2.11:25565"
            }
          ]
        }
      }
    }
  }
}
```

### n8n.yml

Source : `/srv/docker-shared/traefik/dynamic/n8n.yml`. SHA-256 : `053a208d91ff131b89245ee1ad5b7602f4d1a246da82ce0aff6c1809f3dd13a2`.

```json
{
  "http": {
    "routers": {
      "n8n": {
        "rule": "Host(`n8n.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "service": "n8n",
        "middlewares": [
          "CORP@file"
        ],
        "tls": {}
      }
    },
    "services": {
      "n8n": {
        "loadBalancer": {
          "passHostHeader": true,
          "servers": [
            {
              "url": "http://n8n:5678"
            }
          ]
        }
      }
    }
  }
}
```

### nas.yml

Source : `/srv/docker-shared/traefik/dynamic/nas.yml`. SHA-256 : `c028cb26236e9f7bf71877e72f8e8c165120e26aee8aba3faa5df38153cfbf29`.

```json
{
  "http": {
    "routers": {
      "nas": {
        "rule": "Host(`nas.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "service": "nas",
        "tls": {}
      }
    },
    "services": {
      "nas": {
        "loadBalancer": {
          "passHostHeader": false,
          "serversTransport": "nas-transport",
          "servers": [
            {
              "url": "https://192.168.201.61:5001"
            },
            {
              "url": "https://[2a01:e0a:8ce:68c1::61]:5001"
            }
          ]
        }
      }
    },
    "serversTransports": {
      "nas-transport": {
        "serverName": "gan-nas-720-01.gangneux.org"
      }
    }
  }
}
```

### openwebui.yml

Source : `/srv/docker-shared/traefik/dynamic/openwebui.yml`. SHA-256 : `0a4bef0449043cbd9a92d6a5bf80b377c17c1500639f5478b1b620ec0eb5599d`.

```json
{
  "http": {
    "routers": {
      "openwebui": {
        "rule": "Host(`owui.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "service": "openwebui",
        "tls": {}
      }
    },
    "services": {
      "openwebui": {
        "loadBalancer": {
          "passHostHeader": true,
          "servers": [
            {
              "url": "http://openwebui:8080"
            }
          ]
        }
      }
    }
  }
}
```

### portainer.yml

Source : `/srv/docker-shared/traefik/dynamic/portainer.yml`. SHA-256 : `be7ec68eb0ff8ea776bc8d9abee2f2b3ccfb5bb4161f8f863a64ac482b81b298`.

```json
{
  "http": {
    "serversTransports": {
      "portainer-tls": {
        "insecureSkipVerify": true
      }
    },
    "routers": {
      "portainer": {
        "rule": "Host(`portainer.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "middlewares": [
          "private-networks@file"
        ],
        "service": "portainer",
        "tls": {}
      }
    },
    "services": {
      "portainer": {
        "loadBalancer": {
          "passHostHeader": true,
          "serversTransport": "portainer-tls@file",
          "healthCheck": {
            "path": "/api/status",
            "interval": "10s",
            "timeout": "3s"
          },
          "servers": [
            {
              "url": "https://192.168.201.21:9443"
            },
            {
              "url": "https://[2a01:e0a:8ce:68c1::21]:9443"
            },
            {
              "url": "https://192.168.201.22:9443"
            },
            {
              "url": "https://[2a01:e0a:8ce:68c1::22]:9443"
            },
            {
              "url": "https://192.168.201.23:9443"
            },
            {
              "url": "https://[2a01:e0a:8ce:68c1::23]:9443"
            }
          ]
        }
      }
    }
  }
}
```

### qbittorrent.yml

Source : `/srv/docker-shared/traefik/dynamic/qbittorrent.yml`. SHA-256 : `30f1f2bfaadf1024661494b5dd6cc9ebb04bbe18b43b057e4160ca7d60cf6542`.

```json
{
  "http": {
    "routers": {
      "qbittorrent": {
        "rule": "Host(`qbittorrent.gangneux.org`)",
        "entryPoints": [
          "websecure"
        ],
        "middlewares": [
          "private-networks@file"
        ],
        "service": "qbittorrent",
        "tls": {}
      }
    },
    "services": {
      "qbittorrent": {
        "loadBalancer": {
          "passHostHeader": true,
          "healthCheck": {
            "path": "/",
            "interval": "10s",
            "timeout": "3s"
          },
          "servers": [
            {
              "url": "http://192.168.205.40:8080"
            },
            {
              "url": "http://[2a01:e0a:8ce:68c5::40]:8080"
            }
          ]
        }
      }
    }
  }
}
```

### super-agent-oauth.yml

Source : `/srv/docker-shared/traefik/dynamic/super-agent-oauth.yml`. SHA-256 : `e6426bfa7c83985d56ea70102cfb6f9028f125ebe97576b87c6885a2adde76d3`.

```json
{
  "http": {
    "routers": {
      "super-agent-oauth": {
        "rule": "Host(`auth.gangneux.org`) && (PathPrefix(`/oauth/microsoft/authorize/`) || Path(`/oauth/microsoft/callback`) || PathPrefix(`/oauth/google/authorize/`) || Path(`/oauth/google/callback`))",
        "entryPoints": [
          "websecure"
        ],
        "service": "super-agent-oauth",
        "tls": {}
      }
    },
    "services": {
      "super-agent-oauth": {
        "loadBalancer": {
          "servers": [
            {
              "url": "http://provider-gateway:8081"
            }
          ]
        }
      }
    }
  }
}
```

Voir [HA et synchronisation NAS](sauvegardes-ha.md) et [fiche conteneur](containers/traefik.md).
