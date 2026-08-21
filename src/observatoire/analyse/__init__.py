"""Calcul des indices. Aucun appel reseau, fonctions pures.

L'ADR 0008 reduit volontairement cette couche a une seule operation dynamique :
la reponderation d'un vecteur de prix par un vecteur de poids. Tout le reste,
y compris l'assemblage de l'indice Observatoire, se fait dans le pipeline.
"""

from observatoire.analyse.indice import indice, rebaser

__all__ = ["indice", "rebaser"]
