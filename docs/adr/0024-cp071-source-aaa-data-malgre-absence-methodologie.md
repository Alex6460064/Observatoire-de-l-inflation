# `CP071` (achat de véhicules) : adoption d'AAA Data malgré l'absence de méthodologie publiée

Session du 24/08/2026. L'ADR 0020 avait déjà évalué Argus/AAA Data pour
`CP071` et les avait écartés : « commercial, pas d'API — citation presse au
mieux ». Réévalué aujourd'hui sur décision explicite d'Alexandre : hors
data.gouv, aucune source gratuite de prix automobile n'aura jamais de
protocole publié, et une série chiffrée avec source citée est préférable à
l'absence de série.

## Vérifications faites aujourd'hui (confirment l'ADR 0020, rien de nouveau)

- **AAA Data** : communiqués de presse périodiques (« Intelligence Auto
  n°X », ~11/an), chiffres tête de gamme cités (36 700 € en 2024 ; 25 884 €
  essence / 42 788 € électrique en 2025), **aucune méthodologie publiée**
  (échantillon, base de transactions/immatriculations), aucun fichier
  téléchargeable ni API. Vérifié directement sur `aaa-data.fr` le
  24/08/2026.
- **Argus** : n'est pas un prix moyen de voiture neuve — c'est une cote de
  décote sur l'occasion (modèle propriétaire opaque, gratuit en version
  simplifiée seulement). Écarté : objet statistique différent, pas
  simplement une source plus faible.
- **`data.roole.fr`** republie ces chiffres de troisième main (« AAA Data
  via BFMTV », « L'Argus via Auto Infos/La Tribune Auto/Caradisiac ») —
  jamais le citer comme source ; toujours remonter à l'article AAA Data
  d'origine.

## Décision

`CP071` est adopté comme candidat source propre de l'indice Observatoire,
badge `qualite = synthese_presse` — définition `CONTEXT.md` : « un chiffre
repris d'un communiqué dont la méthode reste un secret commercial. Ni
rejouable ni auditable. » Cas d'usage exact.

**Source retenue : communiqués AAA Data (« Intelligence Auto »), jamais une
republication tierce (Roole, BFMTV, etc.).** Argus n'est pas retenu comme
source de prix.

**L'archivage trimestriel ADEME Car Labelling (ADR 0020) est arrêté.** AAA
Data devient la source retenue ; pas de double maintenance sur le candidat
écarté (`collecte.ademe`).

**Collecte des points historiques différée à une session dédiée**, pas
faite pendant ce grill (data entry hors périmètre d'une session de
documentation). `CP071` reste sur repli IPCH jusque-là — aucun changement à
`poids.csv`/`prix.csv` aujourd'hui.

## Conséquence sur `docs/METHODOLOGIE.md`

Le tableau 4.2 gagnera une cinquième ligne `CP071` (source AAA Data,
qualité `synthese_presse`) une fois les données collectées et vérifiées. Les
réserves déjà écrites dans l'ADR 0020 (prix non pondéré par les volumes de
vente réels, nature TTC/HT du prix non confirmée) s'appliquent aussi à AAA
Data : leurs chiffres agrégés ne détaillent pas plus le protocole que ne le
faisait ADEME.

## Écarté

Rien de nouveau par rapport au tableau de l'ADR 0020 (Institut Mobilités en
Transition + C-Ways : 2 éditions seulement, pas de série ; miroir GitHub de
l'ADEME : idem ADEME). Aucune meilleure option identifiée aujourd'hui.
