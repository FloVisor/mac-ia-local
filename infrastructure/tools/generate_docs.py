"""Render the dated sanitized inventory as navigable Markdown; no remote operations."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
E=ROOT/'evidence'/'2026-10-21'
HOSTS=['docker-01','docker-02','docker-03']
D={h:json.loads((E/(h+'.json')).read_text()) for h in HOSTS}
DETAIL={h:json.loads((E/(h+'.details.json')).read_text()) for h in HOSTS}
P=json.loads((E/'192.168.201.39.json').read_text())
PD=json.loads((E/'192.168.201.39.details.json').read_text())
FRONT=json.loads((E/'frontends.json').read_text())
BACK=json.loads((E/'backends.json').read_text())
DNS=json.loads((E/'dns-mac.json').read_text())
PUBLIC=json.loads((E/'public-ipv4-frontends.json').read_text())


def cell(v):
    if isinstance(v,(dict,list)):v=json.dumps(v,ensure_ascii=False)
    return str(v).replace('|','&#124;').replace('\n','<br>')


def table(headers, rows):
    return '\n'+'| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(cell(v) for v in row)+' |\n' for row in rows)+'\n'


def block(obj):return '\n```json\n'+json.dumps(obj,ensure_ascii=False,indent=2)+'\n```\n'
def write(path,text):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("\n".join(line.rstrip() for line in text.splitlines())+"\n")
def group(c):
    labels=c['config']['labels']
    return labels.get('com.docker.compose.project') or labels.get('com.docker.swarm.service.name') or c['Name'].strip('/')
def slug(s):return re.sub(r'[^a-z0-9-]+','-',s.lower()).strip('-')


groups=defaultdict(list)
for h in HOSTS:
    for c in D[h]['docker']['containers']:groups[group(c)].append((h,c))

notes={
'wg-router': 'WG-Router et son sidecar de routes tournent sur docker-01. NET_ADMIN et /dev/net/tun sont présents. Le sidecar partage le namespace réseau du routeur ; sa liste Networks vide ne signifie pas absence de réseau. La clé WireGuard est un fichier local réel (0600, root), pas un lien vers docker-shared. Le Compose de docker-01 déclare le sidecar wg-router-routes ; ceux de docker-02/03 ne le déclarent pas : dérive de reconstruction à traiter séparément. Le contenu de la clé et les règles VPN ne sont pas exportés ; trafic VPN réel non qualifié.',
'wg-admin': 'WG-Companion tourne sur docker-01 ; son port 8765 est publié sur les adresses LAN propres au nœud (.21 et ::21), pas sur la VIP .30 dans les bindings Docker. Le socket proxy monte docker.sock en lecture seule ; cela ne prouve pas que son API Docker est inoffensive. Les backends .22/.23 refusent la connexion à cet instant, compatible avec un seul compagnon actif. Configuration de droits de proxy et authentification applicative non qualifiées.',
'wg-relay': 'Un relais par nœud sur le bridge local WG_Internal. La présence de trois conteneurs ne rend pas le bridge inter-nœuds. Les arguments de redirection ne sont pas exportés par le filtre général de commande ; leur exécution de bout en bout n’a pas été testée.',
'traefik': 'Voir aussi ../traefik.md pour tous les fichiers dynamiques, les paramètres statiques, ACL, transports TLS et sondes. Service actif sur docker-02, restart=no dans le Compose ; les notifications Keepalived pilotent son cycle de vie. Aucun test de bascule effectué.',
'homeassistant': 'Conteneur privilégié, avec /run/dbus et /etc/localtime montés ; configuration sur docker-shared. Connecté à TRAEFIK_BACKEND et homeassistant_default, à justifier selon les besoins réels. Frontend HEAD / : 405 ; backend depuis Traefik : 200. Pas de panne déduite du refus de méthode HEAD. Aucune session authentifiée ou automation exécutée.',
'ollama-proxy': 'Ollama-Proxy est running/unhealthy. Nginx écoute 11434 et vise http://ollama-tailscale:11434 ; DNS interne 127.0.0.11, IPv6 off pour ce resolver. Healthcheck sur /api/version toutes les 30 s, timeout 5 s, retries 3 ; cinq derniers ExitCode=-1. proxy_connect_timeout=10 s et lecture/envoi 3600 s. La cause initiale et l’accès au modèle distant ne sont pas établis ; aucun appel de génération réalisé.',
'openwebui': 'OpenWebUI, MCPO et Tailscale-Ollama sont présents. OpenWebUI et MCPO healthy ; Tailscale a NET_ADMIN et NET_RAW. Configurations et données persistantes sont sous docker-shared. Frontend owui : 200 via VIP privée IPv4 et IPv6. Échec du chemin IPv4 public depuis le Mac. Aucun test OAuth, MCP métier ou modèle avec identifiants utilisateur.',
'super-agent': 'Cinq composants : application, provider-gateway, entra-sync, PostgreSQL et Redis, tous healthy à la collecte. Limites CPU/RAM explicites ; réseaux privés distincts pour état, fournisseur et sortie. Les routes OAuth sont inventoriées mais leurs endpoints de connexion et callback ne sont pas appelés. Le backend racine du provider-gateway répond 404 : cela ne teste pas les routes OAuth. Sauvegarde applicative déclarée ; voir ../sauvegardes-ha.md.',
'n8n': 'Persistance /srv/docker-shared/n8n/data, réseau TRAEFIK_BACKEND. Frontend protégé par CORP@file ; HTTP 200 depuis le Mac sur les deux familles. Aucun workflow lancé et aucun credential consulté.',
'bookstack': 'BookStack et MariaDB sur docker-02 ; application sur TRAEFIK_BACKEND et réseau privé bookstack_bookstack_private, base sur réseau privé. Données et secrets sous docker-shared. Métadonnées vérifiées : app_key/db_password/db_root_password en 0444, mais répertoires bookstack et secrets en 0700 root ; ne pas conclure à une lecture possible par tous les utilisateurs du nœud à partir des seuls droits des fichiers. Contenus jamais lus. HTTP 302 frontend et 200 après redirection backend. Sauvegarde BookStack déclarée et dernier résultat systemd success, sans restauration testée.',
'qbittorrent': 'Placement actif docker-02, sans déduction de préférence HA. Réseau DMZ, configuration sur docker-shared et trois répertoires médias NAS montés. Frontend et backends IPv4/IPv6 répondent 200. Aucun torrent ajouté, aucune écriture ou vérification VPN de téléchargement.',
'ratiomaster': 'Placement actif docker-02, image locale local/ratiomaster:1.1.0, réseau DMZ, configuration et torrents sur docker-shared. Aucun routeur Web RatioMaster trouvé dans les fichiers Traefik collectés. Fonction métier non testée ; reproductibilité de l’image locale non qualifiée.',
'minecraft': 'Conteneur Java sur docker-02, données sous docker-shared. Publication TCP via entrypoint minecraft de Traefik, backend 172.29.2.11:25565 codé en dur. Une IP overlay fixe en configuration crée une dépendance à vérifier lors des recréations. Aucun client de jeu connecté ; protocole de jeu non qualifié.',
'homepage': 'Homepage healthy sur docker-03. Frontend HTTP 307 ; backend interrogé avec son nom Docker brut répond 400. Le Host utilisé diffère du frontend : ce résultat ne démontre pas une indisponibilité du service publié. Image versionnée ; config partagée.',
'diun': 'DIUN healthy sur docker-03, image latest et socket Docker monté RW. / sur le frontend et le backend répond 404 ; le conteneur peut fournir des métriques ou une autre route, non assimilées à une WebUI fonctionnelle. Nom diun.gangneux.org non résolu depuis le Mac au moment de l’audit. Notifications et mises à jour d’image non déclenchées.',
'portainer_portainer': 'Serveur Swarm, une réplique, contrainte node.role == manager. Volume portainer_data : driver local, mais Options type=nfs vers 192.168.201.39:/srv/docker-shared/portainer. Le montage NFS est confirmé sur docker-03 ; le constat initial de stockage local seul est corrigé. Port 9443 publié par ingress ; frontend 200. Traefik désactive la validation du certificat backend.',
'portainer_agent': 'Service global, trois tâches actives. Monte docker.sock RW et le répertoire des volumes Docker ; accès administratif attendu pour ce composant, à réserver au périmètre de confiance. Trois anciennes tâches arrêtées restent sur docker-01, sans suppression. Données de socket et identifiants Portainer non lus.',
'avahi_reflector': 'Service Swarm une réplique sur docker-02, réseaux MACVLAN FAMILLE_SWARM et PRO_SWARM. Une ancienne tâche arrêtée sur docker-01 conserve un état unhealthy historique. La tâche active est healthy. Réflexion mDNS réelle et absence de fuite inter-réseaux non testées.'}

coverage=[]
for name,items in sorted(groups.items()):
    text=f'# {name}\n\nInstantané du 21 octobre 2026. '+notes.get(name,'')+'\n'
    text+='\n## Conteneurs observés\n'
    text+=table(['Nœud','Nom exact','État / santé','Image déclarée','Redémarrages'],[(h,c['Name'].strip('/'),c['state']['Status']+' / '+c['health'].get('Status','sans état health'),c['config']['Image'],c['RestartCount']) for h,c in items])
    for h,c in items:
        coverage.append({'host':h,'id':c['Id'],'name':c['Name'],'state':c['state']['Status'],'document':'containers/'+slug(name)+'.md'})
        text+=f'\n## {h} — {c["Name"].strip("/")}\n\nID : `{c["Id"]}`. Image effective : `{c["Image"]}`. Création : {c["Created"]}.\n'
        text+='\n### Stockage réel\n'
        text+=table(['Type','Source','Destination','Écriture'],[(m['Type'],m['Source'],m['Destination'],m.get('RW')) for m in c['Mounts']]) if c['Mounts'] else '\nAucun montage déclaré ; la couche writable reste locale. Cela ne prouve pas que l’application n’y écrit aucune donnée importante.\n'
        text+='\n### Réseaux et exposition\n'
        text+=table(['Réseau','IPv4','IPv6','Alias'],[(n,x.get('IPAddress'),x.get('GlobalIPv6Address'),x.get('Aliases')) for n,x in c['network'].get('Networks',{}).items()])
        text+='\nBindings Docker et ports exposés (null = non publié par ce binding, pas preuve d’inaccessibilité sur MACVLAN/overlay) :\n'+block(c['network'].get('Ports',{}))
        text+='\n### Exécution et isolation\n'+block(c['host_config'])
        text+='\nUtilisateur : '+('`'+str(c['config'].get('User'))+'`' if c['config'].get('User') else 'non précisé par Docker, souvent root ; UID effectif dans le processus non vérifié')+'. Healthcheck : '+str(c['config']['healthcheck_present'])+'.\n'
        text+='\nNoms de variables seulement (valeurs exclues) : '+', '.join('`'+k+'`' for k in c['config']['environment_keys_only'])+'.\n'
        text+=f'\nSource : [capture {h}](../evidence/2026-10-21/{h}.json). Aucun log applicatif ni contenu de base exporté.\n'
    cfgs=defaultdict(list)
    for h in HOSTS:
        for cfg in D[h]['docker']['compose']:
            if Path(cfg['path']).parent.name==name:
                cfgs[cfg.get('sha256','NOHASH')].append((h,cfg))
    if cfgs:
        text+='\n## Déclarations Compose filtrées\n\nLes secrets, valeurs d’environnement, commandes, entrypoints et corps des healthchecks sont omis. Ces extraits documentaires ne sont pas des fichiers prêts à redéployer.\n'
        for sha,entries in cfgs.items():
            text+='\nChemin : `'+entries[0][1]['path']+'`. Nœuds : '+', '.join(h for h,_ in entries)+'. SHA-256 : `'+sha+'`.\n'
            text+=block(entries[0][1].get('configuration',entries[0][1]))
    for service in D['docker-01']['docker'].get('services',[]):
        if service['name']==name:text+='\n## Déclaration Swarm filtrée\n'+block(service)
    write('containers/'+slug(name)+'.md',text)

text='# Inventaire de tous les conteneurs\n\nCollecte directe depuis le Mac le 21 octobre 2026 : **35 objets, 31 running et 4 exited**, répartis sur les trois nœuds. Les tâches Swarm anciennes sont conservées.\n'
text+=table(['Domaine','Objets','Actifs','Fiche'],[(name,len(items),sum(c['state']['Running'] for _,c in items),'[Fiche](%s.md)'%slug(name)) for name,items in sorted(groups.items())])
text+='\nLe comptage est celui de docker ps -a à l’instant de collecte. Un état running ou healthy ne constitue pas un test métier. Les captures incluent les digests locaux et les RepoDigests des images ; une image locale sans digest de registre n’est pas qualifiée reproductible.\n'
write('containers/README.md',text)

text='# Docker Swarm et systèmes invités\n\nInstantané du 21 octobre 2026, accès SSH directs depuis le Mac.\n'
text+=table(['Nœud','Version Docker','Conteneurs actifs / total','Manager','État networking.service'],[(h,D[h]['docker']['info']['ServerVersion'],f"{sum(c['state']['Running'] for c in D[h]['docker']['containers'])}/{len(D[h]['docker']['containers'])}",'Leader' if h=='docker-03' else 'Reachable',DETAIL[h]['networking_status'].replace('\n',' ; ')) for h in HOSTS])
text+='\nTrois managers Ready/Active, Debian 13, racine Docker /srv/docker-local/docker. AutoLockManagers=false. Aucun test de perte de quorum ou rotation de certificat.\n\nVoir [tous les conteneurs](containers/README.md) pour images, états, ressources, montages et configurations par application.\n'
text+='\n## Services Swarm\n'+table(['Service','Mode','Placement','Image'],[(s['name'],s['mode'],s['task'].get('Placement',{}),s['task']['container'].get('Image')) for s in D['docker-01']['docker']['services']])
text+='\nRéplicas constatés : avahi 1/1, agent Portainer global 3/3, serveur Portainer 1/1. Les conteneurs Compose autonomes ne sont pas gérés par l’ordonnanceur Swarm.\n'
text+='\n## Système et surface d’accès\n\nnetworking.service est failed, Result=exit-code, ExecMainStatus=1 sur docker-01 et docker-03 ; docker-02 est active/exited avec résultat success. Cela n’annule pas les interfaces actives, mais la configuration au prochain cycle réseau reste à diagnostiquer. Aucun restart effectué.\n\nSur les trois VM, sshd -T indique permitrootlogin=yes et passwordauthentication=yes, en plus de pubkeyauthentication=yes. L’authentification par clé est validée, mais l’authentification par mot de passe n’est pas désactivée. Règles nft, listeners, interfaces, routes et timers sont dans les captures filtrées ; aucune preuve d’isolement depuis un réseau externe non autorisé.\n'
for h in HOSTS:
    text+=f'\n## {h}\n\nCapture : [système, Docker et réseaux](evidence/2026-10-21/{h}.json), [unités, scripts et permissions](evidence/2026-10-21/{h}.details.json).\n'
    text+='\nTimers observés :\n```text\n'+D[h]['host']['timers']+'\n```\n'
write('swarm.md',text)

px=P['proxmox']
text='# Proxmox — inventaire et configuration\n\nAudit SSH direct root@192.168.201.39 le 21 octobre 2026, en lecture seule, contrôle strict de clé hôte et authentification publickey seule. Hôte **GAN-PVE-7200-0**, pve-manager/9.2.11/f6997e698c7933ea, noyau 7.0.14-15-pve.\n'
text+='\nUn seul nœud apparaît dans /cluster/status ; aucune ressource HA et aucune réplication Proxmox déclarées. Les trois VM Docker et le stockage partagé reposent sur ce même hyperviseur. Aucun LXC listé.\n'
text+='\n## Ressources VM\n'+table(['VMID','Nom','CPU','RAM Mio','Onboot','Disques principaux','VirtioFS'],[(vm,c.get('name'),f"{c.get('sockets','1')} × {c.get('cores')}",c.get('memory'),c.get('onboot','non renseigné'),'; '.join(f'{k}: {v}' for k,v in c.items() if re.fullmatch(r'scsi\d+',k)),c.get('virtiofs0','—')) for vm,c in sorted(px['vm_config'].items())])
text+='\nÉtat lors de qm list : toutes running sauf VM 101 TEST, stopped. Les OS et configurations internes de SOPHOS-GW, TEST et DNS-01 ne sont pas audités depuis leurs invités ; seules leurs configurations Proxmox le sont.\n'
text+='\n## Stockages\n'+table(['Nom','Type','Cible','Contenu','Partagé déclaré'],[(s['storage'],s['type'],s.get('path') or s.get('vgname'),s.get('content'),s.get('shared',0)) for s in px['storage_config']])
text+='\n/srv/docker-shared : ext4 sur /dev/mapper/vg_data-docker--shared, volume logique 200 Gio, filesystem environ 196 Gio, utilisation 3 % lors de df. Thinpool vg_data/data : 3,60 Tio, data_percent=4,90 %, metadata_percent=12,09 %. Ce sont des mesures d’occupation, pas un test d’intégrité.\n\nMapping VirtioFS :\n'+block(px['directory_mapping'])
text+='\n## Réseau de l’hyperviseur\n'+table(['Interface','Type','Ports / esclaves','MTU','Adresse / VLAN'],[(x['iface'],x['type'],x.get('bridge_ports') or x.get('slaves',''),x.get('mtu',''),x.get('cidr') or ('VLAN aware '+str(x.get('bridge_vlan_aware')) if x['type']=='bridge' else '')) for x in px['network']])
text+='\nbond0 en 802.3ad, layer3+4 ; vmbr0 trunk VLAN 2–4094 ; vmbr201 management 192.168.201.39/24 et 2a01:e0a:8ce:68c1::39/64. Aucun changement réseau.\n\n## Pare-feu et exploitation\n\npve-firewall status : disabled/running. Cette couche ne peut pas être présentée comme une protection activée ; les politiques Sophos, switch et pare-feu amont n’ont pas été auditées. Aucun service systemd failed sur l’hôte lors de la collecte. SSH root et mot de passe restent autorisés par sshd -T.\n\nsmartctl -H /dev/sda et /dev/sdb : exit 2, stderr vide ; le collecteur initial n’a pas conservé stdout en erreur. Santé physique SMART/RAID **NON_QUALIFIÉE** ; aucune cause ni bonne santé déduite. Pas de nouvel essai équivalent.\n'
text+='\n## Sauvegardes et snapshots\n\nVoir [sauvegardes et HA](sauvegardes-ha.md). Les VM 102, 103 et 104 disposent d’un snapshot avantinstall (sans mémoire). Un snapshot sur le même stockage ne prouve pas une restauration après perte de l’hôte.\n'
text+='\n## Configurations VM filtrées\n\nLes secrets, clés et paramètres cloud-init sensibles sont exclus.\n'
for vm,c in sorted(px['vm_config'].items()):text+=f'\n### VM {vm} — {c.get("name")}\n'+block(c)
text+='\nSources : [capture Proxmox](evidence/2026-10-21/192.168.201.39.json), [snapshots, exports et archives](evidence/2026-10-21/192.168.201.39.details.json). Interface Web/API authentifiée et consoles invitées non testées.\n'
write('proxmox.md',text)

text='# Traefik — configuration et contrôles\n\nAudit du 21 octobre 2026. Conteneur Traefik v3.7.13 sur docker-02. Compose identique par SHA-256 sur les trois nœuds. Configuration dynamique sous /srv/docker-shared/traefik/dynamic, ACME sous /srv/docker-shared/traefik/acme/acme.json ; secrets OVH référencés par fichiers, jamais lus ou exportés.\n\n## Configuration statique active\n'+block(DETAIL['docker-02']['traefik_static_arguments'])
text+='\nLe provider actif déclaré est file avec watch=true. Entrypoints : web :80, websecure :443, minecraft :25565/tcp, health :8082 avec ping. Aucun argument de redirection globale HTTP→HTTPS ou provider Docker n’est présent dans cette liste ; règles réseau et listeners seuls ne constituent pas une preuve d’accès externe.\n\n## Routage et politiques\n'
rows=[]
for cfg in D['docker-02']['docker']['traefik']:
    for proto in ['http','tcp','udp']:
        spec=cfg['configuration'].get(proto,{})
        for name,r in spec.get('routers',{}).items():
            serv=spec.get('services',{}).get(r.get('service'),{})
            rows.append([proto,name,r.get('rule'),r.get('entryPoints'),r.get('middlewares',[]),r.get('service'),serv.get('loadBalancer',{}).get('servers',[])])
text+=table(['Protocole','Routeur','Règle','Entrypoints','Middlewares','Service','Backends'],rows)
text+='\nLes routeurs sans ipAllowList explicite ne sont pas déclarés privés par Traefik dans ces fichiers ; une authentification applicative ou un filtrage amont peuvent exister, non qualifiés ici. acme-bootstrap est une route technique vers 127.0.0.1:65535 pour demander gangneux.org et *.gangneux.org ; son backend n’est pas un service métier et n’a pas été sondé. Aucun endpoint authorize/callback OAuth appelé.\n\nPortainer utilise insecureSkipVerify=true côté backend. Le transport NAS spécifie serverName=gan-nas-720-01.gangneux.org et ne déclare pas ce contournement. Minecraft utilise une adresse overlay numérique plutôt qu’un alias DNS.\n'
text+='\n## Résultats réseau\n\n22 HEAD depuis le Mac en forçant la VIP privée, sans redirection et avec validation TLS normale :\n'
text+=table(['Domaine','Famille','HTTP','TLS curl','Sortie'],[(x['domain'],x['family'],x['http_code'],x['ssl_verify_result'],x['exit']) for x in FRONT['probes']])
text+='\nTLS public observé : TLSv1.3, certificat Let’s Encrypt YR2, SAN gangneux.org et *.gangneux.org, validité du 14 septembre au 13 décembre 2026. Toutes les sondes forcées ont validé le certificat. Aucun contenu ACME ni clé privée lu.\n\n## DNS réellement vu depuis le Mac\n'+table(['Domaine','Adresses / erreur'],sorted(DNS.items()))
text+='\nDIUN et Gluetun ne se résolvent pas depuis le Mac à cet instant. Pour les six noms résolvant vers 82.67.206.214, le HEAD IPv4 via DNS normal a expiré après environ 8 s :\n'+table(['Domaine','Code curl','HTTP','Erreur'],[(x['domain'],x['exit'],x['http_code'],x['error']) for x in PUBLIC['probes']])
text+='\nCes échecs concernent le chemin IPv4 public **depuis le Mac**. Ils ne prouvent ni une panne depuis Internet, ni une cause NAT/hairpin précise. Pas de nouvelle tentative équivalente.\n\n## Backends depuis le conteneur Traefik\n'+table(['URL','Code sonde','HTTP observés','Diagnostic'],[(x['url'],x['exit'],x['http_codes'],x['diagnostic']) for x in BACK['probes']])
text+='\nLes sondes backend utilisent wget --spider, qui peut suivre une redirection ; aucun corps, cookie ou en-tête brut n’est conservé. Les resets HTTPS avec ce client ne prouvent pas une indisponibilité du NAS ou de Portainer, dont les frontends répondent 200. Le Host brut homepage produit 400 alors que home.gangneux.org produit 307. Les backends Gluetun .22/.23 refusés sont compatibles avec le placement actif sur .21. DIUN / produit 404. HomeAssistant / répond 200 côté backend, donc HEAD frontend 405 n’est pas interprété comme panne.\n'
text+='\n## Fichiers dynamiques complets, filtrés\n\nLes fichiers sont identiques par hash sur les trois nœuds. Les valeurs de credentials et d’en-têtes personnalisés sont retirées ; la section suivante couvre tous les YAML trouvés au premier niveau du répertoire déclaré.\n'
for cfg in D['docker-02']['docker']['traefik']:
    text+='\n### '+Path(cfg['path']).name+'\n\nSource : `'+cfg['path']+'`. SHA-256 : `'+cfg['sha256']+'`.\n'+block(cfg['configuration'])
text+='\nVoir [HA et synchronisation NAS](sauvegardes-ha.md) et [fiche conteneur](containers/traefik.md).\n'
write('traefik.md',text)

text='# Architecture observée : stockage et réseaux\n\nÉtat du 21 octobre 2026, en remplacement des hypothèses du premier relevé.\n\n## Chaîne de stockage\n\nProxmox vg_data/docker-shared → ext4 /srv/docker-shared → mapping docker-shared → virtiofs0 des VM 102/103/104 → /srv/docker-shared dans les trois invités. Les montages sont rw ; pas de test d’écriture, de cohérence inter-VM ni de reprise.\n\nPortainer : volume portainer_data avec pilote local **adossé à NFS**, device :/srv/docker-shared/portainer, addr=192.168.201.39,nfsvers=4.1,rw,hard,timeo=600,retrans=2. Même définition sur les trois VM, montage actif confirmé sur docker-03. Le chemin du mountpoint local ne suffit pas à classifier la persistance comme locale.\n\nNAS médias : exports /volume2/Films, /volume2/Series et /volume2/TEMP de GAN-NAS-720-01.gangneux.org, montés en nfs4 sous /srv/media sur les trois invités. NAS sauvegardes /volume2/BACKUP monté côté Proxmox. Occupation NAS à la collecte : 72 %. Accès NFS et montages confirmés ; intégrité des données et restauration non testées.\n\nLes bind mounts de chaque conteneur sont décrits dans les [fiches](containers/README.md). La clé WireGuard, les règles iptables et les scripts de routes du routeur sont encore sous docker-local ; la clé n’est pas un symlink. Le Compose WG-Router diffère entre docker-01 et les deux autres.\n\n## Réseaux Docker\n'
for h in HOSTS:
    text+=f'\n### {h}\n'+table(['Nom','Driver / scope','Internal','Attachable','Sous-réseaux','Options'],[(n['Name'],n['Driver']+' / '+n['Scope'],n.get('Internal'),n.get('Attachable'),n.get('IPAM',{}).get('Config'),n.get('Options')) for n in D[h]['docker']['networks']])
text+='\nTRAEFIK_BACKEND est un overlay attachable non internal, 172.29.2.0/24. Peers déclarés par Docker : 192.168.201.21/22/23 ; aucun datapath sur les adresses 10.168.201.x ne peut être revendiqué à partir de ces observations. Pas de capture réseau. Les options collectées ne déclarent pas encrypted pour les overlays ; cela ne constitue pas une mesure cryptographique du trafic.\n\nWG_Internal est un bridge propre à chaque nœud, pas un réseau inter-nœuds. DMZ, WAN et WG_Transit sont des MACVLAN locaux. FAMILLE_SWARM et PRO_SWARM sont des MACVLAN de scope swarm avec réseaux de configuration. Les réseaux privés BookStack et super-agent répondent à des séparations spécifiques ; aucune suppression automatique recommandée.\n\n## Politique de déploiement issue de l’ancien audit\n\nProposition de référence à conserver pour les prochains changements : données nécessaires à la reprise sous docker-shared ; Compose et scripts reproductibles sous docker-local ; étudier TRAEFIK_BACKEND et les alias DNS en premier ; justifier tout port hôte, bridge, MACVLAN, VLAN ou IP supplémentaire. Ces recommandations n’autorisent aucune migration. Les mécanismes HA réels sont décrits dans [sauvegardes-ha.md](sauvegardes-ha.md).\n'
write('architecture.md',text)

text='# Sauvegardes, HA et reconstruction\n\nAudit de configuration du 21 octobre 2026. Aucun déclenchement de sauvegarde, bascule ou restauration.\n\n## Proxmox\n\nTâche quotidienne 10:00, snapshot/zstd, NAS GAN-NAS-720-01, VM 100/102/103/104/105, repeat-missed=1, rétention keep-last=10. La VM 101 TEST n’est pas incluse dans cette tâche. Les tâches vzdump récentes exposées par l’API ont status=OK ; cela ne prouve pas une restauration.\n'+block(px['backup_jobs'])
text+='\nArchives récentes présentes (métadonnées uniquement, aucun parcours du contenu) :\n'+table(['Archive','Taille octets'],[(Path(x['path']).name,x.get('bytes')) for x in PD['backup_archive_metadata'][:10]])
text+='\nLa présence de sauvegardes des disques VM ne démontre pas une sauvegarde indépendante de /srv/docker-shared exposé via VirtioFS. Aucune preuve d’une copie complète de ce volume hors hyperviseur ni de restauration applicative n’est produite. Les snapshots avantinstall des VM Docker sont sur le même stockage.\n\n## Sauvegardes applicatives et synchronisation de certificats\n'
for h in HOSTS:
    op=json.loads((E/(h+'.operations.json')).read_text())
    text+=f'\n### {h}\n'+block({'unit_last_results':op['unit_last_results'],'backup_scripts':op['backup_scripts']})
text+='\nBookStack : timer quotidien 03:30, script mariadb-dump/tar. Super-agent : timer observé, script référençant pg_dump, redis-cli et tar, chemins sous /srv/docker-shared/super-agent/backups et backup-keys. Les derniers résultats systemd sont success ; ni archives applicatives, ni chiffrement effectif, ni restauration n’ont été vérifiés. Une sauvegarde sous docker-shared ne constitue pas à elle seule une protection contre perte de l’hôte.\n\nLe timer traefik-syno-cert-sync existe sur les trois VM et son dernier résultat est success. Son script référence encore /srv/docker-local/compose/traefik/acme/acme.json, chemin local existant distinct du montage ACME actif /srv/docker-shared/traefik/acme/acme.json. Contenus non lus : identité et fraîcheur de ces états ACME non établies. Aucun secret ou certificat privé copié.\n\n## Keepalived\n'+table(['Instance','VRID','Priorités 01/02/03','VIP déclarée'],[['VI_WG_ROUTER',204,'150 / 140 / 130','192.168.201.30 ; 2a01:e0a:8ce:68c1::30 (excluded IPv6)'],['VI_QBITTORRENT',205,'130 / 140 / 150','no_virtual_ipaddress'],['VI_RATIOMASTER',206,'130 / 150 / 140','no_virtual_ipaddress'],['VI_TRAEFIK',210,'150 / 140 / 130','no_virtual_ipaddress']])
text+='\nTrois services Keepalived actifs, unicast sur ens18, état configuré BACKUP, nopreempt. L’état BACKUP dans le fichier n’est pas le rôle runtime élu. La VIP WG est observée sur docker-01. Traefik/qBittorrent/RatioMaster sont actifs sur docker-02 ; les priorités ne décrivent pas le placement instantané. Les scripts notify master/backup/fault/stop sont référencés, ainsi que les contrôles prérequis et les interfaces suivies.\n\nScripts HA : check-docker.sh, check-*-prereq.sh et *-ha.sh sous /usr/local/sbin. Ils référencent docker, timeout, findmnt/curl selon les services ; les scripts HA utilisent des verrous /run/lock/*-ha.lock locaux. Aucun fencing distribué ni résistance au split-brain n’est démontré. Le résumé statique des scripts ne remplace pas une revue complète de leur logique. Les fichiers Compose WG-Router divergent : sidecar de routes présent seulement sur docker-01.\n'
text+='\n## Configurations Keepalived sans bloc d’authentification\n'
for h in HOSTS:text+=f'\n### {h}\n\n```text\n'+DETAIL[h]['keepalived_without_authentication']+'\n```\n'
text+='\n## Limites de qualification\n\nNOT_RUN : redémarrage réseau, perte d’un manager, bascule de chaque application, perte du stockage/NAS, panne d’hyperviseur, double maître, fencing, reprise sur nœud reconstruit, restauration de sauvegarde, test de génération IA, exécution n8n, OAuth, trafic VPN et session Minecraft. Aucun de ces effets n’est déduit de healthy, success, de trois managers ou de la présence d’un montage partagé.\n'
write('sauvegardes-ha.md',text)

report='''# Audit complet de configuration — 21 octobre 2026

## Résultat et périmètre

Audit en lecture seule depuis le Mac : **1 hyperviseur Proxmox, 6 configurations VM, 3 nœuds Docker, 35 objets conteneur (31 running, 4 exited), 18 fiches applicatives/services, 29 fichiers Compose et 15 fichiers dynamiques Traefik uniques**. Tous les objets retournés par docker ps -a sont reliés à une fiche. Aucun LXC listé. Aucun déploiement, nettoyage, redémarrage ou changement réseau.

Il s’agit d’un audit de configuration et d’exploitation avec sondes réseau limitées. Il ne certifie ni la sécurité complète, ni les parcours métier authentifiés, ni la reprise après sinistre. Les systèmes internes des VM SOPHOS-GW, DNS-01 et TEST, le NAS et le pare-feu physique sont hors collecte interne ; leurs dépendances observées sont documentées.

## Constats à traiter

| ID | Priorité proposée | Constat vérifié | Conséquence / suite distincte |
|---|---|---|---|
| A01 | Haute | Un seul hyperviseur et stockage partagé sur cet hôte ; pas de preuve de copie complète externe de docker-shared | Reprise après perte physique non démontrée ; qualifier la couverture et restaurer en environnement isolé |
| A02 | Haute | Clé WireGuard réelle sous docker-local ; Compose routeur différent, sidecar seulement sur docker-01 | Reconstruction/bascule non équivalente ; inventorier les dépendances locales avant correction |
| A03 | Haute | networking.service failed sur docker-01 et docker-03, exit 1 | Diagnostiquer avant tout futur redémarrage réseau ; aucun restart ici |
| A04 | Haute | Ollama-Proxy running/unhealthy, 7227 échecs consécutifs au premier instantané | Diagnostic de chaîne Nginx/Tailscale/Ollama requis ; aucune cause initiale inventée |
| A05 | Moyenne | Deux noms DNS non résolus depuis le Mac : DIUN et Gluetun | La route forcée n’est pas un accès normal par nom ; vérifier la zone/résolution |
| A06 | Moyenne | Six chemins IPv4 publics vers 82.67.206.214:443 expirent depuis le Mac | Chemin public/hairpin depuis cette source non fonctionnel pendant la sonde ; cause amont non établie |
| A07 | Moyenne | Portainer backend TLS insecureSkipVerify=true | Identité TLS backend non vérifiée par ce transport ; frontend TLS valide séparément |
| A08 | Moyenne | HomeAssistant privileged ; sockets Docker sur Portainer, DIUN et proxy WG | Privilèges à mettre en relation avec les besoins ; pas d’exploitation ou de durcissement appliqué |
| A09 | Moyenne | Sync certificat NAS référence l’ancien état ACME local, fichier encore présent | Résultat systemd success ne prouve pas la fraîcheur de l’état ACME utilisé ; comparer les métadonnées publiques avant changement |
| A10 | À qualifier | Verrous HA locaux, aucun essai de fencing/bascule ; HA Proxmox non déclarée | Aucune garantie de single writer ou de HA physique démontrée |
| A11 | À qualifier | DIUN / retourne 404 ; Minecraft cible une IP overlay numérique ; plusieurs images latest/main/local | Vérifier routes attendues et reproductibilité ; aucune panne métier ni vulnérabilité déduite du seul tag |
| A12 | À qualifier | root SSH et passwordauthentication restent autorisés ; pve-firewall disabled/running | État réel documenté ; protection amont et politique d’accès à confirmer séparément |

Priorités proposées pour revue, sans autorisation de correction implicite. Les références exactes et les configurations filtrées sont accessibles dans les documents par domaine.

## Corrections des premières hypothèses

Le volume Portainer est adossé à NFS malgré le pilote local et son chemin de mountpoint : le premier constat « volume local seul » est invalidé. Les trois VM Docker sur le même Proxmox, le backing ext4 et le mapping VirtioFS sont maintenant vérifiés directement. Les accès de référence sont tous directs depuis le Mac ; aucun rebond nécessaire.

## Preuves et limites des sondes

- 22 HEAD via VIP privée : connexions IPv4 et IPv6 établies, validation TLS normale réussie. Les codes applicatifs restent distincts du succès TLS.
- Six HEAD IPv4 via DNS public normal : timeout curl 28, sans réponse HTTP.
- 24 sondes backend depuis le conteneur Traefik. HTTPS avec wget : resets, limite de client non résolue ; ne pas conclure à une panne de Portainer/NAS dont les frontends répondent 200.
- HomeAssistant : HEAD frontend 405 et backend 200. Homepage : frontend 307, backend au Host Docker 400. DIUN : 404 sur la racine testée. OAuth authorize/callback et backend synthétique ACME exclus.
- Sauvegardes : job quotidien, tâches vzdump récentes OK, archives présentes ; aucune restauration ou lecture des archives. SMART : deux commandes exit 2, stderr vide, stdout d’erreur non conservé ; aucune santé disque déduite.
- Tous les écarts et sondes échouées sont conservés ; aucun retry équivalent ou contournement TLS/authentification.

## Navigation

[Accès](acces.md) · [Proxmox](proxmox.md) · [Swarm](swarm.md) · [Tous les conteneurs](containers/README.md) · [Traefik](traefik.md) · [Architecture](architecture.md) · [Sauvegardes et HA](sauvegardes-ha.md) · [Preuves et SHA-256](evidence/2026-10-21/README.md).

Les configurations exportées sont filtrées : aucune valeur d’environnement Docker, .env, clé privée, contenu ACME, base applicative ou log applicatif. Les chemins, noms de variables et métadonnées de fichiers restent présents pour l’exploitation. Les extraits ne sont pas des manifests prêts à déployer. Un profil review du MCP local a été utilisé pour une revue de périmètre ; ses recommandations ont été confrontées aux observations, pas reprises comme faits.
'''
write('audit-complet-2026-10-21.md',report)

coverage_vm=[{'vmid':vm,'document':'proxmox.md','name':c.get('name')} for vm,c in px['vm_config'].items()]
(E/'coverage.json').write_text(json.dumps({'containers':coverage,'vm_configurations':coverage_vm},indent=2,ensure_ascii=False)+'\n')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(E.glob('*.json')) if p.name!='sha256.json'}
(E/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
write('evidence/2026-10-21/README.md','# Preuves filtrées — 21 octobre 2026\n\nCaptures SSH directes depuis le Mac, horodatées en UTC dans les fichiers ; date de campagne Europe/Paris. Les fichiers *.json sont filtrés sur le serveur avant transfert ; les sources YAML ne sont pas des copies brutes. Les preuves de sondes ne conservent pas les corps, cookies ou en-têtes bruts.\n'+table(['Fichier','SHA-256'],[(f'[{name}]({name})',sha) for name,sha in manifest.items()])+'''\n## Collecte et reproduction

Sources : [collect_remote.py](../../tools/collect_remote.py), [collect_details.py](../../tools/collect_details.py), [run_audit.py](../../tools/run_audit.py). Python 3 et PyYAML sur le Mac ; le parseur YAML existant est fourni en mémoire aux nœuds dépourvus du module, sans installation distante ni fichier temporaire distant. Commandes distantes bornées et métadonnées JSON filtrées. Les erreurs sont explicites.

Pour une nouvelle campagne, choisir un nouveau répertoire ; ne pas remplacer ces preuves :

```bash
python3 infrastructure/tools/run_audit.py --output infrastructure/evidence/NOUVELLE-CAMPAGNE
python3 infrastructure/tools/run_audit.py --details --output infrastructure/evidence/NOUVELLE-CAMPAGNE
```

Le collecteur refuse d’écraser un fichier de preuve existant. Les scripts de sondes et de génération sont spécifiques au relevé du 21 octobre ; adapter la destination et revoir les cibles avant une nouvelle campagne. Une exécution a posteriori n’est pas nécessaire pour consulter les résultats présents.

Les fichiers *.operations.json et dns-mac.json proviennent de lectures ciblées complémentaires : résultats systemd, résumé statique des scripts de sauvegarde, métadonnées de l’ancien chemin ACME, directives non sensibles Nginx, définition du healthcheck Ollama-Proxy et résolution getaddrinfo du Mac. public-ipv4-frontends.json contient les HEAD -4 via DNS normal vers l’IPv4 publique. Aucun contenu secret ni de base n’a été lu lors de ces compléments.

Les résultats systemd success ne constituent pas une preuve de sauvegarde/restauration. Les listes de scripts sont des résumés statiques et des hashes, pas une certification de leur logique. Le filtre de redaction a été durci après la collecte initiale pour les options password=... ; les captures présentes ont été contrôlées séparément et n’ont pas été remplacées.
''')
write('README.md','''# Plateforme Proxmox et Docker Swarm

Audit de configuration et d’exploitation du **21 octobre 2026**, en lecture seule depuis le Mac. Un Proxmox, six configurations VM, trois nœuds Docker, tous les 35 objets conteneur (31 actifs), 18 fiches de services/applications. Aucun changement distant.

| Besoin | Document à charger |
|---|---|
| Résultats, anomalies et limites | [Audit complet](audit-complet-2026-10-21.md) |
| SSH directs depuis le Mac | [Accès](acces.md) |
| Hyperviseur, VM, interfaces, disques | [Proxmox](proxmox.md) |
| Managers, services et systèmes invités | [Swarm](swarm.md) |
| Un conteneur ou une application | [Index des fiches](containers/README.md) |
| Routes, ACL, TLS et backends | [Traefik](traefik.md) |
| Persistance, overlays, MACVLAN et NAS | [Architecture](architecture.md) |
| Sauvegardes, Keepalived et reconstruction | [Sauvegardes et HA](sauvegardes-ha.md) |
| Captures filtrées, couverture et empreintes | [Preuves](evidence/2026-10-21/README.md) |

Les secrets sont exclus. Les extraits ne sont pas prêts à redéployer. Les limites et tests NOT_RUN restent explicites : aucune qualification de bascule, restauration ou parcours métier authentifié. Le premier [relevé partiel](audit-2026-10-21.md) est conservé comme historique, corrigé par cet audit complet.
''')
print(f'Generated {len(groups)} application/service sheets, {len(coverage)} container entries and {len(coverage_vm)} VM entries.')
