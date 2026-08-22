"""Tests de `collecte.insee` — mock de la reponse HTTP, jamais d'appel reseau.

Le XML de `_REPONSE_UNE_SERIE` est un extrait reel de l'API BDM INSEE,
capture le 22/08/2026 (dataflow IPC-2025, IDBANK 011814630), pas une
reponse inventee.
"""

import requests

from observatoire.collecte import fetch_insee_ipc_officiel

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
