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

from observatoire.collecte.eurostat import (
    fetch_eurostat_hbs_poids,
    fetch_eurostat_ipch_officiel,
    fetch_eurostat_ipch_poids_articles,
)
from observatoire.collecte.insee import (
    fetch_insee_ipc_officiel,
    fetch_insee_prix_par_sous_classe,
)
from observatoire.traitement.eurostat import normaliser_eurostat_ipch_officiel
from observatoire.traitement.insee import (
    normaliser_insee_ipc_officiel,
    normaliser_insee_prix_sous_classe,
)
from observatoire.traitement.poids import assembler_poids_quintiles

PRIX_CSV = Path("data/processed/prix.csv")
POIDS_CSV = Path("data/processed/poids.csv")
META_JSON = Path("data/processed/META.json")
CORRESPONDANCE_CSV = Path("data/manual/correspondance_coicop.csv")

COLONNES_PRIX = ["source", "poste", "periode", "valeur", "qualite", "interpole"]
COLONNES_POIDS = ["axe", "modalite", "poste", "pm"]


def postes_avec_poids_non_nul(poids: pd.DataFrame) -> list[str]:
    """Postes a collecter cote prix INSEE : ceux qui pesent reellement quelque
    chose dans au moins un quintile (ticket #12) -- inutile de collecter un
    poste qui pese zero partout.
    """
    return sorted(poids.loc[poids.pm > 0, "poste"].unique())


def collecter_et_normaliser_toutes_sources(poids: pd.DataFrame) -> pd.DataFrame:
    """Appelle collecte + traitement pour chaque source connue.

    INSEE (indice 0, `ipc_officiel`), Eurostat (indice 1, `ipch`), et prix
    INSEE par sous-classe COICOP 2018 pour l'indice 3 (`poids` fournit la
    liste des postes a collecter).
    """
    normalise_insee = normaliser_insee_ipc_officiel(fetch_insee_ipc_officiel())
    normalise_eurostat = normaliser_eurostat_ipch_officiel(
        fetch_eurostat_ipch_officiel()
    )
    normalise_insee_sous_classe = normaliser_insee_prix_sous_classe(
        fetch_insee_prix_par_sous_classe(postes_avec_poids_non_nul(poids))
    )
    return pd.concat(
        [normalise_insee, normalise_eurostat, normalise_insee_sous_classe],
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


def ecrire_meta(chemin: Path, date_collecte: date) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(
        json.dumps({"date_collecte": date_collecte.strftime("%Y-%m-%d")}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    poids = assembler_poids()
    prix = collecter_et_normaliser_toutes_sources(poids)

    PRIX_CSV.parent.mkdir(parents=True, exist_ok=True)
    prix.to_csv(PRIX_CSV, index=False)
    poids.to_csv(POIDS_CSV, index=False)

    ecrire_meta(META_JSON, datetime.now().date())


if __name__ == "__main__":
    main()
