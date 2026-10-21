# Microsoft Learn et Proxmox via Docker MCP Gateway

> Décision du 21 octobre 2026 : Proxmox MCP abandonné et intégration retirée. Ce document conserve les observations historiques ; ses propositions de déploiement/reprise Proxmox ne sont plus actives. Microsoft Learn reste en service. Voir [le bilan du retrait](REMOVAL.md).

État au 21 octobre 2026 : **mission partielle**. Microsoft Learn est déployé et testé depuis Codex natif et OpenClaw Pro, avant et après redémarrage ciblé. Les deux MCP Proxmox ne sont pas installés : les neuf endpoints API inventoriés sont inaccessibles depuis docker-02. Aucun token Proxmox créé ni utilisé, aucune ressource Proxmox modifiée, aucun commit/push.

| MCP | Codex | OpenClaw Pro | Perso | Tests réels |
|---|---|---|---|---|
| Microsoft Learn | PASS | PASS | PASS : absent | Recherche, article et PowerShell via Gateway ; recherche et article par Pro ; persistance PASS |
| Proxmox Nantes | NOT_RUN | NOT_RUN | PASS : absent | FAIL : connectivité TCP/8006 depuis docker-02 |
| Proxmox Le Mans | NOT_RUN | NOT_RUN | PASS : absent | FAIL : connectivité TCP/8006 depuis docker-02 |

## Microsoft Learn appliqué

Serveur officiel `https://learn.microsoft.com/api/mcp`, transport `streamable-http`, aucun conteneur Microsoft local. Gateway conservée au digest `sha256:f5a679a05fc39022a046167bef92aeeb01bcd59485ad27843ae5227db7950688` ; CLI `HEAD`, version MCP Gateway 2.0.1. La version du service Microsoft hébergé n'est pas épinglée ni qualifiée ici.

Définition locale documentée `file://official/microsoft-learn.yaml`, importée par `/docker-mcp profile server add` dans les profils natifs codex/pro ; trois outils sélectionnés explicitement par `profile tools --enable`. Aucun ajout au profil Perso. Format remote confirmé par la documentation Docker et les contrats réellement découverts, et non par une URL de registre assimilée à l'endpoint MCP.

Outils réellement retournés :

- `microsoft_docs_search` : `query` chaîne (facultatif dans le schéma distant, exigé non vide par la politique locale).
- `microsoft_docs_fetch` : `url` chaîne obligatoire.
- `microsoft_code_sample_search` : `query` obligatoire, `language` facultatif, exemple `powershell`.

Les trois outils annoncent `readOnlyHint=true`, `destructiveHint=false`, `idempotentHint=true`. Contrats complets et réponses : `artifacts/learn-proxmox-20261021/gateway-functional-before.json` dans mac-ia-local.

Source réellement récupérée : [Install Active Directory Domain Services](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/deploy/install-active-directory-domain-services--level-100-). Recherche Windows Server 2025 AD DS et recherche d'exemples PowerShell exécutées ; article reçu d'environ 31 ko et réponse d'exemples d'environ 26 ko (tailles JSON, pas mesure réseau).

Codex : appels par le binaire `/opt/homebrew/bin/codex`, app-server natif, zéro tour de modèle ; découverte des deux skills via `skills/list(forceReload=true)`. La fenêtre Desktop courante n'a pas été reconnectée : recette GUI NOT_RUN.

OpenClaw Pro : sessions nouvelles, fournisseur reçu oMLX, coût reçu zéro ; lecture réelle du skill, découverte native `tool_search`, appels différés `tool_call` puis outils `docker_gateway_pro__microsoft_docs_search` et `docker_gateway_pro__microsoft_docs_fetch`. Traces natives vérifiées avant/après recréation des deux services Gateway. Aucun événement d'approbation dans ces traces. Après redémarrage, le skill Proxmox est aussi lu et sa limitation correctement rapportée.

## Isolation et sécurité vérifiées

- PASS : export natif Perso strictement identique à la sauvegarde préalable ; service Perso non redémarré, date UpdatedAt conservée au 21 octobre 15:01:38 UTC.
- PASS : Perso ne découvre que `get_current_time` et `convert_time` via sa Gateway ; nouvelle session OpenClaw Perso sans outil Learn Pro trouvé au catalogue. Cela prouve l'absence dans ce catalogue, pas une exécution refusée d'un outil caché.
- PASS : les deux nouveaux skills ont `blockedByAgentFilter=true`, `modelVisible=false`, `commandVisible=false` pour Perso. Ils restent administrativement énumérables, comme les autres skills centraux filtrés ; aucun isolement des fichiers système revendiqué.
- PASS : les douze scénarios anonyme/token invalide/token croisé renvoient 401 (quatre par profil). Les huit cas Codex/Pro ont été revérifiés après le second redémarrage ; quatre cas Perso dans le collecteur borné.
- PASS : aucun port Gateway publié ; pas de serveur Proxmox MCP donc aucun port de ce type exposé.
- PASS : les trois tokens Gateway absents des 150 dernières lignes des conteneurs inspectés. Ce contrôle est borné ; pas d'inventaire de tous les journaux historiques.
- PASS : 35 tests send-approval, dont accès Pro/Perso, enveloppes différées, URL officielle HTTPS, arguments stricts et protections des emails/messages/fichiers/commandes. Les transports sensibles sont simulés/neutralisés par ces tests : aucun envoi réel.
- PASS : `openclaw config validate`, validation des deux skills, rechargement natif send-approval et invalidation des caches MCP.
- PASS : Time réel sur les trois Gateway, Context7 consultation réelle, Serena métadonnées réelles et Orion `get_skill(orion)` réel après redémarrage. Ce dernier contrôle qualifie la disponibilité documentaire Orion, pas tous ses registres métier.
- Doctor : 36 contrôles, avertissements navigateur/node-hosting/security ; aucune réparation hors périmètre. Détails dans les artefacts.

La limite préexistante du socket Docker manager partagé demeure : la séparation des profils ne constitue pas un confinement du moteur Docker. Aucun droit Docker, réseau ou filtre Perso élargi.

## Proxmox observé et blocage

Inventaire actif lu sur `/srv/ansible/inventories/production/10-clients/mixtrio.yml`, contrôleur `ansible-01.mix3cloud.net`, puis commandes de lecture `pvesh get /cluster/status --output-format json` via ses identités d'inventaire. Le module Ansible command affiche CHANGED par défaut ; ces commandes n'écrivent aucun objet Proxmox.

- Nantes : `CLUSTER-PVE-01`, six nœuds en ligne, quorum présent : A01/A02/A03 = 172.30.240.21/.22/.23 ; B01/B02/B03 = 172.30.240.11/.12/.13.
- Le Mans : `CLUSTER-PVE-C1`, trois nœuds en ligne, quorum présent : C01/C02/C03 = 172.30.240.4/.5/.6.

BLOCKER : depuis docker-02, aucune connexion TCP/8006 aux neuf adresses. `.22` et `.23` : `No route to host` errno 113 ; sept autres : `timed out` à cinq secondes. Route observée vers A01 : `via 192.168.201.1 dev ens18 src 192.168.201.22`.

EVIDENCE : `network-observations.json`, relevé des sorties réelles. Les API ne sont pas atteintes depuis le serveur de déploiement ; TLS et authentification ne sont donc pas testés. La lecture par Ansible prouve l'identité des clusters, pas leur accessibilité depuis Docker.

ATTEMPTS : premier lot A01/B01/C01 ; second lot des six autres endpoints inventoriés ; lecture de la route locale. Aucun scan hors inventaire, tunnel, changement de route, pare-feu, VPN ou contournement.

NEXT REQUIRED ACTION : fournir un chemin réseau autorisé depuis docker-02 vers au moins un endpoint API stable de chacun des deux clusters et leurs noms TLS/certificats valides. Qualifier ensuite les droits API effectifs et le stockage des secrets avant installation. Aucun token créé à l'avance pour un service inutilisable.

Version observée par `pveversion` sur A01 et C01 : `pve-manager/9.2.10/43df2e01f27a1a19`, noyau `7.0.14-12-pve`. Cette lecture ne qualifie pas encore un client MCP avec VE 9.

## Qualification des projets Proxmox

Qualification documentaire et lecture ciblée de sources seulement, aucun candidat installé ni exécuté.

| Critère | akmalovaa/proxmox-mcp | 3kirt/proxmox-mcp |
|---|---|---|
| Révision examinée | ff252d4d82d1d740685ceeddfe5bfd3087167f8b | be22ca5b7fbe83afcdca1a9d1c65c0f0e7f884b8 |
| Version source | 2.3.0 | 0.12.0 |
| Maintenance observée | non archivé, poussé le 1 octobre 2026 | non archivé, poussé le 6 octobre 2026 |
| Transport | stdio et Streamable HTTP | stdio |
| Docker | Dockerfile fourni, image projet GHCR documentée | pas de Dockerfile dans l'arbre examiné ; construction spécifique nécessaire |
| Lecture seule | outils au-dessus du niveau read non enregistrés, allowlist intersectée | client GET uniquement dans la source examinée |
| Multi-cluster | un host par processus ; deux configurations distinctes adaptées | carte de clusters et cluster par outil ; préférer deux configurations pour cette mission |
| TLS | verify_ssl=false par défaut : exiger explicitement true | validation paramétrable ; exiger le mode vérifié |
| Secrets/logs | token pris en charge ; expurgation résultats par défaut ; Sentry inerte sans DSN | token pris en charge ; journalisation annoncée sans token |
| VE 9 réelle | NOT_RUN | NOT_RUN |
| CPU/RAM et logs réels | NOT_RUN | NOT_RUN |

Candidat privilégié pour la prochaine qualification : akmalovaa, pour l'image et les transports fournis, le faible état nécessaire et la réduction explicite des outils. Ce choix reste provisoire : digest d'image, dépendances verrouillées, signature/admission Docker, absence effective d'outils mutateurs, secret loader, TLS et droits résultants restent à valider avant déploiement. Son Dockerfile utilise un tag Python de base ; pour une reconstruction reproductible, il faudra aussi épingler les bases par digest. Sentry ne devra pas être activé.

Architecture envisagée, non appliquée : deux configurations `proxmox-nantes` et `proxmox-lemans`, aucune commutation implicite ; stdio via Gateway pour éviter l'exposition HTTP interne non chiffrée refusée par la Gateway installée ; CPU/RAM limités, secret dédié injecté par mécanisme qualifié, utilisateur technique non root, PVEAuditor et token `privsep=1` avec ACL communes de lecture. Ne pas reprendre l'exemple `privsep=0` de 3kirt. Aucun outil Proxmox ajouté à send-approval tant que ses contrats réels ne sont pas qualifiés.

Aucun droit API effectif Proxmox n'est revendiqué ; aucun test d'écriture, destructif ou simulé sur les clusters ; aucune modification de VM, conteneur, stockage, Ceph ou ACL Proxmox.

## Fichiers modifiés et ressources

Distant docker-02 : ajout `catalog/microsoft-learn.yaml`, profils codex/pro par CLI native, script de recette `validate-learn.py`, sauvegardes `backups/learn-proxmox-20261021/`. Aucun changement de stack, Traefik ou profil Perso.

Mac : trois noms Learn ajoutés au filtre `mcp_servers.docker-mcp-gateway.enabled_tools` de `~/.codex/config.toml` ; filtre Pro via `openclaw mcp tools` ; deux skills ajoutés à `agents.entries.main.skills` par CLI ; sources centrales `shared/microsoft-learn/SKILL.md`, `shared/proxmox/SKILL.md`, matrice `config/access.yaml` et README central ; ajout ciblé dans `openclaw/send-approval/lib/mcp-reads.js` et test `test/microsoft-learn.test.mjs`. Aucune configuration Perso, Orion, LiteLLM, oMLX ou Ollama modifiée.

Mesure instantanée `docker stats` : Gateway Codex 23,86 Mio / 0,00 % CPU ; Pro 23,05 Mio / 0,00 % ; Perso 19,68 Mio / 0,00 %. Ces chiffres couvrent la Gateway entière, pas le coût du service Microsoft distant. Proxmox : NOT_RUN, pas de processus déployé.

## Rollback ciblé

Sauvegardes locales privées : `~/.local/state/learn-proxmox-20261021/` ; exports natifs distants : `/srv/docker-local/compose/mcp-gateway/backups/learn-proxmox-20261021/`. Aucune restauration intégrale à appliquer sur les nombreuses modifications concurrentes du dépôt.

1. Dans les conteneurs Gateway Codex/Pro actuels : `/docker-mcp profile server remove <profil> --name microsoft-learn`, puis recréer seulement `mcp-gateway_codex` et `mcp-gateway_pro`.
2. Retirer les seuls trois noms `microsoft_*` ajoutés dans les filtres clients ; utiliser `openclaw mcp tools docker_gateway_pro --include <liste précédente conservant les évolutions ultérieures>` pour Pro.
3. Retirer uniquement le bloc Microsoft Learn de mcp-reads.js et son test, recharger `send-approval`, puis `openclaw mcp reload`. Préserver les autres exceptions.
4. Retirer les deux noms des seuls skills Pro et les entrées correspondantes de matrice ; retirer leurs deux liens Codex et dossiers centraux seulement si aucune évolution ultérieure ne doit être conservée.
5. Vérifier Time, Context7, Serena, Orion, refus croisés et export Perso. Rollback préparé, non exécuté.

## Références et preuves

- [Microsoft Learn référence officielle](https://learn.microsoft.com/en-us/training/support/mcp-developer-reference)
- [Entrée officielle Docker Microsoft Learn](https://github.com/docker/mcp-registry/blob/main/servers/microsoft-learn/server.yaml)
- [Docker profils à la révision de référence](https://github.com/docker/mcp-gateway/blob/a34df45d4ec0e941a9853ad768c4f6cd818966b3/docs/profiles.md)
- [Docker format des entrées](https://github.com/docker/mcp-gateway/blob/a34df45d4ec0e941a9853ad768c4f6cd818966b3/docs/server-entry-spec.md)
- [akmalovaa révision examinée](https://github.com/akmalovaa/proxmox-mcp/tree/ff252d4d82d1d740685ceeddfe5bfd3087167f8b)
- [3kirt révision examinée](https://github.com/3kirt/proxmox-mcp/tree/be22ca5b7fbe83afcdca1a9d1c65c0f0e7f884b8)

Artefacts complets locaux : `mac-ia-local/artifacts/learn-proxmox-20261021/` ; résumés de sécurité et de traces joints à ce rapport. La revue locale déléguée 1c378896-17cb-4e7e-b657-546806d125a5 a été terminée, mais rejetée à la validation : privilèges, critères HTTP et seuils de latence inventés. Aucun de ces critères n'a servi à configurer ou valider le déploiement.
