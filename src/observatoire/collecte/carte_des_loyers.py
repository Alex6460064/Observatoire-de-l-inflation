"""Collecte "Carte des loyers" : indicateurs de loyers d'annonce par commune,
fichier "appartements" (ADR 0023) -- source propre de `CP041` pour l'indice
Observatoire (ADR 0014).

Source : docs/SOURCES.md, section "Carte des loyers -- indice 4, CP041".
Ministere de la Transition ecologique / ANIL, cinq millesimes (2018, 2022,
2023, 2024, 2025) -- 2019, 2020 et 2021 n'ont jamais ete produits (ADR 0016).

URLs de telechargement direct trouvees via l'API data.gouv.fr le 23/08/2026,
un dataset par millesime (le slug se termine par l'annee). Le fichier
retenu est "Indicateurs de loyer appartement" (toutes typologies), jamais
1-2 pieces, 3 pieces et plus, ni maisons (ADR 0023 : maisons exclues, voir
data/manual/parametres.csv).

⚠️ Deux schemas de colonnes coexistent, verifies le 23/08/2026 en
telechargeant chaque fichier :
- **2018** : en-tetes non guillemetes, colonne commune `INSEE`.
- **2022 a 2025** : en-tetes guillemetes, colonne commune `INSEE_C`, une
  colonne `EPCI` de plus, ordre different.
Les deux encodages sont **latin-1** (accents casses en UTF-8, verifie en
direct), jamais UTF-8.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

TIMEOUT_SECONDES = 60

# Verifiees le 23/08/2026 (voir docstring du module) -- un fichier
# "appartements, toutes typologies" par millesime.
URLS_APPARTEMENTS = {
    2018: (
        "https://static.data.gouv.fr/resources/"
        "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2018/"
        "20201203-114600/indicateurs-loyers-appartements.csv"
    ),
    2022: (
        "https://static.data.gouv.fr/resources/"
        "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2022/"
        "20221216-153948/pred-app-mef-dhup.csv"
    ),
    2023: (
        "https://static.data.gouv.fr/resources/"
        "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2023/"
        "20240115-134743/pred-app-mef-dhup.csv"
    ),
    2024: (
        "https://static.data.gouv.fr/resources/"
        "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2024/"
        "20241205-153050/pred-app-mef-dhup.csv"
    ),
    2025: (
        "https://static.data.gouv.fr/resources/"
        "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/"
        "20251211-145010/pred-app-mef-dhup.csv"
    ),
}

# Millesime a partir duquel le schema 2022-2025 (en-tetes guillemetes,
# colonne INSEE_C) s'applique ; avant, schema 2018 (colonne INSEE).
PREMIER_MILLESIME_SCHEMA_RECENT = 2022

MILLESIMES_DISPONIBLES = tuple(sorted(URLS_APPARTEMENTS))


def fetch_carte_des_loyers(
    millesime: int, raw_dir: Path = Path("data/raw")
) -> pd.DataFrame:
    """Telecharge le fichier "appartements" de la Carte des loyers pour un millesime.

    Source : voir docstring du module et docs/SOURCES.md.

    Args:
        millesime: annee de publication, un de `MILLESIMES_DISPONIBLES`
            (2018, 2022, 2023, 2024, 2025 -- ADR 0016).
        raw_dir: dossier ou le CSV brut est ecrit avant tout traitement.

    Returns:
        Table `commune_insee, loyer_m2` -- une ligne par commune, prix
        predit du loyer d'annonce au m2 (`loypredm2`), charges comprises.

    Raises:
        ValueError: `millesime` hors de `MILLESIMES_DISPONIBLES`, code HTTP
            different de 200, CSV illisible, ou colonne attendue absente (le
            schema a peut-etre change, verifier docs/SOURCES.md).
        requests.RequestException: erreur reseau ou timeout.
    """
    if millesime not in URLS_APPARTEMENTS:
        raise ValueError(
            f"Millesime {millesime} non couvert par la Carte des loyers. "
            f"Millesimes disponibles : {MILLESIMES_DISPONIBLES} (ADR 0016)."
        )

    url = URLS_APPARTEMENTS[millesime]
    try:
        reponse = requests.get(url, timeout=TIMEOUT_SECONDES)
    except requests.RequestException as exc:
        raise requests.RequestException(f"Echec de connexion a {url} : {exc}") from exc

    if reponse.status_code != 200:
        raise ValueError(
            f"{url} a repondu {reponse.status_code} : {reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"carte_des_loyers_appartements_{millesime}.csv").write_bytes(
        reponse.content
    )

    return _parser_csv(reponse.content, millesime)


def _parser_csv(contenu: bytes, millesime: int) -> pd.DataFrame:
    schema_recent = millesime >= PREMIER_MILLESIME_SCHEMA_RECENT
    colonne_commune = "INSEE_C" if schema_recent else "INSEE"

    try:
        table = pd.read_csv(
            BytesIO(contenu),
            sep=";",
            decimal=",",
            encoding="latin-1",
            dtype={colonne_commune: str},
        )
    except (UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"CSV Carte des loyers {millesime} illisible : {exc}") from exc

    colonnes_attendues = {colonne_commune, "loypredm2"}
    colonnes_manquantes = colonnes_attendues - set(table.columns)
    if colonnes_manquantes:
        raise ValueError(
            f"Colonnes attendues absentes du CSV Carte des loyers {millesime} : "
            f"{colonnes_manquantes}. Le schema a peut-etre change, verifier "
            "docs/SOURCES.md."
        )

    out = table[[colonne_commune, "loypredm2"]].rename(
        columns={colonne_commune: "commune_insee", "loypredm2": "loyer_m2"}
    )
    out["commune_insee"] = out["commune_insee"].str.zfill(5)

    return out.reset_index(drop=True)
