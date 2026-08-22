"""Application Streamlit — assemble `viz/` et `analyse/`.

Ne fait aucun appel reseau : elle lit `data/processed/` et recalcule en direct
ce qui depend des choix de l'utilisateur (ADR 0008).

Aujourd'hui : deux courbes, `ipc_officiel` (indice 0) et `ipch` (indice 1) de
l'ADR 0002. Base `2019-12 = 100` codee en dur, sans selecteur d'interface
(ADR 0009).
"""

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from observatoire.analyse.indice import rebaser
from observatoire.viz.courbe import courbe_multi_series

TITRE = "Observatoire de l'Inflation"
REFERENCE = "2019-12"

PRIX_CSV = Path("data/processed/prix.csv")
META_JSON = Path("data/processed/META.json")


@dataclass(frozen=True)
class Indice:
    label: str
    source: str
    poste: str


INDICES = [
    Indice(label="ipc_officiel", source="insee", poste="00"),
    Indice(label="ipch", source="eurostat", poste="TOTAL"),
]


def charger_prix() -> pd.DataFrame:
    return pd.read_csv(PRIX_CSV, dtype={"poste": str, "periode": str})


def charger_meta() -> dict:
    return json.loads(META_JSON.read_text(encoding="utf-8"))


def periode_moins_douze_mois(periode: str) -> str:
    """`AAAA-MM` -> meme mois, annee precedente."""
    annee, mois = periode.split("-")
    return f"{int(annee) - 1}-{mois}"


def rebaser_indice(prix: pd.DataFrame, indice: Indice) -> pd.DataFrame:
    brut = prix.loc[(prix.source == indice.source) & (prix.poste == indice.poste)]
    return rebaser(brut, REFERENCE).sort_values("periode").assign(serie=indice.label)


def main() -> None:
    st.set_page_config(page_title=TITRE, layout="wide")
    st.title(TITRE)

    prix = charger_prix()
    meta = charger_meta()

    rebases = [rebaser_indice(prix, indice) for indice in INDICES]

    col_graphe, col_chiffres = st.columns([3, 1])

    with col_graphe:
        table_viz = pd.concat(rebases, ignore_index=True)[
            ["serie", "periode", "valeur", "interpole"]
        ]
        st.plotly_chart(courbe_multi_series(table_viz), use_container_width=True)

    with col_chiffres:
        for rebase in rebases:
            label = rebase["serie"].iloc[0]
            derniere_periode = rebase["periode"].iloc[-1]
            valeur_actuelle = rebase.loc[
                rebase.periode == derniere_periode, "valeur"
            ].item()
            evolution_depuis_reference = valeur_actuelle / 100.0 - 1

            periode_precedente = periode_moins_douze_mois(derniere_periode)
            valeurs_precedentes = rebase.loc[
                rebase.periode == periode_precedente, "valeur"
            ]

            st.markdown(f"**{label}**")
            st.metric(
                f"Evolution depuis {REFERENCE}",
                f"{evolution_depuis_reference:+.1%}",
            )
            if valeurs_precedentes.empty:
                st.metric("Glissement annuel", "n/a")
                st.caption(f"Periode {periode_precedente} absente des donnees.")
            else:
                glissement_annuel = valeur_actuelle / valeurs_precedentes.item() - 1
                st.metric("Glissement annuel", f"{glissement_annuel:+.1%}")

        st.caption(f"Date de collecte : {meta['date_collecte']}")

    st.subheader("Documentation")
    st.markdown(
        "- `docs/METHODOLOGIE.md` — formules, hypotheses, et les 17 limites\n"
        "- `docs/SOURCES.md` — sources retenues et ecartees\n"
        "- `docs/adr/` — les 19 decisions, avec leurs alternatives ecartees\n"
        "- `CONTEXT.md` — glossaire contraignant, termes bannis compris"
    )


main()
