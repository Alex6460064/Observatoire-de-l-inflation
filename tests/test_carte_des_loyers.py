"""Tests de `collecte.carte_des_loyers` -- mock de la reponse HTTP, jamais
d'appel reseau.

Les lignes de fixture sont des extraits reels des fichiers "appartements"
telecharges et inspectes le 23/08/2026 (voir docs/SOURCES.md et le module) :
schema 2022-2025 (en-tetes guillemetes, colonne `INSEE_C`) et schema 2018
(en-tetes non guillemetes, colonne `INSEE`). Encodage latin-1 reel des deux
fichiers.
"""

import requests

from observatoire.collecte.carte_des_loyers import (
    MILLESIMES_DISPONIBLES,
    fetch_carte_des_loyers,
)

_CSV_2024 = (
    '"id_zone";"INSEE_C";"LIBGEO";"EPCI";"DEP";"REG";"loypredm2";"lwr.IPm2";'
    '"upr.IPm2";"TYPPRED";"nbobs_com";"nbobs_mail";"R2_adj"\n'
    '"1";"86051";"Champagn\xe9-le-Sec";"200070035";"86";"75";'
    "8,48108601820233;6,60248185247569;10,8942094284101;"
    '"maille";0;1044;0,719908446134695\n'
).encode("latin-1")

_CSV_2018 = (
    "id_zone;INSEE;LIBGEO;DEP;REG;EPCI;TYPPRED;loypredm2;lwr.IPm2;upr.IPm2;"
    "R2adj;NBobs_maille;NBobs_commune\n"
    "2362;1001;L'Abergement-Cl\xe9menciat;1;84;200069193;maille;9,372335348;"
    "7,409663525;11,85487972;0,774249278;701;2\n"
).encode("latin-1")


def _reponse_factice(monkeypatch, status_code, contenu: bytes):
    class ReponseFactice:
        def __init__(self):
            self.status_code = status_code
            self.content = contenu
            self.text = contenu.decode("latin-1", errors="replace")

    def fake_get(url, timeout=None):
        return ReponseFactice()

    monkeypatch.setattr(requests, "get", fake_get)


def test_fetch_2024_renvoie_les_colonnes_attendues(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_2024)

    out = fetch_carte_des_loyers(2024, raw_dir=tmp_path)

    assert list(out.columns) == ["commune_insee", "loyer_m2"]


def test_fetch_2024_valeurs_conformes_au_csv(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_2024)

    out = fetch_carte_des_loyers(2024, raw_dir=tmp_path)

    assert out.loc[0, "commune_insee"] == "86051"
    assert out.loc[0, "loyer_m2"] == 8.48108601820233


def test_fetch_2018_schema_different_lit_colonne_insee(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_2018)

    out = fetch_carte_des_loyers(2018, raw_dir=tmp_path)

    assert out.loc[0, "commune_insee"] == "01001"
    assert out.loc[0, "loyer_m2"] == 9.372335348


def test_fetch_zero_pad_les_codes_commune_courts(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_2018)

    out = fetch_carte_des_loyers(2018, raw_dir=tmp_path)

    assert all(len(c) == 5 for c in out["commune_insee"])


def test_fetch_ecrit_le_csv_brut_dans_raw_dir(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_2024)

    fetch_carte_des_loyers(2024, raw_dir=tmp_path)

    assert (tmp_path / "carte_des_loyers_appartements_2024.csv").exists()


def test_fetch_leve_value_error_si_millesime_non_couvert(tmp_path):
    try:
        fetch_carte_des_loyers(2020, raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_fetch_leve_value_error_si_code_http_different_de_200(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 404, b"not found")

    try:
        fetch_carte_des_loyers(2024, raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_millesimes_disponibles_couvre_les_cinq_annees_adr_0016():
    assert MILLESIMES_DISPONIBLES == (2018, 2022, 2023, 2024, 2025)
