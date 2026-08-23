"""Assemblage de la table de prix de l'indice Observatoire (indice 4),
poste par poste (ADR 0014, ADR 0023, METHODOLOGIE section 4.2 bis).

`CP01`/`CP041`/`CP042`/`CP045`/`CP072` sont des groupes HBS 1999
(`data/manual/correspondance_coicop.csv`, colonne `coicop_1999`), pas les
sous-classes COICOP 2018 sur lesquelles tournent `poids.csv`/`prix.csv` des
indices 2 et 3. L'assemblage part du prix IPCH par sous-classe (meme source
que l'indice 2) et remplace, pour chaque groupe a source propre, le prix de
toutes ses sous-classes cibles par la serie du groupe -- meme mecanique que
la substitution `CP042`->`CP041` deja en production pour les indices 2 et 3
(`collecte.insee.SOUS_CLASSES_LOYERS_IMPUTES`).

Aucun appel reseau, aucun effet de bord (ADR 0008 : l'indice Observatoire
est assemble dans le pipeline, jamais dans le dashboard).
"""

from __future__ import annotations

import pandas as pd

COLONNES_PRIX = ["source", "poste", "periode", "valeur", "qualite", "interpole"]


def assembler_prix_indice_observatoire(
    prix_ipch: pd.DataFrame,
    correspondance: pd.DataFrame,
    series_propres: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Remplace, sous-classe par sous-classe, le prix IPCH par les sources propres.

    Args:
        prix_ipch: table `source, poste, periode, valeur, qualite, interpole`
            par sous-classe COICOP 2018 (repli par defaut, METHODOLOGIE 4.2).
        correspondance: `data/manual/correspondance_coicop.csv`, colonnes
            `coicop_2018` (sous-classe), `coicop_1999` (groupe).
        series_propres: groupe HBS 1999 -> table de prix du groupe (memes
            colonnes que `prix_ipch`, `poste` porte le code du groupe, ex.
            `"CP041"`). `CP042` (loyers imputes) recoit la meme table que
            `CP041` -- a passer explicitement par l'appelant
            (`series_propres["CP042"] = series_propres["CP041"]`), comme
            `collecte.insee.SOUS_CLASSES_LOYERS_IMPUTES` le fait deja pour
            les indices 2 et 3 (ADR 0005).

    Returns:
        Table `source, poste, periode, valeur, qualite, interpole` par
        sous-classe COICOP 2018 : les sous-classes couvertes par un groupe
        de `series_propres` portent sa serie sur ses seules periodes
        publiees (aucune extrapolation) ; les autres gardent leur prix IPCH.

    Raises:
        ValueError: un groupe de `series_propres` n'a aucune sous-classe
            cible dans `correspondance` -- schema de correspondance change
            ou code de groupe errone.
    """
    overrides = []
    sous_classes_couvertes: set[str] = set()

    for groupe, serie in series_propres.items():
        cibles = correspondance.loc[
            correspondance["coicop_1999"] == groupe, "coicop_2018"
        ].unique()
        if len(cibles) == 0:
            raise ValueError(
                f"Aucune sous-classe COICOP 2018 pour le groupe {groupe!r} "
                "dans la table de correspondance. Verifier "
                "data/manual/correspondance_coicop.csv."
            )
        for sous_classe in cibles:
            table = serie.copy()
            table["poste"] = sous_classe
            overrides.append(table)
            sous_classes_couvertes.add(sous_classe)

    base = prix_ipch.loc[~prix_ipch["poste"].isin(sous_classes_couvertes)]
    out = pd.concat([base, *overrides], ignore_index=True)

    return out[COLONNES_PRIX].sort_values(["poste", "periode"]).reset_index(drop=True)
