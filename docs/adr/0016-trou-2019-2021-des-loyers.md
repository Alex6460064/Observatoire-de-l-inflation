# Trou 2019-2021 des loyers : interpolation 2018 → 2022

La Carte des loyers n'existe qu'en millésimes 2018, 2022, 2023, 2024 et 2025.
Vérifié : ce n'est pas une lacune de diffusion. Le projet a été lancé en 2018 par
la DGALN avec Agrosup Dijon, l'INRAE, SeLoger et leboncoin ; l'ANIL l'a repris en
2020 et n'a repris les publications qu'en 2022. **Les millésimes 2019, 2020 et
2021 n'ont jamais été produits.**

La valeur de `CP041` est donc interpolée linéairement entre 2018 et 2022, soit
**47 valeurs mensuelles calculées**, toutes marquées `interpole` conformément à
l'ADR 0015, et tracées en pointillé sur toute la zone — pas seulement signalées
au survol.

## Ce que cette décision coûte

**La base 100 est une valeur calculée.** La date de référence de l'ADR 0009,
`2019-12`, tombe au milieu du trou. Sur `CP041`, qui pèse jusqu'à 175 ‰ au
premier quintile, l'ancrage de l'indice Observatoire repose donc sur une valeur
qu'aucune publication ne contient. C'est la conséquence la plus lourde de tout le
dossier, et elle doit figurer en tête de la section « Limites » de
`docs/METHODOLOGIE.md`.

**Le covid est linéarisé.** Une droite entre 2018 et 2022 suppose une évolution
régulière des loyers d'annonce, alors que la période a connu des mouvements réels
— desserrement urbain, gel des loyers dans les zones encadrées. Le sens de
l'erreur est inconnu.

## Alternatives écartées

- **Faire démarrer l'indice Observatoire en 2022** : zéro valeur fabriquée, mais
  l'indice ne dirait plus rien du choc énergétique de 2022 ni du covid, et il
  perdrait la comparaison depuis 2019 qui est le cadrage du projet.
- **IPCH avant 2022, source propre après** : rien d'inventé, mais deux sources de
  prix dans un même poste — interdit par l'ADR 0002 — et la rupture de 2022
  serait lue comme un mouvement de marché.
- **Base 100 de l'indice Observatoire en 2022** : évite d'ancrer un indice sur un
  chiffre calculé, mais les cinq courbes ne partiraient plus du même point, ce
  qui casse la lecture en éventail sur laquelle repose l'ADR 0013.
