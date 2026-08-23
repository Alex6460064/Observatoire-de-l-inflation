"""Collecte prix-carburants.gouv.fr : archives annuelles des changements de
prix par station -- source propre de `CP072` pour l'indice Observatoire
(ADR 0014, ADR 0023).

Source : docs/SOURCES.md, section "Carburants -- indice Observatoire".
`https://donnees.roulez-eco.fr/opendata/annee/{annee}` renvoie un zip
`PrixCarburants_annuel_{annee}.xml` (~300 Mo decompresses par annee,
verifie le 23/08/2026 sur 2019 : zip 24,5 Mo -> XML 302 Mo, encodage
ISO-8859-1).

Ce n'est pas une serie : chaque `<prix>` est un changement de prix date,
station par station, en milliemes d'euro. Ce module se contente d'extraire
et de dedupliquer (dernier changement du jour par station) -- la
propagation en serie quotidienne puis l'agregation mensuelle vivent dans
`traitement.carburants` (ADR 0008).

⚠️ Aucun volume de vente publie : la moyenne est non ponderee par station
(docs/SOURCES.md). Seuls `Gazole` et `E10` (= SP95-E10) sont retenus,
mix simplifie ADR 0023 (`data/manual/parametres.csv`) -- `SP95`, `SP98`,
`E85` et `GPLc` sont ignores.

Parsing en streaming (`xml.etree.ElementTree.iterparse`, element cleare
apres chaque station) : le DOM complet d'un fichier de 300 Mo ne tient pas
raisonnablement en memoire.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

URL_ANNEE = "https://donnees.roulez-eco.fr/opendata/annee/{annee}"

TIMEOUT_SECONDES = 300

# nom XML -> code carburant interne. E10 = SP95-E10 (ADR 0023, le mix
# retenu ne separe pas SP95 sans ethanol / SP98 / E85, voir
# data/manual/parametres.csv).
CARBURANTS_RETENUS = {"Gazole": "gazole", "E10": "sp95_e10"}

MILLESIMES_DISPONIBLES = tuple(range(2019, 2027))


def fetch_prix_carburants(annee: int, raw_dir: Path = Path("data/raw")) -> pd.DataFrame:
    """Telecharge et parse l'archive annuelle prix-carburants.gouv.fr.

    Source : voir docstring du module, verifie le 23/08/2026.

    Args:
        annee: millesime, un de `MILLESIMES_DISPONIBLES` (2019-2026,
            couverture ADR 0014).
        raw_dir: dossier ou le zip brut est ecrit avant tout traitement.

    Returns:
        Table `station_id, carburant, date, valeur` -- une ligne par station,
        carburant (`gazole` ou `sp95_e10`) et jour ayant eu au moins un
        changement de prix ; `valeur` en euros/litre (le milliemes source est
        divise par 1000), dernier changement du jour retenu en cas de
        plusieurs mises a jour le meme jour.

    Raises:
        ValueError: `annee` hors de `MILLESIMES_DISPONIBLES`, code HTTP
            different de 200, zip ou XML illisible.
        requests.RequestException: erreur reseau ou timeout.
    """
    if annee not in MILLESIMES_DISPONIBLES:
        raise ValueError(
            f"Annee {annee} non couverte par l'archivage. Millesimes "
            f"disponibles : {MILLESIMES_DISPONIBLES} (ADR 0014)."
        )

    url = URL_ANNEE.format(annee=annee)
    try:
        reponse = requests.get(url, timeout=TIMEOUT_SECONDES)
    except requests.RequestException as exc:
        raise requests.RequestException(f"Echec de connexion a {url} : {exc}") from exc

    if reponse.status_code != 200:
        raise ValueError(
            f"{url} a repondu {reponse.status_code} : {reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"prix_carburants_annuel_{annee}.zip").write_bytes(reponse.content)

    return _parser_zip(reponse.content, annee)


def _parser_zip(contenu: bytes, annee: int) -> pd.DataFrame:
    try:
        archive = zipfile.ZipFile(BytesIO(contenu))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Zip prix-carburants {annee} illisible : {exc}") from exc

    noms_xml = [n for n in archive.namelist() if n.lower().endswith(".xml")]
    if len(noms_xml) != 1:
        raise ValueError(
            f"Zip prix-carburants {annee} : attendu un seul XML, trouve "
            f"{noms_xml}. Le schema de l'archive a peut-etre change."
        )

    with archive.open(noms_xml[0]) as f:
        return _parser_xml(f, annee)


def _parser_xml(fichier, annee: int) -> pd.DataFrame:
    lignes: dict[tuple[str, str, str], float] = {}
    station_courante = None

    try:
        for event, elem in ET.iterparse(fichier, events=("start", "end")):
            if event == "start" and elem.tag == "pdv":
                station_courante = elem.get("id")
            elif event == "end" and elem.tag == "prix":
                nom = elem.get("nom")
                carburant = CARBURANTS_RETENUS.get(nom)
                if carburant is not None and station_courante is not None:
                    maj = elem.get("maj", "")
                    date = maj[:10]
                    valeur_brute = elem.get("valeur")
                    if date and valeur_brute:
                        # Dernier changement du jour gagne (ordre document
                        # croissant dans le fichier source, verifie le
                        # 23/08/2026).
                        lignes[(station_courante, carburant, date)] = (
                            float(valeur_brute) / 1000.0
                        )
            elif event == "end" and elem.tag == "pdv":
                elem.clear()
                station_courante = None
    except ET.ParseError as exc:
        raise ValueError(f"XML prix-carburants {annee} illisible : {exc}") from exc

    if not lignes:
        raise ValueError(
            f"Aucune ligne Gazole/E10 extraite du XML prix-carburants "
            f"{annee}. Le schema a peut-etre change, verifier docs/SOURCES.md."
        )

    return pd.DataFrame(
        [(s, c, d, v) for (s, c, d), v in lignes.items()],
        columns=["station_id", "carburant", "date", "valeur"],
    )
