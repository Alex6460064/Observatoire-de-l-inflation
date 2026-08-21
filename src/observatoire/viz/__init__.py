"""Composants Plotly reutilisables.

Contraintes heritees des decisions, a respecter dans tout graphe :

- cinq courbes simultanees doivent rester lisibles (ADR 0002) ;
- le graphe principal est mensuel, en niveau, base 2019-12 = 100 (ADR 0013) ;
- les segments interpoles sont traces en pointille, pas seulement signales au
  survol (ADR 0015, ADR 0016) ;
- le millesime des poids accompagne tout panier affiche (ADR 0007).
"""
