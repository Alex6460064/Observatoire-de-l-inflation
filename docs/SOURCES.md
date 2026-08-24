# Sources de données

Toutes les entrées ci-dessous ont été testées le **21 août 2026**. Une source non
testée n'a pas sa place dans ce fichier, et une source absente de ce fichier n'a
pas le droit d'apparaître dans le code.

---

## INSEE — IPC officiel (indices 0 et 3)

**API BDM**, base `https://api.insee.fr/series/BDM/V1`

Testé sans clé d'API : réponse `200`, SDMX-ML. La fiche data.gouv qui annonce un
accès « Restreint » est périmée. L'ancien portail a fermé le 10 septembre 2025 ;
le portail courant est <https://portail-api.insee.fr/>. Limite annoncée :
30 appels / minute / IP.

Miroir observé, même charge utile : `https://www.bdm.insee.fr/series/sdmx/...`

### Changement de base 2025

Depuis les résultats de **janvier 2026**, l'IPC est publié en **base 2025**
(moyenne 100 en 2025) et en nomenclature **eCOICOP v2**. Les séries base 2015
sont arrêtées à `2025-12`. L'INSEE indique qu'il n'y a **ni table de
correspondance ni coefficient de raccordement** entre anciennes et nouvelles
références.

<https://blog.insee.fr/en-janvier-2026-l-indice-des-prix-fait-peau-neuve/>
<https://www.insee.fr/fr/statistiques/documentation/IPC-operations-changement-annee-2026.pdf>

Vérifié : les séries base 2025 sont **rétropolées jusqu'à 1996-01**. L'absence de
table de correspondance porte sur les références idbank, pas sur la profondeur
d'historique. Exemple mesuré, idbank `011814131` (Ensemble CVS) : 367
observations, `1996-01` à `2026-07`.

### Interroger par code COICOP plutôt que par idbank

Le dataflow `IPC-2025` porte une dimension `COICOP2018`, ce qui évite entièrement
la chasse aux idbanks.

```
GET https://api.insee.fr/series/BDM/V1/data/IPC-2025/M...045........
```

Douze champs de clé séparés par des points, sans quoi l'API renvoie `400 Not
enough key values in query, expecting 12 got 11`. Ordre des dimensions :

| pos | dimension | pos | dimension |
|---|---|---|---|
| 2 | `FREQ` | 8 | `MENAGES_IPC` |
| 3 | `INDICATEUR` | 9 | `REF_AREA` |
| 4 | `FORME-VENTE` | 10 | `UNIT_MEASURE` |
| 5 | `COICOP2018` | 11 | `CORRECTION` |
| 6 | `PRIX_CONSO` | 12 | `BASIND` |
| 7 | `NATURE` | 13 | `SERIE_ARRETEE` |

Filtrer sur `MENAGES_IPC=ENSEMBLE` et le `REF_AREA` France entière : la requête
ci-dessus renvoie trois séries, dont une « ménages urbains » et une « France
métropolitaine » dont nous ne voulons pas.

Dataflows disponibles : `IPC-2025`, `IPC-2015`, `IPCH-2025`, `IPCH-2015`,
`IPC-1998`, `IPC-1990`, `IPC-1970-1980`, `IPC-PM-2015`, `IPCH-2005`.

### Clé vérifiée pour l'indice 0 — IPC officiel, France entière, ensemble

Requête réelle, testée le 22/08/2026 (`collecte/insee.py`) :

```
GET https://api.insee.fr/series/BDM/V1/data/IPC-2025/M.IPC.SO.00.SO.INDICE.ENSEMBLE.FE.SO.BRUT.2025.FALSE
```

Cible une série unique, `IDBANK 011814630`. Codes de dimension confirmés en
inspectant la réponse (pas de codelist consultée séparément) :

| dimension | valeur | signifie |
|---|---|---|
| `COICOP2018` | `00` | total, tous postes |
| `PRIX_CONSO` | `SO` | hors loyers imputés (le code `00` sur cette dimension donne la variante « y compris loyers imputés », non publiée comme IPC officiel) |
| `MENAGES_IPC` | `ENSEMBLE` | tous ménages (`URBAIN` = ménages urbains ouvrier/employé, écarté) |
| `REF_AREA` | `FE` | France entière (`FM` = France métropolitaine, écarté) |

### Clé vérifiée pour l'indice 3 — prix INSEE par sous-classe COICOP2018

Testé le 22/08/2026, un appel par code, aucun wildcard possible sur la
dimension `COICOP2018` :

```
GET https://api.insee.fr/series/BDM/V1/data/IPC-2025/M.IPC.SO.<code>.SO.INDICE.ENSEMBLE.FE.SO.BRUT.2025.FALSE
```

| `<code>` testé | niveau | résultat |
|---|---|---|
| `011` | groupe (3 chiffres) | `IDBANK 011814676`, série unique, "01.1 Produits alimentaires" |
| `01111` | sous-classe (5 chiffres) | `IDBANK 011814691`, série unique, "01.1.1.1 Céréales (ND)" |

Chaque code renvoie exactement une série (`<Series>` unique dans la réponse) :
pas de wildcard sur cette dimension, donc **un appel par sous-classe**. La
transposition de poids cible le niveau sous-classe (`prc_hicp_iw`, 293 codes,
section suivante) : collecter l'indice 3 demande donc jusqu'à **293 appels**,
contre une limite de **30 appels/minute/IP** — prévoir un espacement dans la
collecte, pas un appel massif en boucle serrée.

### Pondération de l'IPC officiel — candidat pour la page « panier INSEE »

Recherche du 24/08/2026, pour documenter le panier national INSEE (263
postes, poids sur 10 000, revu chaque année) — distinct des poids de profil
Eurostat HBS de `poids.csv` (section suivante), jamais mélangés sous une
même étiquette.

Fiches trouvées sur insee.fr, ex. « Pondération de l'indice des prix à la
consommation - Base 2025 - Ensemble des ménages - France - Transports,
communications et hôtellerie », `IDBANK 011818239` — un identifiant par
poste/groupe, même famille de séries que l'IPC officiel ci-dessus.

**Appel test réel, le 24/08/2026 :**

```
GET https://api.insee.fr/series/BDM/V1/data/SERIES_BDM/011818239
```

Réponse `200`, SDMX-ML, sans clé d'API — endpoint générique par IDBANK,
plus simple que la clé à 12 dimensions de l'IPC officiel (pas besoin de
reconstruire `FREQ.INDICATEUR...`, l'IDBANK suffit). Confirmé :
`UNIT_MEASURE="P10000"` (poids sur 10 000, comme annoncé sur la fiche),
`FREQ="A"` (annuel), valeurs 2015→2026 identiques à celles affichées sur
`insee.fr/fr/statistiques/serie/011818239` (2019 = 2403, 2024 = 2489).

⚠️ **Un seul IDBANK vérifié pour l'instant** (le groupe « Transports,
communications et hôtellerie »). Il reste à retrouver l'IDBANK de chacun des
263 postes/groupes du panier — pas de wildcard testé sur `SERIES_BDM`, à
vérifier si un catalogue/recherche en masse existe côté INSEE avant de
partir sur 263 appels un par un. `# TODO: collecte complète non faite —
session dédiée, voir docs/METHODOLOGIE.md 4.2 ter.`

Licence : même statut que l'IPC officiel ci-dessus (même producteur, même
API), pas revérifiée séparément — à confirmer à la collecte complète.

---

## Eurostat — prix (indices 1, 2 et 4)

API REST, base
`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/`,
format JSON-stat, sans clé.

| dataset | contenu | dimension produit | couverture |
|---|---|---|---|
| `prc_hicp_minr` | IPCH mensuel, indices et taux | `coicop18`, 555 codes | `1996-01` → `2026-07` |
| `prc_hicp_iw` | poids officiels IPCH | `coicop18` | 1996 → 2026 |
| `prc_hpi_ooq` | coût du logement des occupants | `expend`, 11 codes | → `2026-Q1` |

`prc_hicp_minr` unités : `I15` (indice base 2015=100), et les taux de variation.
`prc_hpi_ooq` unités : `I15_Q`, `I25_Q`, `RCH_Q`, `RCH_A`.

Attention : les datasets `prc_hicp_midx`, `prc_hicp_manr` et `prc_hicp_inw`
appartiennent à la génération **ECOICOP v1** et s'arrêtent à `2025-12`. Utiliser
la génération v2 (`prc_hicp_minr`, `prc_hicp_ainr`, `prc_hicp_iw`).

Couverture `prc_hicp_minr` re-sondée le 21/08/2026 : France, `TOTAL`, `I15`,
**367 observations de `1996-01` à `2026-07`**, `1996-01 = 74,13`,
`2019-12 = 105,78`, `2026-07 = 128,17`. La génération v2 porte donc tout
l'historique recalculé en COICOP 2018 ; passer en v2 ne coûte aucune profondeur.

Valeurs relevées le 21/08/2026, France, base 2015=100 :

| poste | 2019-12 | 2026-03 | évolution |
|---|---|---|---|
| `TOTAL` | 105,78 | 126,17 | +19,3 % |
| `CP01` alimentation | 107,01 | 136,31 | +27,4 % |
| `CP041` loyers réels | 100,95 | 111,22 | +10,2 % |
| `CP045` énergie logement | 113,39 | 165,12 | +45,6 % |

### Couverture par sous-classe COICOP 2018 — vérifiée le 23/08/2026 (ticket 01, indice 2)

Requête multi-codes vérifiée en direct : `coicop18` accepte plusieurs codes en
répétant le paramètre dans l'URL (`coicop18=CP01111&coicop18=CP01112&...`),
pas de syntaxe `+`-joint (testée, renvoie 0 résultat). Contrairement à l'API
BDM INSEE, les codes doivent porter le préfixe `CP` (`CP01111`, pas `01111`)
— un appel avec code nu renvoie une dimension vide. Un seul appel pour les
296 postes de `poids.csv` fonctionne (URL de 5172 caractères, HTTP 200).

Sur les 296 postes, comparé à `sinceTimePeriod=2019-12` (REFERENCE, ADR
0009) :

- **62 postes** n'ont pas d'historique complet côté INSEE à REFERENCE (52
  totalement absents de l'API BDM, 10 dont la série démarre après
  2019-12) — vérifié poste par poste en direct le 23/08/2026.
- **66 postes** n'ont pas d'historique complet côté Eurostat
  `prc_hicp_minr` à REFERENCE (7 codes sans aucune série, 47 codes
  structurellement déclarés par l'API mais sans observation dans la
  fenêtre demandée, 12 dont la série démarre après 2019-12).
- Les 62 trous INSEE sont un **sous-ensemble strict** des 66 trous
  Eurostat. Quatre postes supplémentaires manquent seulement côté
  Eurostat : `CP04210` et `CP04220` (loyers imputés, voir ci-dessous),
  `CP06133` (démarre 2020-01, un mois après REFERENCE), `CP09470`
  (Eurostat n'a que 8 observations, 2025-12 → 2026-07 ; INSEE a
  l'historique complet pour ce poste).
- **CP042 (loyers imputés, commit `f348f9e`)** : les deux sous-classes
  cibles `CP04210` et `CP04220` sont confirmées absentes de
  `prc_hicp_minr` — cohérent avec l'exclusion structurelle des loyers
  imputés du champ HICP, et avec l'absence déjà documentée côté INSEE
  (substitution par le groupe `041`, voir
  `src/observatoire/collecte/insee.py`).

⚠️ Cette vérification a mis en évidence que `data/processed/prix.csv`
local était **périmé** au moment du contrôle (généré avant la dernière
renormalisation de `poids.csv`, commit `859b2d4`) : deux postes marqués
absents dans ce fichier (`CP09470`, `CP09800`) ont en réalité un
historique complet en direct sur l'API INSEE. Les chiffres ci-dessus
viennent d'appels API réels, pas de `prix.csv` — mais le pipeline doit
être rejoué avant de considérer `prix.csv` à jour pour l'indice 3.

---

## Eurostat HBS — poids de profil

Enquête budget des familles, **quinquennale, dernière vague 2020**. Unité `PM`
(pour mille). 150 codes COICOP. Mise à jour du 22/10/2025.

| dataset | axe | dimension | modalités FR |
|---|---|---|---|
| `hbs_str_t223` | niveau de vie | `quant_inc` | `QU1`…`QU5` |
| `hbs_str_t224` | composition | `hhcomp` | `A1`, `A1_DCH`, `A2`, `A2_DCH`, `A_GE3`, `A_GE3_DCH` |
| `hbs_str_t225` | âge | `age` | `Y_LT30`, `Y30-44`, `Y45-59`, `Y_GE60` |
| `hbs_str_t226` | commune | `deg_urb` | `DEG1`, `DEG2`, `DEG3` |
| `hbs_str_t227` | source de revenu | `incsrc` | `PRIM`, `SEC` |

**Ce sont des tables marginales. Aucun croisement n'est publié.** Voir
`docs/adr/0006-un-axe-de-profil-officiel-puis-ajustement-declare.md`.

### Requête vérifiée — `hbs_str_t223`, axe quintile

Testé le 22/08/2026 :

```
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/hbs_str_t223?format=JSON&geo=FR&time=2020&unit=PM
```

`200`, JSON-stat. Dimension `coicop` : 150 codes en nomenclature **ECOICOP v1**
(`CP01` à `CP127`, groupes et sous-niveaux mélangés — cohérent avec la mise en
garde plus bas sur la transposition). Dimension `quant_inc` : `QU1` à `QU5`
plus `UNK`, **les cinq quintiles arrivent dans le même appel**, pas un par
modalité.

⚠️ Chaque valeur porte `"status": "e"` (*estimated*) sur l'intégralité des
points FR — cohérent avec le mécanisme documenté plus bas (vague 2020 FR = 2015
reconverti par coefficient IPCH, jamais une collecte 2020).

### ⚠️ La « vague 2020 » française n'est pas une collecte 2020

Vérifié le 21/08/2026. Métadonnées Eurostat HBS, section 3.1 :

> *The Cyprus, France and Malta Household Budget Survey Data for the year 2020,
> have been produced by converting the Cyprus, France and Malta Household Budget
> Survey Data for the year **2015** to 2020 Reference Year prices using the 2020
> HICP coefficient.*

<https://ec.europa.eu/eurostat/cache/metadata/en/hbs_esms.htm>

Confirmé sur les données : les **47 poids de groupe français sont identiques au
pour mille près entre 2015 et 2020**, écart maximum 0. La revalorisation par
coefficient IPCH agit sur les montants en euros, pas sur les parts.

```
code     2010   2015   2020
CP011     147    132    132
CP041      61     64     64
CP042     134    150    150
CP045      42     43     43
CP072      60     53     53
CP125      65     73     73
```

Côté français, l'enquête Budget de famille est quinquennale et ses millésimes
sont **2006, 2011, 2017, puis 2026** — <https://www.insee.fr/fr/metadonnees/source/serie/s1194>.
Il n'existe **ni millésime 2015 ni millésime 2020**. La structure de budget
utilisée par le projet remonte donc à BdF 2017 ou BdF 2011.

**Le millésime sous-jacent est BdF 2017.** Tranché le 21/08/2026 par le nombre
de ménages enquêtés, publié des deux côtés.

Eurostat, `hbs_car_t315`, dimension `hhcaract=NR`, France :

```
2010   15 797 ménages
2015   16 978
2020   16 978      copie exacte de 2015
```

INSEE, côté français :

| enquête | répondants | collecte | source |
|---|---|---|---|
| BdF 2011 | 10 342 métropole + 5 355 Dom (Mayotte incluse) = **15 697** | octobre 2010 → septembre 2011 | <https://www.insee.fr/fr/metadonnees/source/operation/s1340/processus-statistique> |
| BdF 2017 | 12 000 métropole + 3 900 Dom **hors Mayotte** = 15 900 | **octobre 2016 → octobre 2017** | <https://www.insee.fr/fr/statistiques/4127596> |

`15 697` contre `15 797` : 0,6 % d'écart sur la vague 2010. Pour 2015, l'écart de
1 078 ménages correspond à Mayotte, que l'INSEE enquête « avec un décalage d'un
an » (<https://www.insee.fr/fr/metadonnees/source/operation/s1341/processus-statistique>).
Les deux vagues s'emboîtent.

Échantillon initial de BdF 2017 : « environ 20 700 logements en France
métropolitaine, et 8 000 dans les Dom », plus un sur-échantillon de 2 000 ménages
monoparentaux tiré des fichiers CAF.

**Conséquences.**

1. La collecte s'achève en **octobre 2017**, deux ans et demi avant les
   confinements. La question de leur effet sur la vague est sans objet.
2. Le décalage entre la fin de collecte et la date de référence de l'ADR 0009
   (décembre 2019) est de **2 ans et 2 mois** — ordinaire pour un indice de
   Laspeyres, et non huit ans.
3. Le millésime est vérifié, donc **affichable dans l'interface**.

L'ADR 0007 est amendé en conséquence : son titre parlait de « poids HBS 2020 »,
ce qui était faux.

La prochaine vague est annoncée pour 2026 des deux côtés — Eurostat
(« Next reference year is 2026 ») et INSEE, qui aligne BdF sur les vagues
européennes.

### ⚠️ HBS est en ECOICOP v1, l'IPCH courant en COICOP 2018

Corrigé le 21/08/2026. Une version antérieure de ce fichier affirmait que « 41
des 47 groupes joignent nativement » et que les six manquants étaient légers hors
`CP042`. **Les deux affirmations étaient fausses** : elles comparaient des chaînes
de caractères, pas des contenus.

Mesuré sur les 47 groupes à trois chiffres, poids QU1 FR 2020 :

| | groupes | poids QU1 |
|---|---|---|
| libellé identique | 21 | 526 ‰ |
| libellé divergent | 20 | 199 ‰ |
| absent de l'IPCH v2 | 6 | 268 ‰ |

Une vingtaine des divergences sont des renommages (`CP073` *Transport services* →
*Passenger transport services*), mais **~111 ‰ changent de contenu** :

| code | poids QU1 | HBS (ECOICOP v1) | IPCH v2 (COICOP 2018) |
|---|---|---|---|
| `CP121` | 37 ‰ | Personal care | **Insurance** |
| `CP083` | 22 ‰ | Téléphone, services | Information and communication services |
| `CP093` | 18 ‰ | Loisirs, jardin | Garden products and pets |
| `CP022` | 14 ‰ | Tobacco | Alcohol production services |
| `CP023` | 0 ‰ | Narcotics | Tobacco |

Divisions renommées : `CP08` *Communications* → *Information and communication* ;
`CP09` → *Recreation, sport and culture* ; `CP12` *Miscellaneous goods and
services* → **Insurance and financial services** ; apparition d'un `CP13`.

**Les six groupes « manquants » ne manquent pas — ils ont été renumérotés :**

| HBS v1 | poids QU1 | COICOP 2018 |
|---|---|---|
| `CP121` Personal care | 37 ‰ | `CP131` Personal care |
| `CP123` Personal effects n.e.c. | 3 ‰ | `CP132` Other personal effects |
| `CP124` Social protection | 6 ‰ | `CP133` Social protection |
| `CP125` Insurance | 82 ‰ | `CP121` Insurance |
| `CP126` Financial services n.e.c. | 5 ‰ | `CP122` Financial services |
| `CP127` Other services n.e.c. | 18 ‰ | `CP139` Other services |

`CP042` reste le seul trou réel, traité par
`docs/adr/0005-equivalent-loyer-pour-les-loyers-imputes.md`. La transposition est
décidée par
`docs/adr/0010-transposer-les-poids-hbs-en-coicop-2018.md`.

### Table de correspondance officielle — ✅ vérifiée le 21/08/2026

Correspondance COICOP 2018 ↔ COICOP 1999, produite par l'UNSD en partenariat avec
Eurostat. **Fichier tabulaire récupéré et lu.**

<https://unstats.un.org/unsd/classifications/Econ/Download/COICOP2018_COICOP1999_correspondence_table_final.xlsx>

180 Ko, cinq feuilles. La feuille utile est `Correspondence 2018-1999` : 690
lignes, colonnes `COICOP 2018 Code | COICOP 2018 Title | COICOP 1999 Code |
COICOP 1999 Title | Note/common content`. 458 lignes portent un couple de codes
renseigné des deux côtés, dont 424 au niveau sous-classe 2018 (quatre segments,
`01.1.1.1`).

**La table ne porte aucune colonne de part.** Elle dit où va un poste, jamais
combien. Toute clé de répartition doit donc venir d'ailleurs — voir
`docs/adr/0018-cle-de-repartition-de-la-transposition.md`.

La note de couverture (9 octobre 2024) documente la typologie GSIM des
changements (`RC1` suppression, `RC3.1` fusion, `RC4.1` éclatement, `RC5`
transfert). Elle est en PDF et **n'est pas lisible par les outils de la
session** ; elle n'est pas nécessaire, la feuille tabulaire suffit.
<https://unstats.un.org/unsd/classifications/Econ/Download/Cover_note_COICOP2018_COICOP1999_correspondence_final.pdf>

Catalogue UNSD : <https://unstats.un.org/unsd/classifications/Econ>

Eurostat renvoie vers ShowVoc pour la correspondance ECOICOP ↔ ECOICOP ver. 2.
**L'endpoint SPARQL de ShowVoc est bloqué** par le filtre web de la Commission
(`Access Denied ... st-core-services/SPARQL/evaluateQuery`) ; seul
`Projects/listProjects` répond. La table UNSD la remplace : Eurostat déclare
ECOICOP ver. 2 identique à COICOP 2018 jusqu'au niveau à 5 chiffres.

#### Ampleur mesurée de la transposition

HBS FR 2020 n'est renseigné qu'au **niveau groupe** (trois chiffres) : 47 groupes,
somme exactement 1000 ‰. Confrontés à la correspondance :

| | QU1 | QU3 | QU5 |
|---|---|---|---|
| code identique | 436 ‰ | 427 ‰ | 417 ‰ |
| renommage pur (1 → 1) | 83 ‰ | 94 ‰ | 82 ‰ |
| **éclatement (1 → n)** | **474 ‰** | **472 ‰** | **482 ‰** |

Une partition fermée sous la correspondance — qui éviterait tout découpage — a été
recherchée et **n'existe pas** : les transferts s'enchaînent et 34 groupes 1999
s'agglomèrent en un unique bloc de 576 ‰ (QU3). Piste écartée sur mesure.

Les quatre postes de l'indice Observatoire (ADR 0014) sont épargnés :

```
CP041   0 sortie   0 entrée                        bijectif
CP045   0 sortie   0 entrée                        bijectif
CP01    0 sortie   2 entrées vers 01.3.0.0         poids IPCH FR 2020 = 0,0 ‰
CP072   0 sortie   2 entrées vers 07.2.1.3         3,7 ‰
```

Résidu irréductible : **41 sous-classes 2018 ont plusieurs sources 1999**, soit
148 ‰ du poids IPCH France. La plus lourde est `11.1.1.1` restauration, 57,1 ‰,
alimentée à la fois par `02.2` et `11.1`. Aucune source ne dit dans quelle
proportion.

### ECOICOP v1 est gelé — la transposition n'est pas optionnelle

Mesuré le 21/08/2026 sur `prc_hicp_midx` : le dataset s'intitule désormais
**« HICP - monthly data (index) (1996-2025) »**, dernière observation `2025-12`,
mise à jour du 06/02/2026. Le dossier `prc_hicp_ecoicop2` prend le relais et
couvre `1996-01` → `2026-07` (`prc_hicp_minr`). Rester en ECOICOP v1 pour éviter
la transposition n'est donc plus possible.

### `prc_hicp_iw` — poids d'articles IPCH ECOICOP ver. 2

Clé de répartition retenue par l'ADR 0018. Même API Eurostat, sans clé.
Couverture 1996 → 2026, mise à jour du 18/07/2026.

Dimension `coicop18` (et non `coicop`), dimension `statinfo` à modalité unique
`IW`. Testé sur `geo=FR&time=2020` : 553 codes renseignés sur 559. La somme vaut
**1000 ‰ à chaque niveau** — 13 divisions, 50 groupes, 142 classes, 293
sous-classes — ce qui permet une répartition exacte au niveau de la
sous-classe.

```
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_iw?format=JSON&geo=FR&time=2020
```

⚠️ Piège : les codes `CP0111` (six caractères) sont des **classes**, les codes
`CP01111` (sept caractères) des **sous-classes**. Un filtre sur la mauvaise
longueur renvoie un vecteur vide sans erreur.

⚠️ Périmètre : l'IPCH exclut les loyers imputés. Confronté aux 47 groupes HBS,
**`CP042` est le seul groupe sans aucun poids IPCH atteignable** — 69 ‰ QU1,
154 ‰ QU3, 169 ‰ QU5. Les trois autres groupes sans contrepartie (`CP023`,
`CP103`, `CP122`) pèsent 0 ‰ en France. Traitement par l'ADR 0005.

### `hbs_str_t211` — structure HBS nationale

*Structure of consumption expenditure by COICOP consumption purpose*, sans axe de
ventilation. Testé `geo=FR&time=2020&unit=PM` : 47 groupes, somme 991 ‰.
Sert de dénominateur au ratio quintile/national, mesuré mais **non retenu** comme
méthode de transposition (ADR 0018).

Valeurs relevées, FR 2020, pour mille :

| poste | QU1 | QU3 | QU5 |
|---|---|---|---|
| `CP01` alimentation | 147 | 154 | 128 |
| `CP04` logement total | 347 | 305 | 255 |
| `CP041` loyers réels | 175 | 71 | 25 |
| `CP042` loyers imputés | 69 | 154 | 169 |
| `CP045` énergie logement | 55 | 46 | 36 |
| `CP07` transport | 102 | 121 | 149 |

Somme des douze divisions vérifiée à 1000 ‰ exactement.

---

## Eurostat EU-SILC — seuils de quintile

`ilc_di01` — *Distribution of income by quantiles*. Même API que les autres
datasets Eurostat, sans clé. Couverture 1995 → 2025.

**Échelle d'équivalence : OCDE modifiée.** Vérifiée le 21/08/2026 sur le
glossaire Eurostat, qui la définit mot pour mot :

> *this scale gives a weight to all members of the household [...] : 1.0 to the
> first adult; 0.5 to the second and each subsequent person aged 14 and over;
> 0.3 to each child aged under 14.*

<https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Glossary:Equivalised_disposable_income>

Le revenu de référence est le **revenu disponible après impôts et cotisations**,
sur une période fixe de douze mois — l'année civile ou fiscale précédente pour la
France. C'est cette définition que doit reprendre le formulaire de placement en
quintile (ADR 0012) : demander un revenu net après impôt, pas un salaire brut.

Dimension `statinfo` : `TC` (*Top cut-off point*) et `SHARE`. Unités `EUR`, `NAC`,
`PPS`. La dimension `quant_inc` mélange quartiles (`Q1`…`Q4`), quintiles
(`QU1`…`QU4`) et déciles — filtrer explicitement.

Relevé le 21/08/2026, France, `TC`, `EUR`, 2025 — **revenu équivalisé** :

| quintile | seuil haut €/an | €/mois |
|---|---|---|
| `QU1` | 17 304 | 1 442 |
| `QU2` | 23 445 | 1 954 |
| `QU3` | 29 571 | 2 464 |
| `QU4` | 38 723 | 3 227 |

⚠️ **Non vérifié** : l'échelle d'équivalence exacte employée par EU-SILC
(vraisemblablement OCDE modifiée, 1 / 0,5 / 0,3). À confirmer sur la fiche de
métadonnées du dataset avant tout calcul d'unités de consommation.

⚠️ Ces seuils viennent d'EU-SILC, les poids de HBS. Approximation assumée, voir
`docs/adr/0012-placer-le-visiteur-dans-un-quintile.md`.

## Carburants — indice Observatoire

<https://www.prix-carburants.gouv.fr/rubrique/opendata/> — Licence Ouverte.
Prix relevés par station, tous carburants (Gazole, SP95, SP98, E10, E85, GPLc).

| flux | URL |
|---|---|
| instantané | `https://donnees.roulez-eco.fr/opendata/instantane` |
| quotidien | `https://donnees.roulez-eco.fr/opendata/jour` |
| stock annuel | `https://donnees.roulez-eco.fr/opendata/annee` |

**Testés le 21/08/2026 :** les trois flux renvoient `200`, `application/zip` —
instantané 0,95 Mo, quotidien 1,1 Mo, annuel 24,7 Mo.

**Les archives par année existent**, non documentées sur la page open data :
`https://donnees.roulez-eco.fr/opendata/annee/2019` renvoie
`PrixCarburants_annuel_2019.xml`, **302 Mo décompressés**. Vérifié aussi pour
2024. Huit millésimes 2019→2026 ≈ 2,4 Go de XML.

⚠️ Ce n'est **pas une série** : chaque `<prix>` est un changement de prix daté,
station par station.

```xml
<pdv id="1000001" cp="01000" pop="R">
  <prix nom="Gazole" id="1" maj="2019-01-04T10:53:48" valeur="1328"/>
```

⚠️ **Le format de `valeur` change de millésime, découvert et vérifié le
23/08/2026** en comparant les huit archives locales : 2019-2021 en millième
d'euro, entier sans séparateur décimal (`"1328"` = 1,328 €) ; 2022-2026 déjà
en euros, avec point décimal (`"1.572"` = 1,572 €). Aucun mélange à
l'intérieur d'un même millésime (vérifié sur l'intégralité de 2019, 2020,
2021, 2022, 2026 — seule exception : ~0,04 % de valeurs aberrantes du type
`"1"`/`"2"` en 2022+, déjà incohérentes économiquement). Un bug de pipeline
divisait uniformément par 1000, ce qui effondrait `CP072` à ~0,1 % de sa
valeur réelle sur 2022+ et biaisait fortement l'indice Observatoire à la
baisse sur cette période — corrigé le 23/08/2026, `collecte.carburants`
détecte le format par présence d'un point décimal, valeur par valeur.

Construire une moyenne mensuelle nationale impose de propager le dernier prix
connu de chaque station sur chaque jour, puis d'agréger.

⚠️ **Aucun volume de vente n'est publié** : la pondération ne peut être que par
station, ce qui donne le même poids à une station d'autoroute et à un
hypermarché.

`data.economie.gouv.fr` : seuls les flux quotidien et instantané y sont exposés
(`prix-carburants-quotidien`, 74 770 enregistrements). **Aucun historique.**

### Mix gazole / essences (ADR 0023) — UFIP/CPDP, vérifié le 23/08/2026

`nom="E10"` dans le XML = SP95-E10, le mix retenu pour représenter
l'ensemble des essences (`SP95` sans éthanol, `SP98`, `E85` non séparés,
`data/manual/parametres.csv`). Parts sourcées, dépêche AFP citant le bilan
2025 de l'Union française des industries pétrolières (Ufip), via le Comité
professionnel du pétrole (CPDP) :

<https://www.connaissancedesenergies.org/afp/la-consommation-francaise-de-carburants-en-baisse-en-2025-le-diesel-en-recul-mais-toujours-dominant-260115>

Citations exactes, vérifiées mot pour mot le 23/08/2026 :

> les livraisons de gazole ont baissé de 3,4% pour atteindre 32 millions de m3

> La part du gazole dans la consommation française de carburants routiers
> reste toutefois prépondérante, avec 67,3% à fin 2025

> les livraisons fléchissant de 0,6% par rapport à 2024, avec 47,5 millions
> de mètres cubes

Soit **67,3 % gazole / 32,7 % essences** (32,0 / 47,5 Mm³). Le communiqué
UFIP original (`energiesetmobilites.fr`) n'a pas été localisé sous une URL
stable citable — la dépêche AFP ci-dessus est la source retenue.

---

## CRE — tarif réglementé de vente d'électricité (indice 4, `CP045`)

Testé le 21/08/2026. Publié par la Commission de régulation de l'énergie sur
data.gouv, jeu « Historique des tarifs réglementés de vente d'électricité pour
les consommateurs résidentiels », mis à jour le 04/02/2026.

<https://www.data.gouv.fr/datasets/historique-des-tarifs-reglementes-de-vente-delectricite-pour-les-consommateurs-residentiels>

| option | URL |
|---|---|
| Base | `https://www.cre.fr/fileadmin/Documents/Open_data/Marches_de_detail/Option_Base.csv` |
| Heures pleines / creuses | `.../Option_HPHC.csv` |
| Tempo | `.../Option_Tempo.csv` |
| Notice | `.../Notice.txt` |

`Option_Base.csv` : `200`, 5,8 Ko, **111 lignes, 23/07/2012 → 01/02/2026**.
Séparateur `;`, décimale virgule, dates `JJ/MM/AAAA`.

```
DATE_DEBUT;DATE_FIN;P_SOUSCRITE;PART_FIXE_HT;PART_FIXE_TTC;PART_VARIABLE_HT;PART_VARIABLE_TTC
01/02/2026;;9;176,16;235,9;0,1297;0,19266
```

⚠️ C'est un **barème**, pas un prix : `abonnement + kWh × consommation`. En faire
un indice suppose un profil de consommation, à sourcer ou à déclarer. Ne couvre
que les ménages restés au tarif réglementé.

Licence déclarée `notspecified` sur data.gouv. **Ce n'est pas un blocage** —
voir la section « Régime des licences » en fin de fichier. Producteur badgé
`public-service` et `certified`.

**Gaz** : les jeux CRE équivalents existent mais sont arrêtés à 2024, cohérent
avec la suppression du TRV gaz en juillet 2023. Le « prix repère » qui l'a
remplacé n'est pas sur data.gouv. Poste non couvert pour l'instant.

---

## Carte des loyers — indice 4, `CP041`

Testé le 21/08/2026. Ministère de la Transition écologique, « Indicateurs de
loyers d'annonce par commune ». Loyer prédit au m², par commune, avec intervalle
de confiance.

Millésimes publiés : **2018, 2022, 2023, 2024, 2025**. ⚠️ **Trou sur 2019, 2020 et
2021**, juste après la date de référence de l'ADR 0009.

<https://www.data.gouv.fr/datasets/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025>

`pred-app-mef-dhup.csv` (2025) : `200`, 4,8 Mo, **34 901 lignes**. Séparateur `;`,
décimale virgule. Quatre fichiers par millésime : appartements, appartements 1 ou
2 pièces, appartements 3 pièces et plus, maisons.

```
"id_zone";"INSEE_C";"LIBGEO";"EPCI";"DEP";"REG";"loypredm2";"lwr.IPm2";"upr.IPm2";"TYPPRED";"nbobs_com";"nbobs_mail";"R2_adj"
```

Licences : `lov2` pour 2018, 2022 et 2023 ; `notspecified` pour 2024 et 2025.
Même producteur, même série : oubli de métadonnée, pas changement de droits. Voir
la section « Régime des licences » en fin de fichier.

⚠️ **Loyers d'annonce, pas loyers payés.** Mesure le prix demandé pour un logement
remis sur le marché ; l'IPCH `CP041` mesure le loyer de l'ensemble du parc,
locataires en place compris. L'écart est une différence de champ, flux contre
stock. Voir `docs/adr/0014-perimetre-de-l-indice-observatoire-en-v1.md`.

### URLs de téléchargement direct, fichier appartements — vérifiées le 23/08/2026

Un jeu de données data.gouv.fr distinct par millésime (le slug se termine par
l'année). Chaque URL testée en direct (`curl`, code `200`), voir
`collecte/carte_des_loyers.py::URLS_APPARTEMENTS` (ADR 0023) :

| millésime | URL |
|---|---|
| 2018 | `https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2018/20201203-114600/indicateurs-loyers-appartements.csv` |
| 2022 | `https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2022/20221216-153948/pred-app-mef-dhup.csv` |
| 2023 | `https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2023/20240115-134743/pred-app-mef-dhup.csv` |
| 2024 | `https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2024/20241205-153050/pred-app-mef-dhup.csv` |
| 2025 | `https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/20251211-145010/pred-app-mef-dhup.csv` |

⚠️ **Deux schémas de colonnes.** 2018 : en-têtes non guillemetés, colonne
commune `INSEE`, ordre différent. 2022-2025 : en-têtes guillemetés, colonne
commune `INSEE_C`, une colonne `EPCI` de plus. Les deux fichiers sont en
**encodage latin-1** (vérifié en direct : `é` casse en UTF-8), jamais UTF-8,
malgré l'absence de mention d'encodage sur la page data.gouv.

### Pondération du parc locatif communal — ✅ identifiée le 21/08/2026

Agréger les 34 901 communes exige une pondération par le parc locatif. La source
est le recensement INSEE, base communale « Logement en 2022 » :

<https://www.insee.fr/fr/statistiques/fichier/8581474/base-cc-logement-2022_csv.zip>

41 Mo compressés, séparateur `;`, encodage **latin-1**, 34 903 communes,
265 colonnes. Un fichier `meta_base-cc-logement-2022.CSV` accompagne les données
et donne le libellé de chaque variable.

| variable | libellé officiel |
|---|---|
| `CODGEO` | code commune — joint sur `INSEE_C` de la Carte des loyers |
| `P22_RP` | nombre de résidences principales en 2022 |
| `P22_RP_LOC` | résidences principales occupées par locataires |
| `P22_RP_LOCHLMV` | dont HLM loué vide |

Le parc à retenir est le **locatif privé**, champ de la Carte des loyers, soit
`P22_RP_LOC - P22_RP_LOCHLMV`. Totaux France mesurés :

```
résidences principales   32 699 970
locataires               13 539 006
  dont HLM                4 819 730
locatif privé             8 719 277
```

Les millésimes 2011 et 2016 sont dans le même fichier (`P11_`, `P16_`), ce qui
permet de faire varier la pondération dans le temps si besoin.

⚠️ **Limite connue.** `loypredm2` est un prix au mètre carré. Une agrégation
rigoureuse pondérerait par la **surface louée**, pas par le nombre de logements.
La base ne publie aucune variable de surface — seulement un nombre de pièces
(`P22_RP_1P` à `P22_RP_5P`), et non ventilé par statut d'occupation. La
pondération par nombre de logements sous-pondère donc les communes à grands
logements. À écrire dans les limites.

---

## ARCEP — indice des prix des communications électroniques (indice 4, `CP08`)

Testé le 22/08/2026. Publication annuelle de l'Arcep (autorité de régulation,
**pas un institut statistique** — validé comme source indice 4 le 22/08/2026),
« Évolution des prix des services de communications électroniques ». PDF récupéré
et lu en entier.

<https://www.arcep.fr/cartes-et-donnees/nos-publications-chiffrees/marches-des-communications-electroniques-en-france-enquetes-trimestrielles-et-annuelles/indice-des-prix-des-services-fixes-et-mobiles.html>

Dernière édition : `evolution-prix-services-fixes-mobiles-2025_mai2026.pdf`,
28/05/2026, 1,2 Mo. Méthodologie « inspirée de celle de l'Insee », mais
**sans ajustement hédonique** : la qualité (débit, techno) est traitée par
**segmentation** — DSL et fibre restent deux profils de prix distincts, jamais
mélangés dans une régression — et non par correction d'un indice unique.

### Deux indices publiés, à ne pas confondre

- **Indice des prix** — évolution du prix des offres catalogue, usages et
  structure de clientèle neutralisés. **C'est celui retenu pour `CP08`.**
- **Indice de dépense minimale** — inclut usages et structure clientèle, mis à
  jour chaque janvier. Pas un indice de prix pur. **Ne jamais l'utiliser comme
  substitut de `CP08`.**

Base 100 : janvier 2012 (services fixes), janvier 2010 (services mobiles).
Valeurs relevées le 22/08/2026, indice des prix en moyenne annuelle :

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Fixe, ensemble | 79,6 | 81,1 | 82,3 | 77,8 | 74,6 |
| Mobile, ensemble des forfaits | 45,7 | 45,4 | 42,5 | 35,5 | 32,6 |

### Panel, pas un scraping indépendant

Données transmises par **4 opérateurs seulement** (Bouygues Telecom, Free,
Orange, SFR) sous obligation réglementaire (décision Arcep n° 2025-0429), plus
les MVNO de plus d'un million de clients pour le mobile. Clients professionnels
et Outre-mer exclus.

⚠️ **Les prix par offre ne sont jamais publiés.** Confidentiels, transmis par
les opérateurs. Seuls les indices agrégés sortent, en PDF : un tableau annuel
(2021→2025 dans l'édition 2025) et des graphiques avec valeurs ponctuelles
étiquetées année par année — pas une série mensuelle exploitable en l'état.

### Licence — régime différent des autres sources publiques

Vérifié le 22/08/2026 sur `arcep.fr/mentions-legales.html`. **Pas de Licence
Ouverte.** Citation exacte :

> Les informations présentées sur ce site sont des données publiques qui ne
> peuvent être utilisées à des fins commerciales ou publicitaires.

Réutilisation permise si intégrité respectée, source et date citées, lien
retour vers l'original. Régime plus restrictif que la Licence Ouverte (qui
autorise l'usage commercial) et différent du régime par défaut L322-1 CRPA
documenté plus bas pour la CRE et la Carte des loyers. Compatible avec le
projet (non commercial), mais **à ne pas généraliser aux autres sources** sans
vérification individuelle.

### Qualité et limites, pour `docs/METHODOLOGIE.md`

Qualité `etude_publiee` : protocole publié, échantillon et méthode décrits,
mais **pas rejouable** — panel fermé aux 4 opérateurs, données brutes non
publiques. Relevé restera manuel, un point par an, comme Familles Rurales.

⚠️ Substitue le sous-indice `CP08` de l'INSEE ; garde les poids HBS inchangés.
Étendre le périmètre de l'indice Observatoire (ADR 0014, 4 postes en v1) à un
cinquième poste `CP08` reste **une décision d'architecture séparée**, pas
tranchée par ce test de source — à formaliser dans un ADR si retenu.

---

## Alimentation `CP01` — Familles Rurales, Observatoire des prix

> Cette section remplace un passage intitulé « Alimentation — aucune source
> ouverte trouvée », **devenu faux le 21/08/2026**. Il concluait qu'aucune source
> alimentaire n'existait hors panels commerciaux. Trois existent ; elles
> n'étaient pas cherchées au bon endroit. Voir l'ADR 0019.

Source retenue pour `CP01` dans l'indice Observatoire. Qualité **`etude_publiee`**
au sens de `CONTEXT.md` : pas d'API, mais un protocole publié, décrit, critiquable.

<https://www.famillesrurales.org/observatoire-des-prix-2021>

Familles Rurales est une association de défense des consommateurs. Son
Observatoire des prix de grande consommation en est à sa **20ᵉ édition**
(l'édition 2021 s'annonce elle-même comme la 15ᵉ consécutive). Chaque édition
paraît en dossier de presse PDF, téléchargeable sans compte.

### Protocole, relevé dans les PDF eux-mêmes

Fiche méthodologique de l'édition 2025, citation exacte :

> L'enquête a été réalisée sur quatre périodes, février, avril, juin et
> octobre 2025 dans **135 magasins** par une équipe de **100 « veilleurs
> consommation »** sur **42 départements**.

Quatre surfaces de vente : hypermarchés, supermarchés, EDMP (établissements à
dominante marques propres, type hard-discount), magasins spécialisés bio. Trois
gammes relevées : marques nationales, premiers prix (le plus bas constaté en
magasin), produits biologiques.

Stabilité du protocole, mesurée sur les trois éditions testées le 21/08/2026 :

| édition | magasins | veilleurs | départements | produits | périodes |
|---|---|---|---|---|---|
| 2021 | 148 | 107 | 37 | **97** | fév, avr, juin, oct |
| 2022 | 134 | 98 | 37 | **85** | fév, avr, juin, oct |
| 2025 | 135 | 100 | 42 | **83** | fév, avr, juin, oct |

Le calendrier, les surfaces de vente et les gammes sont **identiques sur les trois
éditions**. Le panier, lui, dérive : 97 produits en 2021, 83 en 2025.

Le panier est construit sur les **12 groupes d'aliments du PNNS** (Plan national
nutrition santé), pas sur la consommation observée.

### Ce qui est chaînable, et ce qui ne l'est pas

⚠️ **Les coûts bruts de panier ne sont pas chaînables.** Un quart des produits a
changé entre 2021 et 2025. Comparer 450 € à 539 € ne compare pas des prix.

Ce qui est chaînable, ce sont les **évolutions que l'association calcule
elle-même** sur produits comparables et publie dans chaque dossier.

Valeurs relevées le 21/08/2026 :

| période | panier Familles Rurales | inflation alimentaire officielle |
|---|---|---|
| sept. 2019 → sept. 2021 | **+2,2 %** (fruits et légumes frais **+9 %**) | — |
| édition 2022, sur un an | **+8,3 %** | **+12 %** (INSEE) |
| 2023 → 2025 | **+9,4 %** | **+14,7 %** |
| 2024 → 2025 | **−0,75 %** | **+1,7 %** |

**Le panier de l'association monte systématiquement moins que l'IPC
alimentaire**, de 3 à 5 points par an pendant la flambée. Trois éditions sur
trois, même sens. C'est un biais orienté à l'**inverse** du récit militant, ce qui
est la meilleure protection possible pour un projet qui affiche un écart face à
l'INSEE. À dire en clair dans `docs/METHODOLOGIE.md` : cette source **ne charge
pas** l'INSEE, elle l'allège.

### Ancrage à la date de référence — écart de trois mois

L'édition 2021 publie explicitement la période **« septembre 2019 → septembre
2021 »**. La date de référence de l'ADR 0009 est **`2019-12`**. La série remonte
donc bien avant la flambée, mais **son point de départ tombe trois mois avant la
base 100**. Traitement dans l'ADR 0019.

`# TODO: à vérifier` — les éditions 2019 et 2020 n'ont pas été récupérées.
Existence, URL et périodes couvertes à confirmer avant de figer le raccord.

### Ce que la source n'est pas

**Le panier PNNS n'est pas `CP01`.** C'est un panier **normatif** — ce qu'il
faudrait manger — et non ce que les ménages achètent. Les fruits et légumes y
pèsent près du tiers du budget, bien plus que dans la consommation réelle. Pas
d'alcool, pas de restauration, peu de produits transformés. L'écart de champ est
au moins aussi important que celui du PGC-FLS, et **dans l'autre sens**.

**Échantillon non probabiliste.** 135 magasins choisis par des bénévoles sur 42
départements. Mais protocole stable, périodes fixes et composition d'échantillon
décrite — ce qui le distingue d'une collecte opportuniste.

### Licence — régime différent des sources publiques

⚠️ Familles Rurales est une **association privée**, pas une administration.
L'article L322-1 du CRPA documenté plus bas **ne s'applique pas** : ses dossiers
de presse sont des œuvres protégées.

Conséquence pratique : les **valeurs chiffrées publiées sont des faits**, non
appropriables, réutilisables avec mention de source. En revanche le PDF lui-même
ne doit pas être redistribué depuis le dépôt. Les chiffres entrent dans
`data/manual/releves.csv` avec leur `source_url` ; jamais le document.

### Éditions testées et récupérées le 21/08/2026

Préfixe commun :
`https://www.famillesrurales.org/sites/multisite.famillesrurales.org._www/files/ckeditor/actualites/fichiers/`

| édition | fichier | poids |
|---|---|---|
| 2025 | `observatoire%20des%20prix%202025%20-%20familles%20rurales.pdf` | 1,7 Mo |
| 2022 | `Observatoire%202022%20VDef.pdf` | 2,4 Mo |
| 2021 | `Observatoire%20des%20Prix%20Familles%20Rurales%202021%20d%C3%A9f.pdf` | 1,3 Mo |

⚠️ Piège d'extraction, coûteux : les trois PDF utilisent **trois encodages de
police différents**. Un extracteur naïf (flux `FlateDecode` + opérateurs `Tj`)
lit 2022 correctement et sort du charabia sur 2021 ; lire les tables `ToUnicode`
règle 2025 mais pas tout. Prévoir que la collecte `CP01` **restera manuelle** —
cohérent avec l'ADR 0004, mais ne pas budgéter de parseur automatique.

⚠️ Ne pas confondre avec l'« Observatoire des prix des fruits et légumes » de la
même association, qui paraît en juillet sur un périmètre bien plus étroit.
L'Observatoire des prix de grande consommation paraît en janvier ou février.

---

## Alimentation — les trois sources écartées, et pourquoi

Toutes testées le 21/08/2026. Aucune n'est retenue, mais chacune répond à une
question qu'on se reposerait sinon.

### FranceAgriMer, « Point conso » — écartée sur l'historique

<https://www.franceagrimer.fr/chiffre-et-analyses-economiques/point-conso>

Publication d'un **établissement public**, PDF gratuit, qui relaie les panels
**Circana** et **Worldpanel by Numerator** (ex-Kantar). Elle transforme donc un
chiffre de presse payant en publication de service public citable — c'est la
bonne réponse à la question « comment citer un panel commercial proprement ».

Périmètre PGC-FLS, mensuel. **Premier numéro : janvier 2024.** Zéro historique
avant, donc la flambée de 2021-2023 n'est pas couverte. C'est ce qui la
disqualifie pour un indice ancré en `2019-12`.

À reconsidérer en v2 si `CP01` doit gagner une fréquence mensuelle sur la période
récente.

### Baromètre Circana / LSA — écartée sur l'accès

Le baromètre existe toujours, **contrairement à ce que supposait l'ADR 0014** :
avril 2026 à +0,4 % sur un an sur les PGC-FLS, juin 2026 à zéro en hypermarché.
Il n'est pas arrêté fin 2023.

Mais il est diffusé article par article dans une revue professionnelle payante.
Reconstituer un mensuel depuis `2019-12` demanderait de récupérer ~80 articles
derrière un paywall. Ce n'est pas une source, c'est un travail d'archive.
Qualité `synthese_presse` si un point isolé devait servir de contrôle.

### OFPM, FranceAgriMer — hors sujet

<https://observatoire-prixmarges.franceagrimer.fr/>

L'Observatoire de la formation des prix et des marges des produits alimentaires
mesure le **partage de la valeur le long de la filière**, de la ferme au rayon, et
il le fait **à partir de données INSEE**. Il ne produit aucune série de prix à la
consommation indépendante.

L'indice Observatoire a besoin, par définition (`CONTEXT.md`, indice 4), de prix
qui ne viennent pas d'un institut statistique. L'OFPM n'en fournit pas. Écartée
sans réserve.

---

## Open Prices (Open Food Facts) — testée, mesurée, écartée

API publique sans clé : `https://prices.openfoodfacts.org/api/v1/prices`

Base de relevés de prix contributifs adossée à Open Food Facts. Champs utiles par
enregistrement : `date`, `price`, `currency`, `product.code` (EAN), nom du
produit, quantité, `categories_tags`, et un bloc `location` avec l'enseigne OSM et
le code pays. Filtres de date : **`date__gte` / `date__lte`** (double
soulignement).

Écartée pour `CP01`. Ce qui suit est la mesure, pas une impression.

### ⚠️ Piège majeur — le filtre pays est silencieusement ignoré

`location_osm_country=France` **ne filtre pas sur la France**. Preuve :
`location_country=France`, paramètre qui n'existe pas, renvoie exactement le même
total. Un paramètre inconnu est ignoré sans erreur.

Page 1 de juin 2026 « filtrée France » : 53 Kiwi (Norvège), 31 Netto (Allemagne),
10 Extra (Norvège), un relevé en Irak, **zéro France**. Les devises confirment :
1 628 NOK et 1 322 USD sur 6 100 lignes.

Tout chiffre de couverture « France » obtenu avec ce paramètre est un **total
mondial**. Il faut filtrer côté client sur
`location.osm_address_country_code == "FR"`.

Couverture réelle après filtrage correct :

| mois | monde | France | part |
|---|---|---|---|
| 2024-06 | 1 690 | **1 036** | 61 % |
| 2025-06 | 4 181 | **3 015** | 72 % |
| 2026-05 | 8 972 | **5 704** | 64 % |
| 2026-06 | 10 237 | **3 710** | 36 % |

La part France varie de 36 à 72 % d'un mois à l'autre : **ne pas extrapoler** ces
mois en totaux annuels.

### Concentration et rotation de l'échantillon

Les **trois premiers contributeurs** font **54 à 73 %** des relevés France du
mois. La composition en enseignes change entièrement d'un mois sur l'autre :

```
2026-05   Auchan 26,2 %   E. Leclerc 22,2 %   Carrefour 9,8 %
2026-06   Carrefour Market 29,0 %   Auchan 11,8 %   Carrefour City 6,5 %
2025-06   sans enseigne 13,2 %   Auchan 12,1 %   Carrefour City 11,7 %
```

Une variation mensuelle mesurée là-dessus mesure d'abord où trois personnes ont
fait leurs courses ce mois-là.

### Appariement de produits — le chiffre qui tranche

```
2026-05 vs 2026-06   609 EAN communs = 14,1 %   dont >=2 relevés des deux côtés :  75
2025-06 vs 2026-06   251 EAN communs = 10,4 %   dont >=2 relevés des deux côtés :  22
```

Un indice de produits appariés reposerait sur **75 produits** en mensuel et **22**
en glissement annuel, pour un poste qui pèse ~150 ‰ du panier.

### Test décisif — l'indice calculé, des deux façons

Sur `CP01`, mai → juin 2026 :

| méthode | variation |
|---|---|
| officiel INSEE (via OCDE COICOP 2018) | **−0,34 %** |
| Open Prices, produits appariés (606 EAN, moyenne géométrique des ratios) | **+1,58 %** |
| Open Prices, panier naïf (moyenne brute de tous les prix) | **−4,04 %** |

Deux méthodes défendables, même donnée, même mois : **5,6 points d'écart et des
signes opposés**. Aucune n'approche l'officiel. La version appariée annualisée
vaudrait ~+21 %/an.

Distribution des ratios appariés : **médiane exactement +0,00 %** — la plupart des
produits n'ont pas bougé — mais quartiles à **−2,1 %** et **+5,1 %**. La moyenne
est entièrement pilotée par les queues, c'est-à-dire par des promotions, des
formats différents et des enseignes différentes confondus sous le même EAN.

**Conclusion.** Le biais d'Open Prices n'est ni connu ni bornable, et il dépend
davantage du choix de méthode que du mouvement réel des prix. Publier ça face à
l'INSEE reviendrait à fabriquer l'écart puis à le commenter — exactement l'outil
militant que `CLAUDE.md` interdit.

À reconsidérer si le volume France et la stabilité des contributeurs changent
d'ordre de grandeur. Le seuil à retrouver est explicite : quelques milliers de
produits appariés d'un mois sur l'autre, et aucun contributeur au-delà de
quelques pour cent des relevés.

---

## OCDE — testée, redondante, non retenue

API SDMX publique sans clé, `https://sdmx.oecd.org/public/rest/`.

⚠️ **Piège d'ordre des dimensions**, l'inverse d'Eurostat :
`REF_AREA.FREQ.METHODOLOGY.MEASURE.UNIT_MEASURE.EXPENDITURE.ADJUSTMENT.TRANSFORMATION`.
La clé `FRA.M.......` fonctionne ; `M.FRA...` renvoie
`422 Not enough key values in query, expecting 8 got 5`.

Deux flux parallèles, et le premier est gelé :

| flux | dernier mois FR | nomenclature |
|---|---|---|
| `DSD_PRICES@DF_PRICES_ALL` | **2025-12** | ECOICOP v1 |
| `DSD_PRICES_COICOP2018@DF_PRICES_C2018_ALL` | **2026-07** | COICOP 2018 (contient `CP13`) |

Le gel à `2025-12` **confirme de façon indépendante** ce qui avait été établi chez
Eurostat pour ECOICOP v1 (ADR 0010). La bascule de nomenclature est réelle, datée,
et ce n'est pas un artefact Eurostat.

**Non retenue comme source.** La dimension `EXPENDITURE` ne descend jamais sous la
division : 26 modalités pour la France (`CP01` à `CP13`, plus `CP041`, `CP043`,
`CP044`, `CP045`, `CP0722` et des agrégats de commodité `SERV`, `GD`,
`_TXCP01_NRG`). Les poids transposés du projet vont à la **sous-classe** (ADR
0018). L'OCDE est donc strictement plus grossière qu'Eurostat, sur des données du
même producteur (`METHODOLOGY` valant `N` ou `HICP`).

`DSD_CPI_COU_WEIGHTS` a été testée en espérant des poids COICOP : ce sont les
poids **des pays dans l'agrégat OCDE** (France = 4,449 % en 2024). Sans usage ici.

**Usage retenu, limité** : contrôle croisé ponctuel de l'IPC alimentaire français,
ce qui a servi ci-dessus pour le test Open Prices. Pratique parce qu'un seul appel
donne divisions et agrégats en COICOP 2018 jusqu'au mois courant.

---

## Boursorama, convertisseur d'inflation — pas une source, une piste d'interface

<https://www.boursorama.com/budget/simulateurs/convertisseur-inflation>

Convertisseur d'euros constants, données INSEE annuelles, bornes 1901-2025, trois
monnaies (anciens francs, francs, euros). Aucune API, aucune base 100 citée,
aucune limite méthodologique affichée.

Aucune valeur comme donnée. Valeur réelle comme **piste d'interface** : c'est le
geste que l'indice 3 permet de rendre personnel — « 100 € de `2019-12` valent X €
aujourd'hui selon l'IPC officiel, **et Y € selon vos poids** ». Deux nombres au
lieu d'un. Aucune décision prise à ce stade ; pas d'ADR.

---

## Sources écartées

**`github.com/datasets/inflation`** — Banque mondiale, couverture 1973-2014,
granularité pays entier, aucune ventilation par poste. Pour la France, c'est
l'IPC INSEE relayé avec douze ans de retard. Aucun usage.

**NielsenIQ / Circana** — traités en détail plus haut, section « Alimentation —
les trois sources écartées ». En résumé : le baromètre Circana/LSA n'est pas
arrêté fin 2023 comme on l'avait cru, mais il est payant et diffusé article par
article ; le relais public gratuit, « Point conso » de FranceAgriMer, ne commence
qu'en janvier 2024. Utilisables comme **relevé manuel ponctuel** dans
`data/manual/releves.csv`, qualité `synthese_presse`, jamais comme série. Voir
`docs/adr/0004-registre-csv-pour-les-sources-sans-api.md` et l'ADR 0019.

---

## Sources de référence méthodologique

Code de réplication R de François Geerolf, utile pour vérifier nos propres
chiffres HBS contre un travail publié indépendant :
<https://github.com/Francois-Geerolf/inflation-par-categorie>


---

## ADEME Car Labelling — candidat `CP071`, archivage sans historique

Recherche du 23/08/2026 (ADR 0020). `https://www.data.gouv.fr/datasets/ademe-car-labelling`,
ressource CSV : `https://www.data.gouv.fr/api/1/datasets/r/669a1f00-299f-4c7c-9db2-cd32401e7b25`.

Licence Ouverte (Etalab). CSV **téléchargé et inspecté directement** le
23/08/2026 : 3604 lignes, encodage UTF-8 avec BOM (confirmé caractère par
caractère). Colonne `Prix véhicule` (index 51) présente et remplie sur
**3604/3604 lignes** — échantillon : `RENAULT KANGOO 31000`, `MAZDA MX-30
38510`, `B.M.W. 540 77588`.

⚠️ **Aucun historique accessible.** Interrogation directe de l'API `data-fair`
sous-jacente (`https://data.ademe.fr/data-fair/api/v1/datasets/ademe-car-labelling`) :
`"history": null`. Le fichier est écrasé en place à chaque mise à jour
(dernière : 14/07/2026). Aucune archive datée trouvée ailleurs (recherche web
infructueuse sur `carlabelling.ademe.fr`).

⚠️ **Cadence contradictoire selon la source.** La fiche data.gouv.fr annonce
« 2 fois par an » ; `carlabelling.ademe.fr` annonce une actualisation
trimestrielle (janvier, avril, juillet, octobre). Non tranché — à confirmer à
la deuxième capture.

⚠️ **Nature exacte du prix non confirmée — même après consultation du
lexique officiel.** Le glossaire (`carlabelling.ademe.fr/index/glossaire`) ne
définit pas le champ `Prix véhicule`. Le « lexique des données » référencé sur
la fiche data.gouv.fr (`ADEME - Car Labelling - Lexique des données -
2021-03.docx`, consulté le 23/08/2026) a été téléchargé et son texte extrait
directement du XML — il définit `Prix véhicule` par la seule mention
« en euros (si disponible) ». Aucune précision TTC/HT, bonus-malus déduit ou
non, avant/après remise concessionnaire. La source primaire censée trancher
ne tranche pas : `# TODO: nature du prix non confirmable par la documentation
ADEME elle-même — bloquant pour tout calcul d'indice, à traiter comme limite
méthodologique documentée plutôt qu'à deviner.`

**Décision (ADR 0020) : pas d'adoption comme source de `CP071` cette
session.** La date de référence du projet est `2019-12` (ADR 0009) ; sans
historique, `CP071` resterait en IPCH pur jusqu'à la première capture —
même situation que « Point conso » déjà écartée pour `CP01` (ADR 0019),
qui renvoie le remède (raccord de sources) à une méthodologie non encore
validée. Archivage trimestriel démarré dès maintenant
(`collecte.ademe.fetch_ademe_carlabelling`) pour ne pas perdre le millésime
`2026-Q3`, seul accessible faute d'archive rétroactive.

**Cet archivage est arrêté depuis l'ADR 0024** : voir la section AAA Data
ci-dessous, source retenue pour `CP071`.

## AAA Data — Intelligence Auto, source retenue pour `CP071` (ADR 0024)

Vérifié le 24/08/2026, directement sur `www.aaa-data.fr` (attention au
certificat TLS : seul `www.aaa-data.fr` répond, `aaa-data.fr` nu échoue).
Pas d'API, pas de fichier téléchargeable, pas de licence de réutilisation
affichée : des articles HTML, deux formats —

- **communiqué de presse mensuel** (immatriculations du mois, mix de
  motorisations, rarement un prix moyen) ;
- **« Intelligence Auto »**, périodique (~11/an), qui contient le prix moyen
  d'un véhicule neuf, en cumul depuis le 1er janvier de l'année, par
  motorisation.

Aucune des deux ne publie de série mensuelle de prix moyen point par point —
seulement des cumuls annuels glissants. La règle de conversion en points
mensuels comparables à l'IPC (même besoin que Familles Rurales, ADR 0019)
n'est pas tranchée et ne doit pas être codée avant de l'être.

**Chiffres vérifiés et saisis dans `data/manual/releves.csv` aujourd'hui**
(9 lignes, poste `CP071`) :

| source | période | motorisation | prix moyen | évolution |
|---|---|---|---|---|
| Communiqué du 01/01/2026 | année 2025 | essence | 25 657 € | −4,6 % |
| Communiqué du 01/01/2026 | année 2025 | électrique | 42 992 € | −0,1 % |
| Intelligence Auto n°88 (19/01/2026) | année 2025 | essence | 25 884 € | −3,6 % |
| Intelligence Auto n°88 (19/01/2026) | année 2025 | électrique | 42 788 € | −0,8 % |
| Intelligence Auto n°93 (17/06/2026) | cumul janv-mai 2026 | globale | 36 319 € | +3,6 % |
| Intelligence Auto n°93 (17/06/2026) | cumul janv-mai 2026 | électrique | 42 541 € | −0,8 % |
| Intelligence Auto n°93 (17/06/2026) | cumul janv-mai 2026 | hybride | 36 757 € | −1,8 % |
| Intelligence Auto n°93 (17/06/2026) | cumul janv-mai 2026 | essence | 25 202 € | −0,7 % |
| Intelligence Auto n°93 (17/06/2026) | cumul janv-mai 2026 | diesel | 45 463 € | +13,3 % |

URLs exactes : `communique-de-presse-1er-janv-2026`,
`intelligence-auto-n88-marche-des-voitures-neuves-atone-en-2026-reprise-dynamique-attendue-des-2027`,
`intelligence-auto-n93-juin` (toutes sous `https://www.aaa-data.fr/actualites/`,
voir `data/manual/releves.csv` pour les URLs complètes par ligne).

⚠️ **Deux publications, même période nominale, chiffres différents.** Le
communiqué du 01/01/2026 et Intelligence Auto n°88 du 19/01/2026 donnent
tous les deux « le prix moyen de l'année 2025 vs 2024 », avec des valeurs
qui ne concordent pas (25 657 € contre 25 884 € en essence, 42 992 € contre
42 788 € en électrique). Vérifié par citation verbatim des deux articles,
pas une erreur de lecture. AAA Data ne publie ni méthode ni note de révision
expliquant l'écart. **Aucune tentative de trancher laquelle est « la
bonne » — les deux lignes sont conservées dans `data/manual/releves.csv`**,
c'est la donnée telle que la source la publie.

⚠️ **Nature du prix non précisée**, même défaut que l'ADEME ci-dessus : TTC ou
HT, bonus-malus déduit ou non — non documenté par AAA Data. `# TODO: à
vérifier si un lexique AAA Data existe ; sinon limite méthodologique à
documenter dans docs/METHODOLOGIE.md`.

⚠️ **Pondération par les ventes réelles absente** des chiffres cités — même
réserve que l'ADR 0020 pour ADEME.

**Ce qui reste à faire avant tout calcul d'indice** : la règle de conversion
cumul-annuel → point mensuel (à valider dans `docs/METHODOLOGIE.md` avant
codage, CLAUDE.md), le choix entre les deux séries 2025 divergentes ou leur
conservation en parallèle, et la collecte des Intelligence Auto restants
(~92 numéros publiés à ce jour, 9 lignes seulement couvertes aujourd'hui) —
`# TODO: backlog de collecte, session dédiée suivante`.

## Restauration / hôtellerie (`CP11`) — rien trouvé

Recherche du 23/08/2026. Aucune source indépendante et gratuite identifiée :

- Banque de France Webstat (`ICP.M.FR.N.110000.4.INX`) republie l'IPCH
  officiel — zéro indépendance, sans intérêt pour l'indice Observatoire.
- MKG / STR / UMIH publient des baromètres mensuels (RevPAR, prix moyen de
  chambre) — commercial, diffusion PDF régionale, pas d'open data identifié.

`CP11` reste sur l'IPCH. Aucune action de collecte engagée.

## France Assureurs — chiffres citables, pas une source de données

Recherche du 23/08/2026 pour `CP12`/`CP13` (assurance et services divers,
137 ‰ combiné). `https://www.franceassureurs.fr/actualites/les-donnees-cles-de-lassurance-francaise-en-2024/`,
PDF `donnees-cles-2024.pdf` (20 Mo).

PDF téléchargé et extrait en texte (`pdftotext -layout`) le 23/08/2026 —
confirmé, pas seulement cité par un tiers : série annuelle réelle,
**« Prime moyenne HT »**, 2020-2024 :

```
Assurance auto, RC 1ère catégorie      149  151  153  156  162  €  (+3,6 %)
Assurance auto, tous risques/tiers1    243  247  250  257  271  €  (+5,2 %)
Multirisque habitation (MRH)           258  262  268  279  299  €  (+7,2 %)
```

⚠️ **Reproduction « strictement interdite »** sans autorisation écrite
préalable de France Assureurs (mentions légales du site). Une tolérance
existe pour un usage non lucratif, mais sur accord préalable exprès —
non obtenu. Régime plus restrictif que celui déjà accepté pour
NielsenIQ/Circana (ADR 0004, ADR 0019, citation de chiffres publiés en
`synthese_presse`) : ici c'est le site lui-même qui interdit la
republication, pas seulement l'absence de série gratuite.

**Décision : pas d'intégration à `data/manual/releves.csv`.** Citable en
prose dans `docs/METHODOLOGIE.md`, avec attribution, comme commentaire de
contexte à côté de l'IPCH — pas comme un poste `sources propres` de
l'indice Observatoire. Écarté du même geste : data.gouv.fr, « Prix de
l'assurance auto par profil selon les régions françaises » (lesfurets.com,
Licence Ouverte) — dernière mise à jour 16/08/2017, fréquence de mise à
jour non respectée signalée sur la fiche elle-même, série non maintenue.

---

## DARES — Salaire mensuel de base (SMB), comparaison salaires/prix

Testé le 23/08/2026 (ADR 0022). Producteur : Dares (Direction de l'animation
de la recherche, des études et des statistiques, ministère du Travail),
à partir de l'enquête trimestrielle Acemo.

<https://dares.travail-emploi.gouv.fr/donnees/les-indices-de-salaire-de-base>

### Fichier vérifié le 23/08/2026

Fichier XLSX téléchargé et ouvert directement (`openpyxl`), pas seulement
cité : `Dares_serie_salaire_de_base_t1_2026.xlsx`, 252 856 octets, huit
feuilles. Feuille retenue : **`Sal. mens. ensemble`**, ligne `ENS`
« Ensemble des secteurs non agricoles ».

En-tête de la feuille (cellules elles-mêmes) :

```
Titre : Salaire mensuel de base de l'ensemble des salariés depuis juin 2017
Type de données : données trimestrielles
Unité : base 100 en juin 2017
Champ : France hors Mayotte, salariés des établissements d'entreprises
        de 10 salariés ou plus
Source : Dares, enquête trimestrielle Acemo
```

Colonnes trimestrielles juin 2017 → mars 2026 (36 points), plus trois
colonnes de variation (3/6/12 mois). Valeur au point de référence du
projet, `2019-12` (ADR 0009) : **103,8** (colonne « dec » 2019, présente,
pas de trou à cette date). Un trou existe une colonne plus loin, mars 2020
(`'n.d.'`) — à traiter par l'interpolation déjà en place pour les autres
séries trouées (ADR 0015).

Dernier point du fichier testé : mars 2026, valeur 121,9. Glissement annuel
publié en colonne dédiée : +1,7 % sur les douze derniers mois du fichier —
cohérent avec les communiqués Dares consultés le même jour (+1,9 % sur un an
fin juin 2026, trimestre suivant).

### ⚠️ Le champ exclut le secteur public — c'est la définition même du SMB

L'enquête Acemo ne couvre que les entreprises privées de 10 salariés ou plus,
hors secteur agricole, administration publique, activités des ménages et
activités extraterritoriales (précisé sur la page Dares). « Ensemble des
salariés » désigne donc l'ensemble du champ Acemo, pas l'ensemble des
salariés français au sens large. C'est la définition retenue pour la
variable `salaire_smb` du projet (ADR 0022) — à ne jamais présenter comme
couvrant la fonction publique.

### ⚠️ URL du fichier non stable — piège documenté par la Dares elle-même

Le nom de fichier change à chaque publication trimestrielle
(`..._t1_2026.xlsx`, le prochain sera `..._t2_2026.xlsx`, etc.). Les mentions
légales du site le disent explicitement : lier vers la page
`/donnees/les-indices-de-salaire-de-base`, jamais vers le fichier lui-même.
Toute collecte doit donc repartir de cette page à chaque exécution, pas d'une
URL de fichier codée en dur.

### ⚠️ Téléchargement direct (`requests`/`curl`) bloqué — collecte manuelle

Le domaine `dares.travail-emploi.gouv.fr` est hébergé par Cegedim et protégé
par une vérification anti-bot : un `curl` ou `requests.get()` classique,
même avec un `User-Agent` de navigateur, reçoit une page HTML
« Vérification de sécurité » (CAPTCHA) à la place du fichier — vérifié à la
fois sur la page et sur l'URL directe du XLSX. Confirmé aussi indirectement
sur la fiche miroir data.gouv.fr du même jeu de données (« Le robot de
data.gouv.fr n'a pas pu accéder à ce fichier », taille annoncée 245 octets
au lieu des ~247 Ko réels) : le blocage touche aussi le crawler de
data.gouv.fr, pas seulement des clients HTTP non-navigateur.

Un navigateur réel (session Chrome, cookies acceptés) passe la vérification
sans difficulté et télécharge le fichier normalement. **Conséquence pour la
collecte : `salaire_smb` ne peut pas suivre le patron `requests` de
`collecte/insee.py`/`collecte/eurostat.py`.** Même traitement que Familles
Rurales et ARCEP (ADR 0004) : téléchargement manuel périodique (chaque
trimestre, au rythme de publication Dares), fichier archivé dans
`data/raw/` avec sa date, puis lecture/traitement pur en `traitement/`.

### Licence — régime L322-1 CRPA, comme la CRE et la Carte des loyers

Vérifié le 23/08/2026 sur `dares.travail-emploi.gouv.fr/mentions-legales`.
Aucune licence nommée : « informations publiques librement et gratuitement
réutilisables » sous la loi n°78-753 du 17 juillet 1978 — même régime que
celui déjà documenté plus bas pour la CRE et la Carte des loyers
(non-altération, mention de la source, mention de la date de mise à jour).

---

## Régime des licences — vérifié le 21/08/2026

Deux sources de l'indice Observatoire portent la licence `notspecified` sur
data.gouv : la CRE (tarif réglementé) et la Carte des loyers pour ses millésimes
2024 et 2025. **Cela n'interdit pas la réutilisation.**

Guide juridique de data.gouv, « Respecter les conditions de réutilisation » :

> **À défaut de mention d'une licence**, les dispositions de l'article L322-1 du
> CRPA s'appliquent. Cet article fixe des conditions de réutilisation identiques
> à celles de la licence ouverte, à savoir : la **non-altération** des données
> publiques, la **mention de leurs sources** (paternité des données) et la
> **mention de la date de leur dernière mise à jour.**

<https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032255220>
<https://guides.data.gouv.fr/llms-full.txt>

Les deux producteurs sont badgés `public-service` et `certified` sur data.gouv :
Commission de régulation de l'énergie, et Ministère de la Transition écologique.
Pour la Carte des loyers, les millésimes 2018, 2022 et 2023 de la même série sont
en `lov2` explicite — l'absence de licence sur 2024 et 2025 est un oubli de
métadonnée, pas un changement de droits.

### Ce que le projet doit faire pour être en règle

Trois obligations, identiques pour `lov2` et pour `notspecified` :

1. **Ne pas altérer** — au sens de ne pas dénaturer le sens de l'information. La
   transformation en indice est licite ; présenter un chiffre dérivé comme étant
   celui du producteur ne l'est pas. C'est déjà la discipline des ADR 0001 et
   0002.
2. **Mentionner la source** de chaque poste.
3. **Mentionner la date de dernière mise à jour** de la donnée employée.

Ces trois points sont des contraintes d'interface, pas seulement de
documentation.
