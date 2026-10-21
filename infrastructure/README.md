# Plateforme Proxmox et Docker Swarm

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

## Déploiements après audit

- [FreeLLMAPI — 21 octobre 2026](deployments/freellmapi/README.md) : service Swarm privé sur docker-02, vue DNS interne dédiée restant à créer.
- [LiteLLM — 21 octobre 2026](deployments/litellm/README.md) : API publique limitée à trois routes ; administration privée/VPN, exception native non HttpOnly acceptée ; inférence en attente de backend autorisé.

- [Serena — 21 octobre 2026](deployments/serena/REPORT.md) : clones autorisés persistants sur docker-02, analyse sémantique en lecture seule via les profils Codex et Pro ; Perso exclu.
