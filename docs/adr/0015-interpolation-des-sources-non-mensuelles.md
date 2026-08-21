# Interpolation linéaire des sources non mensuelles

L'ADR 0013 impose un graphe mensuel ; trois des quatre postes à source propre de
l'ADR 0014 ne sont pas mensuels. Les valeurs intermédiaires sont obtenues par
**interpolation linéaire** entre deux points publiés.

## Le garde-fou, indissociable de la décision

Interpoler produit des valeurs mensuelles qui n'existent dans aucune publication.
Ce n'est acceptable que si elles restent **discernables d'un relevé à toutes les
étapes** :

- `data/processed/prix.csv` porte une colonne `interpole`, vraie sur tout point
  calculé, fausse sur tout point publié.
- Le tooltip du dashboard affiche explicitement qu'une valeur est interpolée.
- Tout export ou partage conserve la colonne.
- La règle figure dans la section « Limites » de `docs/METHODOLOGIE.md`.

Sans ce marquage, une valeur interpolée devient indiscernable d'une valeur
mesurée, ce qui viole directement la règle d'anti-hallucination de `CLAUDE.md`.
Le drapeau n'est donc pas un raffinement d'interface : il fait partie de la
décision.

## Alternatives écartées

- **Marches d'escalier** : chaque point tracé aurait correspondu à un chiffre
  publié, sans aucune valeur calculée. Écartée pour la lisibilité — les paliers
  et les sauts au 1er janvier rendent la courbe difficile à comparer aux quatre
  autres.
- **Profil intra-annuel emprunté à l'IPCH** : techniquement le plus réaliste
  (désagrégation temporelle), mais fait cohabiter deux sources de prix dans un
  même poste, ce que l'ADR 0002 proscrit, et rend le poste indescriptible en une
  phrase.

## Portée

L'interpolation vaut **entre deux points publiés**. Elle ne dit rien du cas où
la source est absente sur plusieurs années — le trou 2019 à 2021 de la Carte des
loyers relève d'une décision distincte.

Le tarif réglementé d'électricité n'est pas concerné : un barème vaut jusqu'au
suivant, ce qui est une donnée en escalier par nature, pas une lacune à combler.
