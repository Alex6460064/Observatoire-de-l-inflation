"""Orchestrateur du pipeline : collecte + traitement -> data/processed/.

Concatene en memoire les tables nettoyees de chaque source connue et ecrit
`prix.csv` en overwrite complet (pas d'append, pas de merge disque — ADR 0008).
Ajouter une source future se resume a ajouter une entree ici.

Usage : uv run python scripts/run_pipeline.py
"""

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from observatoire.collecte.carburants import (
    MILLESIMES_DISPONIBLES as MILLESIMES_CARBURANTS,
)
from observatoire.collecte.carburants import fetch_prix_carburants
from observatoire.collecte.carte_des_loyers import (
    MILLESIMES_DISPONIBLES as MILLESIMES_CARTE_DES_LOYERS,
)
from observatoire.collecte.carte_des_loyers import fetch_carte_des_loyers
from observatoire.collecte.cre import fetch_cre_tarif_base
from observatoire.collecte.dares import (
    chemin_dernier_fichier_salaire_smb,
    lire_salaire_smb,
)
from observatoire.collecte.eurostat import (
    fetch_eurostat_hbs_poids,
    fetch_eurostat_ipch_officiel,
    fetch_eurostat_ipch_poids_articles,
    fetch_eurostat_prix_par_sous_classe,
)
from observatoire.collecte.insee import (
    fetch_insee_ipc_officiel,
    fetch_insee_prix_par_sous_classe,
)
from observatoire.collecte.recensement_logement import fetch_recensement_logement_2022
from observatoire.traitement.carburants import (
    combiner_mix_cp072,
    construire_prix_carburant,
)
from observatoire.traitement.carte_des_loyers import (
    calculer_locatif_prive,
    calculer_moyenne_ponderee,
    construire_points_annuels,
)
from observatoire.traitement.cre import calculer_cout_annuel, etendre_mensuel
from observatoire.traitement.dares import completer_mensuel, nettoyer_salaire_smb
from observatoire.traitement.eurostat import (
    normaliser_eurostat_ipch_officiel,
    normaliser_eurostat_prix_sous_classe,
)
from observatoire.traitement.insee import (
    normaliser_insee_ipc_officiel,
    normaliser_insee_prix_sous_classe,
)
from observatoire.traitement.interpolation import (
    completer_mensuel as completer_mensuel_generique,
)
from observatoire.traitement.observatoire import assembler_prix_indice_observatoire
from observatoire.traitement.poids import (
    assembler_poids_quintiles,
    exclure_postes_du_panier,
    postes_sans_historique_a_la_reference,
)

PRIX_CSV = Path("data/processed/prix.csv")
POIDS_CSV = Path("data/processed/poids.csv")
SALAIRE_CSV = Path("data/processed/salaire_smb.csv")
META_JSON = Path("data/processed/META.json")
CORRESPONDANCE_CSV = Path("data/manual/correspondance_coicop.csv")
PARAMETRES_CSV = Path("data/manual/parametres.csv")
RAW_DIR = Path("data/raw")

COLONNES_PRIX = ["source", "poste", "periode", "valeur", "qualite", "interpole"]
COLONNES_POIDS = ["axe", "modalite", "poste", "pm"]
COLONNES_SALAIRE = ["source", "poste", "periode", "valeur", "qualite", "interpole"]

# Meme reference que observatoire.pages.indices (ADR 0009) : synchronisee a
# la main, un seul lieu de verite n'existe pas encore dans le projet.
REFERENCE = "2019-12"


def postes_avec_poids_non_nul(poids: pd.DataFrame) -> list[str]:
    """Postes a collecter cote prix, INSEE (indice 3) comme Eurostat (indice
    2, ticket 03) : ceux qui pesent reellement quelque chose dans au moins
    un quintile (ticket #12) -- inutile de collecter un poste qui pese zero
    partout.
    """
    return sorted(poids.loc[poids.pm > 0, "poste"].unique())


def collecter_et_normaliser_toutes_sources(poids: pd.DataFrame) -> pd.DataFrame:
    """Appelle collecte + traitement pour chaque source connue.

    INSEE (indice 0, `ipc_officiel`), Eurostat (indice 1, `ipch`), prix
    INSEE par sous-classe COICOP 2018 pour l'indice 3, et prix Eurostat par
    sous-classe COICOP 2018 pour l'indice 2 (`poids` fournit la liste des
    postes a collecter, partagee entre indices 2 et 3 -- ticket 02).
    """
    normalise_insee = normaliser_insee_ipc_officiel(fetch_insee_ipc_officiel())
    normalise_eurostat = normaliser_eurostat_ipch_officiel(
        fetch_eurostat_ipch_officiel()
    )
    normalise_insee_sous_classe = normaliser_insee_prix_sous_classe(
        fetch_insee_prix_par_sous_classe(postes_avec_poids_non_nul(poids))
    )
    normalise_eurostat_sous_classe = normaliser_eurostat_prix_sous_classe(
        fetch_eurostat_prix_par_sous_classe(postes_avec_poids_non_nul(poids))
    )
    return pd.concat(
        [
            normalise_insee,
            normalise_eurostat,
            normalise_insee_sous_classe,
            normalise_eurostat_sous_classe,
        ],
        ignore_index=True,
    )[COLONNES_PRIX]


def assembler_poids() -> pd.DataFrame:
    """Assemble `poids.csv` : indice 3, axe `quintile_revenu` (ADR 0011).

    Transposition des poids HBS vers COICOP 2018 -- voir
    `traitement.poids.assembler_poids_quintiles` (ticket #11).
    """
    correspondance = pd.read_csv(CORRESPONDANCE_CSV)
    poids_hbs = fetch_eurostat_hbs_poids()
    poids_iw = fetch_eurostat_ipch_poids_articles()
    poids = assembler_poids_quintiles(poids_hbs, poids_iw, correspondance)
    return poids[COLONNES_POIDS]


def construire_salaire_smb(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Salaire mensuel de base (SMB), indice 6 hors ADR 0002 (ADR 0022).

    Pas de reseau : lit le dernier fichier Dares archive dans `raw_dir`
    (telechargement manuel, blocage anti-bot Cegedim -- ADR 0022) plutot
    que de le collecter.
    """
    brut = lire_salaire_smb(chemin_dernier_fichier_salaire_smb(raw_dir))
    propre = nettoyer_salaire_smb(brut)
    return completer_mensuel(propre)[COLONNES_SALAIRE]


def lire_parametre(parametres: pd.DataFrame, poste: str, parametre: str) -> str:
    """Lit une valeur de `data/manual/parametres.csv` (ADR 0017, ADR 0023).

    C'est le seul point du pipeline qui lit ce fichier : les constantes
    `PUISSANCE_RETENUE_KVA`/`CONSOMMATION_ANNUELLE_KWH` (`traitement.cre`) et
    `PART_GAZOLE`/`PART_SP95_E10` (`traitement.carburants`) restent des
    valeurs par defaut utilisables hors pipeline (tests, appel direct), mais
    le pipeline reel passe toujours les valeurs lues ici -- revue de code :
    sans cet appel, editer le CSV n'avait aucun effet sur `prix.csv`.

    Args:
        parametres: `pd.read_csv(PARAMETRES_CSV, sep=";")`.
        poste: colonne `poste` du CSV (ex. `"CP045"`).
        parametre: colonne `parametre` du CSV (ex. `"puissance_souscrite"`).

    Returns:
        La colonne `valeur` de la ligne correspondante (chaine, a convertir
        par l'appelant).

    Raises:
        ValueError: aucune ligne ne correspond a `(poste, parametre)`.
    """
    ligne = parametres.loc[
        (parametres.poste == poste) & (parametres.parametre == parametre)
    ]
    if ligne.empty:
        raise ValueError(
            f"Parametre '{parametre}' absent pour le poste '{poste}' dans "
            f"{PARAMETRES_CSV}. Verifier le fichier (ADR 0017)."
        )
    return ligne["valeur"].iloc[0]


def construire_serie_cp041(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Indice Observatoire, groupe `CP041` (loyers reels, ADR 0014, ADR 0023).

    Carte des loyers, fichier appartements, un point par millesime ponder par
    le parc locatif prive (recensement INSEE 2022), mois manquants combles
    par interpolation lineaire (docs/METHODOLOGIE.md 4.2 bis).
    """
    poids_communal = calculer_locatif_prive(fetch_recensement_logement_2022(raw_dir))
    valeurs = {
        millesime: calculer_moyenne_ponderee(
            fetch_carte_des_loyers(millesime, raw_dir), poids_communal
        )
        for millesime in MILLESIMES_CARTE_DES_LOYERS
    }
    points = construire_points_annuels(valeurs)
    return completer_mensuel_generique(points)[COLONNES_PRIX]


def construire_serie_cp045(
    raw_dir: Path = RAW_DIR, derniere_periode: str | None = None
) -> pd.DataFrame:
    """Indice Observatoire, groupe `CP045` (energie logement, ADR 0014, ADR 0023).

    Bareme CRE, tarif reglemente option Base, cout annuel du profil retenu
    (`data/manual/parametres.csv`) etale en escalier sur ses mois de
    validite (docs/METHODOLOGIE.md 4.2 bis, section 6).
    """
    derniere_periode = derniere_periode or datetime.now().strftime("%Y-%m")
    parametres = pd.read_csv(PARAMETRES_CSV, sep=";")
    puissance_kva = int(lire_parametre(parametres, "CP045", "puissance_souscrite"))
    consommation_kwh = float(
        lire_parametre(parametres, "CP045", "consommation_annuelle")
    )

    bareme = fetch_cre_tarif_base(raw_dir)
    cout = calculer_cout_annuel(
        bareme, puissance_kva=puissance_kva, consommation_annuelle_kwh=consommation_kwh
    )
    return etendre_mensuel(cout, derniere_periode)[COLONNES_PRIX]


def construire_serie_cp072(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Indice Observatoire, groupe `CP072` (utilisation du vehicule, ADR 0014,
    ADR 0023).

    prix-carburants.gouv.fr, archives annuelles 2019-2026, dernier prix connu
    propage par station puis moyenne mensuelle nationale, mix gazole/SP95-E10
    fixe (docs/METHODOLOGIE.md 4.2 bis).
    """
    parametres = pd.read_csv(PARAMETRES_CSV, sep=";")
    part_gazole = float(lire_parametre(parametres, "CP072", "part_gazole")) / 100.0
    part_sp95_e10 = float(lire_parametre(parametres, "CP072", "part_sp95_e10")) / 100.0

    evenements = pd.concat(
        [fetch_prix_carburants(annee, raw_dir) for annee in MILLESIMES_CARBURANTS],
        ignore_index=True,
    )
    prix_gazole = construire_prix_carburant(evenements, "gazole")
    prix_sp95_e10 = construire_prix_carburant(evenements, "sp95_e10")
    return combiner_mix_cp072(
        prix_gazole, prix_sp95_e10, part_gazole=part_gazole, part_sp95_e10=part_sp95_e10
    )[COLONNES_PRIX]


def construire_prix_indice_observatoire(
    prix: pd.DataFrame, postes_pondere: list[str], raw_dir: Path = RAW_DIR
) -> pd.DataFrame:
    """Assemble la table de prix de l'indice 4 (`source="observatoire"`).

    Repli IPCH (source Eurostat, meme que l'indice 2) pour toute sous-classe
    non couverte par une source propre ; `CP042` recoit la meme serie que
    `CP041` (ADR 0005). `CP01` reste en repli IPCH pur -- pas de cle `CP011`
    ni `CP012` ici (ADR 0023, METHODOLOGIE 4.2 bis).
    """
    correspondance = pd.read_csv(CORRESPONDANCE_CSV)
    prix_ipch_souscl = prix.loc[
        (prix.source == "eurostat") & (prix.poste.isin(postes_pondere))
    ]

    serie_cp041 = construire_serie_cp041(raw_dir)
    series_propres = {
        "CP041": serie_cp041,
        "CP042": serie_cp041,
        "CP045": construire_serie_cp045(raw_dir),
        "CP072": construire_serie_cp072(raw_dir),
    }

    assemble = assembler_prix_indice_observatoire(
        prix_ipch_souscl, correspondance, series_propres
    )
    return assemble.assign(source="observatoire")[COLONNES_PRIX]


def ecrire_meta(chemin: Path, date_collecte: date) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(
        json.dumps({"date_collecte": date_collecte.strftime("%Y-%m-%d")}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    poids = assembler_poids()
    prix = collecter_et_normaliser_toutes_sources(poids)

    # Un poste pondere sans historique jusqu'a REFERENCE ne peut pas etre
    # rebase (docs/METHODOLOGIE.md 3.3). Panier commun entre indices 2 et 3
    # (ticket 02) : exclusion = union des trous INSEE et Eurostat, poids.csv
    # reste un seul fichier, renormalise une seule fois.
    postes_pondere = postes_avec_poids_non_nul(poids)
    sans_historique_insee = postes_sans_historique_a_la_reference(
        prix.loc[prix.source == "insee"], postes_pondere, REFERENCE
    )
    sans_historique_eurostat = postes_sans_historique_a_la_reference(
        prix.loc[prix.source == "eurostat"], postes_pondere, REFERENCE
    )
    sans_historique = sorted(set(sans_historique_insee) | set(sans_historique_eurostat))
    poids = exclure_postes_du_panier(poids, sans_historique)
    # Recalcule apres exclusion : la liste d'avant contient encore les
    # postes sans historique, que l'indice 4 ne doit pas assembler non plus
    # (revue de code, meme panier commun que les indices 2 et 3).
    postes_pondere = postes_avec_poids_non_nul(poids)

    prix_observatoire = construire_prix_indice_observatoire(prix, postes_pondere)
    prix = pd.concat([prix, prix_observatoire], ignore_index=True)

    salaire_smb = construire_salaire_smb()

    PRIX_CSV.parent.mkdir(parents=True, exist_ok=True)
    prix.to_csv(PRIX_CSV, index=False)
    poids.to_csv(POIDS_CSV, index=False)
    salaire_smb.to_csv(SALAIRE_CSV, index=False)

    ecrire_meta(META_JSON, datetime.now().date())


if __name__ == "__main__":
    main()
