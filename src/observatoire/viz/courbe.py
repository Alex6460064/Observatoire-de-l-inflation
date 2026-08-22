"""Courbe generique multi-series, en niveau, avec segments interpoles en pointille.

Aucun appel reseau, aucun effet de bord (ADR 0015, ADR 0016).
"""

import pandas as pd
import plotly.graph_objects as go

DASH_INTERPOLE = "dot"
DASH_REEL = "solid"


def courbe_multi_series(donnees: pd.DataFrame, col_serie: str = "serie") -> go.Figure:
    """Trace une courbe en niveau par serie, pointillee sur les segments interpoles.

    Une serie dont `interpole` change de valeur au fil du temps est decoupee en
    plusieurs traces Plotly contigues (une par segment), regroupees sous le
    meme `legendgroup` pour n'apparaitre qu'une fois dans la legende — le point
    de jonction entre deux segments est duplique pour que la ligne reste
    continue a l'oeil.

    Args:
        donnees: table longue avec au moins `periode, valeur, interpole` et
            une colonne `col_serie` identifiant la serie (ADR 0002).
        col_serie: nom de la colonne portant le label de serie.

    Returns:
        Une `plotly.graph_objects.Figure` avec une entree de legende par
        serie distincte.
    """
    fig = go.Figure()

    for label, groupe in donnees.groupby(col_serie, sort=False):
        groupe = groupe.reset_index(drop=True)
        segments = _decouper_en_segments(groupe)

        for i, (interpole, segment) in enumerate(segments):
            fig.add_trace(
                go.Scatter(
                    x=segment["periode"].tolist(),
                    y=segment["valeur"].tolist(),
                    mode="lines",
                    name=label,
                    legendgroup=label,
                    showlegend=(i == 0),
                    line={"dash": DASH_INTERPOLE if interpole else DASH_REEL},
                )
            )

    return fig


def _decouper_en_segments(groupe: pd.DataFrame) -> list[tuple[bool, pd.DataFrame]]:
    """Decoupe une serie triee par periode en segments d'`interpole` constant.

    Le dernier point d'un segment est reinjecte en tete du suivant pour que la
    ligne tracee reste visuellement continue malgre le changement de style.
    Retourne des paires `(interpole_du_segment, points)`.
    """
    changement = groupe["interpole"] != groupe["interpole"].shift()
    id_segment = changement.cumsum()

    segments = []
    dernier_point = None
    for _, bloc in groupe.groupby(id_segment, sort=False):
        interpole = bool(bloc["interpole"].iloc[0])
        if dernier_point is not None:
            bloc = pd.concat([dernier_point, bloc], ignore_index=True)
        segments.append((interpole, bloc))
        dernier_point = bloc.iloc[[-1]]

    return segments
