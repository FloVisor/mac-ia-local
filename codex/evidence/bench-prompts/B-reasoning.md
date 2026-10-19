# Test B — Raisonnement code
Voici un code Python contenant un bug volontaire :

```python
def moyenne(nombres):
    total = 0
    for n in nombres:
        total += n
    return total / len(nombres)
```

1. Identifie le bug précis (cas d'échec).
2. Propose la correction minimale.
3. Donne un test unitaire qui échoue avant et passe après.
Réponds en 3 sections numérotées, sans exécuter de commande.
