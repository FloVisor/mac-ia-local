# Retrait de Proxmox MCP — 21 octobre 2026

Proxmox MCP est abandonné. Microsoft Learn et les MCP préexistants sont conservés.

## Éléments retirés

- Skill exclusivement créé pour le MCP : `/Users/fngux2/AI/skills/shared/proxmox/`, et lien Codex `~/.agents/skills/proxmox`.
- Activation `proxmox` dans `agents.entries.main.skills` d’OpenClaw Pro, entrée `shared.proxmox` de la matrice centrale et ligne associée du README.
- Sources candidates téléchargées `akmalovaa/` et `3kirt/`, scripts réseau dédiés et deux certificats publics de diagnostic. Le manifeste détaillé est dans `artifacts/proxmox-removal-20261021/removed-elements.json`.
- Assertion de l’ancien harnais Codex adaptée pour vérifier désormais l’absence du skill Proxmox.

Aucune déclaration Gateway, outil, image, conteneur, service, variable de connexion, identifiant, secret ni exception send-approval Proxmox n’avait été déployé. Aucun composant partagé n’a donc été supprimé. Les profils distants observés sont codex/pro : Time, Context7, Serena, Microsoft Learn ; perso : Time uniquement.

## Préservation

Les preuves historiques JSON, traces et rapports sont conservés. REPORT.md et ENDPOINTS.md portent une décision d’abandon explicite : leurs anciennes propositions de reprise sont obsolètes. Ces mentions historiques ne sont pas une configuration active.

Le README central précise la stratégie conservée : Ansible pour l’administration réelle ; Context7 pour la documentation Proxmox/Ceph avec vérification de version ; Serena pour les scripts et playbooks. Aucun MCP Ansible créé. Aucun skill préexistant d’administration, Ceph, PBS ou Ansible retiré.

La configuration OpenClaw complète correspond exactement à l’état initial dont seule l’entrée main.skills/proxmox a été retirée. Perso, MCP, fournisseurs et authentification sont préservés. La configuration Codex, le skill Microsoft Learn, les règles send-approval et les instructions Codex/Pro/Perso ont les mêmes SHA256. Détails : `artifacts/proxmox-removal-20261021/verification.json`.

## Validation réelle

| Contrôle | État | Preuve et périmètre |
|---|---|---|
| Microsoft Learn depuis Codex | PASS | App-server natif : recherche, récupération article AD DS, recherche d’exemples ; aucun tour de modèle ni confirmation |
| Microsoft Learn depuis OpenClaw Pro | PASS | Trace native : microsoft_docs_search puis microsoft_docs_fetch réussis ; aucune confirmation, 0 événement approval |
| Proxmox absent de Codex/Pro | PASS | Inventaires réels : 12 outils conservés, aucun outil Proxmox ; découverte Codex des skills rechargée sans Proxmox |
| Perso préservé | PASS | Configuration inchangée ; probe réel : uniquement convert_time et get_current_time, Microsoft Learn absent |
| Context7 | PASS | query_docs réel sur /docker/mcp-gateway |
| Serena | PASS | repository_status réel sur FloVisor/mac-ia-local, révision 366df4d41ae13f84647efbb6170de584828005d6 ; clone distant uniquement |
| Time | PASS | get_current_time réel depuis Codex |
| Orion direct | PASS | get_skill(orion) réel, version 1.0.0 ; configuration Codex inchangée |
| Ansible | PASS | SSH strict vers ANSIBLE-01, UID 0, binaire /usr/local/bin/ansible, inventaire lisible ; aucune exécution de playbook |
| Skills | PASS | Aucun lien cassé dans ~/.agents/skills et AI/skills/shared ; aucun nouveau lien ni doublon créé ; matrice mise à jour |
| Redémarrage/persistance après redémarrage | NOT_RUN | Non nécessaire : aucune configuration Gateway modifiée ; changement skills appliqué à chaud par CLI |

Preuves machine et sorties natives : `artifacts/proxmox-removal-20261021/`. Aucun changement réseau, pare-feu, cluster, LiteLLM/oMLX, service Docker, secret partagé ni accès Ansible. Aucun commit/push.

## Limites observées

Le test Pro a d’abord tenté `skills_read`, outil inexistant (FAIL pour cette tentative de chargement du skill), puis a découvert et exécuté les deux outils Microsoft Learn avec succès. La présence du skill central et son activation Pro sont préservées, mais sa lecture effective durant cette recette n’est pas démontrée. Aucun changement de l’outillage OpenClaw hors périmètre n’a été entrepris. La trace expurgée limite certains contenus volumineux ; les événements runtime de recherche et récupération portent success=true, et la réponse finale identifie l’article officiel. Preuve synthétique : `openclaw-proof.json`.

Le rechargement natif Codex a validé l’absence du skill retiré. Le contexte déjà ouvert de cette conversation peut conserver son ancienne liste de skills jusqu’à une nouvelle session ; l’affichage Desktop de cette conversation n’a pas été testé (NOT_RUN).
