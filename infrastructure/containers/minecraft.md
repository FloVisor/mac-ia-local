# minecraft

Instantané du 21 octobre 2026. Conteneur Java sur docker-02, données sous docker-shared. Publication TCP via entrypoint minecraft de Traefik, backend 172.29.2.11:25565 codé en dur. Une IP overlay fixe en configuration crée une dépendance à vérifier lors des recréations. Aucun client de jeu connecté ; protocole de jeu non qualifié.

## Conteneurs observés

| Nœud | Nom exact | État / santé | Image déclarée | Redémarrages |
|---|---|---|---|---|
| docker-02 | Minecraft | running / sans état health | eclipse-temurin:25-jre | 0 |


## docker-02 — Minecraft

ID : `e90e7f5f66bb6319ea226fa89db141405424ff73f16747181cca58f9665f6d94`. Image effective : `sha256:611e326900ba9edcedfb246ede24efc66a911fa496ac623db9f33cae88a2d83b`. Création : 2026-09-16T18:32:24.795079382Z.

### Stockage réel

| Type | Source | Destination | Écriture |
|---|---|---|---|
| bind | /srv/docker-shared/minecraft/data | /minecraft | True |


### Réseaux et exposition

| Réseau | IPv4 | IPv6 | Alias |
|---|---|---|---|
| TRAEFIK_BACKEND | 172.29.2.11 |  | ["Minecraft", "minecraft", "minecraft"] |


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
  "SecurityOpt": [
    "no-new-privileges:true"
  ],
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

Utilisateur : `1000:1000`. Healthcheck : False.

Noms de variables seulement (valeurs exclues) : `PATH`, `JAVA_HOME`, `LANG`, `LANGUAGE`, `LC_ALL`, `JAVA_VERSION`.

Source : [capture docker-02](../evidence/2026-10-21/docker-02.json). Aucun log applicatif ni contenu de base exporté.

## Déclarations Compose filtrées

Les secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.

Chemin : `/srv/docker-local/compose/minecraft/compose.yml`. Nœuds : docker-02. SHA-256 : `bbf81b65cc1733448b27bf9b338976a766fc4ba40bccfb78dc87d9a8d5eb0930`.

```json
{
  "services": {
    "minecraft": {
      "image": "eclipse-temurin:25-jre",
      "container_name": "Minecraft",
      "restart": "unless-stopped",
      "volumes": [
        "/srv/docker-shared/minecraft/data:/minecraft"
      ],
      "networks": {
        "TRAEFIK_BACKEND": {
          "ipv4_address": "172.29.2.11",
          "aliases": [
            "minecraft"
          ]
        }
      },
      "security_opt": [
        "no-new-privileges:true"
      ],
      "user": "1000:1000",
      "environment_keys_only": [],
      "healthcheck_present": false,
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
