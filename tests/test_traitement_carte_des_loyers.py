"""Tests de `traitement.carte_des_loyers` -- agregation ponderee et
construction de la serie annuelle (ADR 0023)."""

import pandas as pd
import pytest

from observatoire.traitement.carte_des_loyers import (
    calculer_locatif_prive,
    calculer_moyenne_ponderee,
    construire_points_annuels,
)

# --- calculer_locatif_prive -----------------------------------------------------


def test_calculer_locatif_prive_soustrait_le_hlm():
    recensement = pd.DataFrame(
        {
            "codgeo": ["75056", "13055"],
            "p22_rp_loc": [50, 20],
            "p22_rp_lochlmv": [10, 0],
        }
    )

    out = calculer_locatif_prive(recensement).set_index("codgeo")

    assert out.loc["75056", "locatif_prive"] == 40
    assert out.loc["13055", "locatif_prive"] == 20


def test_calculer_locatif_prive_colonnes_de_sortie():
    recensement = pd.DataFrame(
        {"codgeo": ["75056"], "p22_rp_loc": [50], "p22_rp_lochlmv": [10]}
    )

    out = calculer_locatif_prive(recensement)

    assert list(out.columns) == ["codgeo", "locatif_prive"]


# --- calculer_moyenne_ponderee ------------------------------------------------


def test_calculer_moyenne_ponderee_pondere_par_locatif_prive():
    loyers = pd.DataFrame(
        {"commune_insee": ["75056", "13055"], "loyer_m2": [30.0, 12.0]}
    )
    poids = pd.DataFrame({"codgeo": ["75056", "13055"], "locatif_prive": [900, 100]})

    out = calculer_moyenne_ponderee(loyers, poids)

    assert out == pytest.approx((30.0 * 900 + 12.0 * 100) / 1000)


def test_calculer_moyenne_ponderee_ignore_les_communes_non_jointes():
    loyers = pd.DataFrame(
        {"commune_insee": ["75056", "99999"], "loyer_m2": [30.0, 1000.0]}
    )
    poids = pd.DataFrame({"codgeo": ["75056"], "locatif_prive": [900]})

    out = calculer_moyenne_ponderee(loyers, poids)

    assert out == pytest.approx(30.0)


def test_calculer_moyenne_ponderee_leve_value_error_si_jointure_vide():
    loyers = pd.DataFrame({"commune_insee": ["75056"], "loyer_m2": [30.0]})
    poids = pd.DataFrame({"codgeo": ["13055"], "locatif_prive": [100]})

    with pytest.raises(ValueError):
        calculer_moyenne_ponderee(loyers, poids)


def test_calculer_moyenne_ponderee_leve_value_error_si_poids_total_nul():
    loyers = pd.DataFrame({"commune_insee": ["75056"], "loyer_m2": [30.0]})
    poids = pd.DataFrame({"codgeo": ["75056"], "locatif_prive": [0]})

    with pytest.raises(ValueError):
        calculer_moyenne_ponderee(loyers, poids)


# --- construire_points_annuels -------------------------------------------------


def test_construire_points_annuels_ancre_en_janvier():
    out = construire_points_annuels({2018: 10.0, 2022: 12.0})

    assert list(out["periode"]) == ["2018-01", "2022-01"]


def test_construire_points_annuels_colonnes_et_qualite():
    out = construire_points_annuels({2018: 10.0})

    assert list(out.columns) == [
        "source",
        "poste",
        "periode",
        "valeur",
        "qualite",
        "interpole",
    ]
    assert (out["source"] == "carte_des_loyers").all()
    assert (out["poste"] == "CP041").all()
    assert (out["qualite"] == "api_ouverte").all()
    assert (out["interpole"] == False).all()  # noqa: E712


def test_construire_points_annuels_leve_value_error_si_vide():
    with pytest.raises(ValueError):
        construire_points_annuels({})
