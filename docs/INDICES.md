# Les cinq indices — guide de lecture

Ce document explique, indice par indice, ce que chacun mesure et pourquoi il
existe. Il ne remplace pas `docs/METHODOLOGIE.md` (formules, ADR, limites
détaillées) ni `docs/SOURCES.md` (URL, licences) : c'est le point d'entrée
rapide vers les deux.

Vocabulaire contraignant : `CONTEXT.md`. Termes bannis : « inflation réelle »,
« inflation ressentie » comme taux (ADR 0001).

## Le principe commun

Chaque indice est défini par un couple **(source de prix, source de poids)**.
Ce sont les deux seules choses qui changent d'un indice à l'autre — jamais le
traitement qualité (shrinkflation, ajustement hédonique). Croiser deux sources
de prix à l'intérieur d'un même indice est interdit ; comparer se fait en
juxtaposant des courbes, jamais en les mélangeant (METHODOLOGIE §2).

Tous les indices sont rebasés à **100 en 2019-12** (ADR 0009) et, pour les
indices repondérés, agrégés en Laspeyres à poids fixes (METHODOLOGIE §5.2) :

```
I_p(t) = 100 × P_p(t) / P_p(t₀)          I(t) = Σ w_p × I_p(t) / 1000
```

## Tableau de synthèse

| # | nom (variable) | prix | poids | statut code |
|---|---|---|---|---|
| 0 | `ipc_officiel` | INSEE | national INSEE | ✅ collecte + traitement (`collecte/insee.py`, `traitement/insee.py`) |
| 1 | `ipch` | Eurostat | officiels Eurostat | ✅ collecte + traitement (`collecte/eurostat.py`, `traitement/eurostat.py`) |
| 2 | `ipch_repondere` | Eurostat | profil HBS | ✅ collecte + traitement + dashboard (`collecte/eurostat.py`, `traitement/eurostat.py`, `dashboard.py::calculer_indice_2`) |
| 3 | `ipc_repondere` | INSEE | profil HBS | ✅ collecte + traitement + dashboard (`collecte/insee.py`, `traitement/insee.py`, `dashboard.py::calculer_indice_3`) |
| 4 | `indice_observatoire` | sources propres poste par poste | profil HBS | ⏳ pas encore implémenté |

`analyse/indice.py` porte la fonction d'agrégation `(prix, poids) → indice`,
déjà utilisée par les indices 2 et 3 ; servira aussi à l'indice 4 une fois ses
sources de prix propres branchées.

---

## Indice 0 — `ipc_officiel`

**Ce que c'est** : l'indice des prix à la consommation publié par l'INSEE,
référence nationale, panier moyen des ménages français.

**Prix** : INSEE, API BDM, dataflow `IPC-2025`, clé confirmée dans
`docs/SOURCES.md` (`MENAGES_IPC=ENSEMBLE`, `REF_AREA=FE`, `PRIX_CONSO=SO` —
hors loyers imputés).

**Poids** : structure de consommation nationale de l'INSEE, révisée chaque
année par l'Institut — pas les poids HBS du projet.

**Rôle dans le projet** : la référence à laquelle tous les autres indices se
comparent. C'est le chiffre que la presse cite.

---

## Indice 1 — `ipch`

**Ce que c'est** : l'indice des prix harmonisé de la France, publié par
Eurostat pour permettre les comparaisons entre pays européens.

**Prix** : Eurostat, `prc_hicp_minr`, nomenclature COICOP 2018.

**Poids** : poids officiels Eurostat (`prc_hicp_iw`), pas ceux du projet.

**Pourquoi il existe à côté de l'IPC officiel** : champ et méthode diffèrent
de l'IPC INSEE (par exemple sur le traitement des loyers). Il sert surtout de
**source de prix** pour les indices 2 et 4 — c'est de lui, pas de l'IPC INSEE,
que viennent les séries de prix par poste utilisées une fois repondérées,
parce que sa nomenclature COICOP 2018 est celle vers laquelle les poids HBS
sont transposés (METHODOLOGIE §3.2).

---

## Indice 2 — `ipch_repondere`

**Ce que c'est** : les mêmes prix que l'indice 1 (Eurostat), recombinés avec
les poids d'un profil de ménage au lieu des poids officiels Eurostat.

**Prix** : Eurostat, identique à l'indice 1.

**Poids** : profil de ménage HBS (quintile de revenu en v1, ADR 0011),
transposés de ECOICOP v1 vers COICOP 2018 (METHODOLOGIE §3.2-3.3).

**À quoi il sert** : isoler l'effet de la repondération seule, prix Eurostat
constants. Comparé à l'indice 3 (mêmes poids, prix INSEE), il permet de voir
ce qui vient de la méthode INSEE contre méthode Eurostat plutôt que de la
personnalisation (METHODOLOGIE §2).

---

## Indice 3 — `ipc_repondere`

**Ce que c'est** : les prix de l'IPC officiel INSEE, recombinés avec les
poids d'un profil de ménage.

**Prix** : INSEE, identique à l'indice 0.

**Poids** : profil de ménage HBS, identique à l'indice 2.

**À quoi il sert** : c'est la comparaison la plus directe avec l'indice 0 —
même source de prix, seuls les poids changent. C'est le geste central du
projet : « l'IPC dit +X %, avec votre structure de budget ça donne +Y % ».

---

## Indice 4 — `indice_observatoire`

**Ce que c'est** : le seul indice à sources de prix hétérogènes, assumé
comme tel. Quatre postes ont une source de prix propre (ni INSEE ni
Eurostat) ; tout le reste du panier retombe sur l'IPCH (ADR 0014).

| poste | source propre | qualité |
|---|---|---|
| `CP01` alimentation | Familles Rurales | `etude_publiee` |
| `CP041` loyers réels | Carte des loyers (min. Transition écologique) | `api_ouverte` |
| `CP045` énergie logement | CRE, tarif réglementé électricité | `api_ouverte` |
| `CP072` carburant | prix-carburants.gouv.fr | `api_ouverte` |

Ces quatre postes couvrent **24 à 43 % du panier selon le quintile**
(METHODOLOGIE §4.2). `CP042` (loyers imputés) reçoit l'indice de `CP041`
(ADR 0005), comme dans les autres indices.

**Poids** : profil de ménage HBS, identique aux indices 2 et 3.

**Pourquoi il existe** : c'est le seul indice où le projet ne se contente pas
de recombiner des séries officielles — il construit sa propre mesure sur les
postes où une source alternative crédible existe. C'est aussi le plus fragile
méthodologiquement, d'où le badge `qualite` obligatoire sur chacun de ses
postes (METHODOLOGIE §9), absent des quatre autres indices.

**Ce que ce n'est pas** : une tentative de mesurer une hypothétique
« inflation réelle ». Le traitement qualité (shrinkflation, ajustement
hédonique) reste celui des sources d'origine, non corrigé — voir limite 15 de
`docs/METHODOLOGIE.md`.

---

## Pour aller plus loin

- Formules exactes, ADR, limites détaillées → `docs/METHODOLOGIE.md`
- URL, licences, pièges de chaque source → `docs/SOURCES.md`
- Vocabulaire imposé pour l'interface et le code → `CONTEXT.md`
