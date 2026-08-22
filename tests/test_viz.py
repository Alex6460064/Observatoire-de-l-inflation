"""Tests de `viz.courbe` — composant Plotly multi-series (ADR 0015, ADR 0016)."""

import pandas as pd

from observatoire.viz.courbe import courbe_multi_series


def table(lignes):
    """Construit une table longue `serie, periode, valeur, interpole`."""
    return pd.DataFrame(lignes, columns=["serie", "periode", "valeur", "interpole"])


def test_une_trace_par_serie_quand_aucun_segment_interpole():
    donnees = table(
        [
            ("ipc_officiel", "2019-12", 100.0, False),
            ("ipc_officiel", "2020-01", 101.0, False),
            ("ipch", "2019-12", 100.0, False),
            ("ipch", "2020-01", 102.0, False),
        ]
    )

    fig = courbe_multi_series(donnees)

    assert len(fig.data) == 2
    assert {trace.name for trace in fig.data} == {"ipc_officiel", "ipch"}


def test_x_y_d_une_trace_correspondent_a_sa_serie():
    donnees = table(
        [
            ("ipc_officiel", "2019-12", 100.0, False),
            ("ipc_officiel", "2020-01", 101.0, False),
            ("ipch", "2019-12", 100.0, False),
        ]
    )

    fig = courbe_multi_series(donnees)

    trace_ipc = next(t for t in fig.data if t.name == "ipc_officiel")
    assert list(trace_ipc.x) == ["2019-12", "2020-01"]
    assert list(trace_ipc.y) == [100.0, 101.0]


def test_segments_interpoles_en_pointille_non_interpoles_en_plein():
    donnees = table(
        [
            ("ipc_officiel", "2019-12", 100.0, False),
            ("ipc_officiel", "2020-01", 101.0, False),
            ("ipc_officiel", "2020-02", 102.0, True),
            ("ipc_officiel", "2020-03", 103.0, True),
        ]
    )

    fig = courbe_multi_series(donnees)

    traces_ipc = [t for t in fig.data if t.legendgroup == "ipc_officiel"]
    dashes = {t.line.dash for t in traces_ipc}
    assert "dot" in dashes
    assert "solid" in dashes


def test_une_seule_entree_de_legende_par_serie_meme_avec_segments():
    donnees = table(
        [
            ("ipc_officiel", "2019-12", 100.0, False),
            ("ipc_officiel", "2020-01", 101.0, True),
        ]
    )

    fig = courbe_multi_series(donnees)

    traces_ipc = [t for t in fig.data if t.legendgroup == "ipc_officiel"]
    assert len(traces_ipc) == 2
    assert sum(1 for t in traces_ipc if t.showlegend is not False) == 1
