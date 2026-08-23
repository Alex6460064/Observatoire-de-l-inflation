"""Tests de `collecte.ademe` -- mock de la reponse HTTP, jamais d'appel reseau.

Les colonnes et deux lignes de `_CSV_EXTRAIT` sont un extrait reel du CSV
ADEME Car Labelling telecharge et inspecte le 23/08/2026 (voir
docs/SOURCES.md) -- memes noms de colonnes (UTF-8 avec BOM), memes valeurs
(RENAULT KANGOO 31000, MAZDA MX-30 38510), pas une reponse inventee.
"""

import datetime as dt

import requests

from observatoire.collecte.ademe import fetch_ademe_carlabelling

_CSV_EXTRAIT = (
    "﻿Marque;Modèle;Energie;Prix véhicule\n"
    "RENAULT;KANGOO;Diesel;31000\n"
    "MAZDA;MX-30;Electrique;38510\n"
).encode()


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

    out = fetch_ademe_carlabelling(
        raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23)
    )

    assert list(out.columns) == [
        "marque",
        "modele",
        "energie",
        "prix_vehicule",
        "date_extraction",
    ]


def test_fetch_valeurs_conformes_au_csv(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_EXTRAIT)

    out = fetch_ademe_carlabelling(
        raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23)
    )
    out = out.set_index("modele")

    assert out.loc["KANGOO", "prix_vehicule"] == 31000
    assert out.loc["MX-30", "prix_vehicule"] == 38510
    assert (out["date_extraction"] == "2026-08-23").all()


def test_fetch_ecrit_le_csv_brut_dans_raw_dir_avec_la_date(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_EXTRAIT)

    fetch_ademe_carlabelling(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))

    assert (tmp_path / "ademe_carlabelling_2026-08-23.csv").exists()


def test_fetch_leve_value_error_si_code_http_different_de_200(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 404, b"not found")

    try:
        fetch_ademe_carlabelling(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_fetch_leve_value_error_si_colonne_prix_absente(monkeypatch, tmp_path):
    csv_sans_prix = "﻿Marque;Modèle;Energie\nRENAULT;KANGOO;Diesel\n".encode()
    _reponse_factice(monkeypatch, 200, csv_sans_prix)

    try:
        fetch_ademe_carlabelling(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_fetch_leve_file_exists_error_si_millesime_deja_capture(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _CSV_EXTRAIT)
    date_extraction = dt.date(2026, 8, 23)
    fetch_ademe_carlabelling(raw_dir=tmp_path, date_extraction=date_extraction)

    try:
        fetch_ademe_carlabelling(raw_dir=tmp_path, date_extraction=date_extraction)
        raised = False
    except FileExistsError:
        raised = True

    assert raised


def test_fetch_leve_value_error_si_prix_non_convertible(monkeypatch, tmp_path):
    csv_prix_corrompu = (
        "﻿Marque;Modèle;Energie;Prix véhicule\nRENAULT;KANGOO;Diesel;31 000 EUR\n"
    ).encode()
    _reponse_factice(monkeypatch, 200, csv_prix_corrompu)

    try:
        fetch_ademe_carlabelling(raw_dir=tmp_path, date_extraction=dt.date(2026, 8, 23))
        raised = False
    except ValueError:
        raised = True

    assert raised
