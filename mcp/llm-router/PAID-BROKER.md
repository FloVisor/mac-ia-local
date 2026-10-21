# Courtier DELEGATED : politique fail-closed, activation interdite

`paid_broker.py` ajoute le noyau de contrôle ; `authorization.py` conserve ses
primitives historiques et le contrat DIRECT. Aucun outil MCP, credential PAID,
route réseau, configuration client ou connexion OpenClaw n'est ajouté.
`router.py` conserve `paid_broker_not_connected` pour les appels payants.

## Contrats obligatoires des adaptateurs de confiance

Le noyau n'accepte aucune identité, décision, estimation ou solde du modèle comme
preuve d'autorité. Ses dépendances sont installées par le service de confiance :

- `authenticate(credential)` : identité cliente et session attestées. Seuls
  `openclaw-pro` et `openclaw-perso` sont admissibles ; DIRECT n'y participe pas.
- `verify_approval(receipt)` : résolution native `allow-once`, référence unique,
  identité/session, empreinte exacte de l'offre et expiration. Une chaîne
  `approved`, une décision permanente, un reçu d'une autre tâche ou un accord
  réutilisé ne constituent pas une autorisation.
- Adaptateur fournisseur par modèle exact : devis non facturant, tarif USD
  versionné et applicable, borne attestée des tokens d'entrée, tarif sortie
  couvrant le raisonnement, frais fixes, échéance, contrat imposant avant appel
  le prix épinglé et le coût maximal. `verify_bound` doit refuser une garantie
  absente/inconnue ; `run` doit faire respecter la garantie, pas estimer ou
  surveiller le coût après génération.
- `shared_coverage(db, team)` : coordination de **toutes** les dépenses et
  réservations de `paid-openrouter-shared`, y compris DIRECT, dans la même
  transaction persistante. Un relevé asynchrone ou un booléen issu du modèle
  n'implémente pas ce contrat. Le callback n'est pas fourni en production.
- `verify_bill(receipt)` : facture définitive attestée, immuable, rattachée à
  l'opération, au fournisseur, au modèle, au tarif et à l'équipe. Un résultat
  texte, une erreur réseau ou une estimation de coût ne sont pas une facture.

**Aucun adaptateur de production n'implémente actuellement ces garanties.** Les
fixtures de test sont explicitement simulées. Leur installation par un opérateur
ne prouverait pas une garantie fournisseur réelle ; elles ne doivent jamais
être reliées aux clés PAID. Sans adaptateurs, le noyau refuse l'exécution.

## Bornes et registre

Monnaie entière en nano-USD (1 USD = 1 000 000 000), sans calcul flottant.
Borne = tokens d'entrée attestés × tarif entrée + tokens de sortie autorisés ×
tarif sortie incluant reasoning + frais fixes. Tarif absent, négatif, devise
inconnue, tarif modifié/expiré, coût non borné ou supérieur au consentement : refus.

Texte seulement, `max_output_tokens` obligatoire entre 1 et 4096 et `n=1`
imposé. Les autres paramètres facturables sont refusés : outils/recherche,
audio/image, service tier, cache, budget reasoning séparé, multiplicateur de
réponses, paramètres arbitraires. Aucun pool ni fallback, retries explicitement 0.
Un adaptateur réel devrait prouver que ses valeurs implicites ne créent aucun
coût hors de la borne ; à défaut il doit refuser le contrat.

L'offre figée inclut tâche, modèle, identité/session, payload normalisé, tarif,
plafond, expiration et équipe. Unicité identité/session/tâche et reçu natif.
Dans le registre **propre au composant** : `BEGIN IMMEDIATE`, somme des dépenses
confirmées + toutes les réservations + nouvelle borne <= enveloppe autorisée,
puis accord consommé et réservation `dispatching` commis avec `synchronous=FULL`
avant le premier appel fournisseur. Erreur/lock/échec de commit : aucun appel.
Le registre est privé 0600 dans un répertoire privé 0700.

La limite 40 USD du registre de qualification est la représentation de
l'enveloppe partagée simulée, pas un deuxième budget attribué en production.
Aucune création ni modification de budget LiteLLM. Importer un solde historique
sans coordonner les appels DIRECT concurrents ne suffit pas à initialiser un
coordinateur réel. Période comptable/réinitialisation mensuelle non intégrées :
aucune remise à zéro automatique, surtout en présence de réservations incertaines.

## Incertitude et réconciliation

Après le commit, aucun second lancement, même après redémarrage, révocation,
expiration, timeout ou arrêt brutal. Une réservation `dispatching` ou `uncertain`
reste intégralement comptée, sans TTL de libération. Une révocation avant envoi
interdit le lancement ; après envoi elle ne prétend ni annuler ni effacer la dette.

Seule une facture définitive vérifiée transforme atomiquement la réservation en
dépense réelle et libère la différence. Une facture provisoire laisse la borne
entière réservée. Facture tardive acceptée même après expiration de l'accord ;
réconciliation répétée idempotente. Zéro USD exige aussi une facture définitive.
Si le fournisseur viole sa garantie de plafond, le montant définitif est conservé
et le compte est gelé : cette détection ne prétend pas annuler une facturation
externe. Un faux fournisseur ne peut pas être rendu sûr par le seul courtier.

## Recette ciblée

```sh
python3 -m unittest discover -s mcp/llm-router -p test_paid_broker.py -v
```

Fournisseur, attestations natives, coordination partagée et factures simulés ;
SQLite temporaire propre aux tests, supprimée à la fin. Aucun appel HTTP,
OpenRouter, LiteLLM ou MCP historique. Aucun test historique relancé.
Voir le rapport [P3-B](../../codex/21-llm-router-p3b.md) pour les statuts et preuves.
