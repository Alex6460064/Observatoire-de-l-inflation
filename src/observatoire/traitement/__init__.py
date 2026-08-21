"""Nettoyage et normalisation. Aucun appel reseau.

Entree DataFrame, sortie DataFrame, sans effet de bord. C'est ce qui rend la
couche testable sans toucher aux APIs.

Produit les tables longues de data/processed/ decrites par l'ADR 0008 :

    prix.csv    source, poste, periode, valeur, qualite, interpole
    poids.csv   axe, modalite, poste, pm

La colonne `interpole` est obligatoire et vraie sur tout point calcule
(ADR 0015). La colonne `qualite` prend les trois valeurs de CONTEXT.md.
"""
