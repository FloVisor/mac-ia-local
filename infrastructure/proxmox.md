# Proxmox — inventaire et configuration

Audit SSH direct root@192.168.201.39 le 21 octobre 2026, en lecture seule, contrôle strict de clé hôte et authentification publickey seule. Hôte **GAN-PVE-7200-0**, pve-manager/9.2.11/f6997e698c7933ea, noyau 7.0.14-15-pve.

Un seul nœud apparaît dans /cluster/status ; aucune ressource HA et aucune réplication Proxmox déclarées. Les trois VM Docker et le stockage partagé reposent sur ce même hyperviseur. Aucun LXC listé.

## Ressources VM

| VMID | Nom | CPU | RAM Mio | Onboot | Disques principaux | VirtioFS |
|---|---|---|---|---|---|---|
| 100 | SOPHOS-GW | 1 × 4 | 8192 | 1 | scsi0: data:vm-100-disk-0,iothread=1,size=40G | — |
| 101 | TEST | 1 × 4 | 8192 | non renseigné | scsi0: data:vm-101-disk-1,iothread=1,size=40G | — |
| 102 | DOCKER-01 | 1 × 4 | 16384 | 1 | scsi0: data:vm-102-disk-0,iothread=1,size=40G; scsi1: data:vm-102-disk-1,iothread=1,size=100G | docker-shared |
| 103 | DOCKER-02 | 1 × 4 | 16384 | 1 | scsi0: data:vm-103-disk-0,iothread=1,size=40G; scsi1: data:vm-103-disk-1,iothread=1,size=100G | docker-shared |
| 104 | DOCKER-03 | 1 × 4 | 16384 | 1 | scsi0: data:vm-104-disk-0,iothread=1,size=40G; scsi1: data:vm-104-disk-1,iothread=1,size=100G | docker-shared |
| 105 | DNS-01 | 1 × 2 | 2048 | non renseigné | scsi0: data:vm-105-disk-0,iothread=1,size=50G | — |


État lors de qm list : toutes running sauf VM 101 TEST, stopped. Les OS et configurations internes de SOPHOS-GW, TEST et DNS-01 ne sont pas audités depuis leurs invités ; seules leurs configurations Proxmox le sont.

## Stockages

| Nom | Type | Cible | Contenu | Partagé déclaré |
|---|---|---|---|---|
| GAN-NAS-720-01 | nfs | /mnt/pve/GAN-NAS-720-01 | backup | 1 |
| data | lvmthin | vg_data | images,rootdir | 0 |
| local | dir | /var/lib/vz | backup,import,iso,vztmpl | 0 |


/srv/docker-shared : ext4 sur /dev/mapper/vg_data-docker--shared, volume logique 200 Gio, filesystem environ 196 Gio, utilisation 3 % lors de df. Thinpool vg_data/data : 3,60 Tio, data_percent=4,90 %, metadata_percent=12,09 %. Ce sont des mesures d’occupation, pas un test d’intégrité.

Mapping VirtioFS :

```json
[
  {
    "digest": "810304f228b10abe22b9b2c8364e4a9d3b354f13",
    "id": "docker-shared",
    "map": [
      "node=GAN-PVE-7200-0,path=/srv/docker-shared"
    ],
    "type": "dir"
  }
]
```

## Réseau de l’hyperviseur

| Interface | Type | Ports / esclaves | MTU | Adresse / VLAN |
|---|---|---|---|---|
| bond0 | bond | nic0 nic1 | 9000 |  |
| vmbr0 | bridge | bond0 | 9000 | VLAN aware 1 |
| vmbr201 | bridge | vmbr0.201 | 1500 | 192.168.201.39/24 |
| nic0 | eth |  |  |  |
| nic1 | eth |  |  |  |


bond0 en 802.3ad, layer3+4 ; vmbr0 trunk VLAN 2–4094 ; vmbr201 management 192.168.201.39/24 et 2a01:e0a:8ce:68c1::39/64. Aucun changement réseau.

## Pare-feu et exploitation

pve-firewall status : disabled/running. Cette couche ne peut pas être présentée comme une protection activée ; les politiques Sophos, switch et pare-feu amont n’ont pas été auditées. Aucun service systemd failed sur l’hôte lors de la collecte. SSH root et mot de passe restent autorisés par sshd -T.

smartctl -H /dev/sda et /dev/sdb : exit 2, stderr vide ; le collecteur initial n’a pas conservé stdout en erreur. Santé physique SMART/RAID **NON_QUALIFIÉE** ; aucune cause ni bonne santé déduite. Pas de nouvel essai équivalent.

## Sauvegardes et snapshots

Voir [sauvegardes et HA](sauvegardes-ha.md). Les VM 102, 103 et 104 disposent d’un snapshot avantinstall (sans mémoire). Un snapshot sur le même stockage ne prouve pas une restauration après perte de l’hôte.

## Configurations VM filtrées

Les secrets, clés et paramètres cloud-init sensibles sont exclus.

### VM 100 — SOPHOS-GW

```json
{
  "boot": "order=scsi0;ide2;net0",
  "cores": "4",
  "cpu": "host",
  "ide2": "none,media=cdrom",
  "machine": "q35",
  "memory": "8192",
  "name": "SOPHOS-GW",
  "net0": "virtio=BC:24:11:A6:72:05,bridge=vmbr201",
  "net1": "virtio=BC:24:11:D0:A6:F3,bridge=vmbr0,tag=200",
  "net2": "virtio=BC:24:11:E1:85:B2,bridge=vmbr0,tag=202",
  "net3": "virtio=BC:24:11:F1:44:F8,bridge=vmbr0,tag=205",
  "net4": "virtio=BC:24:11:C5:6E:D3,bridge=vmbr0,tag=206",
  "net5": "virtio=BC:24:11:38:E5:89,bridge=vmbr0,tag=204",
  "numa": "0",
  "onboot": "1",
  "ostype": "l26",
  "scsi0": "data:vm-100-disk-0,iothread=1,size=40G",
  "scsihw": "virtio-scsi-single",
  "sockets": "1"
}
```

### VM 101 — TEST

```json
{
  "agent": "1,fstrim_cloned_disks=1",
  "bios": "ovmf",
  "boot": "order=scsi0;ide2;ide0;net0",
  "cores": "4",
  "cpu": "host",
  "efidisk0": "data:vm-101-disk-0,efitype=4m,ms-cert=2023k,pre-enrolled-keys=1,size=4M",
  "ide0": "local:iso/virtio-win-0.1.271.iso,media=cdrom,size=709474K",
  "ide2": "none,media=cdrom",
  "machine": "pc-q35-11.0+pve2",
  "memory": "8192",
  "name": "TEST",
  "net0": "virtio=BC:24:11:6D:A2:2B,bridge=vmbr201,mtu=1500",
  "numa": "0",
  "ostype": "win11",
  "scsi0": "data:vm-101-disk-1,iothread=1,size=40G",
  "scsihw": "virtio-scsi-single",
  "sockets": "1"
}
```

### VM 102 — DOCKER-01

```json
{
  "agent": "1",
  "boot": "order=scsi0;ide2;net0",
  "cores": "4",
  "cpu": "host",
  "ide2": "none,media=cdrom",
  "machine": "q35",
  "memory": "16384",
  "name": "DOCKER-01",
  "net0": "virtio=BC:24:11:A1:CE:1A,bridge=vmbr201",
  "net1": "virtio=BC:24:11:39:6F:F7,bridge=vmbr0,tag=1099",
  "net2": "virtio=BC:24:11:0F:CC:55,bridge=vmbr0,tag=205",
  "net3": "virtio=BC:24:11:E9:F6:E7,bridge=vmbr0,tag=204",
  "net4": "virtio=BC:24:11:62:38:01,bridge=vmbr0,tag=200",
  "net5": "virtio=BC:24:11:5A:2F:F4,bridge=vmbr0,tag=202",
  "numa": "0",
  "onboot": "1",
  "ostype": "l26",
  "scsi0": "data:vm-102-disk-0,iothread=1,size=40G",
  "scsi1": "data:vm-102-disk-1,iothread=1,size=100G",
  "scsihw": "virtio-scsi-single",
  "sockets": "1",
  "virtiofs0": "docker-shared"
}
```

### VM 103 — DOCKER-02

```json
{
  "agent": "1",
  "boot": "order=scsi0;ide2;net0",
  "cores": "4",
  "cpu": "host",
  "ide2": "local:iso/debian-13.6.0-amd64-netinst.iso,media=cdrom,size=755M",
  "machine": "q35",
  "memory": "16384",
  "name": "DOCKER-02",
  "net0": "virtio=BC:24:11:2E:F5:82,bridge=vmbr201",
  "net1": "virtio=BC:24:11:68:41:1D,bridge=vmbr0,tag=1099",
  "net2": "virtio=BC:24:11:F9:C0:CE,bridge=vmbr0,tag=205",
  "net3": "virtio=BC:24:11:4E:A0:F9,bridge=vmbr0,tag=204",
  "net4": "virtio=BC:24:11:CA:8B:1F,bridge=vmbr0,tag=200",
  "net5": "virtio=BC:24:11:85:F9:BD,bridge=vmbr0,tag=202",
  "numa": "0",
  "onboot": "1",
  "ostype": "l26",
  "scsi0": "data:vm-103-disk-0,iothread=1,size=40G",
  "scsi1": "data:vm-103-disk-1,iothread=1,size=100G",
  "scsihw": "virtio-scsi-single",
  "sockets": "1",
  "virtiofs0": "docker-shared"
}
```

### VM 104 — DOCKER-03

```json
{
  "agent": "1",
  "boot": "order=scsi0;ide2;net0",
  "cores": "4",
  "cpu": "host",
  "ide2": "local:iso/debian-13.6.0-amd64-netinst.iso,media=cdrom,size=755M",
  "machine": "q35",
  "memory": "16384",
  "name": "DOCKER-03",
  "net0": "virtio=BC:24:11:F0:35:71,bridge=vmbr201",
  "net1": "virtio=BC:24:11:93:C7:40,bridge=vmbr0,tag=1099",
  "net2": "virtio=BC:24:11:88:FF:4F,bridge=vmbr0,tag=205",
  "net3": "virtio=BC:24:11:C8:E6:B6,bridge=vmbr0,tag=204",
  "net4": "virtio=BC:24:11:07:4E:81,bridge=vmbr0,tag=200",
  "net5": "virtio=BC:24:11:B9:AF:B4,bridge=vmbr0,tag=202",
  "numa": "0",
  "onboot": "1",
  "ostype": "l26",
  "scsi0": "data:vm-104-disk-0,iothread=1,size=40G",
  "scsi1": "data:vm-104-disk-1,iothread=1,size=100G",
  "scsihw": "virtio-scsi-single",
  "sockets": "1",
  "virtiofs0": "docker-shared"
}
```

### VM 105 — DNS-01

```json
{
  "agent": "1",
  "boot": "order=scsi0;ide2;net0",
  "cores": "2",
  "cpu": "host",
  "ide2": "none,media=cdrom",
  "machine": "q35",
  "memory": "2048",
  "name": "DNS-01",
  "net0": "virtio=BC:24:11:A1:53:25,bridge=vmbr201",
  "net1": "virtio=BC:24:11:07:5F:08,bridge=vmbr0,mtu=1500,tag=202",
  "numa": "0",
  "ostype": "l26",
  "scsi0": "data:vm-105-disk-0,iothread=1,size=50G",
  "scsihw": "virtio-scsi-single",
  "sockets": "1"
}
```

Sources : [capture Proxmox](evidence/2026-10-21/192.168.201.39.json), [snapshots, exports et archives](evidence/2026-10-21/192.168.201.39.details.json). Interface Web/API authentifiée et consoles invitées non testées.
