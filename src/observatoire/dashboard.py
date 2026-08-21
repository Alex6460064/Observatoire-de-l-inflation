"""Application Streamlit — assemble `viz/` et `analyse/`.

Ne fait aucun appel reseau : elle lit `data/processed/` et recalcule en direct
ce qui depend des choix de l'utilisateur (ADR 0008).

ETAT : squelette. Le pipeline n'ecrit pas encore `data/processed/`, donc il n'y
a rien a afficher. Cette page dit ou en est le projet plutot que de simuler une
interface sur des donnees inventees.
"""

import streamlit as st

TITRE = "Observatoire de l'Inflation"

st.set_page_config(page_title=TITRE, layout="wide")
st.title(TITRE)

st.info(
    "**Phase de conception methodologique.** Les sources sont validees et la "
    "methodologie est arretee ; le pipeline de collecte reste a ecrire. "
    "Aucune courbe n'est affichee parce qu'aucune donnee n'a encore ete "
    "collectee — afficher un graphe de demonstration sur des valeurs inventees "
    "contredirait la regle d'anti-hallucination du projet."
)

st.subheader("Ce que cette page affichera")
st.markdown(
    """
Cinq indices etiquetes, au pas mensuel, en niveau, base `2019-12 = 100`
(ADR 0002, ADR 0009, ADR 0013) :

| # | indice | prix | poids |
|---|---|---|---|
| 0 | IPC officiel | INSEE | panier moyen national |
| 1 | IPCH | Eurostat | officiels Eurostat |
| 2 | IPCH repondere | Eurostat | profil de menage |
| 3 | IPC repondere | INSEE | profil de menage |
| 4 | Indice Observatoire | sources propres, poste par poste | profil de menage |

Avec, en permanence : le millesime des poids a cote du panier (ADR 0007), un
badge de qualite de source par poste de l'indice 4 (ADR 0004), les segments
interpoles en pointille (ADR 0015), et la date de collecte du dernier run du
pipeline (ADR 0008).
"""
)

st.subheader("Documentation")
st.markdown(
    "- `docs/METHODOLOGIE.md` — formules, hypotheses, et les 17 limites\n"
    "- `docs/SOURCES.md` — sources retenues et ecartees\n"
    "- `docs/adr/` — les 19 decisions, avec leurs alternatives ecartees\n"
    "- `CONTEXT.md` — glossaire contraignant, termes bannis compris"
)
