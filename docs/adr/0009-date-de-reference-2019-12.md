# Date de référence 2019-12, historique complet stocké

Les cinq indices de l'ADR 0002 n'ont pas la même base native : Eurostat sert
`I15` (2015 = 100), l'INSEE publie en base 2025 depuis janvier 2026. Les
superposer impose de tout rebaser sur une date commune. Ce choix n'est pas
cosmétique : la date de référence est la phrase que lit le visiteur — « depuis
cette date, votre panier a fait +X % ».

**La référence est `2019-12`**, dernier mois avant le choc covid. Elle couvre
covid puis le choc énergétique, elle correspond au cadrage de la vidéo d'origine,
et surtout les valeurs déjà relevées dans `docs/SOURCES.md` partent de ce mois :
nos courbes seront directement vérifiables contre elles (`TOTAL` +19,3 %, `CP01`
+27,4 %, `CP041` +10,2 %, `CP045` +45,6 % entre `2019-12` et `2026-03`).

**Le pipeline stocke toute la profondeur disponible**, pas seulement la période
affichée. Tronquer à la collecte serait irréversible pour un gain de quelques
dizaines de kilo-octets. La date de référence est un paramètre de lecture, pas
une propriété de la donnée : elle est offerte à l'utilisateur dans une liste
courte, jamais en saisie libre sur toute la profondeur.

## Pourquoi pas 2020-01, l'année des poids

Ce serait le Laspeyres canonique — poids et référence la même année, rien à
justifier. Mais la référence tomberait à l'intérieur de la période de prix
perturbés, et le récit deviendrait « depuis le début du covid » au lieu de
« depuis avant ». L'écart entre les poids et la référence est un étirement
acceptable, et il est déjà couvert par l'ADR 0007.

> ⚠️ Amendement du 21/08/2026. Cette section raisonnait sur des « poids 2020 »
> qui n'existent pas : la vague Eurostat 2020 est, pour la France, une copie de la
> vague 2015, elle-même issue de l'enquête Budget de famille 2017 collectée
> d'octobre 2016 à octobre 2017. L'écart poids ↔ référence n'est donc pas d'un an
> mais de **deux ans et deux mois**. Le raisonnement tient — 2020-01 reste écarté
> pour la même raison — mais le chiffre était faux. Voir l'ADR 0007 amendé.

## Pourquoi pas de sélecteur libre

Avec des poids fixes 2020, une référence 1996 est calculable et méthodologiquement
creuse : elle projetterait la structure de budget de 2020 sur trente ans de prix.
La donnée reste stockée, le choix reste borné.

## Vérifications ouvertes que cette décision rend nécessaires

- ~~**La vague HBS 2020 a-t-elle été collectée pendant les confinements ?**~~
  **Vérifié le 21/08/2026 : non.** Il n'existe aucune collecte 2020 pour la
  France. Les poids proviennent de l'enquête Budget de famille 2017, collectée
  d'octobre 2016 à octobre 2017, soit deux ans et demi avant le premier
  confinement. Les poids ne sont pas déformés par le covid ; ils sont simplement
  antérieurs. Sources dans `docs/SOURCES.md`, conséquences dans l'ADR 0007.
- **L'indice Observatoire démarrera plus tard que les quatre autres**, sa
  couverture étant plafonnée par le stock `roulez-eco` (non testé) et par des
  relevés manuels forcément récents. La courbe sera plus courte ; l'interface doit
  le montrer, pas le masquer.
