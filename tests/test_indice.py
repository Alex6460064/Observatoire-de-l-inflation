"""Tests de `analyse.indice` — les deux formules de docs/METHODOLOGIE.md 5.2.

Les valeurs attendues sont calculees a la main dans les commentaires : un test
qui reprendrait la formule du code ne prouverait rien.
"""

import pandas as pd
import pytest

from observatoire.analyse import indice, rebaser

REFERENCE = "2019-12"


def prix_long(lignes):
    """Construit une table longue `poste, periode, valeur`."""
    return pd.DataFrame(lignes, columns=["poste", "periode", "valeur"])


# --- rebaser ---------------------------------------------------------------


def test_rebaser_met_la_reference_a_100():
    prix = prix_long(
        [
            ("CP01", "2019-12", 107.01),
            ("CP01", "2026-03", 136.31),
        ]
    )

    out = rebaser(prix, REFERENCE)

    assert out.loc[out.periode == REFERENCE, "valeur"].item() == 100.0


def test_rebaser_conserve_l_evolution_relative():
    # 136,31 / 107,01 = 1,27381... soit +27,4 % (docs/SOURCES.md, CP01)
    prix = prix_long(
        [
            ("CP01", "2019-12", 107.01),
            ("CP01", "2026-03", 136.31),
        ]
    )

    out = rebaser(prix, REFERENCE)

    valeur = out.loc[out.periode == "2026-03", "valeur"].item()
    assert valeur == pytest.approx(127.381, abs=1e-3)


def test_rebaser_rebase_chaque_poste_sur_sa_propre_reference():
    prix = prix_long(
        [
            ("CP01", "2019-12", 200.0),
            ("CP01", "2020-01", 210.0),
            ("CP045", "2019-12", 50.0),
            ("CP045", "2020-01", 60.0),
        ]
    )

    out = rebaser(prix, REFERENCE).set_index(["poste", "periode"]).valeur

    assert out[("CP01", "2020-01")] == pytest.approx(105.0)
    assert out[("CP045", "2020-01")] == pytest.approx(120.0)


def test_rebaser_refuse_un_poste_sans_valeur_a_la_reference():
    # Laisser passer produirait un NaN silencieux, donc un poste qui disparait
    # de l'agregation sans que personne ne le voie.
    prix = prix_long(
        [
            ("CP01", "2019-12", 100.0),
            ("CP045", "2020-01", 60.0),
        ]
    )

    with pytest.raises(ValueError, match="CP045"):
        rebaser(prix, REFERENCE)


def test_rebaser_refuse_une_valeur_nulle_a_la_reference():
    prix = prix_long([("CP01", "2019-12", 0.0), ("CP01", "2020-01", 1.0)])

    with pytest.raises(ValueError, match="CP01"):
        rebaser(prix, REFERENCE)


# --- indice ----------------------------------------------------------------


def test_indice_agrege_au_prorata_des_poids():
    # 600 ‰ a 110 et 400 ‰ a 120  ->  (600*110 + 400*120) / 1000 = 114,0
    prix = prix_long(
        [
            ("CP01", "2020-01", 110.0),
            ("CP045", "2020-01", 120.0),
        ]
    )
    poids = pd.Series({"CP01": 600.0, "CP045": 400.0})

    out = indice(prix, poids)

    assert out["2020-01"] == pytest.approx(114.0)


def test_indice_vaut_100_quand_tous_les_postes_valent_100():
    prix = prix_long(
        [
            ("CP01", "2019-12", 100.0),
            ("CP045", "2019-12", 100.0),
        ]
    )
    poids = pd.Series({"CP01": 147.0, "CP045": 853.0})

    out = indice(prix, poids)

    assert out["2019-12"] == pytest.approx(100.0)


def test_indice_rend_une_serie_indexee_par_periode():
    prix = prix_long(
        [
            ("CP01", "2019-12", 100.0),
            ("CP01", "2020-01", 110.0),
        ]
    )
    poids = pd.Series({"CP01": 1000.0})

    out = indice(prix, poids)

    assert list(out.index) == ["2019-12", "2020-01"]


def test_indice_refuse_des_poids_qui_ne_somment_pas_a_1000():
    # ADR 0006 : apres ajustement au curseur, le vecteur est renormalise a
    # 1000 ‰. Un vecteur non normalise ici signale un bug en amont.
    prix = prix_long([("CP01", "2020-01", 110.0)])
    poids = pd.Series({"CP01": 900.0})

    with pytest.raises(ValueError, match="1000"):
        indice(prix, poids)


def test_indice_refuse_un_poste_pondere_absent_des_prix():
    # Ignorer silencieusement sous-estimerait l'indice sans le dire.
    prix = prix_long([("CP01", "2020-01", 110.0)])
    poids = pd.Series({"CP01": 600.0, "CP045": 400.0})

    with pytest.raises(ValueError, match="CP045"):
        indice(prix, poids)


def test_indice_refuse_une_periode_incomplete():
    # 2020-01 n'a pas CP045 : agreger donnerait un point calcule sur 600 ‰ de
    # panier, indiscernable d'un point complet sur la courbe.
    prix = prix_long(
        [
            ("CP01", "2019-12", 100.0),
            ("CP045", "2019-12", 100.0),
            ("CP01", "2020-01", 110.0),
        ]
    )
    poids = pd.Series({"CP01": 600.0, "CP045": 400.0})

    with pytest.raises(ValueError, match="2020-01"):
        indice(prix, poids)
