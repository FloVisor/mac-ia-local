# Adaptateur DIRECT Codex Desktop → LiteLLM

Ajout P3-A option B. GPT conserve son provider, son authentification ChatGPT,
ses métadonnées et son chemin via le proxy Ollama existant. Aucun binaire du
proxy n'est remplacé. Les quinze alias approuvés ont chacun une route vers
`127.0.0.1:11439/v1`, puis LiteLLM HTTPS avec une clé DIRECT dédiée.

L'adaptateur ne traite aucun modèle GPT, embedding ou Muse-Glimmer. Le catalogue
exclut ces deux derniers ; la référence historique Muse-Glimmer de l'auto-review
du proxy n'est pas modifiée, pour préserver sa politique actuelle.

## Contrats et limites

- Identité `codex-direct`, credentials LOCAL/FREE et PAID distincts, lus depuis
  leurs fichiers existants privés avec vérification propriétaire, mode et symlink.
  Aucun credential MCP, MASTER_KEY ou header ChatGPT n'est envoyé à LiteLLM.
- Trois alias PAID : habilitation et rattachement serveur à l'équipe existante
  `paid-openrouter-shared`, budget partagé 40 USD / 1mo, relus avant activation.
  Les droits, révocations et limites continuent d'être appliqués par LiteLLM.
  Aucun nouveau budget ni consentement global/par génération ajouté. Ce chemin
  DIRECT ne constitue pas un courtier de consentement DELEGATED.
- Responses converti en Chat Completions **non streaming** ; réponse complète
  traduite ensuite en SSE Responses. Pas de token visible pendant l'inférence.
  Annulation client : fermeture de la connexion amont ; l'arrêt effectif chez
  chaque fournisseur reste à qualifier. Deux requêtes simultanées au maximum,
  refus 429 au-delà, aucun retry ni fallback ajouté par l'adaptateur.
- Historique stateless intégral nécessaire ; pas de `previous_response_id`
  serveur. Texte, appels de fonctions, sorties d'outils, namespaces et outils
  custom textuels sont traduits. Images et autres items non pris en charge sont
  refusés. Les fonctions ne sont jamais exécutées par l'adaptateur.
- `web_search` hébergé OpenAI n'est pas transmissible aux tiers : il est exclu
  des seuls appels de l'adaptateur. Aucune modification des outils GPT.
- Qwen oMLX : Off/Minimal désactivés ; Low512, Medium2048, High8192, Max16384.
  Depuis l'audit de cohérence du 21 octobre, `max_tokens` réserve la réponse
  demandée (2048 par défaut) **plus** le budget de pensée ; le contexte réserve
  ce total avant tout envoi. Paramètres oMLX
  injectés par l'ancien proxy supprimés/reconstruits à partir de l'effort demandé.
- Clouds : effort demandé conservé ; aucune valeur numérique oMLX transposée.
  Les traces distinguent demande, valeur envoyée, conversion attendue d'après
  les adaptateurs installés, et application réelle inconnue. FreeLLMAPI convertit
  Max→High, Groq none/minimal→Low, Mistral supprime l'effort ; LiteLLM transforme
  Max→xhigh sur OpenRouter payant. Les niveaux cloud non qualifiés ne sont pas
  annoncés comme des capacités dans le sélecteur. Les pools n'offrent aucune
  garantie de niveau commun.
- Entrées cloud et Ollama : admission de contexte prudente 8192, **maximum non
  qualifié**. Admission oMLX 131072. Estimation conservatrice UTF-8 des messages
  transformés, instructions et outils, marge 256 et génération réservée ; refus
  `context_budget_exceeded_return_to_codex` avant inférence. Pas de troncature
  dans l'adaptateur. `Retry-After` valide est conservé sans retry automatique.
  Le lanceur CLI `codex/scripts/llm-router-direct.py` emprunte également cet
  adaptateur ; ses overrides 8192/7000 ou 131072/100000 ne changent pas le
  fichier global Codex. La compatibilité multimodale
  et tous les outils n'est pas revendiquée.

## Synchronisation et état

`manage.py` lit `/v1/models` pour chacune des deux identités DIRECT et intersecte
la politique chat approuvée du dépôt. Il conserve **toutes les entrées GPT
existantes à l'identique**, GPT-6.1-Sol prioritaire et GPT-6-Sol masqué compris.
Le catalogue embarqué du binaire Desktop est consulté à chaque cycle pour
diagnostic ; une nouvelle version GPT n'est pas autorisée automatiquement.
Pas de copie manuelle des listes de modèles LiteLLM dans ce script.

Synchronisation toutes les 300 secondes par un LaunchAgent distinct. Fichiers
temporaires privés et remplacement atomique par fichier, verrou du gestionnaire,
routes publiées avant le catalogue, santé exigée avant publication. Les fichiers
appartiennent à la configuration documentée du proxy et de Codex, pas à une base
interne. Les anciennes routes révoquées restent des routes de refus vers
l'adaptateur, pour éviter un fallback natif d'une session ancienne.
Une modification concurrente d'une entrée appartenant au lot bloque l'écriture.
Une erreur de découverte ou de credential n'élargit jamais les droits.

`~/.config/codex-litellm-adapter/` : configuration privée et secret d'entrée
loopback. `~/.local/state/codex-litellm-adapter/` : snapshot initial, manifestes,
candidats, état de synchronisation et journal JSONL sans prompt ni clé.
Deux LaunchAgents `org.gangneux.codex-litellm-adapter` et suffixe `-sync`.

Le catalogue Desktop est chargé au démarrage de l'app-server. L'écriture du
fichier ne prouve pas un rafraîchissement à chaud de la fenêtre existante.
Ne pas redémarrer l'application qui héberge une session de travail en cours.

## Commandes

Depuis la racine du dépôt, Python système/Homebrew sans dépendance tierce :

```sh
# Préparer une seule fois avec la preuve serveur filtrée de l'identité/budget.
python3 codex/litellm-adapter/manage.py prepare --identity-evidence CHEMIN_PREUVE_JSON
python3 codex/litellm-adapter/manage.py start
# Attendre le démarrage effectif ; activate exige /health=ok.
python3 codex/litellm-adapter/manage.py activate
python3 codex/litellm-adapter/manage.py schedule
```

Une préparation interrompue ne remplace pas sa sauvegarde : reprise seulement
si les deux configurations actives correspondent encore au snapshot initial.

```sh
# Retour arrière ciblé. Arrête d'abord le synchroniseur, restaure seulement les
# entrées possédées par le lot, puis arrête l'adaptateur et retire ses LaunchAgents.
python3 codex/litellm-adapter/manage.py rollback

# Réactivation après rollback, sans réémettre de clé ni recréer un budget :
python3 codex/litellm-adapter/manage.py start
python3 codex/litellm-adapter/manage.py activate
python3 codex/litellm-adapter/manage.py schedule
```

Le rollback refuse un conflit sur les entrées possédées. Il préserve les entrées
étrangères et toutes les autres options de configuration ; il ne restaure jamais
globalement `config.toml`. Conserver les snapshots et clés privées pour la
traçabilité/réactivation ; aucune clé cliente partagée avec P3-B n'est révoquée.

Tests nouveaux uniquement : `test_adapter.py`, `test_manage.py`. Les preuves de
recette sont référencées dans [le rapport P3-A](../20-llm-router-p3a.md).


## Ollama : fin de réponse et associations d'outils

Sur le seul alias `local-ollama/qwen3:4b-instruct`, le pont fournit l'entier
`usage.output_tokens_details.reasoning_tokens` requis par Desktop. En l'absence
de détail fournisseur, 0 est un défaut de protocole tracé, pas un effort mesuré.
Les IDs des appels et résultats sont conservés, y compris custom et résultats
hors ordre ; les associations incohérentes sont refusées. Aucun regroupement
aveugle des messages assistant textuels. Le callback Qwen de LiteLLM restaure les
IDs retirés par sa conversion 1.104.5 ; le contexte imposé demeure 8192.

Les traces de cette route ne contiennent que types, rôles et IDs d'association.
Recette bornée et rollback : dernière section de `../20-llm-router-p3a.md`.
Tests synthétiques : `python3 -m unittest discover -s codex/litellm-adapter -q`.
