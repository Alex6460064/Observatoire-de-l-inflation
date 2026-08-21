# Périmètre de l'indice Observatoire en v1

L'indice Observatoire est **l'objectif premier du projet**, pas une extension.
Il est construit dès la v1, sur quatre postes à source propre ; tout le reste du
panier retombe sur l'IPCH.

| poste | source propre | fréquence | couverture |
|---|---|---|---|
| `CP01` alimentation | Familles Rurales, Observatoire des prix (ADR 0019) | annuelle | 2019→2025 |
| `CP041` loyers réels | « Carte des loyers », ministère de la Transition écologique | annuelle | 2018, 2022→2025 |
| `CP045` énergie logement | CRE, tarif réglementé de vente d'électricité | barème daté | 2012→2026 |
| `CP072` utilisation du véhicule | prix-carburants.gouv.fr, archives annuelles | quotidienne | 2019→2026 |

Poids HBS 2020 couverts par une source propre :

```
              CP01   CP041   CP045   CP072   total
QU1            147     175      55      48    425 ‰
QU3            154      71      46      58    329 ‰
QU5            128      25      36      50    239 ‰
```

Soit **24 à 43 % du panier selon le quintile**. L'indice Observatoire n'est donc
pas une variante cosmétique de l'IPCH repondéré : il en diffère sur les postes
qui ont le plus augmenté depuis 2019.

## Les réserves, toutes destinées à `docs/METHODOLOGIE.md`

**`CP041` mesure autre chose que l'IPCH.** La Carte des loyers donne des **loyers
d'annonce** — le prix demandé pour un logement remis sur le marché. L'IPCH `CP041`
mesure le loyer payé par l'ensemble du parc, locataires en place compris, dont le
loyer est plafonné par l'indexation. L'écart entre les deux est une différence de
**champ — flux contre stock —, pas une erreur de l'INSEE.** Afficher cet écart
sans l'écrire ferait du projet l'outil militant que `CLAUDE.md` interdit.

> ⚠️ **Amendement du 21/08/2026 — cette réserve est périmée. Voir l'ADR 0019.**
> Elle concluait de trois requêtes `data.gouv` qu'aucune source alimentaire
> ouverte n'existait. C'était faux : le catalogue `data.gouv` ne recense ni les
> associations de consommateurs ni les publications d'établissements publics hors
> jeux de données. `CP01` prend désormais Familles Rurales, qualité
> `etude_publiee` et non `synthese_presse`. Le texte d'origine est conservé
> ci-dessous parce que sa dernière phrase reste la règle du projet.

**`CP01` repose sur la source la plus faible pour le poste le plus lourd.** Les
panels Kantar, NielsenIQ et Circana sont commerciaux ; leur sortie publique est
un communiqué, pas une série. Trois requêtes sur data.gouv le 21/08/2026
(`prix produits alimentaires`, `observatoire prix marges`,
`relevés de prix consommation`) renvoient zéro résultat. Le périmètre de ces
chiffres est celui des « PGC-FLS » de la grande distribution, **qui n'est pas
`CP01`** : il exclut une partie du frais traditionnel. Deux à trois points par an.
Qualité `synthese_presse` au sens de l'ADR 0004, badge visible dans l'interface.

Cette réserve a été exposée avant décision et la décision a été maintenue. Elle
est assumée, à condition d'être écrite et affichée.

> La réserve de champ n'a pas disparu, elle a changé de sens. Familles Rurales
> relève un panier **normatif PNNS**, pas la consommation observée : fruits et
> légumes près du tiers du budget, ni alcool ni restauration. L'écart de champ est
> au moins aussi lourd que celui du PGC-FLS, et il pousse dans l'autre sens.
> Détail et chiffres dans l'ADR 0019.

**Le tarif réglementé n'est pas un prix, c'est un barème.** `abonnement + kWh ×
consommation` : en faire un indice suppose un profil de consommation. Il ne
couvre que les ménages restés au tarif réglementé.

**Les carburants ne peuvent pas être pondérés par les volumes vendus.** Aucun
volume n'est publié : une moyenne sur les stations donne le même poids à une
station d'autoroute et à un hypermarché. L'INSEE, lui, pondère.

**La Carte des loyers est communale.** Agréger 34 901 communes en un chiffre
national exige une pondération par le parc locatif, pas une moyenne simple.

## Ce qui reste à trancher, créé par cette décision

1. Comment une source annuelle ou ponctuelle devient une courbe sur un graphe
   mensuel (ADR 0013), sans fabriquer de valeurs.
2. Le trou 2019, 2020, 2021 de la Carte des loyers, juste après la date de
   référence de l'ADR 0009.
3. La pondération d'agrégation des communes.
4. La table de paramètres : profil de consommation électrique, mix de carburants,
   chacun sourcé ou déclaré.
