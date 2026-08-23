"""Normalisation de la sortie `collecte.dares` (ADR 0022).

Aucun appel reseau, aucun effet de bord.
"""

import pandas as pd

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


def completer_mensuel(propre: pd.DataFrame) -> pd.DataFrame:
    """Comble les mois manquants entre deux trimestres publies (ADR 0015).

    Le SMB est trimestriel quand le graphe du projet est mensuel (ADR 0013).
    Deux des trois mois de chaque trimestre sont interpoles lineairement
    entre les deux trimestres publies qui les encadrent -- et de la meme
    facon tout trimestre reellement absent du fichier source (ex. 2020-03),
    puisqu'il n'existe alors dans la table d'entree aucune ligne a
    interpoler autour de lui : il se comble comme un mois ordinaire, sur un
    intervalle plus large.

    Args:
        propre: sortie de `nettoyer_salaire_smb`, un seul poste.

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
            "completer_mensuel attend un seul poste (SMB, ligne ENS), "
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
