# Comparaison salaires/prix : ajout de `salaire_smb`

Jusqu'ici le projet publie cinq indices de prix étiquetés (ADR 0002), jamais de
série salariale. L'utilisateur demande d'ajouter une courbe d'évolution des
salaires, superposée aux cinq indices, pour visualiser la divergence entre
salaire et prix — pas un pouvoir d'achat déflaté, pas une nouvelle « inflation
réellement vécue » calculée à l'envers.

Décision prise après entretien dirigé (`/grill-me`, 23/08/2026) et vérification
directe de la source (voir `docs/SOURCES.md`, section « DARES — Salaire mensuel
de base »).

## Décision

Une sixième série, **`salaire_smb`**, distincte des cinq indices de l'ADR 0002 —
elle n'a ni prix ni poids HBS, donc n'entre pas dans leur table de nommage.

- **Grandeur** : salaire nominal seul. Aucune déflation par un indice de prix en
  V1 — décider quel indice servirait de déflateur est une question ouverte à part
  entière, non tranchée ici.
- **Agrégat** : SMB (salaire mensuel de base), enquête Acemo, Dares. Salaire brut
  avant cotisations, hors primes et heures supplémentaires — grandeur la plus
  proche d'un « prix du travail », symétrique des indices de prix affichés à côté.
- **Périmètre** : ligne `ENS` (« Ensemble des secteurs non agricoles ») de la
  feuille `Sal. mens. ensemble` du fichier Dares — établissements privés de 10
  salariés ou plus, France hors Mayotte, hors agriculture, administration
  publique, activités des ménages et activités extraterritoriales. C'est
  l'« ensemble des salariés » au sens du champ Acemo, pas de la France entière :
  **la fonction publique n'est pas couverte**, à dire explicitement dans
  l'interface partout où `salaire_smb` apparaît.
- **Fréquence** : trimestrielle (Acemo), quand les cinq indices de prix sont
  mensuels. `salaire_smb` n'aura donc une valeur observée qu'un mois sur trois ;
  les deux mois intermédiaires suivent l'interpolation de l'ADR 0015, drapeau
  `interpole` jusqu'à l'interface comme pour toute valeur comblée.
- **Base 100** : rebasée sur `2019-12` (ADR 0009), même règle que les cinq
  indices — formule de rebasage déjà écrite en `docs/METHODOLOGIE.md` §5.2,
  aucune formule nouvelle à valider. Valeur du fichier Dares au point de
  référence : **103,8** (base d'origine 100 = juin 2017), point réellement
  observé, pas interpolé.

## Pourquoi un ADR pour un ajout qui semble mineur

Trois raisons, posées explicitement pendant l'entretien :

1. **Nouvelle source de données**, hors du système INSEE/Eurostat déjà en place —
   nouveau producteur (Dares), nouveau régime d'accès (voir plus bas), nouveau
   risque de confusion de périmètre (secteur privé seul).
2. **Nouveau terme à River dans `CONTEXT.md`** — `salaire_smb` n'est pas un des
   cinq indices, la discipline de nommage doit s'étendre explicitement pour ne
   pas laisser planer d'ambiguïté sur « quel salaire, sur quel champ ».
3. **Nouvelle courbe hors du cadre ADR 0002** — le graphe passe de cinq séries
   toutes définies par (source de prix, source de poids) à six, dont une qui n'a
   ni prix ni poids. Vaut la peine d'être tranché une fois, pas improvisé au fil
   du code.

## Contrainte de collecte : pas de `requests`, patron ADR 0004

Le fichier Dares est un XLSX réel, à jour, licite (régime L322-1 CRPA, comme la
CRE et la Carte des loyers) — mais **le domaine `dares.travail-emploi.gouv.fr`
est protégé par une vérification anti-bot Cegedim** qui bloque `curl` et
`requests.get()`, même avec un `User-Agent` de navigateur. Vérifié à la fois sur
la page et sur l'URL directe du fichier ; confirmé indirectement par le propre
crawler de data.gouv.fr, qui échoue aussi sur la fiche miroir du même jeu de
données.

`salaire_smb` ne peut donc pas suivre le patron `requests` de
`collecte/insee.py` ou `collecte/eurostat.py`. Même traitement que Familles
Rurales et ARCEP (ADR 0004) : téléchargement manuel, périodique (rythme
trimestriel Acemo), fichier archivé daté dans `data/raw/`, puis lecture pure
dans `traitement/` — aucune fonction de `collecte/` n'appelle le réseau pour
cette source.

Contrainte supplémentaire propre à cette source : le nom du fichier change à
chaque publication (`..._t1_2026.xlsx`, puis `..._t2_2026.xlsx`, etc.) — les
mentions légales Dares le disent explicitement. Toute redirection vers le
fichier doit donc repartir de la page
`dares.travail-emploi.gouv.fr/donnees/les-indices-de-salaire-de-base`, jamais
d'une URL de fichier codée en dur.

## Ce que la décision laisse ouvert

- `traitement/` et `viz/` restent à écrire : parser la feuille `Sal. mens.
  ensemble`, rebaser sur `2019-12`, interpoler les deux mois manquants par
  trimestre, superposer sur le graphe existant.
- Le premier fichier a été téléchargé et inspecté le 23/08/2026
  (`Dares_serie_salaire_de_base_t1_2026.xlsx`, feuille `Sal. mens. ensemble`,
  103,8 en `2019-12`) — à archiver dans `data/raw/` avec sa date au moment de
  l'implémentation, pas seulement dans ce document.
- Aucun déflateur choisi : si un salaire réel (pouvoir d'achat) est demandé plus
  tard, c'est une décision séparée, avec son propre ADR — lequel des cinq
  indices sert de déflateur n'est pas une évidence.
