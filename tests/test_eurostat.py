"""Tests de `collecte.eurostat` — mock de la reponse HTTP, jamais d'appel reseau.

Le JSON de `_REPONSE_DEUX_OBS` est un extrait reel de l'API Eurostat, capture
le 22/08/2026 (dataset prc_hicp_minr, geo=FR, coicop18=TOTAL, unit=I15), pas
une reponse inventee.
"""

import requests

from observatoire.collecte.eurostat import fetch_eurostat_ipch_officiel

_REPONSE_DEUX_OBS = """{
"version":"2.0","class":"dataset",
"label":"HICP - ECOICOP ver.2 - indices and rates of change, monthly",
"source":"ESTAT","value":{"0":74.13,"1":74.42},
"id":["freq","unit","coicop18","geo","time"],
"size":[1,1,1,1,2],
"dimension":{
  "freq":{"category":{"index":{"M":0}}},
  "unit":{"category":{"index":{"I15":0}}},
  "coicop18":{"category":{"index":{"TOTAL":0}}},
  "geo":{"category":{"index":{"FR":0}}},
  "time":{"category":{"index":{"1996-01":0,"1996-02":1}}}
}}"""


def _reponse_factice(monkeypatch, status_code, texte):
    class ReponseFactice:
        def __init__(self):
            self.status_code = status_code
            self.text = texte

    def fake_get(url, params=None, timeout=None):
        return ReponseFactice()

    monkeypatch.setattr(requests, "get", fake_get)


def test_fetch_renvoie_source_poste_periode_valeur(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _REPONSE_DEUX_OBS)

    out = fetch_eurostat_ipch_officiel(raw_dir=tmp_path)

    assert list(out.columns) == ["source", "poste", "periode", "valeur"]
    assert (out["source"] == "eurostat").all()
    assert (out["poste"] == "TOTAL").all()


def test_fetch_parse_les_periodes_et_valeurs_dans_l_ordre(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _REPONSE_DEUX_OBS)

    out = fetch_eurostat_ipch_officiel(raw_dir=tmp_path)

    assert list(out["periode"]) == ["1996-01", "1996-02"]
    assert list(out["valeur"]) == [74.13, 74.42]


def test_fetch_leve_value_error_si_code_http_different_de_200(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 404, "not found")

    try:
        fetch_eurostat_ipch_officiel(raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_fetch_ecrit_le_json_brut_dans_raw_dir(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _REPONSE_DEUX_OBS)

    fetch_eurostat_ipch_officiel(raw_dir=tmp_path)

    fichiers = list(tmp_path.glob("eurostat_ipch_officiel_*.json"))
    assert len(fichiers) == 1
