from pathlib import Path

import pytest

from observatoire.collecte.releves_manuels import charger_releves_manuels

EN_TETE = (
    "poste,periode,periode_type,motorisation,valeur,unite,evolution_pct,"
    "qualite,source_nom,source_url,date_consultation,notes\n"
)


def ecrire_csv(tmp_path: Path, lignes: str) -> Path:
    chemin = tmp_path / "releves.csv"
    chemin.write_text(EN_TETE + lignes, encoding="utf-8")
    return chemin


def test_charge_les_lignes_valides(tmp_path):
    chemin = ecrire_csv(
        tmp_path,
        "CP071,2025,annuel,essence,25657,EUR,-4.6,synthese_presse,AAA Data,"
        "https://www.aaa-data.fr/x/,2026-08-24,note\n",
    )

    table = charger_releves_manuels(chemin=chemin)

    assert len(table) == 1
    assert table.loc[0, "valeur"] == 25657
    assert table.loc[0, "evolution_pct"] == -4.6


def test_filtre_par_poste(tmp_path):
    chemin = ecrire_csv(
        tmp_path,
        "CP071,2025,annuel,essence,25657,EUR,-4.6,synthese_presse,AAA Data,"
        "https://www.aaa-data.fr/x/,2026-08-24,note\n"
        "CP01,2025,annuel,,100,indice,1.0,etude_publiee,Familles Rurales,"
        "https://exemple.org/,2026-08-24,note\n",
    )

    table = charger_releves_manuels(poste="CP071", chemin=chemin)

    assert len(table) == 1
    assert table.loc[0, "poste"] == "CP071"


def test_rejette_ligne_sans_source_url(tmp_path):
    chemin = ecrire_csv(
        tmp_path,
        "CP071,2025,annuel,essence,25657,EUR,-4.6,synthese_presse,AAA Data,"
        ",2026-08-24,note\n",
    )

    with pytest.raises(ValueError, match="source_url"):
        charger_releves_manuels(chemin=chemin)


def test_rejette_ligne_sans_periode(tmp_path):
    chemin = ecrire_csv(
        tmp_path,
        "CP071,,annuel,essence,25657,EUR,-4.6,synthese_presse,AAA Data,"
        "https://www.aaa-data.fr/x/,2026-08-24,note\n",
    )

    with pytest.raises(ValueError, match="periode"):
        charger_releves_manuels(chemin=chemin)


def test_rejette_qualite_hors_des_trois_crans(tmp_path):
    chemin = ecrire_csv(
        tmp_path,
        "CP071,2025,annuel,essence,25657,EUR,-4.6,officieux,AAA Data,"
        "https://www.aaa-data.fr/x/,2026-08-24,note\n",
    )

    with pytest.raises(ValueError, match="qualite"):
        charger_releves_manuels(chemin=chemin)


def test_fichier_introuvable(tmp_path):
    with pytest.raises(FileNotFoundError):
        charger_releves_manuels(chemin=tmp_path / "absent.csv")


def test_le_registre_reel_est_valide():
    table = charger_releves_manuels(poste="CP071")

    assert len(table) == 9
    assert set(table["qualite"]) == {"synthese_presse"}
