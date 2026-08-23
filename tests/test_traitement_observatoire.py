"""Tests de `traitement.observatoire` -- assemblage de l'indice 4 par
substitution groupe -> sous-classes (ADR 0023)."""

import pandas as pd
import pytest

from observatoire.traitement.observatoire import assembler_prix_indice_observatoire


def _prix(lignes):
    """lignes: (source, poste, periode, valeur, qualite, interpole)"""
    return pd.DataFrame(
        lignes, columns=["source", "poste", "periode", "valeur", "qualite", "interpole"]
    )


def _correspondance(lignes):
    """lignes: (coicop_2018, coicop_1999)"""
    return pd.DataFrame(lignes, columns=["coicop_2018", "coicop_1999"])


def test_substitue_les_sous_classes_du_groupe_couvert():
    prix_ipch = _prix(
        [
            ("eurostat", "CP04110", "2019-01", 100.0, "api_ouverte", False),
            ("eurostat", "CP07211", "2019-01", 50.0, "api_ouverte", False),
        ]
    )
    correspondance = _correspondance([("CP04110", "CP041"), ("CP07211", "CP072")])
    cp041 = _prix([("carte_des_loyers", "CP041", "2019-01", 8.0, "api_ouverte", False)])

    out = assembler_prix_indice_observatoire(
        prix_ipch, correspondance, {"CP041": cp041}
    )
    ligne = out.loc[out["poste"] == "CP04110"].iloc[0]

    assert ligne["valeur"] == 8.0
    assert ligne["source"] == "carte_des_loyers"


def test_garde_ipch_pour_les_sous_classes_non_couvertes():
    prix_ipch = _prix(
        [
            ("eurostat", "CP04110", "2019-01", 100.0, "api_ouverte", False),
            ("eurostat", "CP07211", "2019-01", 50.0, "api_ouverte", False),
        ]
    )
    correspondance = _correspondance([("CP04110", "CP041"), ("CP07211", "CP072")])
    cp041 = _prix([("carte_des_loyers", "CP041", "2019-01", 8.0, "api_ouverte", False)])

    out = assembler_prix_indice_observatoire(
        prix_ipch, correspondance, {"CP041": cp041}
    )
    ligne = out.loc[out["poste"] == "CP07211"].iloc[0]

    assert ligne["valeur"] == 50.0
    assert ligne["source"] == "eurostat"


def test_cp042_recoit_la_meme_table_que_cp041():
    prix_ipch = _prix(
        [
            ("eurostat", "CP04110", "2019-01", 100.0, "api_ouverte", False),
            ("eurostat", "CP04210", "2019-01", 999.0, "api_ouverte", False),
        ]
    )
    correspondance = _correspondance([("CP04110", "CP041"), ("CP04210", "CP042")])
    cp041 = _prix([("carte_des_loyers", "CP041", "2019-01", 8.0, "api_ouverte", False)])

    out = assembler_prix_indice_observatoire(
        prix_ipch, correspondance, {"CP041": cp041, "CP042": cp041}
    )

    assert out.loc[out["poste"] == "CP04110", "valeur"].iloc[0] == 8.0
    assert out.loc[out["poste"] == "CP04210", "valeur"].iloc[0] == 8.0


def test_serie_propre_ne_couvre_que_ses_propres_periodes():
    prix_ipch = _prix(
        [
            ("eurostat", "CP04110", "1996-01", 60.0, "api_ouverte", False),
            ("eurostat", "CP04110", "2019-01", 100.0, "api_ouverte", False),
        ]
    )
    correspondance = _correspondance([("CP04110", "CP041")])
    cp041 = _prix([("carte_des_loyers", "CP041", "2019-01", 8.0, "api_ouverte", False)])

    out = assembler_prix_indice_observatoire(
        prix_ipch, correspondance, {"CP041": cp041}
    )

    assert list(out["periode"]) == ["2019-01"]


def test_leve_value_error_si_groupe_sans_sous_classe_cible():
    prix_ipch = _prix([("eurostat", "CP04110", "2019-01", 100.0, "api_ouverte", False)])
    correspondance = _correspondance([("CP04110", "CP041")])
    cp099 = _prix([("x", "CP099", "2019-01", 1.0, "api_ouverte", False)])

    with pytest.raises(ValueError):
        assembler_prix_indice_observatoire(prix_ipch, correspondance, {"CP099": cp099})


def test_colonnes_de_sortie():
    prix_ipch = _prix([("eurostat", "CP04110", "2019-01", 100.0, "api_ouverte", False)])
    correspondance = _correspondance([("CP04110", "CP041")])

    out = assembler_prix_indice_observatoire(prix_ipch, correspondance, {})

    assert list(out.columns) == [
        "source",
        "poste",
        "periode",
        "valeur",
        "qualite",
        "interpole",
    ]
