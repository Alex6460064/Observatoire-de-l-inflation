"""Interpolation lineaire generique entre points publies (ADR 0015).

Extrait de `traitement.dares` (ADR 0022) pour reutilisation par toute source
non mensuelle -- Dares (trimestriel) comme Carte des loyers (annuel avec
trous, ADR 0016). Aucun appel reseau, aucun effet de bord.
"""

import pandas as pd


def completer_mensuel(propre: pd.DataFrame) -> pd.DataFrame:
    """Comble les mois manquants entre deux points publies (ADR 0015).

    Chaque mois qui n'existe pas dans la table d'entree est interpole
    lineairement entre les deux points publies qui l'encadrent -- y compris
    un point entierement absent de la source (ex. un trimestre marque
    "n.d.", ou un millesime jamais produit) : il se comble comme un mois
    ordinaire, sur un intervalle plus large.

    Args:
        propre: table `source, poste, periode, valeur, qualite, interpole`,
            un seul poste, `interpole` toujours `False` en entree (points
            reellement publies).

    Returns:
        Table mensuelle `source, poste, periode, valeur, qualite,
        interpole`, de la premiere a la derniere periode publiee -- aucune
        extrapolation avant ou apres.

    Raises:
        ValueError: plus d'un poste distinct en entree -- cette fonction ne
            sait interpoler qu'une serie a la fois.
    """
    if (propre["poste"] != propre["poste"].iloc[0]).any():
        raise ValueError(
            "completer_mensuel attend un seul poste, "
            f"recu : {sorted(propre['poste'].unique())}."
        )

    table = propre.sort_values("periode").reset_index(drop=True)
    source = table["source"].iloc[0]
    poste = table["poste"].iloc[0]
    qualite = table["qualite"].iloc[0]

    index_mensuel = pd.period_range(
        table["periode"].min(), table["periode"].max(), freq="M"
    )
    serie = table.set_index(pd.PeriodIndex(table["periode"], freq="M"))["valeur"]
    serie = serie.reindex(index_mensuel)
    interpole = serie.isna().to_numpy()
    serie = serie.interpolate(method="linear")

    return pd.DataFrame(
        {
            "source": source,
            "poste": poste,
            "periode": index_mensuel.strftime("%Y-%m"),
            "valeur": serie.to_numpy(),
            "qualite": qualite,
            "interpole": interpole,
        }
    )
