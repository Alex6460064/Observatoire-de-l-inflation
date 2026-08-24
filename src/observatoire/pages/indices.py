"""Page 1 — Indices : assemble `viz/` et `analyse/`.

Ne fait aucun appel reseau : elle lit `data/processed/` et recalcule en direct
ce qui depend des choix de l'utilisateur (ADR 0008).

Cinq courbes : `ipc_officiel` (indice 0) et `ipch` (indice 1), base
`2019-12 = 100` codee en dur (ADR 0009) ; `ipch_repondere` (indice 2),
`ipc_repondere` (indice 3) et `indice_observatoire` (indice 4, `CP01` en
repli IPCH temporaire -- ADR 0023), recalculees en direct a chaque
changement de quintile via un selecteur Streamlit partage -- meme panier
pour les trois (panier commun, docs/METHODOLOGIE.md section 3.3), seule la
repondering est dynamique (docs/METHODOLOGIE.md section 7), `rebaser`/
`indice` de `analyse/indice.py` sont reutilises tels quels ; `salaire_smb`,
salaire nominal Dares superpose aux cinq indices de prix, hors du cadre des
cinq indices de l'ADR 0002 -- pas de prix, pas de poids HBS (ADR 0022).
"""

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from observatoire.analyse.indice import indice, rebaser
from observatoire.viz.courbe import courbe_multi_series

REFERENCE = "2019-12"

PRIX_CSV = Path("data/processed/prix.csv")
POIDS_CSV = Path("data/processed/poids.csv")
SALAIRE_CSV = Path("data/processed/salaire_smb.csv")
META_JSON = Path("data/processed/META.json")

# Seul axe de profil expose en v1 (ADR 0011) -- docs/METHODOLOGIE.md section 7.
AXE_QUINTILE_REVENU = "quintile_revenu"
QUINTILES = ("QU1", "QU2", "QU3", "QU4", "QU5")
MILLESIME_POIDS = "enquete Budget de famille 2017"


@dataclass(frozen=True)
class Indice:
    label: str
    source: str
    poste: str


INDICES = [
    Indice(label="ipc_officiel", source="insee", poste="00"),
    Indice(label="ipch", source="eurostat", poste="TOTAL"),
]

# Hors du cadre des cinq indices de l'ADR 0002 -- pas de prix, pas de poids
# HBS, salaire nominal seul (ADR 0022). Reutilise `rebaser_indice` tel quel :
# meme schema de colonnes que prix.csv.
SALAIRE_SMB = Indice(label="salaire_smb", source="dares", poste="ENS")


def charger_prix() -> pd.DataFrame:
    return pd.read_csv(PRIX_CSV, dtype={"poste": str, "periode": str})


def charger_poids() -> pd.DataFrame:
    return pd.read_csv(POIDS_CSV, dtype={"poste": str, "modalite": str})


def charger_salaire_smb() -> pd.DataFrame:
    return pd.read_csv(SALAIRE_CSV, dtype={"poste": str, "periode": str})


def charger_meta() -> dict:
    return json.loads(META_JSON.read_text(encoding="utf-8"))


def periode_moins_douze_mois(periode: str) -> str:
    """`AAAA-MM` -> meme mois, annee precedente."""
    annee, mois = periode.split("-")
    return f"{int(annee) - 1}-{mois}"


def rebaser_indice(prix: pd.DataFrame, indice: Indice) -> pd.DataFrame:
    brut = prix.loc[(prix.source == indice.source) & (prix.poste == indice.poste)]
    return rebaser(brut, REFERENCE).sort_values("periode").assign(serie=indice.label)


def _calculer_indice_repondere(
    prix: pd.DataFrame,
    poids: pd.DataFrame,
    modalite: str,
    source: str,
    serie: str,
) -> pd.DataFrame:
    """Recalcule en direct un indice reponderee (2 ou 3) pour une modalite de
    quintile. Commun aux deux : meme panier de poids -- panier commun entre
    indices 2 et 3, decide au ticket 02 (docs/METHODOLOGIE.md 3.3) -- seule
    la source de prix (`insee` ou `eurostat`) change.

    La courbe ne demarre qu'a la premiere periode ou tous les postes du
    panier ont une valeur, et s'arrete a la derniere periode ou c'est encore
    le cas (limite 18, meme principe que la limite 17) : `indice` refuse
    tout point agrege sur un panier partiel plutot que de l'afficher
    silencieusement. La borne de fin importe pour l'indice 4 : `CP041`
    (Carte des loyers, publication annuelle) s'arrete plus tot que `CP045`/
    `CP072` (bareme/quotidien, jusqu'a aujourd'hui) -- sans elle, `indice`
    leverait au premier mois ou seul `CP041` manque (ADR 0023).

    `interpole` vaut `True` sur une periode des qu'au moins un poste pondere
    y est interpole (ADR 0015) -- pour l'indice 4, la plupart des mois de
    `CP041` le sont (METHODOLOGIE section 5.3).
    """
    vecteur = (
        poids.loc[
            (poids.axe == AXE_QUINTILE_REVENU)
            & (poids.modalite == modalite)
            & (poids.pm > 0)
        ]
        .set_index("poste")
        .pm
    )
    brut = prix.loc[(prix.source == source) & (prix.poste.isin(vecteur.index))]
    debut = brut.groupby("poste").periode.min().max()
    fin = brut.groupby("poste").periode.max().min()
    brut = brut.loc[(brut.periode >= debut) & (brut.periode <= fin)]

    rebase = rebaser(brut, REFERENCE)
    valeurs = indice(rebase, vecteur)
    interpole_par_periode = (
        rebase.groupby("periode")["interpole"].any().reindex(valeurs.index)
    )

    return pd.DataFrame(
        {
            "serie": serie,
            "periode": valeurs.index,
            "valeur": valeurs.to_numpy(),
            "interpole": interpole_par_periode.to_numpy(),
        }
    )


def calculer_indice_2(
    prix: pd.DataFrame, poids: pd.DataFrame, modalite: str
) -> pd.DataFrame:
    """Indice 2 (IPCH repondere) : prix Eurostat par sous-classe COICOP 2018."""
    return _calculer_indice_repondere(
        prix, poids, modalite, source="eurostat", serie="ipch_repondere"
    )


def calculer_indice_3(
    prix: pd.DataFrame, poids: pd.DataFrame, modalite: str
) -> pd.DataFrame:
    """Indice 3 (IPC repondere) : prix INSEE par sous-classe COICOP 2018."""
    return _calculer_indice_repondere(
        prix, poids, modalite, source="insee", serie="ipc_repondere"
    )


def calculer_indice_4(
    prix: pd.DataFrame, poids: pd.DataFrame, modalite: str
) -> pd.DataFrame:
    """Indice 4 (indice Observatoire) : prix assembles dans le pipeline,
    source `observatoire` (ADR 0014, ADR 0023, docs/METHODOLOGIE.md 4.2 bis).

    `CP01` reste en repli IPCH temporaire (ADR 0023) : la courbe couvre
    11 a 28 % du panier selon le quintile, pas les 24-43 % vises a terme.
    Meme panier que les indices 2 et 3 (poids identiques) ; la courbe
    demarre a la premiere periode ou `CP041`/`CP045`/`CP072` sont tous les
    trois disponibles, en pratique `CP072` (2019, ADR 0014).
    """
    return _calculer_indice_repondere(
        prix, poids, modalite, source="observatoire", serie="indice_observatoire"
    )


def render() -> None:
    st.title("Observatoire de l'Inflation")

    prix = charger_prix()
    poids = charger_poids()
    salaire_smb = charger_salaire_smb()
    meta = charger_meta()

    col_selecteur, _ = st.columns([1, 3])
    with col_selecteur:
        modalite = st.selectbox(
            "Quintile de niveau de vie (indice repondere)", QUINTILES, index=2
        )
        st.caption(f"Poids de profil : {MILLESIME_POIDS}.")

    rebases = [rebaser_indice(prix, indice) for indice in INDICES]
    rebases.append(rebaser_indice(salaire_smb, SALAIRE_SMB))
    rebases.append(calculer_indice_2(prix, poids, modalite))
    rebases.append(calculer_indice_3(prix, poids, modalite))
    rebases.append(calculer_indice_4(prix, poids, modalite))

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
        "- `docs/METHODOLOGIE.md` — formules, hypotheses, et les limites\n"
        "- `docs/SOURCES.md` — sources retenues et ecartees\n"
        "- `docs/adr/` — les 24 decisions, avec leurs alternatives ecartees\n"
        "- `CONTEXT.md` — glossaire contraignant, termes bannis compris"
    )
