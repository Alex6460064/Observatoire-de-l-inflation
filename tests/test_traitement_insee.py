"""Tests de `traitement.insee` — normalisation vers le schema prix.csv (ADR 0008)."""

import pandas as pd

from observatoire.traitement.insee import normaliser_insee_ipc_officiel


def brut(lignes):
    """Construit la table `source, poste, periode, valeur` renvoyee par la collecte."""
    return pd.DataFrame(lignes, columns=["source", "poste", "periode", "valeur"])


def test_normaliser_produit_exactement_les_colonnes_du_schema():
    prix = brut([("insee", "00", "2019-12", 100.0)])

    out = normaliser_insee_ipc_officiel(prix)

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
            ("insee", "00", "2019-12", 100.0),
            ("insee", "00", "2020-01", 101.0),
        ]
    )

    out = normaliser_insee_ipc_officiel(prix)

    assert (out["qualite"] == "api_ouverte").all()


def test_normaliser_met_interpole_false_sur_toutes_les_lignes():
    prix = brut(
        [
            ("insee", "00", "2019-12", 100.0),
            ("insee", "00", "2020-01", 101.0),
        ]
    )

    out = normaliser_insee_ipc_officiel(prix)

    assert (out["interpole"] == False).all()  # noqa: E712


def test_normaliser_conserve_source_poste_periode_valeur_inchanges():
    prix = brut([("insee", "00", "2019-12", 100.0)])

    out = normaliser_insee_ipc_officiel(prix)

    ligne = out.iloc[0]
    assert ligne["source"] == "insee"
    assert ligne["poste"] == "00"
    assert ligne["periode"] == "2019-12"
    assert ligne["valeur"] == 100.0
