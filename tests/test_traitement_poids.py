"""Tests de `traitement.poids.transposer_poids_hbs` -- formule et cas
particuliers de docs/METHODOLOGIE.md section 3.3 (ADR 0018).

Fixtures synthetiques uniquement : aucun appel reseau, independant du vrai
`data/manual/correspondance_coicop.csv`.
"""

import pandas as pd
import pytest

from observatoire.traitement.poids import transposer_poids_hbs


def correspondance(paires):
    """Construit une table `coicop_2018, coicop_1999` a partir de tuples."""
    return pd.DataFrame(paires, columns=["coicop_2018", "coicop_1999"])


def test_transposition_nominale_repartit_au_prorata_et_conserve_la_masse():
    # 80 ‰ repartis au prorata de 30/40 et 10/40 -> 60 et 20, somme = 80.
    poids_hbs = pd.Series({"CP12": 80.0})
    poids_iw = pd.Series({"CP1211": 30.0, "CP1212": 10.0})
    table = correspondance([("CP1211", "CP12"), ("CP1212", "CP12")])

    out = transposer_poids_hbs(poids_hbs, poids_iw, table)

    assert out["CP1211"] == pytest.approx(60.0)
    assert out["CP1212"] == pytest.approx(20.0)
    assert out.sum() == pytest.approx(80.0)


def test_transposition_cas_bijectif_sans_poids_ipch():
    # CP042-like : une seule sous-classe cible, aucun poids IPCH atteignable
    # (absente de poids_iw) -> passage integral du poids du groupe.
    poids_hbs = pd.Series({"CP042": 169.0})
    poids_iw = pd.Series({"CP0111": 500.0})  # sans rapport avec CP042
    table = correspondance([("CP04211", "CP042")])

    out = transposer_poids_hbs(poids_hbs, poids_iw, table)

    assert out["CP04211"] == pytest.approx(169.0)


def test_transposition_sous_classe_multi_source_repartit_a_parts_egales():
    # CP0731 est alimentee par CP07 et CP12 : son poids IPCH (20) est reparti
    # a parts egales (10/10) avant le calcul du ratio de chaque groupe.
    poids_hbs = pd.Series({"CP07": 100.0, "CP12": 50.0})
    poids_iw = pd.Series({"CP0731": 20.0, "CP0732": 30.0})
    table = correspondance(
        [
            ("CP0731", "CP07"),
            ("CP0732", "CP07"),
            ("CP0731", "CP12"),
        ]
    )

    out = transposer_poids_hbs(poids_hbs, poids_iw, table)

    # CP07 : denom = 10 (CP0731 effectif) + 30 (CP0732) = 40
    #   CP0731 <- 100 * 10/40 = 25 ; CP0732 <- 100 * 30/40 = 75
    # CP12 : denom = 10 (CP0731 effectif) -> passage integral -> 50
    assert out["CP0731"] == pytest.approx(25.0 + 50.0)
    assert out["CP0732"] == pytest.approx(75.0)
    # Masse conservee par groupe : CP07 -> 25 + 75 = 100 ; CP12 -> 50.
    assert out["CP0732"] + 25.0 == pytest.approx(100.0)


def test_transposition_plusieurs_cibles_sans_poids_ipch_repartit_a_parts_egales():
    # CP042-like generalise (docs/METHODOLOGIE.md 3.3, mise a jour 22/08/2026) :
    # deux sous-classes cibles, aucune n'a de poids IPCH -> moitie chacune.
    poids_hbs = pd.Series({"CP042": 169.0})
    poids_iw = pd.Series({"CP0111": 500.0})  # sans rapport avec CP042
    table = correspondance([("CP04210", "CP042"), ("CP04220", "CP042")])

    out = transposer_poids_hbs(poids_hbs, poids_iw, table)

    assert out["CP04210"] == pytest.approx(84.5)
    assert out["CP04220"] == pytest.approx(84.5)
    assert out.sum() == pytest.approx(169.0)


def test_transposition_leve_erreur_si_groupe_absent_de_la_correspondance():
    poids_hbs = pd.Series({"CP999": 10.0})
    poids_iw = pd.Series({"CP1211": 30.0})
    table = correspondance([("CP1211", "CP12")])

    with pytest.raises(ValueError, match="CP999"):
        transposer_poids_hbs(poids_hbs, poids_iw, table)


def test_transposition_leve_erreur_si_poids_ipch_invalide():
    # Une sous-classe presente mais avec une valeur NaN (donnee Eurostat
    # corrompue) ne doit jamais produire une part silencieusement fausse.
    poids_hbs = pd.Series({"CP08": 40.0})
    poids_iw = pd.Series({"CP0811": float("nan"), "CP0812": 15.0})
    table = correspondance([("CP0811", "CP08"), ("CP0812", "CP08")])

    with pytest.raises(ValueError, match="CP08"):
        transposer_poids_hbs(poids_hbs, poids_iw, table)
