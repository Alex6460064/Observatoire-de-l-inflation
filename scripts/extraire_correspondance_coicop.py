"""Script one-off : construit data/manual/correspondance_coicop.csv.

Source : table de correspondance officielle COICOP 2018 <-> COICOP 1999,
produite par l'UNSD en partenariat avec Eurostat (docs/SOURCES.md, verifiee
le 21/08/2026) :
<https://unstats.un.org/unsd/classifications/Econ/Download/COICOP2018_COICOP1999_correspondence_table_final.xlsx>

Feuille utile : "Correspondence 2018-1999", colonnes "COICOP 2018 Code" et
"COICOP 1999 Code". Seules les lignes au niveau sous-classe COICOP 2018 (4
segments, ex. "01.1.1.1") sont retenues -- c'est le niveau des poids
d'articles IPCH (`prc_hicp_iw`) que `traitement.poids.transposer_poids_hbs`
utilise comme cle de repartition (docs/METHODOLOGIE.md 3.3).

Le code COICOP 1999 associe est publie a 3 segments (niveau classe, ex.
"04.2.1"). Il est tronque a ses deux premiers segments pour retrouver le
niveau groupe a trois chiffres utilise par les poids HBS (`hbs_str_t223`,
ADR 0018, docs/METHODOLOGIE.md 3.2) -- ex. "04.2.1" -> groupe "04.2". C'est
une decision mecanique de granularite (aligner deux nomenclatures deja
validees), pas une formule nouvelle -- mais elle n'est ecrite nulle part
ailleurs : `# TODO: a confirmer avec Alexandre` si des groupes HBS attendus
manquent une fois `poids.csv` assemble (ticket #11).

Les deux codes sont reecrits sans point vers la convention du projet (celle
deja renvoyee telle quelle par les API Eurostat/INSEE) : "01.1.1.1" ->
"CP01111", "04.2.1" -> tronque "04.2" -> "CP042".

Usage : uv run python scripts/extraire_correspondance_coicop.py
"""

from pathlib import Path

import openpyxl
import pandas as pd
import requests

URL_UNSD = (
    "https://unstats.un.org/unsd/classifications/Econ/Download/"
    "COICOP2018_COICOP1999_correspondence_table_final.xlsx"
)
FEUILLE = "Correspondence 2018-1999"

RAW_XLSX = Path("data/raw/coicop2018_coicop1999_correspondence.xlsx")
CSV_SORTIE = Path("data/manual/correspondance_coicop.csv")

TIMEOUT_SECONDES = 30

# Niveau sous-classe COICOP 2018 : 4 segments separes par un point.
SEGMENTS_SOUS_CLASSE = 4
# Niveau groupe COICOP 1999 (HBS) : les deux premiers segments seulement.
SEGMENTS_GROUPE_1999 = 2


def _telecharger_xlsx(chemin: Path) -> None:
    reponse = requests.get(URL_UNSD, timeout=TIMEOUT_SECONDES)
    if reponse.status_code != 200:
        raise ValueError(
            f"UNSD a repondu {reponse.status_code} pour {URL_UNSD} : "
            f"{reponse.text[:500]}"
        )
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_bytes(reponse.content)


def _code_sans_point(code_pointe: str, n_segments: int | None = None) -> str:
    """Convertit "01.1.1.1" en "CP01111" (ou tronque a `n_segments` d'abord)."""
    segments = code_pointe.split(".")
    if n_segments is not None:
        segments = segments[:n_segments]
    return "CP" + "".join(segments)


def extraire_correspondance(chemin_xlsx: Path) -> pd.DataFrame:
    """Lit la feuille UNSD et renvoie la table `coicop_2018, coicop_1999`.

    Ne garde que les lignes ou COICOP 2018 est au niveau sous-classe (4
    segments) et ou un code COICOP 1999 existe reellement (pas de placeholder
    "-").
    """
    classeur = openpyxl.load_workbook(chemin_xlsx, read_only=True, data_only=True)
    feuille = classeur[FEUILLE]
    lignes_brutes = list(feuille.iter_rows(values_only=True))[1:]  # sans l'en-tete

    lignes = []
    for code_2018, _titre_2018, code_1999, _titre_1999, _note in lignes_brutes:
        if not code_2018 or not code_1999:
            continue
        code_1999 = str(code_1999).strip()
        if code_1999 in ("", "-"):
            continue
        if str(code_2018).count(".") + 1 != SEGMENTS_SOUS_CLASSE:
            continue

        lignes.append(
            {
                "coicop_2018": _code_sans_point(str(code_2018)),
                "coicop_1999": _code_sans_point(code_1999, SEGMENTS_GROUPE_1999),
            }
        )

    return (
        pd.DataFrame(lignes)
        .sort_values(["coicop_1999", "coicop_2018"])
        .reset_index(drop=True)
    )


def main() -> None:
    if not RAW_XLSX.exists():
        _telecharger_xlsx(RAW_XLSX)

    correspondance = extraire_correspondance(RAW_XLSX)

    CSV_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    correspondance.to_csv(CSV_SORTIE, index=False)

    print(f"{len(correspondance)} lignes ecrites dans {CSV_SORTIE}")
    print(f"{correspondance.coicop_1999.nunique()} groupes COICOP 1999 distincts")
    print(f"{correspondance.coicop_2018.nunique()} sous-classes COICOP 2018 distinctes")


if __name__ == "__main__":
    main()
