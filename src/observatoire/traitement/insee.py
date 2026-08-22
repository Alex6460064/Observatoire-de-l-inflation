"""Normalisation de la sortie `collecte.insee` vers le schema prix.csv (ADR 0008).

Aucun appel reseau, aucun effet de bord.
"""

import pandas as pd

QUALITE_INSEE = "api_ouverte"  # endpoint public rejouable (CONTEXT.md)


def normaliser_insee_ipc_officiel(prix: pd.DataFrame) -> pd.DataFrame:
    """Ajoute `qualite` et `interpole` a la table `source, poste, periode, valeur`.

    L'IPC officiel est une donnee mensuelle reellement publiee par un
    endpoint public rejouable : `qualite` vaut toujours `api_ouverte` et
    `interpole` toujours `False` (jamais une valeur calculee).

    Args:
        prix: table longue renvoyee par `collecte.insee.fetch_insee_ipc_officiel`.

    Returns:
        La meme table, colonnes `source, poste, periode, valeur, qualite, interpole`.
    """
    out = prix.copy()
    out["qualite"] = QUALITE_INSEE
    out["interpole"] = False
    return out
