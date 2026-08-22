"""Collecte de l'IPCH officiel Eurostat, France entiere (indice 1).

Source : docs/SOURCES.md, section "Eurostat -- prix (indices 1, 2 et 4)".
Dataset `prc_hicp_minr` (generation ECOICOP v2), format JSON-stat, sans cle.

Requete verifiee en interrogeant l'API en direct le 22/08/2026 : `geo=FR`,
`coicop18=TOTAL`, `unit=I15` (base 2015=100), `freq=M`. Valeurs de controle
confirmees ce jour-la : 1996-01 = 74,13, 2019-12 = 105,78, 2026-07 = 128,17,
identiques a la re-verification du 21/08/2026 dans docs/SOURCES.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

PRC_HICP_MINR_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr"
)

COICOP_TOTAL = "TOTAL"

TIMEOUT_SECONDES = 30


def fetch_eurostat_ipch_officiel(
    start_period: str = "1996-01",
    raw_dir: Path = Path("data/raw"),
) -> pd.DataFrame:
    """Telecharge l'IPCH officiel France entiere (COICOP `TOTAL`, base I15).

    Source : API Eurostat, dataset `prc_hicp_minr` (voir docs/SOURCES.md,
    verifie le 22/08/2026).

    Args:
        start_period: premiere periode demandee, format AAAA-MM.
        raw_dir: dossier ou le JSON brut est ecrit avant tout traitement.

    Returns:
        Table longue `source, poste, periode, valeur`. `poste` vaut "TOTAL",
        le code COICOP 2018 brut du total tel que renvoye par l'API -- le
        renommer vers la convention du projet est du ressort de
        `traitement/`.

    Raises:
        requests.RequestException: erreur reseau ou timeout.
        ValueError: code HTTP different de 200, reponse illisible en JSON,
            ou dimension `coicop18` ne resolvant pas a un seul code (la
            requete ne cible plus une serie unique : verifier
            docs/SOURCES.md).
    """
    try:
        reponse = requests.get(
            PRC_HICP_MINR_URL,
            params={
                "format": "JSON",
                "geo": "FR",
                "coicop18": COICOP_TOTAL,
                "unit": "I15",
                "freq": "M",
                "sinceTimePeriod": start_period,
            },
            timeout=TIMEOUT_SECONDES,
        )
    except requests.RequestException as exc:
        raise requests.RequestException(
            f"Echec de connexion a l'API Eurostat ({PRC_HICP_MINR_URL}) : {exc}"
        ) from exc

    if reponse.status_code != 200:
        raise ValueError(
            f"API Eurostat a repondu {reponse.status_code} pour "
            f"{PRC_HICP_MINR_URL} : {reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"eurostat_ipch_officiel_{start_period}.json").write_text(
        reponse.text, encoding="utf-8"
    )

    return _parser_json_stat(reponse.text)


def _parser_json_stat(texte_json: str) -> pd.DataFrame:
    try:
        donnees = json.loads(texte_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Reponse de l'API Eurostat illisible en JSON : {exc}"
        ) from exc

    codes_coicop = donnees["dimension"]["coicop18"]["category"]["index"]
    if len(codes_coicop) != 1:
        raise ValueError(
            f"{len(codes_coicop)} codes coicop18 renvoyes, un seul attendu pour "
            "cette requete. Verifier COICOP_TOTAL contre docs/SOURCES.md."
        )
    poste = next(iter(codes_coicop))

    index_periodes = donnees["dimension"]["time"]["category"]["index"]
    valeurs = donnees["value"]

    lignes = [
        {
            "source": "eurostat",
            "poste": poste,
            "periode": periode,
            "valeur": float(valeurs[str(idx)]),
        }
        for periode, idx in index_periodes.items()
        if str(idx) in valeurs
    ]
    return pd.DataFrame(lignes).sort_values("periode").reset_index(drop=True)
