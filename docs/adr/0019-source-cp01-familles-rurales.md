# Source propre de `CP01` : Familles Rurales

L'ADR 0014 inscrit `CP01` alimentation au périmètre de l'indice Observatoire avec
la source « relevés de presse (Kantar, NielsenIQ, Circana) », la qualité
`synthese_presse`, et une colonne couverture qui dit **« à établir »**. C'est le
poste le plus lourd du périmètre — 147 ‰ au premier quintile, 154 ‰ au troisième,
128 ‰ au cinquième — adossé à la source la plus faible.

Cette décision remplace cette ligne. Trois des hypothèses de l'ADR 0014 étaient
fausses, chacune vérifiée le 21/08/2026 et documentée dans `docs/SOURCES.md`.

## Ce qui était faux

**« Aucune source alimentaire ouverte n'existe. »** Trois existent : Familles
Rurales, « Point conso » de FranceAgriMer, et Open Prices. Aucune n'avait été
cherchée. La conclusion venait de trois requêtes `data.gouv` — un catalogue qui ne
recense ni les associations de consommateurs ni les publications d'établissements
publics hors jeux de données.

**« Le baromètre de presse s'arrête fin 2023. »** Non : avril 2026 à +0,4 % sur un
an sur les PGC-FLS, juin 2026 à zéro en hypermarché. Il tourne toujours.

**« La presse est la seule option, donc `synthese_presse` est le plafond. »** Non :
Familles Rurales publie un protocole complet, ce qui la place à `etude_publiee`,
un cran au-dessus.

## Décision

`CP01` prend pour source propre l'**Observatoire des prix de grande consommation
de Familles Rurales**, qualité **`etude_publiee`**.

L'objet chaîné est **l'évolution que l'association publie elle-même**, calculée
par elle sur produits comparables — jamais le coût brut de son panier. Le panier
perd un quart de ses produits entre 2021 (97) et 2025 (83) ; comparer 450 € à
539 € ne comparerait pas des prix.

Une valeur publiée par édition, interpolée linéairement entre deux points selon
l'ADR 0015, colonne `interpole` vraie sur tout point calculé.

## Pourquoi celle-là

Elle est la seule des trois à couvrir la période qui fait l'intérêt du projet.

| candidate | couverture | fréquence | qualité | verdict |
|---|---|---|---|---|
| **Familles Rurales** | **2019 →** | annuelle | `etude_publiee` | retenue |
| Point conso (FranceAgriMer) | 2024-01 → | mensuelle | `etude_publiee` | rate la flambée |
| Circana / LSA | ~2019 → | mensuelle | `synthese_presse` | payante, article par article |
| Open Prices | 2024 → utilisable | quotidienne | `api_ouverte` | mesurée, écartée |

Point conso est la meilleure source **de 2024 à aujourd'hui** : mensuelle,
gratuite, service public, périmètre PGC-FLS cohérent avec ce que l'ADR 0014 avait
déjà accepté. Elle est écartée uniquement parce qu'un indice ancré en `2019-12`
serait en IPCH sur toute la flambée de 2021-2023 — c'est-à-dire vide de sens.
Elle reste le candidat naturel d'une v2 qui accepterait un raccord de sources.

Open Prices a été codée avant d'être jugée. Sur `CP01`, mai → juin 2026 :
l'officiel fait **−0,34 %**, la méthode des produits appariés **+1,58 %**, le
panier naïf **−4,04 %**. Deux méthodes défendables, même donnée, même mois, 5,6
points d'écart et des signes opposés. Un indice apparié reposerait sur 75 produits
en mensuel. Le biais n'est pas bornable ; le détail est dans `docs/SOURCES.md`.

## Ce que la décision achète, au-delà de la couverture

Le panier de Familles Rurales monte **systématiquement moins** que l'IPC
alimentaire : +8,3 % contre +12 % sur l'édition 2022, +9,4 % contre +14,7 % de
2023 à 2025, −0,75 % contre +1,7 % de 2024 à 2025. Trois éditions sur trois, même
sens, 3 à 5 points d'écart par an pendant la flambée.

Une source propre qui pousse l'écart dans le sens **opposé** au récit militant est
la meilleure protection dont ce projet puisse disposer. Elle rend littéralement
impossible le reproche que `CLAUDE.md` cherche à éviter : sur `CP01`, l'indice
Observatoire dira que l'INSEE **surestime** la hausse, pas l'inverse.

## Le coût, entièrement à écrire

**Le panier PNNS n'est pas `CP01`.** C'est un panier normatif — ce qu'il faudrait
manger — pas ce que les ménages achètent. Fruits et légumes près du tiers du
budget, pas d'alcool, pas de restauration, peu de transformé. L'écart de champ est
au moins aussi lourd que celui du PGC-FLS que l'ADR 0014 avait accepté, et il va
**dans l'autre sens**. C'est très probablement d'où vient l'écart favorable
ci-dessus, et il faut le dire dans la même phrase que le résultat.

**La base 100 de `CP01` est une valeur calculée.** L'édition 2021 publie la
période « septembre 2019 → septembre 2021 ». La date de référence de l'ADR 0009
est `2019-12`. Le point de départ tombe **trois mois avant la base 100**, qui est
donc interpolée sur un intervalle de 24 mois traversant le covid.

C'est la deuxième fois : l'ADR 0016 a déjà rendu la base 100 de `CP041`
interpolée. Cumulé, au premier quintile, **322 ‰ du panier — `CP01` 147 ‰ plus
`CP041` 175 ‰ — s'ancrent sur une valeur qu'aucune publication ne contient.**
Presque un tiers. Cette phrase ouvre la section « Limites » de
`docs/METHODOLOGIE.md`, devant celle de l'ADR 0016 qu'elle englobe.

**Annuelle contre mensuelle.** Quatre collectes par an, une publication annuelle :
onze valeurs mensuelles sur douze sont calculées. L'ADR 0015 s'applique
intégralement.

**Échantillon non probabiliste.** 135 magasins choisis par des bénévoles. Le
protocole est stable et décrit, ce qui le sépare d'une collecte opportuniste, mais
il ne devient pas représentatif pour autant.

## Ce que la décision laisse ouvert

`# TODO: à vérifier` — seules les éditions **2021, 2022 et 2025** ont été
récupérées et lues. Il manque 2019, 2020, 2023, 2024 et 2026. Le raccord ne peut
pas être figé, ni la série écrite dans `data/manual/releves.csv`, tant que chaque
édition n'a pas fourni sa période de référence exacte et son évolution publiée.

Les périodes de référence publiées **ne sont pas homogènes** d'une édition à
l'autre : l'édition 2021 raisonne sur deux ans (sept. 2019 → sept. 2021), les
suivantes sur un an. Il faudra une règle explicite pour convertir ces intervalles
en points datés, et elle devra être écrite dans `docs/METHODOLOGIE.md` avant
d'être codée, comme l'exige `CLAUDE.md`.

**La collecte restera manuelle.** Les trois PDF testés utilisent trois encodages
de police différents ; aucun extracteur unique ne les lit tous. Ne pas budgéter de
parseur automatique — c'est exactement le cas d'usage de l'ADR 0004.

## Conséquence sur l'ADR 0001

L'amendement de l'ADR 0001 vérifie poste par poste qu'aucune source de l'indice 4
ne corrige la shrinkflation ni l'ajustement hédonique. Sa ligne « relevés de presse
PGC-FLS » devient « Familles Rurales, panier PNNS ». La conclusion ne bouge pas :
les relevés portent sur des produits nommés à un instant donné, sans suivi de
qualité ni de grammage dans le temps. Le bannissement d'« inflation réelle » tient.
