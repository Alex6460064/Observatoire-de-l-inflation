"""Rebasage et agregation des indices.

Les deux formules de `docs/METHODOLOGIE.md` section 5.2, et rien d'autre.
L'ADR 0008 reduit volontairement la couche `analyse/` a ces operations : tout
l'arbitrage de sources se fait en amont, dans le pipeline.

Aucun appel reseau, aucun effet de bord.

Les trois `ValueError` de ce module ne sont pas du zele defensif. Chacune
empeche un chiffre faux de s'afficher sans que personne ne le voie, ce que
`CLAUDE.md` interdit explicitement.
"""

import pandas as pd

# Les poids de profil sont exprimes en pour mille et somment a 1000 (ADR 0006,
# qui impose la renormalisation apres tout ajustement au curseur).
TOTAL_POUR_MILLE = 1000.0

# Tolerance sur cette somme. Les poids Eurostat sont publies a l'entier, la
# renormalisation introduit des flottants : 0,5 ‰ absorbe l'arrondi sans
# laisser passer un vecteur reellement mal normalise.
TOLERANCE_POUR_MILLE = 0.5


def rebaser(prix: pd.DataFrame, reference: str) -> pd.DataFrame:
    """Rebase chaque poste sur `reference`, qui vaut alors 100.

    `I_p(t) = 100 * P_p(t) / P_p(t0)` — voir `docs/METHODOLOGIE.md` 5.2.

    Args:
        prix: table longue `poste, periode, valeur`.
        reference: periode servant de base 100, `2019-12` par defaut du
            projet (ADR 0009).

    Returns:
        La meme table, colonne `valeur` rebasee. Les autres colonnes
        (`qualite`, `interpole`) sont conservees telles quelles.

    Raises:
        ValueError: si un poste n'a pas de valeur a la reference, ou si cette
            valeur est nulle. Les deux produiraient un `NaN` ou un `inf`
            silencieux, donc un poste qui sort de l'agregation sans le dire.
    """
    base = prix.loc[prix.periode == reference].set_index("poste").valeur

    manquants = sorted(set(prix.poste) - set(base.index))
    if manquants:
        raise ValueError(
            f"Aucune valeur a la reference {reference} pour : {manquants}. "
            "Un poste sans base 100 ne peut pas etre rebase."
        )

    nuls = sorted(base.index[base == 0])
    if nuls:
        raise ValueError(
            f"Valeur nulle a la reference {reference} pour : {nuls}. "
            "Le rebasage divise par cette valeur."
        )

    out = prix.copy()
    out["valeur"] = 100.0 * out.valeur / out.poste.map(base)
    return out


def indice(prix: pd.DataFrame, poids: pd.Series) -> pd.Series:
    """Agrege des postes rebases en un indice, par les poids de profil.

    Laspeyres a poids fixes : `I(t) = somme_p w_p * I_p(t) / 1000`.
    Les poids ne dependent pas de `t` — c'est la limite 6 de
    `docs/METHODOLOGIE.md`.

    Args:
        prix: table longue `poste, periode, valeur`, deja rebasee.
        poids: parts budgetaires en pour mille, indexees par poste.

    Returns:
        L'indice, indexe par periode et trie.

    Raises:
        ValueError: si les poids ne somment pas a 1000, si un poste pondere
            est absent des prix, ou si une periode ne couvre pas tous les
            postes ponderes.
    """
    total = float(poids.sum())
    if abs(total - TOTAL_POUR_MILLE) > TOLERANCE_POUR_MILLE:
        raise ValueError(
            f"Les poids somment a {total:.1f} et non a 1000 pour mille. "
            "Renormaliser avant d'agreger (ADR 0006)."
        )

    absents = sorted(set(poids.index) - set(prix.poste))
    if absents:
        raise ValueError(
            f"Postes ponderes absents des prix : {absents}. "
            "Les ignorer sous-estimerait l'indice sans le signaler."
        )

    # PD010 suggere `pivot_table`. Refuse volontairement : `pivot_table`
    # agrege les doublons (periode, poste) par une moyenne silencieuse, la
    # seule chose que ce module existe pour empecher. `pivot` leve, et un
    # doublon est un bug de pipeline qui doit se voir.
    table = (
        prix.loc[prix.poste.isin(poids.index)]  # noqa: PD010
        .pivot(index="periode", columns="poste", values="valeur")
        .reindex(columns=poids.index)
    )

    incompletes = sorted(table.index[table.isna().any(axis=1)])
    if incompletes:
        raise ValueError(
            f"Periodes ne couvrant pas tous les postes ponderes : {incompletes}. "
            "Un point agrege sur un panier partiel est indiscernable d'un point "
            "complet une fois trace."
        )

    return table.mul(poids, axis=1).sum(axis=1) / TOTAL_POUR_MILLE
