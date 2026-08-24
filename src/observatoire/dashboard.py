"""Point d'entree Streamlit multipage.

Une seule page pour l'instant, `pages/indices.py` (page 1). Page 2, « panier
INSEE » pedagogique (CONTEXT.md, `docs/SOURCES.md`), non ajoutee : un seul
IDBANK sur 263 est verifie, collecte complete differee a une session dediee
(`docs/METHODOLOGIE.md` section 4.2 ter, TODO explicite dans
`docs/SOURCES.md`) -- pas de page avec 262 postes manquants ou inventes.
"""

import streamlit as st

from observatoire.pages import indices

st.set_page_config(page_title="Observatoire de l'Inflation", layout="wide")

page_indices = st.Page(indices.render, title="Indices", default=True)

st.navigation([page_indices]).run()
