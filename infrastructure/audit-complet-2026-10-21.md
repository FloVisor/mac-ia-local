# Audit complet de configuration — 21 octobre 2026

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
