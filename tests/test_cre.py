"""Tests de `collecte.cre` -- mock de la reponse HTTP, jamais d'appel reseau.

Les lignes de `_CSV_EXTRAIT` sont un extrait reel de `Option_Base.csv`
telecharge et inspecte le 23/08/2026 (voir docs/SOURCES.md) : premiere
periode de bareme (23/07/2012, 3 et 6 kVA) et derniere ligne en cours de
validite (01/02/2026, 6 kVA, `DATE_FIN` vide).
"""

import datetime as dt

import pandas as pd
import requests

from observatoire.collecte.cre import fetch_cre_tarif_base

_CSV_EXTRAIT = (
    b"DATE_DEBUT;DATE_FIN;P_SOUSCRITE;PART_FIXE_HT;PART_FIXE_TTC;"
    b"PART_VARIABLE_HT;PART_VARIABLE_TTC\n"
    b"23/07/2012;31/07/2013;3;55,56;69,37;0,0822;0,1256\n"
    b"23/07/2012;31/07/2013;6;65,64;82,98;0,0828;0,1263\n"
    b"01/02/2026;;6;141,6;188,2;0,1308;0,19398\n"
)


def _reponse_factice(monkeypatch, status_code, contenu: bytes):
    class ReponseFactice:
        def __init__(self):
            self.status_code = status_code
            self.content = contenu
            self.text = contenu.decode("utf-8", errors="replace")

    def fake_get(url, timeout=None):
        return ReponseFactice()

    monkeypatch.setattr(requests, "get", fake_get)


def test_fetch_renvoie_les_colonnes_attendues(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_EXTRAIT)

    out = fetch_cre_tarif_base(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))

    assert list(out.columns) == [
        "date_debut",
        "date_fin",
        "puissance_kva",
        "part_fixe_ttc",
        "part_variable_ttc",
    ]


def test_fetch_valeurs_conformes_au_csv(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_EXTRAIT)

    out = fetch_cre_tarif_base(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))
    ligne_6kva_2012 = out.loc[
        (out["puissance_kva"] == 6) & (out["date_debut"] == "2012-07-23")
    ].iloc[0]

    assert ligne_6kva_2012["part_fixe_ttc"] == 82.98
    assert ligne_6kva_2012["part_variable_ttc"] == 0.1263
    assert ligne_6kva_2012["date_fin"] == pd.Timestamp("2013-07-31")


def test_fetch_date_fin_none_pour_le_bareme_en_cours(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_EXTRAIT)

    out = fetch_cre_tarif_base(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))
    ligne_2026 = out.loc[out["date_debut"] == "2026-02-01"].iloc[0]

    assert ligne_2026["date_fin"] is None


def test_fetch_ecrit_le_csv_brut_dans_raw_dir_avec_la_date(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_EXTRAIT)

    fetch_cre_tarif_base(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))

    assert (tmp_path / "cre_tarif_base_2026-08-23.csv").exists()


def test_fetch_leve_value_error_si_code_http_different_de_200(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 404, b"not found")

    try:
        fetch_cre_tarif_base(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_fetch_leve_value_error_si_colonne_absente(monkeypatch, tmp_path):
    csv_sans_puissance = (
        b"DATE_DEBUT;DATE_FIN;PART_FIXE_TTC;PART_VARIABLE_TTC\n"
        b"23/07/2012;31/07/2013;82,98;0,1263\n"
    )
    _reponse_factice(monkeypatch, 200, csv_sans_puissance)

    try:
        fetch_cre_tarif_base(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))
        raised = False
    except ValueError:
        raised = True

    assert raised
