# Transposer les poids HBS en COICOP 2018

Les poids et les prix ne parlent pas la même langue. L'enquête Eurostat HBS 2020
est publiée en **ECOICOP v1**, l'IPCH courant (`prc_hicp_minr`) en
**COICOP 2018**. Joindre par le code produit des correspondances fausses et
silencieuses, pas des valeurs manquantes.

Mesuré le 21/08/2026 sur les 47 groupes HBS à trois chiffres, poids QU1 FR 2020 :
21 groupes ont un libellé identique (526 ‰), 20 divergent (199 ‰), 6 sont absents
de la v2 (268 ‰). Une vingtaine des divergences sont de simples renommages, mais
**environ 111 ‰ changent réellement de contenu**. Les pires :

```
CP121  37 ‰   HBS = Personal care          COICOP 2018 = Insurance
CP083  22 ‰   HBS = Téléphone, services    COICOP 2018 = Information and communication services
CP093  18 ‰   HBS = Loisirs, jardin        COICOP 2018 = Garden products and pets
CP022  14 ‰   HBS = Tobacco                COICOP 2018 = Alcohol production services
CP023   0 ‰   HBS = Narcotics              COICOP 2018 = Tobacco
```

Au niveau des divisions, `CP08` passe de *Communications* à *Information and
communication*, `CP12` de *Miscellaneous goods and services* à **Insurance and
financial services**, et une division `CP13` apparaît.

## La décision

Les prix restent en COICOP 2018, et les poids HBS sont transposés une fois pour
toutes vers cette nomenclature. La transposition vit dans un CSV versionné,
vérifié à la main contre la table de correspondance officielle COICOP 2018 ↔
COICOP 1999 publiée par l'UNSD en partenariat avec Eurostat. Même dispositif que
l'ADR 0004 : une donnée sourcée dans un fichier, jamais une table en dur dans le
code.

```
data/manual/correspondance_coicop.csv
  hbs_ecoicop_v1, coicop2018, part, source_url
```

Pour les rares groupes qui se scindent — `CP091` *Audio-visual, photographic and
information processing equipment* se répartit entre `CP081` équipement TIC et
`CP091` biens durables de loisir — la colonne `part` porte une clé de ventilation
tirée de `prc_hicp_iw`, les poids officiels de l'IPCH en COICOP 2018. La somme
des `part` d'un même groupe HBS doit valoir 1, et cette contrainte est vérifiée au
chargement.

## Ce que ça débloque

Les six groupes réputés « non joignants » ne manquaient pas : COICOP 2018 les a
renumérotés dans la division `CP13`.

```
CP121 Personal care       37 ‰  →  CP131 Personal care
CP123 Personal effects     3 ‰  →  CP132 Other personal effects
CP124 Social protection    6 ‰  →  CP133 Social protection
CP125 Insurance           82 ‰  →  CP121 Insurance
CP126 Financial services   5 ‰  →  CP122 Financial services
CP127 Other services      18 ‰  →  CP139 Other services
```

`CP042` reste le seul trou réel, traité par l'ADR 0005. La question du traitement
des cinq autres postes est close.

## Alternative écartée : rester en ECOICOP v1

`prc_hicp_midx` et `prc_hicp_inw` partagent la nomenclature de HBS et joignent
exactement, sans aucune table à vérifier. Mais ces datasets sont **arrêtés à
`2025-12`** : le dashboard serait figé le jour de sa publication et ne se
mettrait plus jamais à jour. Pour une démonstration destinée à être montrée,
c'est disqualifiant — et il n'existe aucun chemin de sortie qui ne repasse pas
par la présente décision.

Vérifié le 21/08/2026 : `prc_hicp_minr`, France, `TOTAL`, `I15` couvre
`1996-01` → `2026-07`, 367 observations. Passer en COICOP 2018 ne coûte **aucune
profondeur d'historique**.

## Alternative écartée : agréger au niveau commun

Ne garder que les postes au contenu identique dans les deux nomenclatures
reviendrait à fusionner `CP08` à `CP13` en un bloc unique — soit à perdre la
granularité précisément là où les profils de ménage divergent le plus :
télécoms, loisirs, assurance.

## Ce qui reste bloquant

La table officielle n'a **pas encore été récupérée sous forme exploitable**. La
note de couverture UNSD est datée du 9 octobre 2024 ; son contenu, sa granularité
et sa réversibilité restent non vérifiés. Aucun code de transposition ne s'écrit
avant que la table figure dans `docs/SOURCES.md` et que les 47 lignes aient été
relues une par une.
