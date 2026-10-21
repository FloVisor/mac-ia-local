# Preuves filtrées — 21 octobre 2026

Captures SSH directes depuis le Mac, horodatées en UTC dans les fichiers ; date de campagne Europe/Paris. Les fichiers *.json sont filtrés sur le serveur avant transfert ; les sources YAML ne sont pas des copies brutes. Les preuves de sondes ne conservent pas les corps, cookies ou en-têtes bruts.

| Fichier | SHA-256 |
|---|---|
| [192.168.201.39.details.json](192.168.201.39.details.json) | 1c1417156a8e9a19ad12c94596ea97426a521493733254fc54143c3a8f6151a9 |
| [192.168.201.39.json](192.168.201.39.json) | c7fd0ce8cddee580f79f3e6535edaef4162ef027fd8d60caa061e4f252c32b0a |
| [backends.json](backends.json) | bead2dd7ab44ebded9a75872340ae459040a8cf230e3ee649e6893cc01301663 |
| [bookstack-permissions.json](bookstack-permissions.json) | d7237e79f62d162c84042dc878babb03fa63151c8252f564f0def8a1b614c122 |
| [coverage.json](coverage.json) | 7082679712bb85efafc3ef81169cd6842b11e7dbef6140770e5ce01ad171039d |
| [dns-mac.json](dns-mac.json) | 65f0021a92feba78384d51a42efe074f0cef7a6edd112a5b818a3b501adef396 |
| [docker-01.details.json](docker-01.details.json) | 3af574c1e30c1f2183b8a39ae7bbbfa97daa614f3ed6be2f0989642476e71f91 |
| [docker-01.json](docker-01.json) | 18e6a722be9b4d583df713492b5360cbdf5638f4b6b09be00ad831fb70a91795 |
| [docker-01.operations.json](docker-01.operations.json) | 53b4ad6bf4211da0373710ab44e98c7376686e59acd6efd7056eb8043510c507 |
| [docker-02.details.json](docker-02.details.json) | 0031108907e62fb8f2e68f9ad0c9a26d99403d9483bc0480bb96c96df1007655 |
| [docker-02.json](docker-02.json) | a4f10ddcf9e29c8cff157631d9b293fa50c856b1e3f6cc24d3e556729f4f521a |
| [docker-02.operations.json](docker-02.operations.json) | 22e079faf35159338e4beedaa64e390c6b2d3f3a7f2e8909ac38a46d9a3d11a4 |
| [docker-03.details.json](docker-03.details.json) | 2b819e333e0a61f7f8843171c93c8ff5a895eb7683c5e87fb808b23f0bcf49b0 |
| [docker-03.json](docker-03.json) | dd54d31757784002ce3091f242bffe0f0fe4ca756d50833555622bbc9292dcf4 |
| [docker-03.operations.json](docker-03.operations.json) | 6dbaeffc27a106aad3dceb8273c419716a66bc56625f0dc644c4a75936e1bac0 |
| [frontends.json](frontends.json) | 07175938c7803ba324e57fec70ad2236e95b54792a99b777674586d292e1b4d6 |
| [public-ipv4-frontends.json](public-ipv4-frontends.json) | 5ab14d74b4feb1b3534f9a9be23511b1798cd997163286625611339ef8c4e1e7 |


## Collecte et reproduction

Sources : [collect_remote.py](../../tools/collect_remote.py), [collect_details.py](../../tools/collect_details.py), [run_audit.py](../../tools/run_audit.py). Python 3 et PyYAML sur le Mac ; le parseur YAML existant est fourni en mémoire aux nœuds dépourvus du module, sans installation distante ni fichier temporaire distant. Commandes distantes bornées et métadonnées JSON filtrées. Les erreurs sont explicites.

Pour une nouvelle campagne, choisir un nouveau répertoire ; ne pas remplacer ces preuves :

```bash
python3 infrastructure/tools/run_audit.py --output infrastructure/evidence/NOUVELLE-CAMPAGNE
python3 infrastructure/tools/run_audit.py --details --output infrastructure/evidence/NOUVELLE-CAMPAGNE
```

Le collecteur refuse d’écraser un fichier de preuve existant. Les scripts de sondes et de génération sont spécifiques au relevé du 21 octobre ; adapter la destination et revoir les cibles avant une nouvelle campagne. Une exécution a posteriori n’est pas nécessaire pour consulter les résultats présents.

Les fichiers *.operations.json et dns-mac.json proviennent de lectures ciblées complémentaires : résultats systemd, résumé statique des scripts de sauvegarde, métadonnées de l’ancien chemin ACME, directives non sensibles Nginx, définition du healthcheck Ollama-Proxy et résolution getaddrinfo du Mac. public-ipv4-frontends.json contient les HEAD -4 via DNS normal vers l’IPv4 publique. Aucun contenu secret ni de base n’a été lu lors de ces compléments.

Les résultats systemd success ne constituent pas une preuve de sauvegarde/restauration. Les listes de scripts sont des résumés statiques et des hashes, pas une certification de leur logique. Le filtre de redaction a été durci après la collecte initiale pour les options password=... ; les captures présentes ont été contrôlées séparément et n’ont pas été remplacées.
