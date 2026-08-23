"""Tests de `collecte.carburants` -- mock de la reponse HTTP, jamais d'appel
reseau.

`_XML_EXTRAIT` reproduit la structure reelle du fichier
`PrixCarburants_annuel_2019.xml` inspecte le 23/08/2026 (voir
docs/SOURCES.md et le module) : balises `pdv`/`prix`, attributs `nom`,
`maj`, `valeur` en milliemes d'euro.
"""

import zipfile
from io import BytesIO

import requests

from observatoire.collecte.carburants import (
    MILLESIMES_DISPONIBLES,
    fetch_prix_carburants,
)

_XML_EXTRAIT = """<?xml version="1.0" encoding="ISO-8859-1" standalone="yes"?>
<pdv_liste>
<pdv id="1000001" latitude="4620114" longitude="519791" cp="01000" pop="R">
  <adresse>596 AVENUE DE TREVOUX</adresse>
  <ville>SAINT-DENIS</ville>
  <prix nom="Gazole" id="1" maj="2019-01-04T10:53:48" valeur="1328"/>
  <prix nom="Gazole" id="1" maj="2019-01-07T10:25:25" valeur="1348"/>
  <prix nom="E10" id="2" maj="2019-01-04T10:53:48" valeur="1450"/>
  <prix nom="SP98" id="6" maj="2019-01-04T10:53:48" valeur="1520"/>
</pdv>
<pdv id="1000002" latitude="4600000" longitude="500000" cp="75001" pop="A">
  <prix nom="Gazole" id="1" maj="2019-01-04T09:00:00" valeur="1310"/>
  <prix nom="Gazole" id="1" maj="2019-01-04T18:00:00" valeur="1315"/>
</pdv>
</pdv_liste>
""".encode("ISO-8859-1")


def _zip_factice(xml: bytes, annee: str = "2019") -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"PrixCarburants_annuel_{annee}.xml", xml)
    return buffer.getvalue()


def _reponse_factice(monkeypatch, status_code, contenu: bytes):
    class ReponseFactice:
        def __init__(self):
            self.status_code = status_code
            self.content = contenu
            self.text = "erreur"

    def fake_get(url, timeout=None):
        return ReponseFactice()

    monkeypatch.setattr(requests, "get", fake_get)


def test_fetch_renvoie_les_colonnes_attendues(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice(_XML_EXTRAIT))

    out = fetch_prix_carburants(2019, raw_dir=tmp_path)

    assert list(out.columns) == ["station_id", "carburant", "date", "valeur"]


def test_fetch_convertit_les_milliemes_en_euros(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice(_XML_EXTRAIT))

    out = fetch_prix_carburants(2019, raw_dir=tmp_path)
    ligne = out[
        (out["station_id"] == "1000001")
        & (out["carburant"] == "sp95_e10")
        & (out["date"] == "2019-01-04")
    ].iloc[0]

    assert ligne["valeur"] == 1.45


_XML_EXTRAIT_2022 = """<?xml version="1.0" encoding="ISO-8859-1" standalone="yes"?>
<pdv_liste>
<pdv id="1000001" latitude="4620114" longitude="519791" cp="01000" pop="R">
  <adresse>596 AVENUE DE TREVOUX</adresse>
  <ville>SAINT-DENIS</ville>
  <prix nom="Gazole" id="1" maj="2022-06-01T10:53:48" valeur="1.867"/>
  <prix nom="E10" id="2" maj="2022-06-01T10:53:48" valeur="1.699"/>
</pdv>
</pdv_liste>
""".encode("ISO-8859-1")


def test_fetch_lit_le_format_decimal_2022_sans_diviser_par_1000(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice(_XML_EXTRAIT_2022, "2022"))

    out = fetch_prix_carburants(2022, raw_dir=tmp_path)
    ligne = out[
        (out["station_id"] == "1000001")
        & (out["carburant"] == "gazole")
        & (out["date"] == "2022-06-01")
    ].iloc[0]

    assert ligne["valeur"] == 1.867


def test_fetch_ignore_les_carburants_hors_mix(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice(_XML_EXTRAIT))

    out = fetch_prix_carburants(2019, raw_dir=tmp_path)

    assert set(out["carburant"]) == {"gazole", "sp95_e10"}


def test_fetch_garde_le_dernier_changement_du_jour(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice(_XML_EXTRAIT))

    out = fetch_prix_carburants(2019, raw_dir=tmp_path)
    lignes_station2 = out[out["station_id"] == "1000002"]

    assert len(lignes_station2) == 1
    assert lignes_station2.iloc[0]["valeur"] == 1.315


def test_fetch_ecrit_le_zip_brut_dans_raw_dir(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice(_XML_EXTRAIT))

    fetch_prix_carburants(2019, raw_dir=tmp_path)

    assert (tmp_path / "prix_carburants_annuel_2019.zip").exists()


def test_fetch_leve_value_error_si_annee_non_couverte(tmp_path):
    try:
        fetch_prix_carburants(2018, raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_fetch_leve_value_error_si_code_http_different_de_200(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 404, b"not found")

    try:
        fetch_prix_carburants(2019, raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_millesimes_disponibles_couvre_2019_a_2026():
    assert MILLESIMES_DISPONIBLES == (2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026)
