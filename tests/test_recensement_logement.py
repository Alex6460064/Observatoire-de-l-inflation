"""Tests de `collecte.recensement_logement` -- mock de la reponse HTTP,
jamais d'appel reseau.

Le zip est construit en memoire ; les noms de colonnes (`CODGEO`, `P22_RP`,
`P22_RP_LOC`, `P22_RP_LOCHLMV`, encodage latin-1) reproduisent ceux du
fichier `base-cc-logement-2022.CSV` reellement telecharge et inspecte le
23/08/2026 (voir docs/SOURCES.md) -- le fichier reel fait 103 Mo, injouable
tel quel dans un test.
"""

import zipfile
from io import BytesIO

import requests

from observatoire.collecte.recensement_logement import (
    NOM_CSV_DANS_ZIP,
    fetch_recensement_logement_2022,
)

_CSV_CONTENU = (
    "CODGEO;P22_LOG;P22_RP;P22_RP_LOC;P22_RP_LOCHLMV\n"
    "01001;300;280;50;10\n"
    "1002;120;100;20;0\n"
).encode("latin-1")


def _zip_factice() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(NOM_CSV_DANS_ZIP, _CSV_CONTENU)
        archive.writestr("meta_base-cc-logement-2022.CSV", b"dummy")
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


def test_fetch_renvoie_les_colonnes_brutes_sans_calcul(monkeypatch, tmp_path):
    """Une fonction de collecte ne calcule rien (CLAUDE.md) -- le parc
    locatif prive se calcule dans `traitement.carte_des_loyers` (revue de
    code du 23/08/2026)."""
    _reponse_factice(monkeypatch, 200, _zip_factice())

    out = fetch_recensement_logement_2022(raw_dir=tmp_path)

    assert list(out.columns) == ["codgeo", "p22_rp_loc", "p22_rp_lochlmv"]


def test_fetch_valeurs_conformes_au_csv(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice())

    out = fetch_recensement_logement_2022(raw_dir=tmp_path).set_index("codgeo")

    assert out.loc["01001", "p22_rp_loc"] == 50
    assert out.loc["01001", "p22_rp_lochlmv"] == 10
    assert out.loc["01002", "p22_rp_loc"] == 20
    assert out.loc["01002", "p22_rp_lochlmv"] == 0


def test_fetch_zero_pad_les_codes_commune_courts(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice())

    out = fetch_recensement_logement_2022(raw_dir=tmp_path)

    assert all(len(c) == 5 for c in out["codgeo"])


def test_fetch_ecrit_le_zip_brut_dans_raw_dir(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 200, _zip_factice())

    fetch_recensement_logement_2022(raw_dir=tmp_path)

    assert (tmp_path / "insee_recensement_logement_2022.zip").exists()


def test_fetch_leve_value_error_si_code_http_different_de_200(monkeypatch, tmp_path):
    _reponse_factice(monkeypatch, 404, b"not found")

    try:
        fetch_recensement_logement_2022(raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_fetch_leve_value_error_si_csv_absent_du_zip(monkeypatch, tmp_path):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("autre_fichier.CSV", b"rien")
    _reponse_factice(monkeypatch, 200, buffer.getvalue())

    try:
        fetch_recensement_logement_2022(raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_fetch_leve_value_error_si_colonne_absente(monkeypatch, tmp_path):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            NOM_CSV_DANS_ZIP, "CODGEO;P22_LOG\n01001;300\n".encode("latin-1")
        )
    _reponse_factice(monkeypatch, 200, buffer.getvalue())

    try:
        fetch_recensement_logement_2022(raw_dir=tmp_path)
        raised = False
    except ValueError:
        raised = True

    assert raised
