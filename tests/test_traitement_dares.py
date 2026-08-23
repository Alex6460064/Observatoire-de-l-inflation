"""Tests de `traitement.dares` -- normalisation et interpolation (ADR 0022)."""

import pandas as pd

from observatoire.traitement.dares import completer_mensuel, nettoyer_salaire_smb


def brut(lignes):
    """Construit la table `source, poste, periode, valeur` renvoyee par la collecte."""
    return pd.DataFrame(lignes, columns=["source", "poste", "periode", "valeur"])


# --- nettoyer_salaire_smb ----------------------------------------------------


def test_nettoyer_produit_exactement_les_colonnes_du_schema():
    prix = brut([("dares", "ENS", "2019-12", 103.8)])

    out = nettoyer_salaire_smb(prix)

    assert list(out.columns) == [
        "source",
        "poste",
        "periode",
        "valeur",
        "qualite",
        "interpole",
    ]


def test_nettoyer_met_qualite_etude_publiee():
    prix = brut([("dares", "ENS", "2019-12", 103.8)])

    out = nettoyer_salaire_smb(prix)

    assert (out["qualite"] == "etude_publiee").all()


def test_nettoyer_met_interpole_false_sur_toutes_les_lignes():
    prix = brut(
        [
            ("dares", "ENS", "2019-12", 103.8),
            ("dares", "ENS", "2020-03", 104.8),
        ]
    )

    out = nettoyer_salaire_smb(prix)

    assert (out["interpole"] == False).all()  # noqa: E712


# --- completer_mensuel --------------------------------------------------------


def _propre(lignes):
    """Construit une table `nettoyer_salaire_smb`-shaped pour les tests."""
    return pd.DataFrame(
        [(s, p, per, v, "etude_publiee", False) for s, p, per, v in lignes],
        columns=["source", "poste", "periode", "valeur", "qualite", "interpole"],
    )


def test_completer_mensuel_produit_une_ligne_par_mois():
    propre = _propre(
        [
            ("dares", "ENS", "2019-09", 103.3),
            ("dares", "ENS", "2019-12", 103.8),
        ]
    )

    out = completer_mensuel(propre)

    assert list(out["periode"]) == ["2019-09", "2019-10", "2019-11", "2019-12"]


def test_completer_mensuel_ne_modifie_pas_les_points_publies():
    propre = _propre(
        [
            ("dares", "ENS", "2019-09", 103.3),
            ("dares", "ENS", "2019-12", 103.8),
        ]
    )

    out = completer_mensuel(propre).set_index("periode")

    assert out.loc["2019-09", "valeur"] == 103.3
    assert out.loc["2019-12", "valeur"] == 103.8
    assert out.loc["2019-09", "interpole"] == False  # noqa: E712
    assert out.loc["2019-12", "interpole"] == False  # noqa: E712


def test_completer_mensuel_interpole_lineairement_les_mois_intermediaires():
    propre = _propre(
        [
            ("dares", "ENS", "2019-09", 100.0),
            ("dares", "ENS", "2019-12", 106.0),
        ]
    )

    out = completer_mensuel(propre).set_index("periode")

    assert out.loc["2019-10", "valeur"] == 102.0
    assert out.loc["2019-11", "valeur"] == 104.0
    assert out.loc["2019-10", "interpole"] == True  # noqa: E712
    assert out.loc["2019-11", "interpole"] == True  # noqa: E712


def test_completer_mensuel_comble_un_trimestre_entierement_absent():
    """Cas reel du fichier Dares : le trimestre 2020-03 est marque 'n.d.',
    donc absent de la table d'entree -- se comble comme un mois ordinaire,
    sur un intervalle de six mois plutot que trois."""
    propre = _propre(
        [
            ("dares", "ENS", "2019-12", 103.8),
            ("dares", "ENS", "2020-06", 104.8),
        ]
    )

    out = completer_mensuel(propre).set_index("periode")

    assert list(out.index) == [
        "2019-12",
        "2020-01",
        "2020-02",
        "2020-03",
        "2020-04",
        "2020-05",
        "2020-06",
    ]
    assert out.loc["2020-03", "valeur"] == 104.3
    assert out.loc["2020-03", "interpole"] == True  # noqa: E712


def test_completer_mensuel_ne_extrapole_pas():
    propre = _propre(
        [
            ("dares", "ENS", "2019-09", 100.0),
            ("dares", "ENS", "2019-12", 103.0),
        ]
    )

    out = completer_mensuel(propre)

    assert out["periode"].min() == "2019-09"
    assert out["periode"].max() == "2019-12"


def test_completer_mensuel_conserve_source_poste_qualite():
    propre = _propre(
        [
            ("dares", "ENS", "2019-09", 100.0),
            ("dares", "ENS", "2019-12", 103.0),
        ]
    )

    out = completer_mensuel(propre)

    assert (out["source"] == "dares").all()
    assert (out["poste"] == "ENS").all()
    assert (out["qualite"] == "etude_publiee").all()


def test_completer_mensuel_leve_value_error_si_plusieurs_postes():
    propre = _propre(
        [
            ("dares", "ENS", "2019-09", 100.0),
            ("dares", "AUTRE", "2019-12", 103.0),
        ]
    )

    try:
        completer_mensuel(propre)
        raised = False
    except ValueError:
        raised = True

    assert raised
