"""Tests de `traitement.eurostat` — normalisation vers le schema prix.csv (ADR 0008)."""

import pandas as pd

from observatoire.traitement.eurostat import (
    normaliser_eurostat_ipch_officiel,
    normaliser_eurostat_prix_sous_classe,
)


def brut(lignes):
    """Construit la table `source, poste, periode, valeur` renvoyee par la collecte."""
    return pd.DataFrame(lignes, columns=["source", "poste", "periode", "valeur"])


def test_normaliser_produit_exactement_les_colonnes_du_schema():
    prix = brut([("eurostat", "TOTAL", "2019-12", 105.78)])

    out = normaliser_eurostat_ipch_officiel(prix)

    assert list(out.columns) == [
        "source",
        "poste",
        "periode",
        "valeur",
        "qualite",
        "interpole",
    ]


def test_normaliser_met_qualite_api_ouverte_sur_toutes_les_lignes():
    prix = brut(
        [
            ("eurostat", "TOTAL", "2019-12", 105.78),
            ("eurostat", "TOTAL", "2020-01", 106.0),
        ]
    )

    out = normaliser_eurostat_ipch_officiel(prix)

    assert (out["qualite"] == "api_ouverte").all()


def test_normaliser_met_interpole_false_sur_toutes_les_lignes():
    prix = brut(
        [
            ("eurostat", "TOTAL", "2019-12", 105.78),
            ("eurostat", "TOTAL", "2020-01", 106.0),
        ]
    )

    out = normaliser_eurostat_ipch_officiel(prix)

    assert (out["interpole"] == False).all()  # noqa: E712


def test_normaliser_conserve_source_poste_periode_valeur_inchanges():
    prix = brut([("eurostat", "TOTAL", "2019-12", 105.78)])

    out = normaliser_eurostat_ipch_officiel(prix)

    ligne = out.iloc[0]
    assert ligne["source"] == "eurostat"
    assert ligne["poste"] == "TOTAL"
    assert ligne["periode"] == "2019-12"
    assert ligne["valeur"] == 105.78


# --- normaliser_eurostat_prix_sous_classe -----------------------------------


def test_normaliser_prix_sous_classe_produit_exactement_les_colonnes_du_schema():
    prix = brut([("eurostat", "CP01111", "2019-12", 96.45)])

    out = normaliser_eurostat_prix_sous_classe(prix)

    assert list(out.columns) == [
        "source",
        "poste",
        "periode",
        "valeur",
        "qualite",
        "interpole",
    ]


def test_normaliser_prix_sous_classe_met_qualite_api_ouverte_et_interpole_false():
    prix = brut(
        [
            ("eurostat", "CP01111", "2019-12", 96.45),
            ("eurostat", "CP01112", "2019-12", 97.53),
        ]
    )

    out = normaliser_eurostat_prix_sous_classe(prix)

    assert (out["qualite"] == "api_ouverte").all()
    assert (out["interpole"] == False).all()  # noqa: E712
