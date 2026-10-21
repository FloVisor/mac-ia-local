# qbittorrent

Instantané du 21 octobre 2026. Placement actif docker-02, sans déduction de préférence HA. Réseau DMZ, configuration sur docker-shared et trois répertoires médias NAS montés. Frontend et backends IPv4/IPv6 répondent 200. Aucun torrent ajouté, aucune écriture ou vérification VPN de téléchargement.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-02 | qBittorrent | running / sans état health | lscr.io/linuxserver/qbittorrent:5.2.3_v2.0.14-ls475 | 0 |


## docker-02 — qBittorrent

ID : `6b519d426d02eb3466b0247329642da8d2d66c96493f8931bb2a57a94567e7f2`. Image effective : `sha256:8d48fa8c619caadfb103f04efea8747e2a2762d6c7551690919cffb987e61cee`. Création : 2026-09-26T06:33:35.627611072Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/qbittorrent/config | /config | True |
| bind | /srv/media/Films | /volume2/Films | True |
| bind | /srv/media/Series | /volume2/Series | True |
| bind | /srv/media/TEMP | /volume2/TEMP | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| DMZ | 192.168.205.40 | 2a01:e0a:8ce:68c5::40 | ["qBittorrent", "qbittorrent"] |


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

Noms de variables seulement (valeurs exclues) : `PUID`, `PGID`, `TZ`, `WEBUI_PORT`, `TORRENTING_PORT`, `PATH`, `PS1`, `HOME`, `TERM`, `S6_CMD_WAIT_FOR_SERVICES_MAXTIME`, `S6_VERBOSITY`, `S6_STAGE2_HOOK`, `VIRTUAL_ENV`, `LSIO_FIRST_PARTY`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/qbittorrent/compose.yml`. Nœuds : docker-01, docker-02, docker-03. SHA-256 : `3eaebafdf624e5f249689744935be0193e277302e76350d2906d42915a86a5a4`.

```json
{
  "services": {
    "qbittorrent": {
      "image": "lscr.io/linuxserver/qbittorrent:5.2.3_v2.0.14-ls475",
      "container_name": "qBittorrent",
      "volumes": [
        "/srv/docker-shared/qbittorrent/config:/config",
        "/srv/media/Films:/volume2/Films",
        "/srv/media/Series:/volume2/Series",
        "/srv/media/TEMP:/volume2/TEMP"
      ],
      "networks": {
        "DMZ": {
          "ipv4_address": "192.168.205.40",
          "ipv6_address": "2a01:e0a:8ce:68c5::40"
        }
      },
      "environment_keys_only": [
        "PUID",
        "PGID",
        "TZ",
        "WEBUI_PORT",
        "TORRENTING_PORT"
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
