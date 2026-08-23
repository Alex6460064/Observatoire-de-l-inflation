"""Tests de `collecte.insee` — mock de la reponse HTTP, jamais d'appel reseau.

Le XML de `_REPONSE_UNE_SERIE` est un extrait reel de l'API BDM INSEE,
capture le 22/08/2026 (dataflow IPC-2025, IDBANK 011814630), pas une
reponse inventee.

`_REPONSE_01111`, `_REPONSE_041` et `_REPONSE_SANS_RESULTAT` sont eux aussi
des extraits reels (recadres sur deux observations), captures en direct le
22/08/2026 pour les codes sous-classe `01111` (IDBANK 011814691), groupe
`041` (IDBANK 011815633) et sous-classe `04210` (loyers imputes, 404 "aucun
resultat").
"""

import time

import requests

from observatoire.collecte import fetch_insee_ipc_officiel
from observatoire.collecte.insee import (
    NB_TENTATIVES_CONNEXION,
    SOUS_CLASSES_LOYERS_IMPUTES,
    fetch_insee_prix_par_sous_classe,
    fetch_insee_prix_sous_classe,
)

_REPONSE_UNE_SERIE = """<?xml version='1.0' encoding='UTF-8'?>
<message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
<message:DataSet>
<Series REF_AREA="FE" UNIT_MEASURE="SO" PRIX_CONSO="SO" CORRECTION="BRUT"
        SERIE_ARRETEE="FALSE" NATURE="INDICE" INDICATEUR="IPC" FREQ="M"
        COICOP2018="00" MENAGES_IPC="ENSEMBLE" FORME-VENTE="SO" BASIND="2025"
        IDBANK="011814630"
        TITLE_FR="IPC - Base 2025 - Ensemble des menages - France - Coicop 00">
<Obs TIME_PERIOD="2026-01" OBS_VALUE="99.62" OBS_STATUS="A"/>
<Obs TIME_PERIOD="2025-12" OBS_VALUE="98.40" OBS_STATUS="A"/>
</Series>
</message:DataSet>
</message:StructureSpecificData>"""

_REPONSE_DEUX_SERIES = _REPONSE_UNE_SERIE.replace(
    "</message:DataSet>",
    '<Series REF_AREA="FM" COICOP2018="00"><Obs TIME_PERIOD="2026-01" '
    'OBS_VALUE="1.0"/></Series></message:DataSet>',
)


class _ReponseFactice:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


def test_fetch_insee_ipc_officiel_parse_en_table_longue(monkeypatch, tmp_path):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _ReponseFactice(200, _REPONSE_UNE_SERIE)
    )

    out = fetch_insee_ipc_officiel(raw_dir=tmp_path)

    assert list(out.columns) == ["source", "poste", "periode", "valeur"]
    assert set(out["source"]) == {"insee"}
    assert set(out["poste"]) == {"00"}
    # trie par periode croissante
    assert list(out["periode"]) == ["2025-12", "2026-01"]
    assert out.loc[out.periode == "2026-01", "valeur"].item() == 99.62


def test_fetch_insee_ipc_officiel_sauvegarde_le_brut_avant_traitement(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _ReponseFactice(200, _REPONSE_UNE_SERIE)
    )

    fetch_insee_ipc_officiel(raw_dir=tmp_path)

    fichiers = list(tmp_path.glob("*.xml"))
    assert len(fichiers) == 1
    assert fichiers[0].read_text(encoding="utf-8") == _REPONSE_UNE_SERIE


def test_fetch_insee_ipc_officiel_refuse_un_code_http_different_de_200(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _ReponseFactice(500, "erreur serveur")
    )

    try:
        fetch_insee_ipc_officiel(raw_dir=tmp_path)
    except ValueError as exc:
        assert "500" in str(exc)
    else:
        raise AssertionError("ValueError attendue pour un code HTTP != 200")


def test_fetch_insee_ipc_officiel_refuse_plusieurs_series(monkeypatch, tmp_path):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _ReponseFactice(200, _REPONSE_DEUX_SERIES)
    )

    try:
        fetch_insee_ipc_officiel(raw_dir=tmp_path)
    except ValueError as exc:
        assert "2 series" in str(exc)
    else:
        raise AssertionError("ValueError attendue quand la cle SDMX cible 2 series")


# --- fetch_insee_prix_sous_classe -------------------------------------------

_REPONSE_01111 = """<?xml version='1.0' encoding='UTF-8'?>
<message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
<message:DataSet>
<Series REF_AREA="FE" UNIT_MEASURE="SO" PRIX_CONSO="SO" CORRECTION="BRUT"
        SERIE_ARRETEE="FALSE" NATURE="INDICE" INDICATEUR="IPC" FREQ="M"
        COICOP2018="01111" MENAGES_IPC="ENSEMBLE" FORME-VENTE="SO" BASIND="2025"
        IDBANK="011814691"
        TITLE_FR="IPC - Base 2025 - Ensemble des menages - France - Coicop 01.1.1.1">
<Obs TIME_PERIOD="2025-12" OBS_VALUE="99.06" OBS_STATUS="A"/>
<Obs TIME_PERIOD="2025-11" OBS_VALUE="99.41" OBS_STATUS="A"/>
</Series>
</message:DataSet>
</message:StructureSpecificData>"""

_REPONSE_041 = """<?xml version='1.0' encoding='UTF-8'?>
<message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
<message:DataSet>
<Series REF_AREA="FE" UNIT_MEASURE="SO" PRIX_CONSO="SO" CORRECTION="BRUT"
        SERIE_ARRETEE="FALSE" NATURE="INDICE" INDICATEUR="IPC" FREQ="M"
        COICOP2018="041" MENAGES_IPC="ENSEMBLE" FORME-VENTE="SO" BASIND="2025"
        IDBANK="011815633"
        TITLE_FR="IPC - Base 2025 - Ensemble des menages - France - Coicop 04.1">
<Obs TIME_PERIOD="2025-12" OBS_VALUE="100.89" OBS_STATUS="A"/>
<Obs TIME_PERIOD="2025-11" OBS_VALUE="100.83" OBS_STATUS="A"/>
</Series>
</message:DataSet>
</message:StructureSpecificData>"""

# Reponse reelle HTTP 404 pour "04210" (loyers imputes) : l'INSEE ne publie
# aucune serie hors loyers imputes pour ce code, capture le 22/08/2026.
_REPONSE_SANS_RESULTAT = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<mes:Error xmlns:mes="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" '
    'xmlns:com="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">'
    '<mes:ErrorMessage code="100"><com:Text>'
    "Aucun résultat ne correspond à cette requête."
    "</com:Text></mes:ErrorMessage></mes:Error>"
)


def test_fetch_insee_prix_sous_classe_prefixe_le_poste_en_convention_projet(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _ReponseFactice(200, _REPONSE_01111)
    )

    out = fetch_insee_prix_sous_classe("01111", raw_dir=tmp_path)

    assert set(out["poste"]) == {"CP01111"}
    assert out.loc[out.periode == "2025-12", "valeur"].item() == 99.06


def test_fetch_insee_prix_sous_classe_renvoie_une_table_vide_si_code_100(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _ReponseFactice(404, _REPONSE_SANS_RESULTAT)
    )

    out = fetch_insee_prix_sous_classe("04210", raw_dir=tmp_path)

    assert out.empty
    assert list(out.columns) == ["source", "poste", "periode", "valeur"]


def test_fetch_insee_prix_sous_classe_reprend_apres_une_erreur_de_connexion(
    monkeypatch, tmp_path
):
    # Constate le 23/08/2026 : l'API BDM reinitialise parfois la connexion
    # en cours de collecte longue (ConnectionResetError). Une reprise doit
    # aboutir sans faire echouer tout le run.
    monkeypatch.setattr(time, "sleep", lambda s: None)
    appels = {"n": 0}

    def fake_get(*a, **k):
        appels["n"] += 1
        if appels["n"] == 1:
            raise requests.exceptions.ConnectionError("connexion reinitialisee")
        return _ReponseFactice(200, _REPONSE_01111)

    monkeypatch.setattr(requests, "get", fake_get)

    out = fetch_insee_prix_sous_classe("01111", raw_dir=tmp_path)

    assert appels["n"] == 2
    assert set(out["poste"]) == {"CP01111"}


def test_fetch_insee_prix_sous_classe_abandonne_apres_le_nombre_de_tentatives(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    appels = {"n": 0}

    def fake_get(*a, **k):
        appels["n"] += 1
        raise requests.exceptions.ConnectionError("connexion reinitialisee")

    monkeypatch.setattr(requests, "get", fake_get)

    try:
        fetch_insee_prix_sous_classe("01111", raw_dir=tmp_path)
        raised = False
    except requests.RequestException:
        raised = True

    assert raised
    assert appels["n"] == NB_TENTATIVES_CONNEXION


def test_fetch_insee_prix_sous_classe_refuse_une_autre_erreur_http(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _ReponseFactice(500, "erreur serveur")
    )

    try:
        fetch_insee_prix_sous_classe("01111", raw_dir=tmp_path)
    except ValueError as exc:
        assert "500" in str(exc)
    else:
        raise AssertionError("ValueError attendue pour un code HTTP != 200")


# --- fetch_insee_prix_par_sous_classe ---------------------------------------


def _get_factice_par_code(reponses):
    def fake_get(url, params=None, timeout=None):
        for code, reponse in reponses.items():
            if f".SO.{code}.SO." in url:
                return reponse
        raise AssertionError(f"code inattendu dans l'URL : {url}")

    return fake_get


def test_fetch_par_sous_classe_concatene_les_codes_trouves(monkeypatch, tmp_path):
    monkeypatch.setattr(
        requests,
        "get",
        _get_factice_par_code(
            {
                "01111": _ReponseFactice(200, _REPONSE_01111),
                "011": _ReponseFactice(200, _REPONSE_041.replace("041", "011")),
            }
        ),
    )

    out = fetch_insee_prix_par_sous_classe(
        ["CP01111", "CP011"], raw_dir=tmp_path, delai_secondes=0
    )

    assert set(out["poste"]) == {"CP01111", "CP011"}


def test_fetch_par_sous_classe_substitue_cp041_pour_les_loyers_imputes(
    monkeypatch, tmp_path
):
    assert SOUS_CLASSES_LOYERS_IMPUTES == ("CP04210", "CP04220")

    monkeypatch.setattr(
        requests,
        "get",
        _get_factice_par_code(
            {
                "04210": _ReponseFactice(404, _REPONSE_SANS_RESULTAT),
                "04220": _ReponseFactice(404, _REPONSE_SANS_RESULTAT),
                "041": _ReponseFactice(200, _REPONSE_041),
            }
        ),
    )

    out = fetch_insee_prix_par_sous_classe(
        ["CP04210", "CP04220"], raw_dir=tmp_path, delai_secondes=0
    )

    # Les deux postes recoivent la serie CP041 (docs/METHODOLOGIE.md 3.4),
    # mais restent identifies par leur propre code -- c'est le poids qui les
    # distingue dans poids.csv, pas le prix.
    assert set(out["poste"]) == {"CP04210", "CP04220"}
    valeurs_04210 = out.loc[out.poste == "CP04210"].set_index("periode").valeur
    assert valeurs_04210["2025-12"] == 100.89


def test_fetch_par_sous_classe_ne_recollecte_cp041_qu_une_fois(monkeypatch, tmp_path):
    appels_041 = []

    def fake_get(url, params=None, timeout=None):
        if ".SO.041.SO." in url:
            appels_041.append(url)
            return _ReponseFactice(200, _REPONSE_041)
        return _ReponseFactice(404, _REPONSE_SANS_RESULTAT)

    monkeypatch.setattr(requests, "get", fake_get)

    fetch_insee_prix_par_sous_classe(
        ["CP04210", "CP04220"], raw_dir=tmp_path, delai_secondes=0
    )

    assert len(appels_041) == 1


def test_fetch_par_sous_classe_refuse_un_code_sans_resultat_hors_loyers_imputes(
    monkeypatch, tmp_path
):
    # Aucune substitution n'est documentee pour un poste autre que CP042 :
    # un "aucun resultat" ailleurs doit remonter, pas disparaitre.
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _ReponseFactice(404, _REPONSE_SANS_RESULTAT)
    )

    try:
        fetch_insee_prix_par_sous_classe(
            ["CP09999"], raw_dir=tmp_path, delai_secondes=0
        )
    except ValueError as exc:
        assert "CP09999" in str(exc)
    else:
        raise AssertionError(
            "ValueError attendue : aucune substitution documentee pour CP09999"
        )
