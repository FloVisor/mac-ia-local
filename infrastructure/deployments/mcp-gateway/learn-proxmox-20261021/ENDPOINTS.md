# Tests des deux endpoints Proxmox depuis docker-02

> Décision du 21 octobre 2026 : Proxmox MCP abandonné et intégration retirée. Ce document conserve les observations historiques ; ses propositions de déploiement/reprise Proxmox ne sont plus actives. Microsoft Learn reste en service. Voir [le bilan du retrait](REMOVAL.md).

Relevés du 21 octobre 2026, vers 21 h 05–21 h 06 Europe/Paris. Aucun déploiement MCP repris : l'endpoint accessible est un hôte Proxmox autonome hors Nantes/Le Mans ; l'endpoint Le Mans reste inaccessible. Microsoft Learn et les autres MCP n'ont pas été modifiés.

| Contrôle | 192.168.201.39:8006 | 172.30.240.4:8006 |
|---|---|---|
| Route hôte | PASS : directe, ens18, source 192.168.201.22 | PASS : via 192.168.201.1, ens18, source 192.168.201.22 |
| TCP depuis hôte | PASS : connexion établie | FAIL : timeout à 5 secondes |
| HTTPS strict hôte /api2/json/version | FAIL TLS : curl 60, CA émettrice non approuvée | FAIL réseau : curl 28, timeout de connexion ; HTTP 000 |
| HTTPS diagnostic temporaire -k | HTTP 401, aucun identifiant envoyé | NOT_RUN : aucun TLS atteint |
| Version reçue par API | NOT_RUN : endpoint protégé, aucune version dans le 401 | NOT_RUN : aucune réponse HTTP |
| Version observée autrement | PASS : VE 9.2.11 via SSH de lecture | VE 9.2.10 relevé via Ansible dans la recette précédente ; pas de nouvelle observation API |
| Identité vérifiée | GAN-PVE-7200-0, hôte autonome ; hors CLUSTER-PVE-01 et CLUSTER-PVE-C1 | PVE-C01 / CLUSTER-PVE-C1 selon lecture réelle Ansible de la mission précédente ; pas de nouvelle identité API |
| TCP depuis conteneur | PASS : nc rc=0 | FAIL : nc rc=1, Host is unreachable |
| HTTPS strict conteneur | FAIL TLS : curl 60, IP absente des SAN | FAIL réseau : curl 28, timeout ; HTTP 000 |
| HTTPS -k conteneur | HTTP 401, aucun identifiant envoyé | NOT_RUN |
| Certificat présenté | Certificat Proxmox du nœud, vérifié hors ligne avec sa CA et son nom DNS | NOT_RUN : handshake non atteint |

L'échec TCP de C01 n'est pas une absence de route locale : `ip route get` retourne une route. Le conteneur rapporte Host is unreachable lors du test TCP, puis le client HTTPS expire ; la cause amont exacte n'est pas démontrée. Aucune connexion refusée n'a été observée.

## Réseau Docker et NAT

Conteneur unique `proxmox-endpoint-diagnostic-20261021`, image locale figée par ID `58adaa4e8dca` (curl 8.22.0, OpenSSL 3.5.8), raccordé au réseau attachable overlay `TRAEFIK_BACKEND`, identique au réseau utilisé par les conteneurs MCP existants. Aucun port publié, cap-drop ALL, no-new-privileges, filesystem read-only, 128 Mio et 0,25 CPU ; aucun volume ni secret monté.

Adresse overlay observée : 172.29.2.167/24 ; subnet du réseau inchangé 172.29.2.0/24. Pour les deux cibles, la route de sortie du conteneur est `via 172.18.0.1 dev eth1 src 172.18.0.12`, via docker_gwbridge.

Une capture limitée à quatre paquets SYN/SYN-ACK pour une connexion TCP sans requête HTTP vers 192.168.201.39 démontre :

- Avant NAT : 172.18.0.12:37037 vers 192.168.201.39:8006 sur docker_gwbridge.
- Après NAT : 192.168.201.22:37037 vers 192.168.201.39:8006 sur ens18.
- Retour SYN-ACK : 192.168.201.39:8006 vers 192.168.201.22:37037.

La règle POSTROUTING existante MASQUERADE pour 172.18.0.0/16 a été lue, sans modification. Le conteneur rejoint l'hôte sur la connectivité observée ; aucun défaut spécifique à l'overlay n'est démontré. Le NAT de la connexion vers C01 n'a pas été capturé : ne pas extrapoler cette preuve de paquet à cet endpoint.

Le conteneur a été supprimé après les tests. Aucun changement de routage, pare-feu ou définition de réseau, aucun redémarrage de service, VM ou nœud.

## Certificat de 192.168.201.39

Certificat public réellement reçu : CN `GAN-PVE-7200-0.gangneux.org`, RSA 2048, émis par la CA Proxmox `0ccacd61-117a-43f2-95d6-784f5b0e971b`. Validité du 7 septembre 2026 au 6 septembre 2028. La chaîne envoyée contient le certificat du nœud ; la CA racine n'est pas envoyée.

SAN IP : 127.0.0.1, ::1, 172.30.236.141. SAN DNS : localhost, GAN-PVE-7200-0, GAN-PVE-7200-0.gangneux.org. **192.168.201.39 n'est pas un SAN.**

Empreinte SHA256 du certificat : `07:FE:87:24:CD:03:6A:97:76:CB:4D:6F:61:28:BA:F6:B6:50:7E:7F:4F:51:6B:66:7B:1C:5C:21:3A:0F:97:CA`.

La CA publique a été obtenue via SSH à clé hôte vérifiée, sans lecture de clé privée. Empreinte SHA256 : `92:CF:A6:A7:F2:ED:27:77:11:29:90:A8:41:F3:44:E8:34:6F:ED:56:6E:4E:9A:C4:E4:6D:AE:A9:3B:A3:DF:64`, validité 7 septembre 2026–4 septembre 2036.

Validation hors ligne avec cette CA :

- PASS : chaîne et nom `GAN-PVE-7200-0.gangneux.org`, openssl verify rc=0.
- FAIL attendu : chaîne et IP 192.168.201.39, erreur 64 IP address mismatch.

Deux causes TLS distinctes sont donc établies : confiance absente du magasin système de l'hôte et inadéquation du nom utilisé. Le diagnostic -k ne corrige aucune des deux. Aucun certificat installé globalement, aucun paramètre permanent verify_ssl=false, aucune nouvelle requête API authentifiée après le 401.

## Qualification et authentification

SSH de lecture sur 192.168.201.39 : `hostname`, `pveversion`, `pvesh get /cluster/status`. Résultat : `GAN-PVE-7200-0`, `pve-manager/9.2.11/f6997e698c7933ea`, noyau 7.0.14-15-pve, un seul nœud local, aucun objet cluster dans le résultat. Le certificat et les données locales concordent avec Proxmox VE. Ce serveur ne doit pas être substitué silencieusement à Nantes ou Le Mans.

Le GET anonyme /api2/json/version répond 401 sur cet endpoint : cela établit qu'une authentification est requise, pas qu'un identifiant a été rejeté. Aucun token, mot de passe ni cookie d'authentification envoyé ; aucune tentative alternative. Les endpoints nécessaires au MCP (inventaire nœuds, statut cluster, ressources et stockage) restent NOT_RUN depuis Docker, car non qualifiés sans identité API autorisée et cible attendue.

Préparation de l'authentification : spécification uniquement, rien créé. Pour une cible validée, prévoir un utilisateur technique non root, un token dédié séparé par cluster, privilèges séparés, rôle PVEAuditor et ACL de lecture limitées ; vérifier l'intersection effective des droits utilisateur/token. Utiliser le mécanisme de secrets qualifié existant, jamais une valeur dans Git ou le rapport. La présente mission interdit les modifications des clusters : aucune création de compte/token/ACL et aucune réutilisation d'identifiants administrateur.

Pour l'hôte GAN, une future qualification TLS utiliserait un nom SAN validé et la CA dédiée, sans désactiver la vérification ; cela ne l'autorise pas à devenir une cible MCP. Sa résolution DNS depuis Docker n'a pas été testée car cet hôte n'est pas l'un des clusters demandés.

## Blocage et prochaine action

BLOCKER : aucun des deux endpoints ne fournit actuellement un accès exploitable aux deux clusters attendus.

EVIDENCE : 192.168.201.39 est joignable mais hors périmètre Nantes/Le Mans, TLS non valide pour son IP et API anonyme 401 ; 172.30.240.4 a une route mais échoue au TCP depuis l'hôte et le conteneur.

ATTEMPTS : routes et TCP hôte ; HTTPS strict, puis -k uniquement pour distinguer le TLS ; mêmes contrôles depuis le conteneur ; identification SSH de lecture du serveur accessible ; validation hors ligne de sa chaîne ; capture TCP bornée pour établir le NAT. Aucun contournement d'authentification ni mutation réseau.

NEXT REQUIRED ACTION : fournir ou rétablir un endpoint autorisé vers Nantes et un vers Le Mans, ou indiquer explicitement si GAN-PVE est une cible supplémentaire souhaitée. Prévoir ensuite des tokens de lecture dédiés déjà provisionnés par un administrateur ou une autorisation distincte de leur création, ainsi que les noms TLS et CA appropriés. Ne pas attendre les neuf nœuds : un endpoint stable par cluster suffira pour reprendre la qualification.

## Preuves

Fichiers complets sous `mac-ia-local/artifacts/proxmox-endpoints-20261021/` : `host-results.json`, `container-results.txt`, `nat-observation.json`, `offline-certificate-verification.json`, `verified-identity.json`, scripts et certificats publics. Les données de sessions TLS ont été retirées du relevé ; seuls les certificats publics et diagnostics utiles sont conservés.

Aucun accès MCP Proxmox ajouté à Codex ou OpenClaw Pro ; Perso inchangé. Aucun changement des autres MCP, aucun commit/push.

Revue préparatoire déléguée locale `e101b41a-8334-4195-b80c-52b6d529d671` terminée mais rejetée : hypothèses Traefik non applicables, champs de réponse version inventés et critères NAT incorrects. Aucun de ces éléments n’a été utilisé ; les observations et validations explicites ci-dessus font foi.
