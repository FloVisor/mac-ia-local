# Architecture observée : stockage et réseaux

État du 21 octobre 2026, en remplacement des hypothèses du premier relevé.

## Chaîne de stockage

Proxmox vg_data/docker-shared → ext4 /srv/docker-shared → mapping docker-shared → virtiofs0 des VM 102/103/104 → /srv/docker-shared dans les trois invités. Les montages sont rw ; pas de test d’écriture, de cohérence inter-VM ni de reprise.

Portainer : volume portainer_data avec pilote local **adossé à NFS**, device :/srv/docker-shared/portainer, addr=192.168.201.39,nfsvers=4.1,rw,hard,timeo=600,retrans=2. Même définition sur les trois VM, montage actif confirmé sur docker-03. Le chemin du mountpoint local ne suffit pas à classifier la persistance comme locale.

NAS médias : exports /volume2/Films, /volume2/Series et /volume2/TEMP de GAN-NAS-720-01.gangneux.org, montés en nfs4 sous /srv/media sur les trois invités. NAS sauvegardes /volume2/BACKUP monté côté Proxmox. Occupation NAS à la collecte : 72 %. Accès NFS et montages confirmés ; intégrité des données et restauration non testées.

Les bind mounts de chaque conteneur sont décrits dans les [fiches](containers/README.md). La clé WireGuard, les règles iptables et les scripts de routes du routeur sont encore sous docker-local ; la clé n’est pas un symlink. Le Compose WG-Router diffère entre docker-01 et les deux autres.

## Réseaux Docker

### docker-01

| Nom | Driver / scope | Internal | Attachable | Sous-réseaux | Options |
|---|---|---|---|---|---|
| DMZ | macvlan / local | False | False | [{"Subnet": "192.168.205.0/24", "Gateway": "192.168.205.1"}, {"Subnet": "2a01:e0a:8ce:68c5::/64", "Gateway": "2a01:e0a:8ce:68c5::1"}] | {"parent": "ens20"} |
| FAMILLE_SWARM | macvlan / swarm | False | True | [] | None |
| FAMILLE_SWARM_CFG | null / local | False | False | None | {"macvlan_mode": "bridge", "parent": "ens18"} |
| PRO_SWARM | macvlan / swarm | False | True | [] | None |
| PRO_SWARM_CFG | null / local | False | False | None | {"macvlan_mode": "bridge", "parent": "ens23"} |
| TRAEFIK_BACKEND | overlay / swarm | False | True | [{"Subnet": "172.29.2.0/24", "Gateway": "172.29.2.1"}] | {"com.docker.network.driver.overlay.vxlanid_list": "4097"} |
| WAN | macvlan / local | False | False | [{"Subnet": "192.168.200.0/24", "Gateway": "192.168.200.254"}, {"Subnet": "2a01:e0a:8ce:68c0::/64", "Gateway": "2a01:e0a:8ce:68c0::1"}] | {"parent": "ens22"} |
| WG_Internal | bridge / local | False | False | [{"Subnet": "172.31.204.0/24", "Gateway": "172.31.204.1"}] | {} |
| WG_Transit | macvlan / local | False | False | [{"Subnet": "192.168.204.0/24"}, {"Subnet": "2a01:e0a:8ce:68c4::/64"}] | {"parent": "ens21"} |
| bridge | bridge / local | False | False | [{"Subnet": "172.17.0.0/16", "Gateway": "172.17.0.1"}] | {"com.docker.network.bridge.default_bridge": "true", "com.docker.network.bridge.enable_icc": "true", "com.docker.network.bridge.enable_ip_masquerade": "true", "com.docker.network.bridge.host_binding_ipv4": "0.0.0.0", "com.docker.network.bridge.name": "docker0", "com.docker.network.driver.mtu": "1500"} |
| docker_gwbridge | bridge / local | False | False | [{"Subnet": "172.18.0.0/16", "Gateway": "172.18.0.1"}] | {"com.docker.network.bridge.enable_icc": "false", "com.docker.network.bridge.enable_ip_masquerade": "true", "com.docker.network.bridge.name": "docker_gwbridge"} |
| homeassistant_default | bridge / local | False | False | [{"Subnet": "172.19.0.0/16", "Gateway": "172.19.0.1"}] | {} |
| host | host / local | False | False | None | {} |
| ingress | overlay / swarm | False | False | [{"Subnet": "172.29.0.0/24", "Gateway": "172.29.0.1"}] | {"com.docker.network.driver.mtu": "1550", "com.docker.network.driver.overlay.vxlanid_list": "4100"} |
| none | null / local | False | False | None | {} |
| portainer_agent_network | overlay / swarm | False | True | [{"Subnet": "172.29.1.0/24", "Gateway": "172.29.1.1"}] | {"com.docker.network.driver.mtu": "1550", "com.docker.network.driver.overlay.vxlanid_list": "4101"} |
| super-agent_SUPER_AGENT_EGRESS | bridge / local | False | False | [{"Subnet": "172.20.0.0/16", "Gateway": "172.20.0.1"}] | {} |
| super-agent_SUPER_AGENT_PROVIDER | bridge / local | True | False | [{"Subnet": "172.22.0.0/16", "Gateway": "172.22.0.1"}] | {} |
| super-agent_SUPER_AGENT_STATE | bridge / local | True | False | [{"Subnet": "172.21.0.0/16", "Gateway": "172.21.0.1"}] | {} |


### docker-02

| Nom | Driver / scope | Internal | Attachable | Sous-réseaux | Options |
|---|---|---|---|---|---|
| DMZ | macvlan / local | False | False | [{"Subnet": "192.168.205.0/24", "Gateway": "192.168.205.1"}, {"Subnet": "2a01:e0a:8ce:68c5::/64", "Gateway": "2a01:e0a:8ce:68c5::1"}] | {"parent": "ens20"} |
| FAMILLE_SWARM | macvlan / swarm | False | True | [{"Subnet": "192.168.201.0/24", "IPRange": "192.168.201.80/28", "Gateway": "192.168.201.1", "AuxiliaryAddresses": {"r90": "192.168.201.90", "r91": "192.168.201.91", "r92": "192.168.201.92", "r93": "192.168.201.93", "r94": "192.168.201.94", "r95": "192.168.201.95"}}, {"Subnet": "2a01:e0a:8ce:68c1::/64", "IPRange": "2a01:e0a:8ce:68c1::80/124", "Gateway": "2a01:e0a:8ce:68c1::1", "AuxiliaryAddresses": {"r8a": "2a01:e0a:8ce:68c1::8a", "r8b": "2a01:e0a:8ce:68c1::8b", "r8c": "2a01:e0a:8ce:68c1::8c", "r8d": "2a01:e0a:8ce:68c1::8d", "r8e": "2a01:e0a:8ce:68c1::8e", "r8f": "2a01:e0a:8ce:68c1::8f"}}] | {"macvlan_mode": "bridge", "parent": "ens18"} |
| FAMILLE_SWARM_CFG | null / local | False | False | None | {"macvlan_mode": "bridge", "parent": "ens18"} |
| PRO_SWARM | macvlan / swarm | False | True | [{"Subnet": "192.168.202.0/24", "IPRange": "192.168.202.80/28", "Gateway": "192.168.202.1", "AuxiliaryAddresses": {"r90": "192.168.202.90", "r91": "192.168.202.91", "r92": "192.168.202.92", "r93": "192.168.202.93", "r94": "192.168.202.94", "r95": "192.168.202.95"}}, {"Subnet": "2a01:e0a:8ce:68c2::/64", "IPRange": "2a01:e0a:8ce:68c2::80/124", "Gateway": "2a01:e0a:8ce:68c2::1", "AuxiliaryAddresses": {"r8a": "2a01:e0a:8ce:68c2::8a", "r8b": "2a01:e0a:8ce:68c2::8b", "r8c": "2a01:e0a:8ce:68c2::8c", "r8d": "2a01:e0a:8ce:68c2::8d", "r8e": "2a01:e0a:8ce:68c2::8e", "r8f": "2a01:e0a:8ce:68c2::8f"}}] | {"macvlan_mode": "bridge", "parent": "ens23"} |
| PRO_SWARM_CFG | null / local | False | False | None | {"macvlan_mode": "bridge", "parent": "ens23"} |
| TRAEFIK_BACKEND | overlay / swarm | False | True | [{"Subnet": "172.29.2.0/24", "Gateway": "172.29.2.1"}] | {"com.docker.network.driver.overlay.vxlanid_list": "4097"} |
| WAN | macvlan / local | False | False | [{"Subnet": "192.168.200.0/24", "Gateway": "192.168.200.254"}, {"Subnet": "2a01:e0a:8ce:68c0::/64", "Gateway": "2a01:e0a:8ce:68c0::1"}] | {"parent": "ens22"} |
| WG_Internal | bridge / local | False | False | [{"Subnet": "172.31.204.0/24", "Gateway": "172.31.204.1"}] | {} |
| WG_Transit | macvlan / local | False | False | [{"Subnet": "192.168.204.0/24"}, {"Subnet": "2a01:e0a:8ce:68c4::/64"}] | {"parent": "ens21"} |
| bookstack_bookstack_private | bridge / local | True | False | [{"Subnet": "172.19.0.0/16", "Gateway": "172.19.0.1"}] | {} |
| bridge | bridge / local | False | False | [{"Subnet": "172.17.0.0/16", "Gateway": "172.17.0.1"}] | {"com.docker.network.bridge.default_bridge": "true", "com.docker.network.bridge.enable_icc": "true", "com.docker.network.bridge.enable_ip_masquerade": "true", "com.docker.network.bridge.host_binding_ipv4": "0.0.0.0", "com.docker.network.bridge.name": "docker0", "com.docker.network.driver.mtu": "1500"} |
| docker_gwbridge | bridge / local | False | False | [{"Subnet": "172.18.0.0/16", "Gateway": "172.18.0.1"}] | {"com.docker.network.bridge.enable_icc": "false", "com.docker.network.bridge.enable_ip_masquerade": "true", "com.docker.network.bridge.name": "docker_gwbridge"} |
| host | host / local | False | False | None | {} |
| ingress | overlay / swarm | False | False | [{"Subnet": "172.29.0.0/24", "Gateway": "172.29.0.1"}] | {"com.docker.network.driver.mtu": "1550", "com.docker.network.driver.overlay.vxlanid_list": "4100"} |
| none | null / local | False | False | None | {} |
| portainer_agent_network | overlay / swarm | False | True | [{"Subnet": "172.29.1.0/24", "Gateway": "172.29.1.1"}] | {"com.docker.network.driver.mtu": "1550", "com.docker.network.driver.overlay.vxlanid_list": "4101"} |


### docker-03

| Nom | Driver / scope | Internal | Attachable | Sous-réseaux | Options |
|---|---|---|---|---|---|
| DMZ | macvlan / local | False | False | [{"Subnet": "192.168.205.0/24", "Gateway": "192.168.205.1"}, {"Subnet": "2a01:e0a:8ce:68c5::/64", "Gateway": "2a01:e0a:8ce:68c5::1"}] | {"parent": "ens20"} |
| FAMILLE_SWARM | macvlan / swarm | False | True | [] | None |
| FAMILLE_SWARM_CFG | null / local | False | False | None | {"macvlan_mode": "bridge", "parent": "ens18"} |
| PRO_SWARM | macvlan / swarm | False | True | [] | None |
| PRO_SWARM_CFG | null / local | False | False | None | {"macvlan_mode": "bridge", "parent": "ens23"} |
| TRAEFIK_BACKEND | overlay / swarm | False | True | [{"Subnet": "172.29.2.0/24", "Gateway": "172.29.2.1"}] | {"com.docker.network.driver.overlay.vxlanid_list": "4097"} |
| WAN | macvlan / local | False | False | [{"Subnet": "192.168.200.0/24", "Gateway": "192.168.200.254"}, {"Subnet": "2a01:e0a:8ce:68c0::/64", "Gateway": "2a01:e0a:8ce:68c0::1"}] | {"parent": "ens22"} |
| WG_Internal | bridge / local | False | False | [{"Subnet": "172.31.204.0/24", "Gateway": "172.31.204.1"}] | {} |
| WG_Transit | macvlan / local | False | False | [{"Subnet": "192.168.204.0/24"}, {"Subnet": "2a01:e0a:8ce:68c4::/64"}] | {"parent": "ens21"} |
| bridge | bridge / local | False | False | [{"Subnet": "172.17.0.0/16", "Gateway": "172.17.0.1"}] | {"com.docker.network.bridge.default_bridge": "true", "com.docker.network.bridge.enable_icc": "true", "com.docker.network.bridge.enable_ip_masquerade": "true", "com.docker.network.bridge.host_binding_ipv4": "0.0.0.0", "com.docker.network.bridge.name": "docker0", "com.docker.network.driver.mtu": "1500"} |
| docker_gwbridge | bridge / local | False | False | [{"Subnet": "172.18.0.0/16", "Gateway": "172.18.0.1"}] | {"com.docker.network.bridge.enable_icc": "false", "com.docker.network.bridge.enable_ip_masquerade": "true", "com.docker.network.bridge.name": "docker_gwbridge"} |
| host | host / local | False | False | None | {} |
| ingress | overlay / swarm | False | False | [{"Subnet": "172.29.0.0/24", "Gateway": "172.29.0.1"}] | {"com.docker.network.driver.mtu": "1550", "com.docker.network.driver.overlay.vxlanid_list": "4100"} |
| none | null / local | False | False | None | {} |
| portainer_agent_network | overlay / swarm | False | True | [{"Subnet": "172.29.1.0/24", "Gateway": "172.29.1.1"}] | {"com.docker.network.driver.mtu": "1550", "com.docker.network.driver.overlay.vxlanid_list": "4101"} |


TRAEFIK_BACKEND est un overlay attachable non internal, 172.29.2.0/24. Peers déclarés par Docker : 192.168.201.21/22/23 ; aucun datapath sur les adresses 10.168.201.x ne peut être revendiqué à partir de ces observations. Pas de capture réseau. Les options collectées ne déclarent pas encrypted pour les overlays ; cela ne constitue pas une mesure cryptographique du trafic.

WG_Internal est un bridge propre à chaque nœud, pas un réseau inter-nœuds. DMZ, WAN et WG_Transit sont des MACVLAN locaux. FAMILLE_SWARM et PRO_SWARM sont des MACVLAN de scope swarm avec réseaux de configuration. Les réseaux privés BookStack et super-agent répondent à des séparations spécifiques ; aucune suppression automatique recommandée.

## Politique de déploiement issue de l’ancien audit

Proposition de référence à conserver pour les prochains changements : données nécessaires à la reprise sous docker-shared ; Compose et scripts reproductibles sous docker-local ; étudier TRAEFIK_BACKEND et les alias DNS en premier ; justifier tout port hôte, bridge, MACVLAN, VLAN ou IP supplémentaire. Ces recommandations n’autorisent aucune migration. Les mécanismes HA réels sont décrits dans [sauvegardes-ha.md](sauvegardes-ha.md).
