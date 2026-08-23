"""Collecte ADEME Car Labelling : catalogue des vehicules neufs commercialises
en France, candidat de source propre pour `CP071` (achat de vehicules).

Source : docs/SOURCES.md, section "ADEME Car Labelling -- candidat CP071".
Le champ `Prix vehicule` est confirme present et rempli (3604/3604 lignes,
verifie le 23/08/2026 sur l'export du 14/07/2026). Licence Ouverte (Etalab).

Piege : l'API data-fair sous-jacente (data.ademe.fr) expose `"history": null`
-- aucune archive datee accessible. Le fichier est ecrase en place a chaque
mise a jour. Cette fonction doit donc etre executee et son resultat archive
a chaque mise a jour pour construire un historique ; il n'existe aucun moyen
de recuperer les millesimes anterieurs a la premiere execution (ADR 0020).

ADR 0020 : pas d'adoption de `CP071` comme poste de l'indice Observatoire
tant que le raccord de sources (IPCH avant la premiere capture, serie propre
apres) n'est pas valide dans docs/METHODOLOGIE.md. Cette fonction ne fait donc
que collecter et archiver -- aucun poste COICOP, aucune agregation, aucun
calcul d'indice.
"""

from __future__ import annotations

import datetime as dt
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

CSV_URL = (
    "https://www.data.gouv.fr/api/1/datasets/r/669a1f00-299f-4c7c-9db2-cd32401e7b25"
)

TIMEOUT_SECONDES = 30

# Noms de colonnes tels que publies par ADEME (UTF-8 avec BOM, verifie
# caractere par caractere le 23/08/2026 -- voir docs/SOURCES.md) vers la
# convention interne du projet.
COLONNES_RETENUES = {
    "Marque": "marque",
    "Modèle": "modele",
    "Energie": "energie",
    "Prix véhicule": "prix_vehicule",
}


def fetch_ademe_carlabelling(
    raw_dir: Path = Path("data/raw"),
    date_extraction: dt.date | None = None,
) -> pd.DataFrame:
    """Telecharge l'export courant du catalogue ADEME Car Labelling.

    Source : data.gouv.fr, jeu de donnees `ademe-car-labelling` (voir
    docs/SOURCES.md, verifie le 23/08/2026).

    Args:
        raw_dir: dossier ou le CSV brut est ecrit avant tout traitement.
        date_extraction: date attribuee a cet export, par defaut aujourd'hui.
            A fixer explicitement pour un nom de fichier reproductible
            (tests, ou reconstitution d'un archivage manque).

    Returns:
        Table `marque, modele, energie, prix_vehicule, date_extraction`, une
        ligne par version commercialisee au moment de l'extraction. Aucun
        poste COICOP, aucune agregation : l'ADR 0020 n'a pas encore valide de
        formule pour convertir ce catalogue en indice `CP071`.

    Raises:
        requests.RequestException: erreur reseau ou timeout.
        FileExistsError: un fichier existe deja pour `date_extraction` --
            la source ecrase son fichier en place (ADR 0020), un second appel
            le meme jour ecraserait un millesime deja capture.
        ValueError: code HTTP different de 200, CSV illisible, colonne
            attendue absente, ou valeur de `prix_vehicule` non convertible
            (le schema ADEME a pu changer -- verifier contre docs/SOURCES.md
            avant de corriger silencieusement).
    """
    date_extraction = date_extraction or dt.date.today()

    try:
        reponse = requests.get(CSV_URL, timeout=TIMEOUT_SECONDES)
    except requests.RequestException as exc:
        raise requests.RequestException(
            f"Echec de connexion a data.gouv.fr ({CSV_URL}) : {exc}"
        ) from exc

    if reponse.status_code != 200:
        raise ValueError(
            f"data.gouv.fr a repondu {reponse.status_code} pour {CSV_URL} : "
            f"{reponse.text[:500]}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    nom_fichier = f"ademe_carlabelling_{date_extraction.isoformat()}.csv"
    chemin_fichier = raw_dir / nom_fichier
    if chemin_fichier.exists():
        raise FileExistsError(
            f"{chemin_fichier} existe deja. La source ecrase son fichier en "
            "place (ADR 0020) : un second appel le meme jour ecraserait un "
            "millesime deja capture sans laisser de trace. Supprimer le "
            "fichier a la main si le re-telechargement est volontaire."
        )
    chemin_fichier.write_bytes(reponse.content)

    return _parser_csv(reponse.content, date_extraction)


def _parser_csv(contenu: bytes, date_extraction: dt.date) -> pd.DataFrame:
    try:
        table = pd.read_csv(StringIO(contenu.decode("utf-8-sig")), sep=";", dtype=str)
    except (UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"CSV ADEME Car Labelling illisible : {exc}") from exc

    colonnes_manquantes = set(COLONNES_RETENUES) - set(table.columns)
    if colonnes_manquantes:
        raise ValueError(
            f"Colonnes attendues absentes du CSV ADEME : {colonnes_manquantes}. "
            "Le schema a peut-etre change, verifier docs/SOURCES.md."
        )

    table = table[list(COLONNES_RETENUES)].rename(columns=COLONNES_RETENUES)

    prix_brut = table["prix_vehicule"]
    prix_converti = pd.to_numeric(prix_brut, errors="coerce")
    prix_non_vide = prix_brut.notna() & (prix_brut.str.strip() != "")
    non_convertible = prix_non_vide & prix_converti.isna()
    if non_convertible.any():
        exemples = prix_brut[non_convertible].head(5).tolist()
        raise ValueError(
            f"{non_convertible.sum()} valeurs de 'Prix vehicule' non numeriques "
            f"apres nettoyage (exemples : {exemples}). Le schema a peut-etre "
            "change, verifier docs/SOURCES.md avant de corriger silencieusement."
        )
    table["prix_vehicule"] = prix_converti
    table["date_extraction"] = date_extraction.isoformat()

    return table.reset_index(drop=True)
