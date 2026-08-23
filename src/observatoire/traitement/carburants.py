"""Normalisation de la sortie `collecte.carburants` en serie de prix `CP072`
(ADR 0014, ADR 0023).

Algorithme documente dans docs/SOURCES.md : "construire une moyenne
mensuelle nationale impose de propager le dernier prix connu de chaque
station sur chaque jour, puis d'agreger" -- une moyenne directe des
changements de prix serait biaisee vers les stations qui changent leurs prix
souvent. Moyenne **non ponderee** par station, faute de volumes de vente
publies (meme section).

Le mix retenu (ADR 0023, `data/manual/parametres.csv`) combine `gazole` et
`sp95_e10` (67,3 % / 32,7 %, bilan UFIP 2025) en une seule serie `CP072` --
`SP98`, `SP95` sans ethanol et `E85` ne sont pas separes.

Aucun appel reseau, aucun effet de bord.
"""

from __future__ import annotations

import pandas as pd

POSTE_CP072 = "CP072"
SOURCE_CARBURANTS = "carburants"
QUALITE_CARBURANTS = "api_ouverte"

# ADR 0023 / data/manual/parametres.csv.
PART_GAZOLE = 0.673
PART_SP95_E10 = 0.327


def propager_quotidien(evenements_carburant: pd.DataFrame) -> pd.Series:
    """Moyenne nationale quotidienne, dernier prix connu propage par station.

    Args:
        evenements_carburant: sortie de
            `collecte.carburants.fetch_prix_carburants`, deja filtree sur un
            seul carburant (colonnes `station_id, date, valeur`).

    Returns:
        Serie indexee par date (index `DatetimeIndex` journalier, de la
        premiere a la derniere date presente dans `evenements_carburant`) :
        moyenne, sur les seules stations ayant deja publie un prix ce jour-la
        ou avant, de leur dernier prix connu.

    Raises:
        ValueError: `evenements_carburant` vide.
    """
    if evenements_carburant.empty:
        raise ValueError("propager_quotidien recoit une table vide.")

    grille = evenements_carburant.pivot_table(
        index="date", columns="station_id", values="valeur", aggfunc="last"
    )
    grille.index = pd.DatetimeIndex(grille.index)
    grille = grille.reindex(
        pd.date_range(grille.index.min(), grille.index.max(), freq="D")
    )
    grille = grille.ffill()

    return grille.mean(axis=1, skipna=True)


def agreger_mensuel(quotidien: pd.Series) -> pd.Series:
    """Moyenne mensuelle nationale a partir de la serie quotidienne.

    Args:
        quotidien: sortie de `propager_quotidien`.

    Returns:
        Serie indexee par periode `AAAA-MM`.
    """
    mensuel = quotidien.resample("MS").mean()
    mensuel.index = mensuel.index.strftime("%Y-%m")
    return mensuel


def construire_prix_carburant(evenements: pd.DataFrame, carburant: str) -> pd.DataFrame:
    """Table de prix mensuelle pour un seul carburant (`gazole` ou `sp95_e10`).

    Args:
        evenements: sortie de `collecte.carburants.fetch_prix_carburants`,
            un ou plusieurs millesimes concatenes.
        carburant: code interne (`collecte.carburants.CARBURANTS_RETENUS`).

    Returns:
        Table `source, poste, periode, valeur, qualite, interpole` --
        `poste` porte le code carburant, `interpole` toujours `False`
        (couverture quotidienne continue, ADR 0014, pas de trou a combler).

    Raises:
        ValueError: aucune ligne pour `carburant`.
    """
    filtre = evenements.loc[evenements["carburant"] == carburant]
    if filtre.empty:
        raise ValueError(f"Aucun evenement pour le carburant '{carburant}'.")

    mensuel = agreger_mensuel(propager_quotidien(filtre))

    table = mensuel.rename("valeur").reset_index()
    table = table.rename(columns={table.columns[0]: "periode"})
    table["source"] = SOURCE_CARBURANTS
    table["poste"] = carburant
    table["qualite"] = QUALITE_CARBURANTS
    table["interpole"] = False
    return table[["source", "poste", "periode", "valeur", "qualite", "interpole"]]


def combiner_mix_cp072(
    prix_gazole: pd.DataFrame,
    prix_sp95_e10: pd.DataFrame,
    part_gazole: float = PART_GAZOLE,
    part_sp95_e10: float = PART_SP95_E10,
) -> pd.DataFrame:
    """Combine gazole et SP95-E10 en une seule serie `CP072` (ADR 0023).

    `valeur = part_gazole * prix_gazole + part_sp95_e10 * prix_sp95_e10`,
    memes periodes uniquement (intersection).

    Args:
        prix_gazole: sortie de `construire_prix_carburant(..., "gazole")`.
        prix_sp95_e10: sortie de `construire_prix_carburant(..., "sp95_e10")`.
        part_gazole: part du mix, defaut ADR 0023 (67,3 %, UFIP 2025).
        part_sp95_e10: part du mix, defaut ADR 0023 (32,7 %).

    Returns:
        Table `source, poste, periode, valeur, qualite, interpole`, poste
        `CP072`.

    Raises:
        ValueError: aucune periode commune aux deux tables, ou
            `part_gazole + part_sp95_e10` ne somme pas a 1 (a 1e-6 pres).
    """
    if abs((part_gazole + part_sp95_e10) - 1.0) > 1e-6:
        raise ValueError(
            f"part_gazole ({part_gazole}) + part_sp95_e10 ({part_sp95_e10}) "
            "ne somme pas a 1."
        )

    fusion = prix_gazole.merge(
        prix_sp95_e10, on="periode", suffixes=("_gazole", "_sp95_e10")
    )
    if fusion.empty:
        raise ValueError("Aucune periode commune entre les series gazole et sp95_e10.")

    fusion["valeur"] = (
        part_gazole * fusion["valeur_gazole"]
        + part_sp95_e10 * fusion["valeur_sp95_e10"]
    )
    fusion["source"] = SOURCE_CARBURANTS
    fusion["poste"] = POSTE_CP072
    fusion["qualite"] = QUALITE_CARBURANTS
    fusion["interpole"] = fusion["interpole_gazole"] | fusion["interpole_sp95_e10"]

    return (
        fusion[["source", "poste", "periode", "valeur", "qualite", "interpole"]]
        .sort_values("periode")
        .reset_index(drop=True)
    )
