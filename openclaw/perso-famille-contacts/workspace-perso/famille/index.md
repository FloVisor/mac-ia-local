# famille/index.md — Annuaire familial (Perso)

Annuaire compact. Chargé **à la demande**, jamais injecté en permanence.
Une fiche détaillée par personne : `famille/personnes/<identifiant>.md`.

Les coordonnées (téléphone, email, adresse, anniversaire) ne sont **pas** ici :
elles se lisent dans Contacts Apple via `perso-contacts` (lecture seule).

## Identités

| id | Nom | Alias confirmés | Liens | Fiche |
| --- | --- | --- | --- | --- |
| utilisateur | Florian GANGNEUX | — | moi | [fiche](personnes/utilisateur.md) |
| epouse | Anaïs GANGNEUX | « ma femme », « mon épouse » | épouse de Florian | [fiche](personnes/epouse.md) |
| fille | Emma GANGNEUX | — | fille de Florian | [fiche](personnes/fille.md) |
| fils | Timéo GANGNEUX | Timeo | fils de Florian | [fiche](personnes/fils.md) |
| pere | Thierry GANGNEUX | « mon père » | père de Florian, mari d'Alice | [fiche](personnes/pere.md) |
| alice | Alice PENNINGTON MELLOR | — | épouse de Thierry | [fiche](personnes/alice.md) |
| mere | Valérie GANGNEUX | « ma mère » | mère de Florian | [fiche](personnes/mere.md) |
| mathys | Mathys GANGNEUX | — | frère de Florian | [fiche](personnes/mathys.md) |
| alexis | Alexis GANGNEUX | — | frère de Florian | [fiche](personnes/alexis.md) |
| nadine | Nadine SIMON | — | belle-mère de Florian | [fiche](personnes/nadine.md) |
| philippe | Philippe DELORME | — | conjoint de Nadine | [fiche](personnes/philippe.md) |
| chloe | Chloé JOUBERT | Cholé Joubert | belle-sœur de Florian | [fiche](personnes/chloe.md) |
| alexandre | Alexandre CORBIN | — | compagnon de Chloé | [fiche](personnes/alexandre.md) |
| esteban | Esteban | — | enfant de Chloé et Alexandre | [fiche](personnes/esteban.md) |
| augustin | Augustin | — | enfant de Chloé et Alexandre | [fiche](personnes/augustin.md) |
| melissa | Melissa BLOT | Melissa Joubert | belle-sœur de Florian | [fiche](personnes/melissa.md) |
| benjamin | Benjamin | — | mari de Melissa | [fiche](personnes/benjamin.md) |
| aerys | Aerys | — | enfant de Melissa et Benjamin | [fiche](personnes/aerys.md) |
| kenji | Kenji | — | enfant de Melissa et Benjamin | [fiche](personnes/kenji.md) |
| georgette | Georgette SIMON | — | grand-mère d'Anaïs | [fiche](personnes/georgette.md) |
| yannick | Yannick SIMON | — | oncle d'Anaïs | [fiche](personnes/yannick.md) |

## Règles de résolution

- « ma femme » / « mon épouse » → `epouse`. « mon père » → `pere`. « ma mère » → `mere`.
- « Chloé » ou « Cholé » → `chloe`. « Melissa Joubert » → `melissa`.
- « le compagnon de Chloé » → `alexandre` (jamais Benjamin).
- « le mari de Melissa » → `benjamin`, sans supposer son patronyme.
- Ne jamais prendre le premier résultat d'une recherche Contacts.
- Ne pas attribuer de patronyme aux enfants dont seul le prénom est fourni.
- Ne pas proposer spontanément de contacter `nadine`.
- Les liens ci-dessus valent pour Florian comme locuteur ; pour un tiers, demander une précision.
