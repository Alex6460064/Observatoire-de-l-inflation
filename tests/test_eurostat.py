"""Tests de `collecte.eurostat` — mock de la reponse HTTP, jamais d'appel reseau.

Le JSON de `_REPONSE_DEUX_OBS` est un extrait reel de l'API Eurostat, capture
le 22/08/2026 (dataset prc_hicp_minr, geo=FR, coicop18=TOTAL, unit=I15), pas
une reponse inventee.

`_REPONSE_HBS_POIDS` et `_REPONSE_IW_POIDS` sont des extraits reels et
recadres (moins de codes, memes valeurs) des datasets `hbs_str_t223` et
`prc_hicp_iw`, capture le 22/08/2026 -- coherents avec les valeurs deja
relevees dans docs/SOURCES.md (`CP01` QU1=147, QU3=154, QU5=128).
"""

import requests

from observatoire.collecte.eurostat import (
    fetch_eurostat_hbs_poids,
    fetch_eurostat_ipch_officiel,
    fetch_eurostat_ipch_poids_articles,
    fetch_eurostat_prix_par_sous_classe,
)

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


# --- fetch_eurostat_hbs_poids -----------------------------------------------

# Recadre sur deux postes (CP01, CP011) et les cinq quintiles + UNK ; memes
# valeurs que la reponse reelle du 22/08/2026.
_REPONSE_HBS_POIDS = """{
"version":"2.0","class":"dataset","source":"ESTAT",
"value":{"0":147,"1":134,"2":150,"3":138,"4":154,"5":143,"6":150,"7":138,"8":128,"9":119},
"status":{"0":"e","1":"e","2":"e","3":"e","4":"e","5":"e","6":"e","7":"e","8":"e","9":"e"},
"id":["freq","quant_inc","coicop","unit","geo","time"],
"size":[1,6,2,1,1,1],
"dimension":{
  "freq":{"category":{"index":{"M":0}}},
  "quant_inc":{"category":{"index":{"QU1":0,"QU2":1,"QU3":2,"QU4":3,"QU5":4,"UNK":5}}},
  "coicop":{"category":{"index":{"CP01":0,"CP011":1}}},
  "unit":{"category":{"index":{"PM":0}}},
  "geo":{"category":{"index":{"FR":0}}},
  "time":{"category":{"index":{"2020":0}}}
}}"""


def test_fetch_hbs_poids_renvoie_les_cinq_quintiles_sans_unk(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _REPONSE_HBS_POIDS)

    out = fetch_eurostat_hbs_poids(raw_dir=tmp_path)

    assert set(out["modalite"]) == {"QU1", "QU2", "QU3", "QU4", "QU5"}
    assert list(out.columns) == ["modalite", "poste", "valeur"]


def test_fetch_hbs_poids_valeurs_conformes_a_l_api(monkeypatch, tmp_path):
    # Reponse reelle du 22/08/2026, code groupe CP011 (voir fixture).
    _reponse_factice(monkeypatch, 200, _REPONSE_HBS_POIDS)

    out = fetch_eurostat_hbs_poids(raw_dir=tmp_path)
    out = out.set_index(["modalite", "poste"]).valeur

    assert out[("QU1", "CP011")] == 134
    assert out[("QU3", "CP011")] == 143
    assert out[("QU5", "CP011")] == 119


def test_fetch_hbs_poids_exclut_les_codes_hors_niveau_groupe(monkeypatch, tmp_path):
    # docs/METHODOLOGIE.md 3.2 : seuls les 47 groupes HBS a trois chiffres
    # ("CP" + 3 chiffres) sont utilisables par la transposition. `CP01`
    # (niveau division, 2 chiffres) fait partie des "sous-niveaux melanges"
    # de l'API et doit etre exclu, sous peine de fausser la jointure avec
    # data/manual/correspondance_coicop.csv (ticket #11).
    _reponse_factice(monkeypatch, 200, _REPONSE_HBS_POIDS)

    out = fetch_eurostat_hbs_poids(raw_dir=tmp_path)

    assert set(out["poste"]) == {"CP011"}


def test_fetch_hbs_poids_ecrit_le_json_brut_dans_raw_dir(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _REPONSE_HBS_POIDS)

    fetch_eurostat_hbs_poids(raw_dir=tmp_path)

    assert list(tmp_path.glob("eurostat_hbs_poids_*.json"))


def test_fetch_hbs_poids_leve_value_error_si_code_http_different_de_200(
    monkeypatch, tmp_path
):
    _reponse_factice(monkeypatch, 404, "not found")

    try:
        fetch_eurostat_hbs_poids(raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


# --- fetch_eurostat_ipch_poids_articles -------------------------------------

# Recadre sur quatre codes coicop18 -- une classe (CP0111, 6 caracteres), deux
# sous-classes (CP01111, CP01112) et un code agregat special (FOOD_NP, 7
# caracteres mais pas une sous-classe -- le piege documente dans
# docs/SOURCES.md). Memes valeurs que la reponse reelle du 22/08/2026.
_REPONSE_IW_POIDS = """{
"version":"2.0","class":"dataset","source":"ESTAT",
"value":{"0":25.18,"1":0.49,"2":0.21,"3":51.44},
"id":["freq","coicop18","statinfo","geo","time"],
"size":[1,4,1,1,1],
"dimension":{
  "freq":{"category":{"index":{"M":0}}},
  "coicop18":{"category":{"index":{"CP0111":0,"CP01111":1,"CP01112":2,"FOOD_NP":3}}},
  "statinfo":{"category":{"index":{"IW":0}}},
  "geo":{"category":{"index":{"FR":0}}},
  "time":{"category":{"index":{"2020":0}}}
}}"""


def test_fetch_ipch_poids_articles_exclut_classes_et_codes_speciaux(
    monkeypatch, tmp_path
):
    _reponse_factice(monkeypatch, 200, _REPONSE_IW_POIDS)

    out = fetch_eurostat_ipch_poids_articles(raw_dir=tmp_path)

    assert set(out["poste"]) == {"CP01111", "CP01112"}


def test_fetch_ipch_poids_articles_valeurs_conformes_a_l_api(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _REPONSE_IW_POIDS)

    out = fetch_eurostat_ipch_poids_articles(raw_dir=tmp_path).set_index("poste").valeur

    assert out["CP01111"] == 0.49
    assert out["CP01112"] == 0.21


def test_fetch_ipch_poids_articles_ecrit_le_json_brut_dans_raw_dir(
    monkeypatch, tmp_path
):
    _reponse_factice(monkeypatch, 200, _REPONSE_IW_POIDS)

    fetch_eurostat_ipch_poids_articles(raw_dir=tmp_path)

    assert list(tmp_path.glob("eurostat_ipch_poids_articles_*.json"))


def test_fetch_ipch_poids_articles_leve_value_error_si_code_http_different_de_200(
    monkeypatch, tmp_path
):
    _reponse_factice(monkeypatch, 404, "not found")

    try:
        fetch_eurostat_ipch_poids_articles(raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


# --- fetch_eurostat_prix_par_sous_classe ------------------------------------

# Extrait reel (deux sous-classes, deux periodes) de la reponse batch
# prc_hicp_minr capturee le 23/08/2026 pour les 296 postes de poids.csv --
# voir docs/SOURCES.md.
_REPONSE_PRIX_SOUS_CLASSE = """{
"version":"2.0","class":"dataset","source":"ESTAT",
"value":{"0":96.45,"1":96.09,"2":97.53,"3":97.18},
"id":["freq","unit","coicop18","geo","time"],
"size":[1,1,2,1,2],
"dimension":{
  "freq":{"category":{"index":{"M":0}}},
  "unit":{"category":{"index":{"I15":0}}},
  "coicop18":{"category":{"index":{"CP01111":0,"CP01112":1}}},
  "geo":{"category":{"index":{"FR":0}}},
  "time":{"category":{"index":{"2019-12":0,"2020-01":1}}}
}}"""


def test_fetch_prix_sous_classe_renvoie_source_poste_periode_valeur(
    monkeypatch, tmp_path
):
    _reponse_factice(monkeypatch, 200, _REPONSE_PRIX_SOUS_CLASSE)

    out = fetch_eurostat_prix_par_sous_classe(
        ["CP01111", "CP01112"], start_period="2019-12", raw_dir=tmp_path
    )

    assert list(out.columns) == ["source", "poste", "periode", "valeur"]
    assert (out["source"] == "eurostat").all()
    assert set(out["poste"]) == {"CP01111", "CP01112"}


def test_fetch_prix_sous_classe_valeurs_conformes_a_l_api(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _REPONSE_PRIX_SOUS_CLASSE)

    out = (
        fetch_eurostat_prix_par_sous_classe(
            ["CP01111", "CP01112"], start_period="2019-12", raw_dir=tmp_path
        )
        .set_index(["poste", "periode"])
        .valeur
    )

    assert out[("CP01111", "2019-12")] == 96.45
    assert out[("CP01112", "2020-01")] == 97.18


def test_fetch_prix_sous_classe_ecrit_le_json_brut_dans_raw_dir(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _REPONSE_PRIX_SOUS_CLASSE)

    fetch_eurostat_prix_par_sous_classe(
        ["CP01111", "CP01112"], start_period="2019-12", raw_dir=tmp_path
    )

    assert list(tmp_path.glob("eurostat_prix_sous_classe_*.json"))


def test_fetch_prix_sous_classe_leve_value_error_si_code_http_different_de_200(
    monkeypatch, tmp_path
):
    _reponse_factice(monkeypatch, 404, "not found")

    try:
        fetch_eurostat_prix_par_sous_classe(["CP01111"], raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised
