"""Tests de `traitement.poids.assembler_poids_quintiles` -- empile
`transposer_poids_hbs` sur les cinq modalites de quintile (ticket #11,
docs/METHODOLOGIE.md section 7, axe `quintile_revenu`).

Fixtures synthetiques uniquement : aucun appel reseau.
"""

import pandas as pd
import pytest

from observatoire.traitement.poids import assembler_poids_quintiles

QUINTILES = ("QU1", "QU2", "QU3", "QU4", "QU5")


def poids_hbs_long(valeurs_par_modalite):
    """Construit une table `modalite, poste, valeur` a partir d'un dict
    {modalite: {poste: valeur}}.
    """
    return pd.DataFrame(
        [
            {"modalite": modalite, "poste": poste, "valeur": valeur}
            for modalite, postes in valeurs_par_modalite.items()
            for poste, valeur in postes.items()
        ]
    )


def correspondance(paires):
    return pd.DataFrame(paires, columns=["coicop_2018", "coicop_1999"])


def _cinq_quintiles(poste_valeur):
    return {q: {"CP12": poste_valeur} for q in QUINTILES}


def test_assemblage_empile_les_cinq_modalites_avec_l_axe_quintile_revenu():
    hbs = poids_hbs_long(_cinq_quintiles(80.0))
    iw = pd.DataFrame([{"poste": "CP1211", "valeur": 30.0}])
    table = correspondance([("CP1211", "CP12")])

    out = assembler_poids_quintiles(hbs, iw, table)

    assert list(out.columns) == ["axe", "modalite", "poste", "pm"]
    assert (out["axe"] == "quintile_revenu").all()
    assert set(out["modalite"]) == set(QUINTILES)


def test_assemblage_transpose_chaque_modalite_independamment():
    # QU1 : un seul enfant (bijectif) -> poids intact. QU3 : prorata normal.
    hbs = poids_hbs_long(
        {
            "QU1": {"CP042": 169.0},
            "QU2": {"CP042": 100.0},
            "QU3": {"CP042": 154.0},
            "QU4": {"CP042": 120.0},
            "QU5": {"CP042": 169.0},
        }
    )
    iw = pd.DataFrame([{"poste": "CP0111", "valeur": 500.0}])  # sans rapport
    table = correspondance([("CP04210", "CP042")])

    out = assembler_poids_quintiles(hbs, iw, table).set_index(["modalite", "poste"]).pm

    assert out[("QU1", "CP04210")] == pytest.approx(169.0)
    assert out[("QU3", "CP04210")] == pytest.approx(154.0)


def test_assemblage_leve_erreur_si_une_modalite_de_quintile_manque():
    # QU5 absent : ecrire un poids.csv incomplet serait une donnee inventee.
    valeurs = _cinq_quintiles(80.0)
    del valeurs["QU5"]
    hbs = poids_hbs_long(valeurs)
    iw = pd.DataFrame([{"poste": "CP1211", "valeur": 30.0}])
    table = correspondance([("CP1211", "CP12")])

    with pytest.raises(ValueError, match="QU5"):
        assembler_poids_quintiles(hbs, iw, table)
