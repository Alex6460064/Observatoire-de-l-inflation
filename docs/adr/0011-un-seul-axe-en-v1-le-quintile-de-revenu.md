# Un seul axe en v1 : le quintile de revenu

L'ADR 0006 impose de choisir **un** axe de profil. La v1 n'en expose qu'un seul :
`hbs_str_t223`, dimension `quant_inc` (*Income quantile*), modalités `QU1` à
`QU5`.

Les cinq tables HBS ont été téléchargées et comparées le 21/08/2026 sur leur
pouvoir discriminant — l'amplitude du poids entre la modalité la plus haute et la
plus basse, en ‰, France 2020 :

| poste | niveau de vie | âge | composition | commune | revenu |
|---|---|---|---|---|---|
| `CP041` loyers réels | **150** | 100 | 73 | 52 | 92 |
| `CP042` loyers imputés | 100 | **134** | 62 | 30 | 34 |
| `CP01` alimentation | 26 | **67** | 40 | 18 | 33 |
| `CP07` transport | 47 | 44 | **69** | 29 | 62 |
| `CP125` assurance | 20 | 40 | 39 | 16 | **61** |
| `CP11` restaurants | 31 | **42** | 27 | 18 | 43 |

Le quintile écrase tout sur `CP041`, de 175 ‰ au premier à 25 ‰ au cinquième.
C'est le poste où le projet est le plus parlant, et l'axe qui sépare le plus
nettement locataires et propriétaires.

## Les autres axes sont collectés, pas exposés

`poids.csv` contient les cinq tables — ~3 000 lignes, coût nul. Exposer un axe de
plus est un changement d'interface, pas un changement de pipeline. Cohérent avec
l'ADR 0008 : le pipeline stocke tout ce qui est disponible.

`hbs_str_t227` restera probablement masquée même en v2 : ses modalités *Primary
income* / *Secondary income* sont inintelligibles pour un visiteur, et sa
modalité `UNK` produit des valeurs aberrantes (`CP041` à 148 ‰, `CP125` à 26 ‰)
qui trahissent un sous-effectif.

## Ce que cette décision coûte, et qu'il faut traiter

L'axe retenu est **le seul que l'utilisateur ne peut pas renseigner de lui-même**.
Un visiteur connaît son âge et la composition de son foyer ; il ne connaît pas son
quintile de revenu, et **HBS ne publie aucun seuil** permettant de le lui dire.
Sans repère chiffré, il choisira au jugé — et l'ensemble du résultat dépend de ce
choix.

Le problème est donc déplacé, pas résolu : il faut une source de seuils, citable
et datée, ou un autre dispositif de sélection. Décision à prendre avant
l'interface ; sans elle, la v1 n'est pas honnête.
