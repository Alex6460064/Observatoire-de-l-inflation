"""Collecte INSEE : recensement de la population, base communale "Logement
en 2022" -- pondere l'agregation communale de `CP041` (ADR 0014, ADR 0023).

Source : docs/SOURCES.md, section "Ponderation du parc locatif communal".
<https://www.insee.fr/fr/statistiques/fichier/8581474/base-cc-logement-2022_csv.zip>,
41 Mo compresses, `base-cc-logement-2022.CSV` a l'interieur (103 Mo,
encodage latin-1, separateur `;`), verifie le 23/08/2026.

Distinct de `collecte.insee` : autre jeu de donnees INSEE (recensement de la
population, pas l'API BDM des prix), pas de nomenclature COICOP en jeu.

Ce module ne calcule rien (`CLAUDE.md` : "une fonction de collecte ne
calcule rien") -- il renvoie les colonnes brutes du recensement, zfill des
codes communes mis a part (normalisation de type, pas un calcul). Le calcul
du parc locatif prive (`P22_RP_LOC - P22_RP_LOCHLMV`) vit dans
`traitement.carte_des_loyers.calculer_locatif_prive` (revue de code du
23/08/2026).
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

ZIP_URL = (
    "https://www.insee.fr/fr/statistiques/fichier/8581474/base-cc-logement-2022_csv.zip"
)
NOM_CSV_DANS_ZIP = "base-cc-logement-2022.CSV"

TIMEOUT_SECONDES = 60

# Locatif prive = ensemble des residences principales louees, hors HLM loue
# vide -- champ de la Carte des loyers (loyers d'annonce), verifie le
# 21/08/2026 (docs/SOURCES.md).
COLONNES_RETENUES = ["CODGEO", "P22_RP_LOC", "P22_RP_LOCHLMV"]


def fetch_recensement_logement_2022(raw_dir: Path = Path("data/raw")) -> pd.DataFrame:
    """Telecharge et lit la base communale "Logement en 2022" de l'INSEE.

    Source : voir docs/SOURCES.md, verifie le 23/08/2026.

    Args:
        raw_dir: dossier ou le zip brut est ecrit avant tout traitement.

    Returns:
        Table `codgeo, p22_rp_loc, p22_rp_lochlmv` -- une ligne par commune,
        colonnes brutes du recensement (voir
        `traitement.carte_des_loyers.calculer_locatif_prive` pour le parc
        locatif prive).

    Raises:
        requests.RequestException: erreur reseau ou timeout.
        ValueError: code HTTP different de 200, zip illisible, fichier CSV
            attendu absent du zip, ou colonne attendue absente (le schema a
            peut-etre change, verifier docs/SOURCES.md).
    """
    try:
        reponse = requests.get(ZIP_URL, timeout=TIMEOUT_SECONDES)
    except requests.RequestException as exc:
        raise requests.RequestException(
            f"Echec de connexion a insee.fr ({ZIP_URL}) : {exc}"
        ) from exc

    if reponse.status_code != 200:
        raise ValueError(
            f"insee.fr a repondu {reponse.status_code} pour {ZIP_URL} : "
            f"{reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "insee_recensement_logement_2022.zip").write_bytes(reponse.content)

    return _parser_zip(reponse.content)


def _parser_zip(contenu: bytes) -> pd.DataFrame:
    try:
        archive = zipfile.ZipFile(BytesIO(contenu))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Zip du recensement logement illisible : {exc}") from exc

    if NOM_CSV_DANS_ZIP not in archive.namelist():
        raise ValueError(
            f"'{NOM_CSV_DANS_ZIP}' absent du zip (contenu : "
            f"{archive.namelist()}). Le schema a peut-etre change, "
            "verifier docs/SOURCES.md."
        )

    with archive.open(NOM_CSV_DANS_ZIP) as f:
        try:
            table = pd.read_csv(
                f, sep=";", encoding="latin-1", usecols=COLONNES_RETENUES
            )
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            colonnes_manquantes = set(COLONNES_RETENUES) - set(
                pd.read_csv(
                    archive.open(NOM_CSV_DANS_ZIP), sep=";", encoding="latin-1", nrows=0
                ).columns
            )
            if colonnes_manquantes:
                raise ValueError(
                    f"Colonnes attendues absentes du CSV recensement : "
                    f"{colonnes_manquantes}. Le schema a peut-etre change, "
                    "verifier docs/SOURCES.md."
                ) from exc
            raise ValueError(f"CSV recensement logement illisible : {exc}") from exc

    table["codgeo"] = table["CODGEO"].astype(str).str.zfill(5)
    table = table.rename(
        columns={"P22_RP_LOC": "p22_rp_loc", "P22_RP_LOCHLMV": "p22_rp_lochlmv"}
    )

    return table[["codgeo", "p22_rp_loc", "p22_rp_lochlmv"]].reset_index(drop=True)
