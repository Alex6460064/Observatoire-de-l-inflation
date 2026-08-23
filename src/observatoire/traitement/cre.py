"""Normalisation de la sortie `collecte.cre` en serie de prix `CP045`
(ADR 0014, ADR 0023).

Le tarif reglemente est un bareme (`abonnement + kWh x consommation`), pas un
prix : en faire un indice suppose un profil de consommation, choix de
l'Observatoire (ADR 0017). Les valeurs retenues sont dans
`data/manual/parametres.csv` -- puissance 6 kVA, consommation annuelle
4 500 kWh (sourcee CRE), option Base.

Aucun appel reseau, aucun effet de bord.
"""

from __future__ import annotations

import pandas as pd

POSTE_CP045 = "CP045"
SOURCE_CRE = "cre"
QUALITE_CRE = "api_ouverte"

# ADR 0023 / data/manual/parametres.csv.
PUISSANCE_RETENUE_KVA = 6
CONSOMMATION_ANNUELLE_KWH = 4500.0


def calculer_cout_annuel(
    bareme: pd.DataFrame,
    puissance_kva: int = PUISSANCE_RETENUE_KVA,
    consommation_annuelle_kwh: float = CONSOMMATION_ANNUELLE_KWH,
) -> pd.DataFrame:
    """Cout annuel TTC du profil retenu, pour chaque periode de bareme.

    `cout = part_fixe_ttc + part_variable_ttc * consommation_annuelle_kwh`
    (METHODOLOGIE section 6).

    Args:
        bareme: sortie de `collecte.cre.fetch_cre_tarif_base`.
        puissance_kva: puissance souscrite retenue.
        consommation_annuelle_kwh: consommation annuelle retenue.

    Returns:
        Table `date_debut, date_fin, valeur`, une ligne par periode de
        validite du bareme pour cette puissance.

    Raises:
        ValueError: aucune ligne du bareme ne correspond a `puissance_kva`.
    """
    filtre = bareme.loc[bareme["puissance_kva"] == puissance_kva].copy()
    if filtre.empty:
        raise ValueError(
            f"Aucune ligne du bareme CRE pour puissance_kva={puissance_kva}. "
            "Le schema ou les paliers publies ont peut-etre change."
        )

    filtre["valeur"] = filtre["part_fixe_ttc"] + (
        filtre["part_variable_ttc"] * consommation_annuelle_kwh
    )
    return (
        filtre[["date_debut", "date_fin", "valeur"]]
        .sort_values("date_debut")
        .reset_index(drop=True)
    )


def etendre_mensuel(cout_annuel: pd.DataFrame, derniere_periode: str) -> pd.DataFrame:
    """Etale chaque periode de bareme sur ses mois de validite (en escalier).

    Le tarif reglemente n'est **pas** interpole (METHODOLOGIE section 5.3) :
    un bareme vaut jusqu'au suivant, donc chaque mois de la periode de
    validite recoit exactement la meme valeur -- `interpole` reste `False`
    partout, ce sont des valeurs reellement en vigueur, pas calculees entre
    deux points.

    Args:
        cout_annuel: sortie de `calculer_cout_annuel`, triee par
            `date_debut`. La derniere ligne a `date_fin=None` (bareme en
            cours) : sa validite est prolongee jusqu'a `derniere_periode`.
        derniere_periode: derniere periode `AAAA-MM` a produire, pour borner
            la ligne de bareme en cours de validite.

    Returns:
        Table mensuelle `source, poste, periode, valeur, qualite,
        interpole`.

    Raises:
        ValueError: `cout_annuel` vide, ou une ligne autre que la derniere a
            `date_fin=None`.
    """
    if cout_annuel.empty:
        raise ValueError("etendre_mensuel recoit une table vide.")

    manquantes = cout_annuel["date_fin"].isna()
    if manquantes.sum() > 1 or (manquantes.any() and not manquantes.iloc[-1]):
        raise ValueError(
            "Seule la derniere periode du bareme peut avoir date_fin=None "
            "(bareme en cours de validite)."
        )

    lignes = []
    for _, ligne in cout_annuel.iterrows():
        debut = ligne["date_debut"].to_period("M")
        fin = (
            ligne["date_fin"].to_period("M")
            if pd.notna(ligne["date_fin"])
            else pd.Period(derniere_periode, freq="M")
        )
        for periode in pd.period_range(debut, fin, freq="M"):
            lignes.append((str(periode), ligne["valeur"]))

    table = (
        pd.DataFrame(lignes, columns=["periode", "valeur"])
        .drop_duplicates(subset="periode", keep="first")
        .sort_values("periode")
        .reset_index(drop=True)
    )
    table["source"] = SOURCE_CRE
    table["poste"] = POSTE_CP045
    table["qualite"] = QUALITE_CRE
    table["interpole"] = False
    return table[["source", "poste", "periode", "valeur", "qualite", "interpole"]]
