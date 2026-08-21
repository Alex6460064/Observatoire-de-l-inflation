"""Observatoire de l'Inflation.

Compare l'IPC officiel de l'INSEE aux quatre autres indices de l'ADR 0002.

La separation des couches est stricte et non negociable :

    collecte/    telecharge, ne transforme rien, ecrit dans data/raw/
    traitement/  nettoie et normalise, aucun appel reseau
    analyse/     calcule, aucun appel reseau, fonctions pures
    viz/         composants Plotly reutilisables
    dashboard.py assemble viz + analyse, aucun appel reseau

Voir docs/METHODOLOGIE.md section 7 et l'ADR 0008.
"""
