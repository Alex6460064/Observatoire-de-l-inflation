"""Collecte CRE : bareme historique du tarif reglemente de vente
d'electricite (TRVE), option Base -- source propre de `CP045` pour l'indice
Observatoire (ADR 0014, ADR 0023).

Source : docs/SOURCES.md, section "CRE -- tarif reglemente de vente
d'electricite (indice 4, CP045)". Verifie le 21/08/2026 : 111 lignes,
23/07/2012 -> 01/02/2026, licence `notspecified` sur data.gouv mais couverte
par le regime L322-1 CRPA (docs/SOURCES.md, section "Regime des licences").

C'est un bareme, pas une serie de prix : `abonnement + kWh x consommation`.
Ce module ne fait que collecter et normaliser le bareme brut -- le calcul du
cout pour le profil de consommation retenu (ADR 0023,
`data/manual/parametres.csv`) vit dans `traitement.cre`.
"""

from __future__ import annotations

import datetime as dt
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

CSV_URL = (
    "https://www.cre.fr/fileadmin/Documents/Open_data/Marches_de_detail/Option_Base.csv"
)

TIMEOUT_SECONDES = 30

# Colonnes du CSV CRE (verifiees le 21/08/2026, docs/SOURCES.md) vers la
# convention interne. Les parts HT sont ecartees : seul le TTC entre dans un
# indice de prix paye par un menage.
COLONNES_RETENUES = {
    "DATE_DEBUT": "date_debut",
    "DATE_FIN": "date_fin",
    "P_SOUSCRITE": "puissance_kva",
    "PART_FIXE_TTC": "part_fixe_ttc",
    "PART_VARIABLE_TTC": "part_variable_ttc",
}


def fetch_cre_tarif_base(
    raw_dir: Path = Path("data/raw"),
    date_extraction: dt.date | None = None,
) -> pd.DataFrame:
    """Telecharge le bareme CRE du tarif reglemente, option Base.

    Source : data.gouv.fr / cre.fr, voir docs/SOURCES.md, verifie le
    21/08/2026.

    Args:
        raw_dir: dossier ou le CSV brut est ecrit avant tout traitement.
        date_extraction: date attribuee a cet export, par defaut aujourd'hui.

    Returns:
        Table `date_debut, date_fin, puissance_kva, part_fixe_ttc,
        part_variable_ttc` -- une ligne par periode de validite et par
        puissance souscrite. `date_fin` est `None` (pas `NaT`) pour la ligne
        en cours de validite.

    Raises:
        requests.RequestException: erreur reseau ou timeout.
        ValueError: code HTTP different de 200, CSV illisible, colonne
            attendue absente, ou valeur non convertible (le schema CRE a pu
            changer -- verifier contre docs/SOURCES.md avant de corriger
            silencieusement).
    """
    date_extraction = date_extraction or dt.date.today()

    try:
        reponse = requests.get(CSV_URL, timeout=TIMEOUT_SECONDES)
    except requests.RequestException as exc:
        raise requests.RequestException(
            f"Echec de connexion a cre.fr ({CSV_URL}) : {exc}"
        ) from exc

    if reponse.status_code != 200:
        raise ValueError(
            f"cre.fr a repondu {reponse.status_code} pour {CSV_URL} : "
            f"{reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    nom_fichier = f"cre_tarif_base_{date_extraction.isoformat()}.csv"
    (raw_dir / nom_fichier).write_bytes(reponse.content)

    return _parser_csv(reponse.content)


def _parser_csv(contenu: bytes) -> pd.DataFrame:
    try:
        table = pd.read_csv(
            StringIO(contenu.decode("utf-8-sig")),
            sep=";",
            decimal=",",
            dtype={"DATE_DEBUT": str, "DATE_FIN": str},
        )
    except (UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"CSV CRE Option_Base illisible : {exc}") from exc

    colonnes_manquantes = set(COLONNES_RETENUES) - set(table.columns)
    if colonnes_manquantes:
        raise ValueError(
            f"Colonnes attendues absentes du CSV CRE : {colonnes_manquantes}. "
            "Le schema a peut-etre change, verifier docs/SOURCES.md."
        )

    table = table[list(COLONNES_RETENUES)].rename(columns=COLONNES_RETENUES)

    for colonne in ("date_debut", "date_fin"):
        table[colonne] = pd.to_datetime(
            table[colonne], format="%d/%m/%Y", errors="coerce"
        )
    if table["date_debut"].isna().any():
        raise ValueError(
            "Au moins une valeur de DATE_DEBUT non convertible en date. "
            "Le format CRE a peut-etre change, verifier docs/SOURCES.md."
        )

    for colonne in ("puissance_kva", "part_fixe_ttc", "part_variable_ttc"):
        if not pd.api.types.is_numeric_dtype(table[colonne]):
            raise ValueError(
                f"Colonne '{colonne}' non numerique apres lecture. "
                "Le schema CRE a peut-etre change, verifier docs/SOURCES.md."
            )

    table["date_fin"] = (
        table["date_fin"].astype(object).where(table["date_fin"].notna(), None)
    )

    return table.reset_index(drop=True)
