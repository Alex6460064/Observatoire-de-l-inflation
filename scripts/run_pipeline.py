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

from observatoire.collecte.eurostat import fetch_eurostat_ipch_officiel
from observatoire.collecte.insee import fetch_insee_ipc_officiel
from observatoire.traitement.eurostat import normaliser_eurostat_ipch_officiel
from observatoire.traitement.insee import normaliser_insee_ipc_officiel

PRIX_CSV = Path("data/processed/prix.csv")
META_JSON = Path("data/processed/META.json")

COLONNES_PRIX = ["source", "poste", "periode", "valeur", "qualite", "interpole"]


def collecter_et_normaliser_toutes_sources() -> pd.DataFrame:
    """Appelle collecte + traitement pour chaque source connue.

    Aujourd'hui : INSEE (indice 0, `ipc_officiel`) et Eurostat (indice 1, `ipch`).
    """
    normalise_insee = normaliser_insee_ipc_officiel(fetch_insee_ipc_officiel())
    normalise_eurostat = normaliser_eurostat_ipch_officiel(
        fetch_eurostat_ipch_officiel()
    )
    return pd.concat([normalise_insee, normalise_eurostat], ignore_index=True)[
        COLONNES_PRIX
    ]


def ecrire_meta(chemin: Path, date_collecte: date) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(
        json.dumps({"date_collecte": date_collecte.strftime("%Y-%m-%d")}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    prix = collecter_et_normaliser_toutes_sources()

    PRIX_CSV.parent.mkdir(parents=True, exist_ok=True)
    prix.to_csv(PRIX_CSV, index=False)

    ecrire_meta(META_JSON, datetime.now().date())


if __name__ == "__main__":
    main()
