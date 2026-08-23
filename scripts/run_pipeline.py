"""Orchestrateur du pipeline : collecte + traitement -> data/processed/.

Concatene en memoire les tables nettoyees de chaque source connue et ecrit
`prix.csv` en overwrite complet (pas d'append, pas de merge disque — ADR 0008).
Ajouter une source future se resume a ajouter une entree ici.

Usage : uv run python scripts/run_pipeline.py
"""

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from observatoire.collecte.dares import (
    chemin_dernier_fichier_salaire_smb,
    lire_salaire_smb,
)
from observatoire.collecte.eurostat import (
    fetch_eurostat_hbs_poids,
    fetch_eurostat_ipch_officiel,
    fetch_eurostat_ipch_poids_articles,
    fetch_eurostat_prix_par_sous_classe,
)
from observatoire.collecte.insee import (
    fetch_insee_ipc_officiel,
    fetch_insee_prix_par_sous_classe,
)
from observatoire.traitement.dares import completer_mensuel, nettoyer_salaire_smb
from observatoire.traitement.eurostat import (
    normaliser_eurostat_ipch_officiel,
    normaliser_eurostat_prix_sous_classe,
)
from observatoire.traitement.insee import (
    normaliser_insee_ipc_officiel,
    normaliser_insee_prix_sous_classe,
)
from observatoire.traitement.poids import (
    assembler_poids_quintiles,
    exclure_postes_du_panier,
    postes_sans_historique_a_la_reference,
)

PRIX_CSV = Path("data/processed/prix.csv")
POIDS_CSV = Path("data/processed/poids.csv")
SALAIRE_CSV = Path("data/processed/salaire_smb.csv")
META_JSON = Path("data/processed/META.json")
CORRESPONDANCE_CSV = Path("data/manual/correspondance_coicop.csv")
RAW_DIR = Path("data/raw")

COLONNES_PRIX = ["source", "poste", "periode", "valeur", "qualite", "interpole"]
COLONNES_POIDS = ["axe", "modalite", "poste", "pm"]
COLONNES_SALAIRE = ["source", "poste", "periode", "valeur", "qualite", "interpole"]

# Meme reference que dashboard.py (ADR 0009) : synchronisee a la main, un seul
# lieu de verite n'existe pas encore dans le projet.
REFERENCE = "2019-12"


def postes_avec_poids_non_nul(poids: pd.DataFrame) -> list[str]:
    """Postes a collecter cote prix, INSEE (indice 3) comme Eurostat (indice
    2, ticket 03) : ceux qui pesent reellement quelque chose dans au moins
    un quintile (ticket #12) -- inutile de collecter un poste qui pese zero
    partout.
    """
    return sorted(poids.loc[poids.pm > 0, "poste"].unique())


def collecter_et_normaliser_toutes_sources(poids: pd.DataFrame) -> pd.DataFrame:
    """Appelle collecte + traitement pour chaque source connue.

    INSEE (indice 0, `ipc_officiel`), Eurostat (indice 1, `ipch`), prix
    INSEE par sous-classe COICOP 2018 pour l'indice 3, et prix Eurostat par
    sous-classe COICOP 2018 pour l'indice 2 (`poids` fournit la liste des
    postes a collecter, partagee entre indices 2 et 3 -- ticket 02).
    """
    normalise_insee = normaliser_insee_ipc_officiel(fetch_insee_ipc_officiel())
    normalise_eurostat = normaliser_eurostat_ipch_officiel(
        fetch_eurostat_ipch_officiel()
    )
    normalise_insee_sous_classe = normaliser_insee_prix_sous_classe(
        fetch_insee_prix_par_sous_classe(postes_avec_poids_non_nul(poids))
    )
    normalise_eurostat_sous_classe = normaliser_eurostat_prix_sous_classe(
        fetch_eurostat_prix_par_sous_classe(postes_avec_poids_non_nul(poids))
    )
    return pd.concat(
        [
            normalise_insee,
            normalise_eurostat,
            normalise_insee_sous_classe,
            normalise_eurostat_sous_classe,
        ],
        ignore_index=True,
    )[COLONNES_PRIX]


def assembler_poids() -> pd.DataFrame:
    """Assemble `poids.csv` : indice 3, axe `quintile_revenu` (ADR 0011).

    Transposition des poids HBS vers COICOP 2018 -- voir
    `traitement.poids.assembler_poids_quintiles` (ticket #11).
    """
    correspondance = pd.read_csv(CORRESPONDANCE_CSV)
    poids_hbs = fetch_eurostat_hbs_poids()
    poids_iw = fetch_eurostat_ipch_poids_articles()
    poids = assembler_poids_quintiles(poids_hbs, poids_iw, correspondance)
    return poids[COLONNES_POIDS]


def construire_salaire_smb(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Salaire mensuel de base (SMB), indice 6 hors ADR 0002 (ADR 0022).

    Pas de reseau : lit le dernier fichier Dares archive dans `raw_dir`
    (telechargement manuel, blocage anti-bot Cegedim -- ADR 0022) plutot
    que de le collecter.
    """
    brut = lire_salaire_smb(chemin_dernier_fichier_salaire_smb(raw_dir))
    propre = nettoyer_salaire_smb(brut)
    return completer_mensuel(propre)[COLONNES_SALAIRE]


def ecrire_meta(chemin: Path, date_collecte: date) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(
        json.dumps({"date_collecte": date_collecte.strftime("%Y-%m-%d")}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    poids = assembler_poids()
    prix = collecter_et_normaliser_toutes_sources(poids)

    # Un poste pondere sans historique jusqu'a REFERENCE ne peut pas etre
    # rebase (docs/METHODOLOGIE.md 3.3). Panier commun entre indices 2 et 3
    # (ticket 02) : exclusion = union des trous INSEE et Eurostat, poids.csv
    # reste un seul fichier, renormalise une seule fois.
    postes_pondere = postes_avec_poids_non_nul(poids)
    sans_historique_insee = postes_sans_historique_a_la_reference(
        prix.loc[prix.source == "insee"], postes_pondere, REFERENCE
    )
    sans_historique_eurostat = postes_sans_historique_a_la_reference(
        prix.loc[prix.source == "eurostat"], postes_pondere, REFERENCE
    )
    sans_historique = sorted(set(sans_historique_insee) | set(sans_historique_eurostat))
    poids = exclure_postes_du_panier(poids, sans_historique)

    salaire_smb = construire_salaire_smb()

    PRIX_CSV.parent.mkdir(parents=True, exist_ok=True)
    prix.to_csv(PRIX_CSV, index=False)
    poids.to_csv(POIDS_CSV, index=False)
    salaire_smb.to_csv(SALAIRE_CSV, index=False)

    ecrire_meta(META_JSON, datetime.now().date())


if __name__ == "__main__":
    main()
