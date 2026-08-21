# Observatoire de l'Inflation

**L'IPC officiel mesure un panier moyen national. Ce n'est pas votre panier.**
Quelle différence cela fait-il sur la hausse des prix que vous subissez ?

Cet outil recombine des indices de prix officiels avec la structure de budget
réellement observée pour différents profils de ménage, et compare le résultat à
l'indice officiel. Toute la chaîne est traçable : chaque chiffre affiché remonte
à une source datée et à une formule écrite.

---

## ⚠️ Statut

**Le projet est en phase de conception méthodologique. Le pipeline n'est pas
encore écrit.**

| | état |
|---|---|
| Sources de données | **validées**, testées et documentées — 6 retenues, 5 écartées avec leur raison |
| Décisions d'architecture | **19 ADR** écrits |
| Méthodologie et formules | **écrites** et arrêtées |
| Pipeline de collecte | à écrire |
| Dashboard | à écrire |

Ce n'est pas un ordre habituel. Il est délibéré : sur un projet dont toute la
valeur repose sur l'exactitude de chiffres publics, décider de la méthode après
avoir écrit le code revient à justifier le code après coup.

---

## Ce que l'outil publie

Jamais un chiffre unique. **Cinq indices étiquetés**, chacun défini par un couple
explicite *(source de prix, source de poids)* :

| # | indice | prix | poids |
|---|---|---|---|
| 0 | IPC officiel | INSEE | panier moyen national |
| 1 | IPCH | Eurostat | officiels Eurostat |
| 2 | IPCH repondéré | Eurostat | profil de ménage |
| 3 | IPC repondéré | INSEE | profil de ménage |
| 4 | Indice Observatoire | sources propres, poste par poste | profil de ménage |

Les indices 2 et 3 ne diffèrent que par la source de prix : c'est ce qui rend
lisible la part de l'écart due à la méthode plutôt qu'à la personnalisation.

L'indice 4 est construit sur des sources indépendantes pour quatre postes —
alimentation, loyers, énergie du logement, carburants — soit **24 à 43 % du
panier** selon le niveau de revenu. Chacun de ses postes porte un **badge de
qualité de source** dans l'interface.

---

## Ce que l'outil ne fait pas

Il ne prétend pas mesurer une inflation « réelle » que l'INSEE cacherait. Cet
écart supposé — shrinkflation, ajustement hédonique — exigerait de suivre chaque
produit, son grammage et sa qualité sur plusieurs années. **Aucune source de ce
projet ne le fait, y compris ses sources propres.** Le terme est banni du code,
de la documentation et de l'interface.

Le projet change la source des prix et les poids. Il ne change jamais le
traitement qualité. C'est écrit dans
[l'ADR 0001](docs/adr/0001-bannir-le-terme-inflation-reelle.md).

---

## Trois limites à connaître avant de lire un chiffre

Les 17 limites connues sont dans
[`docs/METHODOLOGIE.md`](docs/METHODOLOGIE.md#8-limites), ordonnées par le poids
de panier qu'elles affectent. Les trois premières :

1. **La base 100 repose en partie sur des valeurs calculées.** La date de
   référence `2019-12` tombe dans un trou de publication des loyers et trois mois
   avant le départ de la série alimentaire. Au premier quintile, **322 ‰ du
   panier s'ancrent sur une valeur qu'aucune publication ne contient.**
2. **Les loyers mesurent autre chose que l'IPCH.** La Carte des loyers donne des
   loyers d'annonce ; l'IPCH mesure le loyer payé par l'ensemble du parc. L'écart
   est une différence de champ, **pas une erreur de l'INSEE**.
3. **Le panier alimentaire est normatif, pas observé.** Il monte
   systématiquement *moins* que l'IPC alimentaire — de 3 à 5 points par an
   pendant la flambée. Sur ce poste, l'Observatoire dira que l'INSEE
   **surestime** la hausse.

---

## Installation

Environnement géré par [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                              # installe l'environnement
uv run streamlit run src/observatoire/dashboard.py   # lance le dashboard
uv run pytest                                        # tests
uv run ruff check . && uv run ruff format .          # lint + format
```

Aucune clé d'API n'est nécessaire : les six sources retenues sont publiques et
sans authentification. Voir [`.env.example`](.env.example).

---

## Structure

```
docs/
  SOURCES.md        sources validées et écartées — URL, date, format, licence, pièges
  METHODOLOGIE.md   formules, hypothèses, et les 17 limites
  adr/              19 décisions d'architecture, avec les alternatives écartées
CONTEXT.md          glossaire contraignant — les termes bannis y sont listés
src/observatoire/
  collecte/         télécharge, ne transforme rien
  traitement/       nettoie et normalise
  analyse/          calcule, aucun appel réseau
  viz/              composants Plotly réutilisables
  dashboard.py      application Streamlit
data/
  raw/              brut téléchargé, jamais versionné, jamais modifié à la main
  manual/           chiffres publiés sans API, versionnés, schéma validé
  processed/        sorties du pipeline, versionnées en CSV
```

La séparation est stricte : **une fonction de collecte ne calcule rien, une
fonction d'analyse ne fait aucun appel réseau.** Le dashboard ne fait aucun appel
réseau du tout — tout ce qui ne dépend pas des choix de l'utilisateur est
pré-calculé et versionné
([ADR 0008](docs/adr/0008-frontiere-pipeline-dashboard.md)).

---

## Sources

Six sources retenues, toutes publiques :
INSEE (API BDM) · Eurostat (IPCH, HBS, EU-SILC) · Commission de régulation de
l'énergie · Carte des loyers (min. de la Transition écologique) ·
prix-carburants.gouv.fr · Familles Rurales (Observatoire des prix).

Cinq candidates ont été testées puis **écartées**, chacune avec la mesure qui l'a
écartée — parmi elles Open Prices et l'API OCDE. Les raisons sont dans
[`docs/SOURCES.md`](docs/SOURCES.md) : les relire avant d'en reproposer une.

Les données publiques réutilisées le sont sous licence ouverte ou sous le régime
de l'article L322-1 du CRPA, qui impose la non-altération, la mention de la
source et celle de sa date de mise à jour.

---

## Licence

Le code est sous licence MIT. Les données restent la propriété de leurs
producteurs, aux conditions rappelées ci-dessus.
