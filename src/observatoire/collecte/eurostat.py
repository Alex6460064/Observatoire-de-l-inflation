"""Collecte des donnees Eurostat : IPCH officiel (indice 1) et poids de
profil pour la transposition HBS -> COICOP 2018 (indice 3, ADR 0018).

Source : docs/SOURCES.md, sections "Eurostat -- prix (indices 1, 2 et 4)" et
"Eurostat HBS -- poids de profil (indices 2, 3 et 4)".

Requetes verifiees en interrogeant les API en direct le 22/08/2026 :
- `prc_hicp_minr` : `geo=FR`, `coicop18=TOTAL`, `unit=I15` (base 2015=100),
  `freq=M`. Valeurs de controle confirmees ce jour-la : 1996-01 = 74,13,
  2019-12 = 105,78, 2026-07 = 128,17, identiques a la re-verification du
  21/08/2026 dans docs/SOURCES.md.
- `hbs_str_t223` : `geo=FR`, `time=2020`, `unit=PM`. Les cinq quintiles
  arrivent dans le meme appel (dimension `quant_inc`). `CP01` QU1=147,
  QU3=154, QU5=128, conforme a `hbs_str_t211` deja relevee dans
  docs/SOURCES.md.
- `prc_hicp_iw` : `geo=FR`, `time=2020`. 553 codes renseignes sur 559 ;
  filtrer sur le format `CP` + 5 chiffres isole les 293 sous-classes du piege
  documente (codes classe a 6 caracteres, codes agregats speciaux comme
  `FOOD_NP` qui tombent aussi a 7 caracteres sans etre des sous-classes).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import requests

PRC_HICP_MINR_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr"
)
HBS_STR_T223_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/hbs_str_t223"
)
PRC_HICP_IW_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_iw"
)

COICOP_TOTAL = "TOTAL"

# Millesime demande aux deux datasets de poids : docs/SOURCES.md ("la vague
# 2020 francaise n'est pas une collecte 2020", mais c'est le seul millesime
# ou les deux datasets sont alignes). Fige en constante, jamais en dur.
ANNEE_POIDS = "2020"

QUINTILES = ("QU1", "QU2", "QU3", "QU4", "QU5")

# Sous-classe COICOP 2018 : "CP" + 5 chiffres. Distingue des classes ("CP" + 4
# chiffres, 6 caracteres) et des codes agregats speciaux qui partagent parfois
# la meme longueur (7) sans suivre ce format, ex. "FOOD_NP" -- piege verifie
# le 22/08/2026, voir docs/SOURCES.md.
REGEX_SOUS_CLASSE = re.compile(r"CP\d{5}$")

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


def _get_eurostat_json(url: str, params: dict, raw_dir: Path, nom_fichier: str) -> str:
    """Appelle un endpoint Eurostat, sauvegarde le JSON brut, renvoie le texte."""
    try:
        reponse = requests.get(url, params=params, timeout=TIMEOUT_SECONDES)
    except requests.RequestException as exc:
        raise requests.RequestException(
            f"Echec de connexion a l'API Eurostat ({url}) : {exc}"
        ) from exc

    if reponse.status_code != 200:
        raise ValueError(
            f"API Eurostat a repondu {reponse.status_code} pour {url} : "
            f"{reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / nom_fichier).write_text(reponse.text, encoding="utf-8")
    return reponse.text


def _decoder_json_stat(texte_json: str) -> pd.DataFrame:
    """Decode un JSON-stat multi-dimensions en table longue, une colonne par
    dimension plus `valeur`. Generique : ne suppose aucune dimension precise.
    """
    try:
        donnees = json.loads(texte_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Reponse de l'API Eurostat illisible en JSON : {exc}"
        ) from exc

    dims = donnees["id"]
    tailles = donnees["size"]
    categories = [
        {
            idx: code
            for code, idx in donnees["dimension"][dim]["category"]["index"].items()
        }
        for dim in dims
    ]

    # JSON-stat : index plat = somme des index de dimension ponderes par le
    # produit des tailles des dimensions suivantes (la premiere dimension
    # varie le plus lentement).
    multiplicateurs = [0] * len(dims)
    acc = 1
    for i in range(len(dims) - 1, -1, -1):
        multiplicateurs[i] = acc
        acc *= tailles[i]

    valeurs = donnees["value"]
    lignes = []
    for cle, valeur in valeurs.items():
        reste = int(cle)
        ligne = {}
        for dim, mult, categorie in zip(dims, multiplicateurs, categories, strict=True):
            idx_dim, reste = divmod(reste, mult) if mult else (0, reste)
            ligne[dim] = categorie[idx_dim]
        ligne["valeur"] = float(valeur)
        lignes.append(ligne)

    return pd.DataFrame(lignes)


def fetch_eurostat_hbs_poids(raw_dir: Path = Path("data/raw")) -> pd.DataFrame:
    """Telecharge les poids de groupe HBS France, les cinq quintiles de niveau
    de vie en un seul appel.

    Source : API Eurostat, dataset `hbs_str_t223` (voir docs/SOURCES.md,
    verifie le 22/08/2026). Poids en ECOICOP v1, non transposes -- voir
    `traitement.poids.transposer_poids_hbs`.

    Args:
        raw_dir: dossier ou le JSON brut est ecrit avant tout traitement.

    Returns:
        Table longue `modalite, poste, valeur`, les modalites `QU1` a `QU5`
        (la modalite `UNK` de l'API est exclue, hors perimetre ADR 0011).

    Raises:
        requests.RequestException: erreur reseau ou timeout.
        ValueError: code HTTP different de 200 ou reponse illisible en JSON.
    """
    texte_json = _get_eurostat_json(
        HBS_STR_T223_URL,
        {"format": "JSON", "geo": "FR", "time": ANNEE_POIDS, "unit": "PM"},
        raw_dir,
        f"eurostat_hbs_poids_{ANNEE_POIDS}.json",
    )

    table = _decoder_json_stat(texte_json)
    table = table.loc[table.quant_inc.isin(QUINTILES)]
    return (
        table[["quant_inc", "coicop", "valeur"]]
        .rename(columns={"quant_inc": "modalite", "coicop": "poste"})
        .sort_values(["modalite", "poste"])
        .reset_index(drop=True)
    )


def fetch_eurostat_ipch_poids_articles(
    raw_dir: Path = Path("data/raw"),
) -> pd.DataFrame:
    """Telecharge les poids d'articles IPCH France au niveau sous-classe.

    Source : API Eurostat, dataset `prc_hicp_iw` (voir docs/SOURCES.md,
    verifie le 22/08/2026). Clef de repartition de la transposition HBS
    (ADR 0018) -- voir `traitement.poids.transposer_poids_hbs`.

    Args:
        raw_dir: dossier ou le JSON brut est ecrit avant tout traitement.

    Returns:
        Table longue `poste, valeur`, filtree aux seules sous-classes COICOP
        2018 (format `CP` + 5 chiffres) -- les codes classe (6 caracteres) et
        les codes agregats speciaux sont exclus (piege documente dans
        docs/SOURCES.md).

    Raises:
        requests.RequestException: erreur reseau ou timeout.
        ValueError: code HTTP different de 200 ou reponse illisible en JSON.
    """
    texte_json = _get_eurostat_json(
        PRC_HICP_IW_URL,
        {"format": "JSON", "geo": "FR", "time": ANNEE_POIDS},
        raw_dir,
        f"eurostat_ipch_poids_articles_{ANNEE_POIDS}.json",
    )

    table = _decoder_json_stat(texte_json)
    sous_classe = table.coicop18.str.fullmatch(REGEX_SOUS_CLASSE)
    table = table.loc[sous_classe]
    return (
        table[["coicop18", "valeur"]]
        .rename(columns={"coicop18": "poste"})
        .sort_values("poste")
        .reset_index(drop=True)
    )
