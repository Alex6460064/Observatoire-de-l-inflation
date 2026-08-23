"""Tests de `traitement.carburants` -- propagation quotidienne, agregation
mensuelle et mix CP072 (ADR 0023)."""

import pandas as pd
import pytest

from observatoire.traitement.carburants import (
    agreger_mensuel,
    combiner_mix_cp072,
    construire_prix_carburant,
    propager_quotidien,
)


def _evenements(lignes):
    """lignes: (station_id, date, valeur)"""
    return pd.DataFrame(lignes, columns=["station_id", "date", "valeur"])


# --- propager_quotidien --------------------------------------------------------


def test_propager_quotidien_propage_le_dernier_prix_connu():
    evenements = _evenements(
        [
            ("s1", "2019-01-01", 1.30),
            ("s1", "2019-01-05", 1.40),
        ]
    )

    out = propager_quotidien(evenements)

    assert out["2019-01-01"] == 1.30
    assert out["2019-01-03"] == 1.30  # propage, pas de changement ce jour
    assert out["2019-01-05"] == 1.40


def test_propager_quotidien_moyenne_les_stations_disponibles():
    evenements = _evenements(
        [
            ("s1", "2019-01-01", 1.00),
            ("s2", "2019-01-03", 2.00),
        ]
    )

    out = propager_quotidien(evenements)

    assert out["2019-01-01"] == 1.00  # s2 pas encore connue
    assert out["2019-01-03"] == pytest.approx(1.5)  # s1 propage + s2


def test_propager_quotidien_leve_value_error_si_vide():
    with pytest.raises(ValueError):
        propager_quotidien(_evenements([]))


# --- agreger_mensuel ------------------------------------------------------------


def test_agreger_mensuel_moyenne_le_mois():
    quotidien = pd.Series(
        [1.0, 2.0, 3.0],
        index=pd.date_range("2019-01-01", periods=3, freq="D"),
    )

    out = agreger_mensuel(quotidien)

    assert list(out.index) == ["2019-01"]
    assert out["2019-01"] == 2.0


# --- construire_prix_carburant --------------------------------------------------


def test_construire_prix_carburant_filtre_et_nomme_le_poste():
    evenements = pd.DataFrame(
        [
            ("s1", "gazole", "2019-01-01", 1.30),
            ("s1", "sp95_e10", "2019-01-01", 1.45),
        ],
        columns=["station_id", "carburant", "date", "valeur"],
    )

    out = construire_prix_carburant(evenements, "gazole")

    assert (out["poste"] == "gazole").all()
    assert (out["source"] == "carburants").all()
    assert (out["qualite"] == "api_ouverte").all()
    assert (out["interpole"] == False).all()  # noqa: E712


def test_construire_prix_carburant_leve_value_error_si_carburant_absent():
    evenements = pd.DataFrame(
        [("s1", "gazole", "2019-01-01", 1.30)],
        columns=["station_id", "carburant", "date", "valeur"],
    )

    with pytest.raises(ValueError):
        construire_prix_carburant(evenements, "sp95_e10")


# --- combiner_mix_cp072 ----------------------------------------------------------


def _serie(poste, lignes):
    return pd.DataFrame(
        [(poste, periode, valeur) for periode, valeur in lignes],
        columns=["poste", "periode", "valeur"],
    ).assign(source="carburants", qualite="api_ouverte", interpole=False)


def test_combiner_mix_applique_les_parts():
    gazole = _serie("gazole", [("2019-01", 1.00)])
    sp95_e10 = _serie("sp95_e10", [("2019-01", 2.00)])

    out = combiner_mix_cp072(gazole, sp95_e10, part_gazole=0.6, part_sp95_e10=0.4)

    assert out.loc[0, "valeur"] == pytest.approx(0.6 * 1.00 + 0.4 * 2.00)
    assert out.loc[0, "poste"] == "CP072"


def test_combiner_mix_garde_seulement_les_periodes_communes():
    gazole = _serie("gazole", [("2019-01", 1.00), ("2019-02", 1.10)])
    sp95_e10 = _serie("sp95_e10", [("2019-01", 2.00)])

    out = combiner_mix_cp072(gazole, sp95_e10)

    assert list(out["periode"]) == ["2019-01"]


def test_combiner_mix_leve_value_error_si_parts_ne_somment_pas_a_1():
    gazole = _serie("gazole", [("2019-01", 1.00)])
    sp95_e10 = _serie("sp95_e10", [("2019-01", 2.00)])

    with pytest.raises(ValueError):
        combiner_mix_cp072(gazole, sp95_e10, part_gazole=0.5, part_sp95_e10=0.4)


def test_combiner_mix_leve_value_error_si_aucune_periode_commune():
    gazole = _serie("gazole", [("2019-01", 1.00)])
    sp95_e10 = _serie("sp95_e10", [("2019-02", 2.00)])

    with pytest.raises(ValueError):
        combiner_mix_cp072(gazole, sp95_e10)
