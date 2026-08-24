"""Chargement du registre des releves manuels (ADR 0004).

Les chiffres publies sans API (communiques de presse, etudes) n'ont pas
d'endpoint a interroger : ils sont saisis a la main dans
`data/manual/releves.csv`, une ligne par chiffre publie, avec sa source
complete. Ce module ne fait que lire et valider ce fichier -- aucun calcul,
aucun rebasage, aucune conversion de periode. Ces valeurs, par periode
heterogene, ne sont pas des points d'indice tant que la regle de raccord
n'est pas validee dans docs/METHODOLOGIE.md.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CSV_PATH = Path("data/manual/releves.csv")

# ADR 0004 : une ligne sans ces trois colonnes remplies est rejetee, pas
# silencieusement ignoree.
COLONNES_OBLIGATOIRES = ("source_url", "periode", "qualite")

QUALITES_VALIDES = {"api_ouverte", "etude_publiee", "synthese_presse"}


def charger_releves_manuels(
    poste: str | None = None, chemin: Path = CSV_PATH
) -> pd.DataFrame:
    """Charge et valide `data/manual/releves.csv`.

    Args:
        poste: si fourni, ne retourne que les lignes de ce poste (ex.
            `"CP071"`).
        chemin: emplacement du registre, par defaut `data/manual/releves.csv`.

    Returns:
        Le registre tel quel (une ligne par chiffre publie), eventuellement
        filtre sur `poste`.

    Raises:
        FileNotFoundError: si `chemin` n'existe pas.
        ValueError: registre illisible, colonne obligatoire absente, ligne
            avec `source_url`, `periode` ou `qualite` manquant, ou valeur de
            `qualite` hors des trois crans de `CONTEXT.md`.
    """
    if not chemin.exists():
        raise FileNotFoundError(f"Registre des releves manuels introuvable : {chemin}")

    try:
        table = pd.read_csv(chemin, dtype=str)
    except pd.errors.ParserError as exc:
        raise ValueError(
            f"Registre des releves manuels illisible ({chemin}) : {exc}"
        ) from exc

    colonnes_manquantes = set(COLONNES_OBLIGATOIRES) - set(table.columns)
    if colonnes_manquantes:
        raise ValueError(
            f"Colonnes obligatoires absentes de {chemin} (ADR 0004) : "
            f"{colonnes_manquantes}"
        )

    for colonne in COLONNES_OBLIGATOIRES:
        vides = table[colonne].isna() | (table[colonne].str.strip() == "")
        if vides.any():
            lignes = (table.index[vides] + 2).tolist()  # +2 : en-tete + 1-index
            raise ValueError(
                f"Ligne(s) {lignes} de {chemin} sans '{colonne}' -- rejetee(s), "
                "pas ignoree(s) silencieusement (ADR 0004)."
            )

    qualites_invalides = set(table["qualite"]) - QUALITES_VALIDES
    if qualites_invalides:
        raise ValueError(
            "Valeur(s) de 'qualite' hors des trois crans de CONTEXT.md dans "
            f"{chemin} : {qualites_invalides}"
        )

    if "valeur" in table.columns:
        table["valeur"] = pd.to_numeric(table["valeur"])
    if "evolution_pct" in table.columns:
        table["evolution_pct"] = pd.to_numeric(table["evolution_pct"])

    if poste is not None:
        table = table[table["poste"] == poste].reset_index(drop=True)

    return table
