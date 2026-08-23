"""Normalisation de la sortie `collecte.dares` (ADR 0022).

Aucun appel reseau, aucun effet de bord.
"""

import pandas as pd

from observatoire.traitement.interpolation import completer_mensuel  # noqa: F401

# Pas d'endpoint rejouable (blocage anti-bot, docs/SOURCES.md), mais un
# protocole publie et decrit (enquete Acemo) -- CONTEXT.md, meme cran que
# Familles Rurales et ARCEP.
QUALITE_DARES = "etude_publiee"


def nettoyer_salaire_smb(brut: pd.DataFrame) -> pd.DataFrame:
    """Ajoute `qualite` et `interpole` a la table `source, poste, periode, valeur`.

    Args:
        brut: table longue renvoyee par `collecte.dares.lire_salaire_smb`.

    Returns:
        La meme table, colonnes `source, poste, periode, valeur, qualite,
        interpole` -- `interpole` toujours `False`, ce sont les trimestres
        reellement publies.
    """
    out = brut.copy()
    out["qualite"] = QUALITE_DARES
    out["interpole"] = False
    return out
