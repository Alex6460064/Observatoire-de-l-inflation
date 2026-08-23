"""Collecte des prix INSEE : IPC officiel (indice 0) et prix par sous-classe
COICOP 2018 pour l'indice 3 (ADR 0018).

Source : docs/SOURCES.md, section "INSEE — IPC officiel". API BDM,
dataflow `IPC-2025`, sans cle, base
`https://api.insee.fr/series/BDM/V1/data/IPC-2025`.

Cle SDMX verifiee en interrogeant l'API en direct le 22/08/2026 : elle cible
une serie unique par valeur de `COICOP2018`, ex. IDBANK 011814630 pour "00"
— "Ensemble des menages - France - Nomenclature Coicop : 00 - Ensemble",
hors loyers imputes (PRIX_CONSO=SO). Ordre des douze dimensions, voir
docs/SOURCES.md : FREQ.INDICATEUR.FORME-VENTE.COICOP2018.PRIX_CONSO.NATURE.
MENAGES_IPC.REF_AREA.UNIT_MEASURE.CORRECTION.BASIND.SERIE_ARRETEE.

Pour l'indice 3, un code sous-classe par appel (`011` groupe 3 chiffres,
`01111` sous-classe 5 chiffres, testes le 22/08/2026 -- voir
docs/SOURCES.md), jusqu'a 293 appels, espaces pour respecter la limite de
30 appels/minute/IP de l'API BDM.

`04210` et `04220` (loyers imputes, cibles de `CP042` dans
data/manual/correspondance_coicop.csv) renvoient un HTTP 404 "aucun
resultat" -- verifie en direct le 22/08/2026 : l'INSEE ne publie pas de
serie hors loyers imputes pour ces codes. `fetch_insee_prix_par_sous_classe`
leur substitue la serie du groupe `041` (loyers reels), meme traitement que
l'indice 4 (docs/METHODOLOGIE.md 3.4).
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
import requests

BDM_IPC_2025_URL = "https://api.insee.fr/series/BDM/V1/data/IPC-2025"

CLE_IPC_OFFICIEL = "M.IPC.SO.00.SO.INDICE.ENSEMBLE.FE.SO.BRUT.2025.FALSE"

TIMEOUT_SECONDES = 30

# 30 appels/minute/IP maximum (docs/SOURCES.md) : marge incluse.
DELAI_ENTRE_APPELS_SECONDES = 2.1

# L'API BDM reinitialise parfois la connexion en cours de collecte longue
# (constate le 23/08/2026, ConnectionResetError sur plusieurs centaines
# d'appels) : une erreur de connexion ponctuelle n'est pas une absence de
# serie, elle merite une reprise avant d'abandonner tout le run.
NB_TENTATIVES_CONNEXION = 3
DELAI_ENTRE_TENTATIVES_SECONDES = 3.0

# CP042 (loyers imputes) se transpose vers ces deux sous-classes
# (data/manual/correspondance_coicop.csv) ; aucune des deux n'a de serie
# INSEE hors loyers imputes. Substitution documentee : docs/METHODOLOGIE.md
# 3.4, meme traitement que l'indice 4.
SOUS_CLASSES_LOYERS_IMPUTES = ("CP04210", "CP04220")
CODE_GROUPE_LOYERS_REELS = "041"


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


COLONNES_PRIX_BRUT = ["source", "poste", "periode", "valeur"]


def _reponse_sans_resultat(reponse: requests.Response) -> bool:
    """Detecte le 404 SDMX "aucun resultat" (code 100), distinct d'une
    erreur reseau ou de configuration -- verifie en direct le 22/08/2026.
    """
    return reponse.status_code == 404 and 'code="100"' in reponse.text


def fetch_insee_prix_sous_classe(
    code: str,
    start_period: str = "1996-01",
    raw_dir: Path = Path("data/raw"),
) -> pd.DataFrame:
    """Telecharge la serie INSEE d'un code COICOP2018 (sans le prefixe "CP").

    Meme cle SDMX que `fetch_insee_ipc_officiel`, code de dimension
    COICOP2018 parametre (docs/SOURCES.md, verifie le 22/08/2026).

    Args:
        code: code COICOP2018 tel qu'attendu par l'API (sans "CP"), ex.
            "01111" pour la sous-classe, "011" pour le groupe.
        start_period: premiere periode demandee, format AAAA-MM.
        raw_dir: dossier ou le XML brut est ecrit avant tout traitement.

    Returns:
        Table longue `source, poste, periode, valeur`, `poste` = "CP" + code
        (convention du projet). Table vide (memes colonnes) si l'API repond
        "aucun resultat" (SDMX ErrorMessage code 100) : ce code COICOP2018
        n'est pas publie par l'INSEE, distinct d'une erreur reseau.

    Raises:
        requests.RequestException: erreur reseau ou timeout.
        ValueError: code HTTP different de 200 (hors "aucun resultat"),
            reponse illisible en XML, ou plusieurs series renvoyees.
    """
    url = f"{BDM_IPC_2025_URL}/M.IPC.SO.{code}.SO.INDICE.ENSEMBLE.FE.SO.BRUT.2025.FALSE"
    reponse = None
    derniere_erreur: requests.RequestException | None = None
    for tentative in range(NB_TENTATIVES_CONNEXION):
        if tentative > 0:
            time.sleep(DELAI_ENTRE_TENTATIVES_SECONDES)
        try:
            reponse = requests.get(
                url, params={"startPeriod": start_period}, timeout=TIMEOUT_SECONDES
            )
            break
        except requests.exceptions.ConnectionError as exc:
            derniere_erreur = exc
        except requests.RequestException as exc:
            raise requests.RequestException(
                f"Echec de connexion a l'API BDM INSEE ({url}) : {exc}"
            ) from exc

    if reponse is None:
        raise requests.RequestException(
            f"Echec de connexion a l'API BDM INSEE ({url}) apres "
            f"{NB_TENTATIVES_CONNEXION} tentatives : {derniere_erreur}"
        ) from derniere_erreur

    if _reponse_sans_resultat(reponse):
        return pd.DataFrame(columns=COLONNES_PRIX_BRUT)

    if reponse.status_code != 200:
        raise ValueError(
            f"API BDM INSEE a repondu {reponse.status_code} pour {url} : "
            f"{reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"insee_prix_{code}_{start_period}.xml").write_text(
        reponse.text, encoding="utf-8"
    )

    table = _parser_sdmx(reponse.text)
    table["poste"] = f"CP{code}"
    return table


def fetch_insee_prix_par_sous_classe(
    postes: Iterable[str],
    start_period: str = "1996-01",
    raw_dir: Path = Path("data/raw"),
    delai_secondes: float = DELAI_ENTRE_APPELS_SECONDES,
) -> pd.DataFrame:
    """Telecharge les prix INSEE de plusieurs postes, un appel par sous-classe.

    Espace les appels de `delai_secondes` pour respecter la limite de 30
    appels/minute/IP de l'API BDM. `CP04210` et `CP04220` (loyers imputes,
    `SOUS_CLASSES_LOYERS_IMPUTES`) recoivent la serie du groupe `041`
    (loyers reels, docs/METHODOLOGIE.md 3.4) si l'INSEE n'a pas de serie
    propre pour eux -- collectee une seule fois, meme si les deux en ont
    besoin.

    Args:
        postes: codes COICOP2018 convention projet ("CP" + code), ex.
            `["CP01111", "CP011"]`.
        start_period: premiere periode demandee, format AAAA-MM.
        raw_dir: dossier ou le XML brut de chaque appel est ecrit.
        delai_secondes: pause entre deux appels reseau.

    Returns:
        Table longue `source, poste, periode, valeur`, un `poste` par entree
        de `postes` (le poste substitue garde son propre code, pas "CP041").

    Raises:
        requests.RequestException, ValueError: comme
            `fetch_insee_prix_sous_classe`. Un "aucun resultat" pour un
            poste hors `SOUS_CLASSES_LOYERS_IMPUTES` leve une `ValueError`
            explicite : aucune autre substitution n'est documentee
            (docs/METHODOLOGIE.md).
    """
    substitut_loyers_reels: pd.DataFrame | None = None
    tables = []

    for i, poste in enumerate(postes):
        if i > 0:
            time.sleep(delai_secondes)

        code = poste.removeprefix("CP")
        table = fetch_insee_prix_sous_classe(code, start_period, raw_dir)

        if table.empty:
            if poste not in SOUS_CLASSES_LOYERS_IMPUTES:
                raise ValueError(
                    f"Aucune serie INSEE pour {poste!r} (code {code!r}) et "
                    "aucune substitution documentee pour ce poste "
                    "(docs/METHODOLOGIE.md 3.4 ne couvre que les loyers "
                    f"imputes, {SOUS_CLASSES_LOYERS_IMPUTES})."
                )
            if substitut_loyers_reels is None:
                time.sleep(delai_secondes)
                substitut_loyers_reels = fetch_insee_prix_sous_classe(
                    CODE_GROUPE_LOYERS_REELS, start_period, raw_dir
                )
            table = substitut_loyers_reels.copy()
            table["poste"] = poste

        tables.append(table)

    return pd.concat(tables, ignore_index=True)[COLONNES_PRIX_BRUT]
