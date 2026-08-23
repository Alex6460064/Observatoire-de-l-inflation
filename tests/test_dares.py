"""Tests de `collecte.dares` -- classeur XLSX construit en memoire, jamais de
reseau ni de fichier reel telecharge (ADR 0022).

La structure des lignes/colonnes (mois, annee, ligne `ENS`, marqueur `n.d.`,
colonne "Variations sur" qui cloture les colonnes trimestrielles) reproduit
celle du classeur Dares reellement telecharge et inspecte le 23/08/2026,
voir docs/SOURCES.md.
"""

import openpyxl
import pytest

from observatoire.collecte.dares import (
    chemin_dernier_fichier_salaire_smb,
    lire_salaire_smb,
)


def _classeur(tmp_path, feuille="Sal. mens. ensemble", avec_ligne_ens=True):
    classeur = openpyxl.Workbook()
    ws = classeur.active
    ws.title = feuille

    ws.append(["Titre", "Salaire mensuel de base..."])
    ws.append(["Type de donnees : ", "donnees trimestrielles"])
    ws.append(["Unite :", "base 100 en juin 2017"])
    ws.append(["Champ :", "France hors Mayotte..."])
    ws.append(["Source :", "Dares, enquete trimestrielle Acemo"])
    ws.append([None, None, "sept", "dec", "mars", "juin", None, "Variations sur : "])
    ws.append([None, None, 2019, 2019, 2020, 2020, None, "3 mois"])
    if avec_ligne_ens:
        ws.append(
            [
                "ENS",
                "Ensemble des secteurs non agricoles",
                103.3,
                103.8,
                "n.d.",
                104.8,
            ]
        )

    chemin = tmp_path / "dares_test.xlsx"
    classeur.save(chemin)
    return chemin


def test_lire_salaire_smb_produit_les_colonnes_attendues(tmp_path):
    chemin = _classeur(tmp_path)

    out = lire_salaire_smb(chemin)

    assert list(out.columns) == ["source", "poste", "periode", "valeur"]


def test_lire_salaire_smb_convertit_mois_annee_en_periode(tmp_path):
    chemin = _classeur(tmp_path)

    out = lire_salaire_smb(chemin).set_index("periode")

    assert out.loc["2019-09", "valeur"] == 103.3
    assert out.loc["2019-12", "valeur"] == 103.8
    assert out.loc["2020-06", "valeur"] == 104.8


def test_lire_salaire_smb_omet_les_trimestres_non_publies(tmp_path):
    chemin = _classeur(tmp_path)

    out = lire_salaire_smb(chemin)

    assert "2020-03" not in set(out["periode"])
    assert len(out) == 3


def test_lire_salaire_smb_source_et_poste_constants(tmp_path):
    chemin = _classeur(tmp_path)

    out = lire_salaire_smb(chemin)

    assert (out["source"] == "dares").all()
    assert (out["poste"] == "ENS").all()


def test_lire_salaire_smb_leve_value_error_si_feuille_absente(tmp_path):
    chemin = _classeur(tmp_path, feuille="Autre feuille")

    with pytest.raises(ValueError):
        lire_salaire_smb(chemin)


def test_lire_salaire_smb_leve_value_error_si_ligne_ens_absente(tmp_path):
    chemin = _classeur(tmp_path, avec_ligne_ens=False)

    with pytest.raises(ValueError):
        lire_salaire_smb(chemin)


# --- chemin_dernier_fichier_salaire_smb --------------------------------------


def test_chemin_dernier_fichier_prend_le_plus_recent(tmp_path):
    (tmp_path / "dares_salaire_smb_2026-06-19.xlsx").write_bytes(b"")
    (tmp_path / "dares_salaire_smb_2026-08-23.xlsx").write_bytes(b"")
    (tmp_path / "dares_salaire_smb_2026-03-01.xlsx").write_bytes(b"")

    out = chemin_dernier_fichier_salaire_smb(tmp_path)

    assert out.name == "dares_salaire_smb_2026-08-23.xlsx"


def test_chemin_dernier_fichier_leve_file_not_found_si_aucun_fichier(tmp_path):
    with pytest.raises(FileNotFoundError):
        chemin_dernier_fichier_salaire_smb(tmp_path)
