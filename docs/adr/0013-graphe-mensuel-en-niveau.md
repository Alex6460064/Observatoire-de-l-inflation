# Graphe mensuel, en niveau

Le graphe principal trace les cinq indices **au pas mensuel, en niveau**, base
`2019-12 = 100` (ADR 0009).

Le mensuel est le plus petit dénominateur commun réel des sources : IPC et IPCH
sont mensuels sur 367 périodes depuis `1996-01`, les carburants sont quotidiens.
Seul l'OOHPI est trimestriel, et il est écarté par l'ADR 0005.

## Pourquoi le niveau plutôt que le glissement annuel

L'ADR 0002 impose que le dashboard reste lisible avec cinq courbes. En niveau,
cinq courbes partant du même point s'écartent en éventail : **l'écart entre
indices, qui est le sujet du projet, se lit comme une distance verticale.** En
glissement annuel, les cinq courbes se croisent en permanence et l'écart cumulé
disparaît du graphe.

Le glissement annuel n'est pas abandonné pour autant — c'est le chiffre que le
public connaît. Il est affiché **en valeur, à côté du graphe**, jamais en courbe :

```
+19,3 % depuis 2019-12       +2,1 % sur un an
```

## Alternative écartée : les moyennes annuelles

Sept points par courbe au lieu de quatre-vingts, plus lisible, moins bruité. Mais
la moyenne annuelle écrase le choc énergétique de 2022 — précisément le moment où
les profils de ménage divergent le plus, donc le moment que le projet existe pour
montrer.

## Alternative écartée : un sélecteur niveau / glissement

Doublerait le travail de visualisation, les notes méthodologiques à rédiger et
les façons de mal lire un chiffre, dans un projet dont toute la valeur tient à ce
que chaque chiffre affiché soit traçable et non ambigu.
