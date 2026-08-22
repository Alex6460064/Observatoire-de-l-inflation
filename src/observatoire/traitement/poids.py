"""Transposition des poids HBS (ECOICOP v1) vers COICOP 2018 (ADR 0018).

Formule et cas particuliers : docs/METHODOLOGIE.md section 3.3. C'est le seam
central de l'indice 3 (et futur indice 2) : `analyse/indice.py` consomme le
resultat sans savoir qu'il vient d'une transposition.

Aucun appel reseau, aucun effet de bord.
"""

import pandas as pd

# Meme esprit que TOLERANCE_POUR_MILLE dans analyse/indice.py : absorbe
# l'arrondi flottant sans laisser passer une masse reellement incoherente
# (poids IPCH manquant ou invalide pour une sous-classe du groupe).
TOLERANCE_POUR_MILLE = 0.5


def transposer_poids_hbs(
    poids_hbs: pd.Series,
    poids_iw: pd.Series,
    correspondance: pd.DataFrame,
) -> pd.Series:
    """Transpose un vecteur de poids de groupe HBS vers COICOP 2018.

    Prorata direct sur les poids d'articles IPCH -- docs/METHODOLOGIE.md 3.3 :
    `w_c = w_g * iw_c / somme(iw_c' issues de g)`. Une sous-classe alimentee
    par plusieurs groupes source repartit son poids IPCH a parts egales entre
    eux avant le calcul du ratio (seule approximation de la methode). Un
    groupe dont l'unique sous-classe cible n'a pas de poids IPCH (type
    `CP042`) lui transmet son poids intact.

    Args:
        poids_hbs: poids de groupe HBS ECOICOP v1, en pour mille, une seule
            modalite de quintile (index = code groupe, ex. "CP041").
        poids_iw: poids d'articles IPCH ECOICOP v2, niveau sous-classe, en
            pour mille (index = code sous-classe COICOP 2018, ex. "CP04111").
            Une sous-classe absente de l'index vaut 0 (aucun poids IPCH
            atteignable) ; une sous-classe presente mais `NaN` est une
            donnee invalide, pas un zero.
        correspondance: table `coicop_2018, coicop_1999`, une ligne par
            couple de codes (data/manual/correspondance_coicop.csv).

    Returns:
        Poids par sous-classe COICOP 2018, en pour mille, index trie.

    Raises:
        ValueError: groupe absent de la correspondance (aucune sous-classe
            cible), plusieurs sous-classes cibles sans aucun poids IPCH
            atteignable (repartition ambigue, non documentee), ou masse
            transposee d'un groupe qui s'ecarte de son poids d'origine au-dela
            de `TOLERANCE_POUR_MILLE` (poids IPCH invalide, ex. `NaN`).
    """
    resultat: dict[str, float] = {}

    for groupe, w_g in poids_hbs.items():
        enfants = sorted(
            set(correspondance.loc[correspondance.coicop_1999 == groupe, "coicop_2018"])
        )
        if not enfants:
            raise ValueError(
                f"Groupe {groupe!r} absent de la table de correspondance : "
                "aucune sous-classe COICOP 2018 cible."
            )

        n_sources = {
            c: correspondance.loc[
                correspondance.coicop_2018 == c, "coicop_1999"
            ].nunique()
            for c in enfants
        }
        iw_effectifs = {c: poids_iw.get(c, 0.0) / n_sources[c] for c in enfants}
        denominateur = sum(iw_effectifs.values())

        if denominateur == 0:
            if len(enfants) != 1:
                raise ValueError(
                    f"Groupe {groupe!r} : aucune de ses {len(enfants)} "
                    "sous-classes cibles n'a de poids IPCH -- repartition "
                    "ambigue, cle de repartition non documentee pour ce cas "
                    "(docs/METHODOLOGIE.md 3.3 ne couvre que le cas bijectif)."
                )
            parts = {enfants[0]: w_g}
        else:
            parts = {c: w_g * iw_c / denominateur for c, iw_c in iw_effectifs.items()}

        total = sum(parts.values())
        if pd.isna(total) or abs(total - w_g) > TOLERANCE_POUR_MILLE:
            raise ValueError(
                f"Groupe {groupe!r} : la somme des parts transposees "
                f"({total}) s'ecarte du poids d'origine ({w_g}) au-dela de "
                f"{TOLERANCE_POUR_MILLE} pour mille. Poids IPCH manquant ou "
                "invalide pour une de ses sous-classes."
            )

        for c, part in parts.items():
            resultat[c] = resultat.get(c, 0.0) + part

    return pd.Series(resultat, name="pm").sort_index()
