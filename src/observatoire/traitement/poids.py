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

# Seul axe de profil expose en v1 (ADR 0011) -- docs/METHODOLOGIE.md section 7.
AXE_QUINTILE_REVENU = "quintile_revenu"

# Meme convention que TOTAL_POUR_MILLE dans analyse/indice.py : les poids de
# profil somment a 1000 pour mille apres renormalisation (docs/METHODOLOGIE.md
# 3.3).
TOTAL_POUR_MILLE = 1000.0

QUINTILES = ("QU1", "QU2", "QU3", "QU4", "QU5")


def transposer_poids_hbs(
    poids_hbs: pd.Series,
    poids_iw: pd.Series,
    correspondance: pd.DataFrame,
) -> pd.Series:
    """Transpose un vecteur de poids de groupe HBS vers COICOP 2018.

    Prorata direct sur les poids d'articles IPCH -- docs/METHODOLOGIE.md 3.3 :
    `w_c = w_g * iw_c / somme(iw_c' issues de g)`. Une sous-classe alimentee
    par plusieurs groupes source repartit son poids IPCH a parts egales entre
    eux avant le calcul du ratio (seule approximation de la methode, avec son
    symetrique ci-dessous). Un groupe dont aucune sous-classe cible n'a de
    poids IPCH (denominateur nul, type `CP042` -- deux cibles, ni l'une ni
    l'autre couverte par l'IPCH) transmet son poids intact, reparti a parts
    egales entre ses sous-classes cibles.

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
            cible), ou masse transposee d'un groupe qui s'ecarte de son poids
            d'origine au-dela de `TOLERANCE_POUR_MILLE` (poids IPCH invalide,
            ex. `NaN`).
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
            # docs/METHODOLOGIE.md 3.3, cas symetrique du multi-source :
            # aucune sous-classe cible n'a de poids IPCH, le poids du groupe
            # traverse intact, reparti a parts egales entre elles.
            parts = {c: w_g / len(enfants) for c in enfants}
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


def assembler_poids_quintiles(
    poids_hbs_long: pd.DataFrame,
    poids_iw_long: pd.DataFrame,
    correspondance: pd.DataFrame,
) -> pd.DataFrame:
    """Empile `transposer_poids_hbs` sur les cinq modalites de quintile.

    C'est l'assemblage reel de `data/processed/poids.csv` (ticket #11,
    docs/METHODOLOGIE.md section 7) : un appel a `transposer_poids_hbs` par
    modalite `QU1`..`QU5`, empiles en table longue. Chaque vecteur transpose
    est renormalise pour sommer exactement a 1000 pour mille -- les poids
    HBS bruts par quintile ne somment jamais exactement a 1000 (arrondi de
    publication de 47 valeurs entieres independantes), ce que
    `analyse.indice` refuserait sinon (docs/METHODOLOGIE.md 3.3).

    Args:
        poids_hbs_long: table `modalite, poste, valeur` (sortie de
            `collecte.eurostat.fetch_eurostat_hbs_poids`).
        poids_iw_long: table `poste, valeur` (sortie de
            `collecte.eurostat.fetch_eurostat_ipch_poids_articles`).
        correspondance: table `coicop_2018, coicop_1999`
            (data/manual/correspondance_coicop.csv).

    Returns:
        Table longue `axe, modalite, poste, pm`, `axe` valant toujours
        `quintile_revenu` (ADR 0011, seul axe expose en v1).

    Raises:
        ValueError: une modalite de `QU1`..`QU5` est absente de
            `poids_hbs_long`, ou toute erreur de `transposer_poids_hbs`
            propagee pour la modalite en cause.
    """
    modalites = set(poids_hbs_long.modalite)
    manquantes = sorted(set(QUINTILES) - modalites)
    if manquantes:
        raise ValueError(
            f"Modalites de quintile absentes de la collecte HBS : "
            f"{manquantes}. Un poids.csv incomplet ne peut pas etre ecrit."
        )

    poids_iw = poids_iw_long.set_index("poste").valeur

    lignes = []
    for modalite in QUINTILES:
        vecteur = (
            poids_hbs_long.loc[poids_hbs_long.modalite == modalite]
            .set_index("poste")
            .valeur
        )
        transpose = transposer_poids_hbs(vecteur, poids_iw, correspondance)
        transpose = transpose * (TOTAL_POUR_MILLE / transpose.sum())
        for poste, pm in transpose.items():
            lignes.append(
                {
                    "axe": AXE_QUINTILE_REVENU,
                    "modalite": modalite,
                    "poste": poste,
                    "pm": pm,
                }
            )

    return (
        pd.DataFrame(lignes, columns=["axe", "modalite", "poste", "pm"])
        .sort_values(["modalite", "poste"])
        .reset_index(drop=True)
    )
