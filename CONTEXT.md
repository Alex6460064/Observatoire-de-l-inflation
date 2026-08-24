# Observatoire de l'Inflation

Contexte unique. Le projet compare l'indice des prix officiel de l'INSEE, calculé
sur un panier moyen national, à ce même indice repondéré par la structure de
budget déclarée par un utilisateur. Il ne produit aucune mesure de prix propre.

## Language

**IPC officiel** :
L'indice des prix à la consommation publié par l'INSEE pour le panier moyen des
ménages français.
_Avoid_: inflation officielle, CPI, indice INSEE

**IPC repondéré** :
Les mêmes sous-indices de prix INSEE, recombinés avec les poids du budget déclaré
par l'utilisateur au lieu des poids du panier moyen national.
_Avoid_: inflation réelle, vraie inflation, inflation vécue

**Inflation réelle** : ⛔ TERME BANNI
Aucune définition opérationnelle dans ce projet. Le distinguer de l'IPC exigerait
de corriger la shrinkflation et l'ajustement hédonique, ce qui suppose une
collecte de prix propre que le projet ne fait pas. Interdit dans le code, la
documentation et l'interface. Les mécanismes qu'il désigne sont traités en prose
dans la section « Limites » de `docs/METHODOLOGIE.md`.

**Inflation ressentie** : ⛔ TERME BANNI comme taux
Ce que l'INSEE mesure est un solde d'opinion sans unité, pas un pourcentage. Ne
jamais l'exprimer en points de pourcentage ni le tracer sur le même axe qu'un
taux.

## Les indices

Le projet publie plusieurs indices distincts et étiquetés, jamais un chiffre
unique. Chaque indice se définit par un couple (source de prix, source de poids).

**Indice 0 — IPC officiel** :
Voir ci-dessus. Publié par l'INSEE, référence nationale.

**Indice 1 — IPCH** :
L'indice des prix harmonisé de la France publié par Eurostat, avec les poids
officiels d'Eurostat. Diffère de l'IPC officiel par son champ et sa méthode.
_Avoid_: HICP, indice européen

**Indice 2 — IPCH repondéré** :
Les prix de l'IPCH recombinés avec les poids du profil de ménage.

**Indice 3 — IPC repondéré** :
Les prix de l'IPC officiel recombinés avec les poids du profil de ménage.

**Indice 4 — Indice Observatoire** :
Notre indice propre, construit poste par poste à partir des sources les mieux
disponibles pour chacun, et recombiné avec les poids du profil de ménage. Seul
indice dont les prix ne viennent pas d'un institut statistique.
_Avoid_: indice maison, vrai indice, notre inflation

**Salaire mensuel de base (`salaire_smb`)** :
Courbe d'évolution du salaire nominal, superposée aux cinq indices pour en
visualiser la divergence. Source Dares (enquête Acemo), établissements privés
de 10 salariés ou plus, France hors Mayotte — **la fonction publique n'est pas
couverte**. Ce n'est pas un sixième indice de l'ADR 0002 : ni source de prix ni
poids de profil. Aucune déflation par un indice de prix en v1.
_Avoid_: salaire, salaires, pouvoir d'achat, salaire réel

## Le panier et les poids

**Poste** :
Une ligne du panier, identifiée par son code COICOP. Toujours désigné par son
code, jamais par un libellé libre.
_Avoid_: catégorie, rubrique, item

**Profil de ménage** :
Une combinaison de caractéristiques (niveau de vie, âge, type de ménage, commune)
à laquelle Eurostat associe une structure de consommation observée.
_Avoid_: persona, utilisateur type

**Poids de profil** :
Le vecteur de parts budgétaires, en pour mille, associé à un profil de ménage.
Issu de l'enquête Eurostat HBS, jamais saisi ni estimé.
_Avoid_: pondération perso, coefficients

**Poids national INSEE** :
Le panier officiel de l'IPC — 263 postes, poids sur 10 000, revu chaque année
par l'INSEE. Source distincte du poids de profil ci-dessus (Eurostat HBS) :
sert à expliquer *le panier de l'INSEE*, jamais mélangé avec les poids de
profil sous une même étiquette « panier ». N'entre dans aucun calcul des cinq
indices — affiché uniquement à des fins pédagogiques (page « panier INSEE »).
_Avoid_: panier INSEE (ambigu, préciser toujours « national » ou « de
profil »), pondération officielle

**Millésime des poids** :
L'année de collecte de l'enquête dont sortent les poids de profil — **2017**, et
non l'année d'étiquette de la vague européenne, qui vaut 2020 pour la France sans
qu'aucune collecte ait eu lieu cette année-là. Le millésime accompagne tout poids
affiché dans l'interface.
_Avoid_: année des poids, vague HBS

**Nomenclature** :
Le système de codes qui définit ce que contient un poste. Deux nomenclatures
coexistent dans le projet : ECOICOP v1, celle des poids HBS 2020, et COICOP 2018,
celle des prix. Un même code peut désigner deux contenus différents selon la
nomenclature ; un poste n'a donc jamais de sens sans elle.
_Avoid_: classification, référentiel

**Table de correspondance** :
La transposition d'un poste d'une nomenclature vers l'autre, adossée à la table
officielle UNSD/Eurostat. Elle dit **où va** un poste, jamais **combien** : elle
ne porte aucune part. Ce qu'elle établit est purement qualitatif.
_Avoid_: mapping, table de conversion

**Clé de répartition** :
Ce qui fournit les parts que la table de correspondance ne donne pas, quand un
poste se scinde. Elle est extérieure à la correspondance et doit être sourcée.
Les parts d'un même poste d'origine somment toujours à 1, si bien qu'une clé
inexacte redistribue à l'intérieur du poste sans en déformer le total.
_Avoid_: pondération de correspondance, coefficient de passage

**Unité de consommation** :
Le diviseur qui rend comparables les revenus de ménages de tailles différentes.
Un revenu de ménage n'est jamais comparé directement à un seuil de quintile.
_Avoid_: part, personne équivalente

**Seuil de quintile** :
Le revenu par unité de consommation qui sépare deux quintiles. Sert uniquement à
placer le visiteur ; il ne rentre dans aucun calcul d'indice.
_Avoid_: tranche, palier

**Qualité de source** :
Le niveau de traçabilité d'un chiffre, en trois crans, attaché à chaque poste de
l'indice 4 et affiché dans l'interface. Le cran ne dit pas si le chiffre est
juste, il dit ce qu'un tiers peut refaire ou vérifier.
- `api_ouverte` — un endpoint public rejouable donne le chiffre.
- `etude_publiee` — pas d'endpoint, mais un protocole publié : échantillon,
  période et méthode décrits, donc critiquables.
- `synthese_presse` — un chiffre repris d'un communiqué dont la méthode reste
  un secret commercial. Ni rejouable ni auditable.

**Date de référence** :
Le mois où toutes les courbes valent 100. Les évolutions affichées se lisent
toujours « depuis » cette date. C'est un paramètre de lecture, pas une propriété
de la donnée.
_Avoid_: année de base, base 100, point de départ

**Relevé manuel** :
Un chiffre issu d'une publication sans API, saisi dans `data/manual/releves.csv`
avec sa source complète. Jamais écrit dans le code.
_Avoid_: constante, valeur en dur
