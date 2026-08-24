import pandas as pd
import pytest

from observatoire.traitement.aaa_data import construire_serie_cp071, extraire_ancrages

PERIODES_IPCH = pd.period_range("2019-12", "2026-07", freq="M").strftime("%Y-%m")


def ipch_constant(valeur: float = 100.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source": "eurostat",
            "poste": "CP071",
            "periode": PERIODES_IPCH,
            "valeur": valeur,
            "qualite": "api_ouverte",
            "interpole": False,
        }
    )


def releves_deux_ancrages() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "poste": "CP071",
                "periode": "2025-01/2025-05",
                "periode_type": "cumul_ytd",
                "motorisation": "globale",
                "valeur": 35043.0,
            },
            {
                "poste": "CP071",
                "periode": "2026-01/2026-05",
                "periode_type": "cumul_ytd",
                "motorisation": "globale",
                "valeur": 36319.0,
            },
            # bruit : ne doit pas etre pris comme ancrage
            {
                "poste": "CP071",
                "periode": "2025",
                "periode_type": "annuel",
                "motorisation": "essence",
                "valeur": 25884.0,
            },
        ]
    )


def test_extraire_ancrages_filtre_globale_cumul_ytd():
    ancrages = extraire_ancrages(releves_deux_ancrages())

    assert list(ancrages["periode"]) == ["2025-05", "2026-05"]
    assert list(ancrages["valeur"]) == [35043.0, 36319.0]


def test_extraire_ancrages_leve_erreur_si_moins_de_deux_points():
    un_seul = releves_deux_ancrages().iloc[[0]]

    with pytest.raises(ValueError, match="ancrage"):
        extraire_ancrages(un_seul)


def test_avant_t1_egale_ipch_pur():
    resultat = construire_serie_cp071(ipch_constant(100.0), releves_deux_ancrages())

    avant = resultat[resultat["periode"] < "2025-05"]
    assert (avant["valeur"] == 100.0).all()
    assert (avant["qualite"] == "api_ouverte").all()
    assert not avant["interpole"].any()


def test_ancrages_chaines_sur_le_niveau_ipch():
    resultat = construire_serie_cp071(ipch_constant(100.0), releves_deux_ancrages())
    resultat = resultat.set_index("periode")

    assert resultat.loc["2025-05", "valeur"] == pytest.approx(100.0)
    assert resultat.loc["2026-05", "valeur"] == pytest.approx(100.0 * 36319 / 35043)
    assert resultat.loc["2025-05", "qualite"] == "synthese_presse"
    assert not resultat.loc["2025-05", "interpole"]
    assert not resultat.loc["2026-05", "interpole"]


def test_entre_ancrages_interpole():
    resultat = construire_serie_cp071(ipch_constant(100.0), releves_deux_ancrages())
    resultat = resultat.set_index("periode")

    milieu = resultat.loc["2025-11"]
    assert 100.0 < milieu["valeur"] < 100.0 * 36319 / 35043
    assert milieu["interpole"]
    assert milieu["qualite"] == "synthese_presse"


def test_apres_t2_valeur_maintenue_a_plat():
    resultat = construire_serie_cp071(ipch_constant(100.0), releves_deux_ancrages())
    resultat = resultat.set_index("periode")

    niveau_t2 = resultat.loc["2026-05", "valeur"]
    for periode in ("2026-06", "2026-07"):
        assert resultat.loc[periode, "valeur"] == pytest.approx(niveau_t2)
        assert resultat.loc[periode, "interpole"]
        assert resultat.loc[periode, "qualite"] == "synthese_presse"


def test_couvre_toute_la_periode_ipch_sans_trou():
    resultat = construire_serie_cp071(ipch_constant(100.0), releves_deux_ancrages())

    assert list(resultat["periode"]) == list(PERIODES_IPCH)
