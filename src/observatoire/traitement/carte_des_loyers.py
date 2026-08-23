"""Normalisation de la sortie `collecte.carte_des_loyers` en serie de prix
`CP041` (ADR 0014, ADR 0023).

Agregation nationale ponderee par le parc locatif prive communal
(`collecte.recensement_logement`, recensement INSEE 2022), fichier
appartements seul (ADR 0023). Chaque millesime est ancre au mois de janvier
de son annee -- convention qui reproduit les "47 valeurs mensuelles
calculees" de l'ADR 0016 entre 2018-01 et 2022-01. Les mois manquants sont
ensuite combles par `traitement.interpolation.completer_mensuel`.

Aucun appel reseau, aucun effet de bord.
"""

from __future__ import annotations

import pandas as pd

POSTE_CP041 = "CP041"
SOURCE_CARTE_DES_LOYERS = "carte_des_loyers"
QUALITE_CARTE_DES_LOYERS = "api_ouverte"


def calculer_locatif_prive(recensement: pd.DataFrame) -> pd.DataFrame:
    """Parc locatif prive communal, a partir des colonnes brutes du recensement.

    `locatif_prive = p22_rp_loc - p22_rp_lochlmv` (residences principales
    louees hors HLM loue vide) -- champ de la Carte des loyers (loyers
    d'annonce), verifie le 21/08/2026 (docs/SOURCES.md). Deplace hors de
    `collecte.recensement_logement` : une fonction de collecte ne calcule
    rien (`CLAUDE.md`, revue de code du 23/08/2026).

    Args:
        recensement: sortie de
            `collecte.recensement_logement.fetch_recensement_logement_2022`.

    Returns:
        Table `codgeo, locatif_prive`.
    """
    out = recensement.copy()
    out["locatif_prive"] = out["p22_rp_loc"] - out["p22_rp_lochlmv"]
    return out[["codgeo", "locatif_prive"]]


def calculer_moyenne_ponderee(loyers: pd.DataFrame, poids: pd.DataFrame) -> float:
    """Moyenne nationale du loyer au m2, ponderee par le parc locatif prive.

    Args:
        loyers: sortie de `collecte.carte_des_loyers.fetch_carte_des_loyers`,
            colonnes `commune_insee, loyer_m2`.
        poids: sortie de
            `collecte.recensement_logement.fetch_recensement_logement_2022`,
            colonnes `codgeo, locatif_prive`.

    Returns:
        La moyenne ponderee de `loyer_m2` sur les communes communes aux deux
        tables (ADR 0023 : fichier appartements seul, maisons exclues du
        calcul en amont).

    Raises:
        ValueError: aucune commune commune aux deux tables, ou poids total
            nul ou negatif -- une jointure vide ou un poids degenere
            produirait une moyenne `NaN` ou absurde sans le signaler.
    """
    fusion = loyers.merge(
        poids, left_on="commune_insee", right_on="codgeo", how="inner"
    )
    if fusion.empty:
        raise ValueError(
            "Aucune commune commune entre la Carte des loyers et le "
            "recensement logement. Verifier le format des codes commune."
        )

    poids_total = fusion["locatif_prive"].sum()
    if poids_total <= 0:
        raise ValueError(
            f"Poids total du locatif prive non positif ({poids_total}). "
            "Verifier data/raw du recensement logement."
        )

    return float((fusion["loyer_m2"] * fusion["locatif_prive"]).sum() / poids_total)


def construire_points_annuels(valeurs: dict[int, float]) -> pd.DataFrame:
    """Table `source, poste, periode, valeur, qualite, interpole` de `CP041`.

    Un point par millesime, ancre en janvier (voir docstring du module).

    Args:
        valeurs: millesime (annee) -> moyenne nationale ponderee du loyer au
            m2, sortie de `calculer_moyenne_ponderee` pour chaque millesime
            de `collecte.carte_des_loyers.MILLESIMES_DISPONIBLES`.

    Returns:
        Table triee par periode, `interpole` toujours `False` -- ce sont les
        points reellement publies, avant `completer_mensuel`.

    Raises:
        ValueError: `valeurs` vide.
    """
    if not valeurs:
        raise ValueError("construire_points_annuels recoit un dictionnaire vide.")

    lignes = [
        (SOURCE_CARTE_DES_LOYERS, POSTE_CP041, f"{annee}-01", valeur)
        for annee, valeur in sorted(valeurs.items())
    ]
    table = pd.DataFrame(lignes, columns=["source", "poste", "periode", "valeur"])
    table["qualite"] = QUALITE_CARTE_DES_LOYERS
    table["interpole"] = False
    return table
