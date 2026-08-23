"""Tests de `traitement.cre` -- calcul du cout CP045 et etalement mensuel
en escalier (ADR 0023)."""

import pandas as pd
import pytest

from observatoire.traitement.cre import calculer_cout_annuel, etendre_mensuel


def _bareme(lignes):
    """lignes: (date_debut, date_fin_ou_None, puissance_kva, fixe_ttc, variable_ttc)"""
    return pd.DataFrame(
        [
            {
                "date_debut": pd.Timestamp(d),
                "date_fin": pd.Timestamp(f) if f else None,
                "puissance_kva": p,
                "part_fixe_ttc": fixe,
                "part_variable_ttc": var,
            }
            for d, f, p, fixe, var in lignes
        ]
    )


# --- calculer_cout_annuel -----------------------------------------------------


def test_calculer_cout_filtre_sur_la_puissance_retenue():
    bareme = _bareme(
        [
            ("2012-07-23", "2013-07-31", 3, 69.37, 0.1256),
            ("2012-07-23", "2013-07-31", 6, 82.98, 0.1263),
        ]
    )

    out = calculer_cout_annuel(bareme, puissance_kva=6, consommation_annuelle_kwh=4500)

    assert len(out) == 1
    assert out.loc[0, "valeur"] == pytest.approx(82.98 + 0.1263 * 4500)


def test_calculer_cout_leve_value_error_si_puissance_absente():
    bareme = _bareme([("2012-07-23", "2013-07-31", 3, 69.37, 0.1256)])

    with pytest.raises(ValueError):
        calculer_cout_annuel(bareme, puissance_kva=6, consommation_annuelle_kwh=4500)


# --- etendre_mensuel -----------------------------------------------------------


def test_etendre_mensuel_produit_une_ligne_par_mois_de_validite():
    cout = pd.DataFrame(
        [
            {
                "date_debut": pd.Timestamp("2012-07-23"),
                "date_fin": pd.Timestamp("2012-10-15"),
                "valeur": 100.0,
            }
        ]
    )

    out = etendre_mensuel(cout, derniere_periode="2012-12")

    assert list(out["periode"]) == ["2012-07", "2012-08", "2012-09", "2012-10"]
    assert (out["valeur"] == 100.0).all()


def test_etendre_mensuel_prolonge_le_bareme_en_cours_jusqu_a_derniere_periode():
    cout = pd.DataFrame(
        [
            {
                "date_debut": pd.Timestamp("2026-02-01"),
                "date_fin": None,
                "valeur": 200.0,
            }
        ]
    )

    out = etendre_mensuel(cout, derniere_periode="2026-05")

    assert list(out["periode"]) == ["2026-02", "2026-03", "2026-04", "2026-05"]


def test_etendre_mensuel_marque_interpole_false_partout():
    cout = pd.DataFrame(
        [
            {
                "date_debut": pd.Timestamp("2012-07-23"),
                "date_fin": pd.Timestamp("2012-08-15"),
                "valeur": 100.0,
            }
        ]
    )

    out = etendre_mensuel(cout, derniere_periode="2012-12")

    assert (out["interpole"] == False).all()  # noqa: E712


def test_etendre_mensuel_ne_repete_pas_un_mois_de_transition():
    cout = pd.DataFrame(
        [
            {
                "date_debut": pd.Timestamp("2012-07-23"),
                "date_fin": pd.Timestamp("2013-07-31"),
                "valeur": 100.0,
            },
            {
                "date_debut": pd.Timestamp("2013-08-01"),
                "date_fin": pd.Timestamp("2014-10-31"),
                "valeur": 110.0,
            },
        ]
    )

    out = etendre_mensuel(cout, derniere_periode="2014-12").set_index("periode")

    assert out.loc["2013-07", "valeur"] == 100.0
    assert out.loc["2013-08", "valeur"] == 110.0
    assert len(out) == len(set(out.index))


def test_etendre_mensuel_leve_value_error_si_plusieurs_lignes_ouvertes():
    cout = pd.DataFrame(
        [
            {
                "date_debut": pd.Timestamp("2012-07-23"),
                "date_fin": None,
                "valeur": 100.0,
            },
            {
                "date_debut": pd.Timestamp("2013-08-01"),
                "date_fin": None,
                "valeur": 110.0,
            },
        ]
    )

    with pytest.raises(ValueError):
        etendre_mensuel(cout, derniere_periode="2014-12")


def test_etendre_mensuel_source_et_poste_constants():
    cout = pd.DataFrame(
        [
            {
                "date_debut": pd.Timestamp("2012-07-23"),
                "date_fin": pd.Timestamp("2012-08-15"),
                "valeur": 100.0,
            }
        ]
    )

    out = etendre_mensuel(cout, derniere_periode="2012-12")

    assert (out["source"] == "cre").all()
    assert (out["poste"] == "CP045").all()
    assert (out["qualite"] == "api_ouverte").all()
