"""Collecte de l'IPC officiel INSEE (indice 0).

Source : docs/SOURCES.md, section "INSEE — IPC officiel". API BDM,
dataflow `IPC-2025`, sans cle, base
`https://api.insee.fr/series/BDM/V1/data/IPC-2025`.

La cle SDMX ci-dessous a ete verifiee en interrogeant l'API en direct le
22/08/2026 : elle cible une serie unique, IDBANK 011814630 — "Ensemble des
menages - France - Nomenclature Coicop : 00 - Ensemble", hors loyers
imputes (PRIX_CONSO=SO). Ordre des douze dimensions, voir docs/SOURCES.md :
FREQ.INDICATEUR.FORME-VENTE.COICOP2018.PRIX_CONSO.NATURE.MENAGES_IPC.
REF_AREA.UNIT_MEASURE.CORRECTION.BASIND.SERIE_ARRETEE.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

BDM_IPC_2025_URL = "https://api.insee.fr/series/BDM/V1/data/IPC-2025"

CLE_IPC_OFFICIEL = "M.IPC.SO.00.SO.INDICE.ENSEMBLE.FE.SO.BRUT.2025.FALSE"

TIMEOUT_SECONDES = 30


def fetch_insee_ipc_officiel(
    start_period: str = "1996-01",
    raw_dir: Path = Path("data/raw"),
) -> pd.DataFrame:
    """Telecharge l'IPC officiel France entiere, ensemble des menages.

    Source : API BDM INSEE, dataflow IPC-2025, IDBANK 011814630 (voir
    docs/SOURCES.md, verifie le 22/08/2026).

    Args:
        start_period: premiere periode demandee, format AAAA-MM.
        raw_dir: dossier ou le XML brut est ecrit avant tout traitement.

    Returns:
        Table longue `source, poste, periode, valeur`. `poste` vaut "00", le
        code COICOP2018 brut du total tel que renvoye par l'API — le
        renommer vers la convention du projet (`CP...`) est du ressort de
        `traitement/`.

    Raises:
        requests.RequestException: erreur reseau ou timeout.
        ValueError: code HTTP different de 200, reponse illisible en XML, ou
            nombre de series different de un (la cle SDMX ne cible plus une
            serie unique : verifier docs/SOURCES.md).
    """
    url = f"{BDM_IPC_2025_URL}/{CLE_IPC_OFFICIEL}"
    try:
        reponse = requests.get(
            url, params={"startPeriod": start_period}, timeout=TIMEOUT_SECONDES
        )
    except requests.RequestException as exc:
        raise requests.RequestException(
            f"Echec de connexion a l'API BDM INSEE ({url}) : {exc}"
        ) from exc

    if reponse.status_code != 200:
        raise ValueError(
            f"API BDM INSEE a repondu {reponse.status_code} pour {url} : "
            f"{reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"insee_ipc_officiel_{start_period}.xml").write_text(
        reponse.text, encoding="utf-8"
    )

    return _parser_sdmx(reponse.text)


def _parser_sdmx(xml_text: str) -> pd.DataFrame:
    try:
        racine = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(
            f"Reponse de l'API BDM INSEE illisible en XML : {exc}"
        ) from exc

    series = racine.findall(".//Series")
    if len(series) != 1:
        raise ValueError(
            f"{len(series)} series renvoyees, une seule attendue pour cette "
            "cle SDMX. Verifier CLE_IPC_OFFICIEL contre docs/SOURCES.md."
        )

    poste = series[0].get("COICOP2018")
    lignes = [
        {
            "source": "insee",
            "poste": poste,
            "periode": obs.get("TIME_PERIOD"),
            "valeur": float(obs.get("OBS_VALUE")),
        }
        for obs in series[0].findall("Obs")
    ]
    return pd.DataFrame(lignes).sort_values("periode").reset_index(drop=True)
