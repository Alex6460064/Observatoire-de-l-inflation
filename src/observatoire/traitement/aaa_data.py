"""Raccord IPCH -> AAA Data pour le groupe `CP071` (ADR 0021, ADR 0025).

Aucun appel reseau, aucun effet de bord. Prend en entree la serie IPCH deja
collectee (`collecte.eurostat.fetch_eurostat_prix_par_sous_classe(["CP071"])`)
et le registre des releves manuels deja charge
(`collecte.releves_manuels.charger_releves_manuels`).
"""

from __future__ import annotations

import pandas as pd

from observatoire.traitement.interpolation import completer_mensuel

QUALITE_AAA_DATA = "synthese_presse"

# Les deux seules lignes de data/manual/releves.csv sur la meme metrique
# (cumul depuis le 1er janvier, toutes motorisations) -- ADR 0025, decision 1.
PERIODE_TYPE_ANCRAGE = "cumul_ytd"
MOTORISATION_ANCRAGE = "globale"


def _mois_ancrage(periode_cumul: str) -> str:
    """`"2026-01/2026-05"` -> `"2026-05"` : ancrage au dernier mois du cumul."""
    return periode_cumul.split("/")[-1]


def extraire_ancrages(releves: pd.DataFrame) -> pd.DataFrame:
    """Filtre `releves.csv` sur les points exploitables pour le raccord.

    Args:
        releves: sortie de `collecte.releves_manuels.charger_releves_manuels(
            poste="CP071")`.

    Returns:
        Table `periode` (mois `AAAA-MM`, ancre au dernier mois du cumul),
        `valeur`, triee chronologiquement.

    Raises:
        ValueError: moins de deux ancrages disponibles -- un raccord (ADR
            0021) exige un ratio entre deux points.
    """
    ancrages = releves.loc[
        (releves["periode_type"] == PERIODE_TYPE_ANCRAGE)
        & (releves["motorisation"] == MOTORISATION_ANCRAGE)
    ].copy()

    if len(ancrages) < 2:
        raise ValueError(
            f"{len(ancrages)} ancrage(s) '{MOTORISATION_ANCRAGE}'/"
            f"'{PERIODE_TYPE_ANCRAGE}' dans releves.csv -- le raccord ADR 0021 "
            "exige au moins deux points sur la meme metrique."
        )

    ancrages["periode"] = ancrages["periode"].map(_mois_ancrage)
    return ancrages[["periode", "valeur"]].sort_values("periode").reset_index(drop=True)


def construire_serie_cp071(
    ipch_cp071: pd.DataFrame, releves: pd.DataFrame
) -> pd.DataFrame:
    """Construit la serie `CP071` complete : IPCH avant `t1`, raccord AAA Data apres.

    Args:
        ipch_cp071: table `source, poste, periode, valeur, qualite, interpole`
            du groupe IPCH `CP071` (`collecte.eurostat.
            fetch_eurostat_prix_par_sous_classe(["CP071"])`, normalisee).
        releves: sortie de `collecte.releves_manuels.charger_releves_manuels(
            poste="CP071")`.

    Returns:
        Table mensuelle `source, poste, periode, valeur, qualite, interpole`,
        de la premiere periode IPCH disponible jusqu'au dernier mois d'IPCH
        fourni :
        - avant `t1` : IPCH tel quel (`qualite="api_ouverte"`,
          `interpole=False`) ;
        - de `t1` a `t2` : niveau IPCH(t1) chaine sur le ratio AAA Data,
          interpolation lineaire entre les deux (ADR 0021, ADR 0015) ;
        - apres `t2` : derniere valeur maintenue a plat, `interpole=True`
          (ADR 0025, decision 3 -- aucune extrapolation de tendance).
    """
    ancrages = extraire_ancrages(releves)
    t1, t2 = ancrages["periode"].iloc[0], ancrages["periode"].iloc[-1]
    valeur_t1, valeur_t2 = ancrages["valeur"].iloc[0], ancrages["valeur"].iloc[-1]
    ratio = valeur_t2 / valeur_t1

    ipch = ipch_cp071.sort_values("periode").reset_index(drop=True)

    avant_t1 = ipch.loc[ipch["periode"] < t1].copy()

    niveau_t1 = ipch.loc[ipch["periode"] == t1, "valeur"]
    if niveau_t1.empty:
        raise ValueError(
            f"Aucune valeur IPCH CP071 pour l'ancrage t1={t1} -- verifier la "
            "couverture de collecte.eurostat.fetch_eurostat_prix_par_sous_classe."
        )
    niveau_t1 = niveau_t1.iloc[0]
    niveau_t2 = niveau_t1 * ratio

    raccord_points = pd.DataFrame(
        {
            "source": "observatoire",
            "poste": "CP071",
            "periode": [t1, t2],
            "valeur": [niveau_t1, niveau_t2],
            "qualite": QUALITE_AAA_DATA,
        }
    )
    raccord_mensuel = completer_mensuel(raccord_points)

    derniere_periode_ipch = ipch["periode"].max()
    apres_t2 = pd.period_range(
        pd.Period(t2, freq="M") + 1,
        pd.Period(derniere_periode_ipch, freq="M"),
        freq="M",
    )
    plat = pd.DataFrame(
        {
            "source": "observatoire",
            "poste": "CP071",
            "periode": apres_t2.strftime("%Y-%m"),
            "valeur": niveau_t2,
            "qualite": QUALITE_AAA_DATA,
            "interpole": True,
        }
    )

    return (
        pd.concat([avant_t1, raccord_mensuel, plat], ignore_index=True)
        .sort_values("periode")
        .reset_index(drop=True)[
            ["source", "poste", "periode", "valeur", "qualite", "interpole"]
        ]
    )
