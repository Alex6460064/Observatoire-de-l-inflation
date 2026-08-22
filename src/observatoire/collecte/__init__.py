"""Telechargement des sources. Ne transforme rien.

Contrat de la couche :

- toute fonction publique cite sa source exacte dans son docstring, et cette
  source figure dans docs/SOURCES.md ;
- le brut telecharge est ecrit dans data/raw/ AVANT toute transformation, pour
  garder une trace rejouable ;
- les erreurs reseau sont traitees explicitement (timeout, code != 200, format
  inattendu) : aucune exception reseau brute ne remonte au dashboard ;
- aucun calcul. Pas de moyenne, pas de rebasage, pas d'indice.
"""

from observatoire.collecte.eurostat import fetch_eurostat_ipch_officiel
from observatoire.collecte.insee import fetch_insee_ipc_officiel

__all__ = ["fetch_eurostat_ipch_officiel", "fetch_insee_ipc_officiel"]
