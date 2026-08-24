# Spec — Encart pédagogique sur l'écart de poids `CP04` (logement)

## Problem Statement

La comparaison des indices affiche déjà les cinq courbes et les poids par
poste, mais l'écart le plus explicatif entre indices officiels et profil de
ménage — `CP04` logement pèse 15,9 % dans les poids officiels IPCH
(indice 1) contre 26,7 à 35,3 % dans le profil de ménage HBS (indices
2/3/4) — n'est visible nulle part dans l'interface. La cause (exclusion
structurelle des loyers imputés `CP042` du champ IPCH, jusqu'à 172 ‰ en
QU5) est documentée en prose dans `docs/METHODOLOGIE.md` (limite 7,
ADR 0005) mais un visiteur qui compare les indices sur le dashboard ne la
découvre jamais au moment où elle serait la plus parlante.

## Solution

Ajouter, sur la page de comparaison des postes par indice, un encart
pédagogique qui affiche ce chiffre (poids logement par source de poids) et
son explication au moment où le visiteur regarde le poste
`CP04`/`CP041`/`CP042`, avec renvoi vers l'ADR 0005 et la limite 7.

## User Stories

1. En tant que visiteur de la page de comparaison des postes, je veux voir
   le poids du logement selon la source de poids consultée (poids officiels
   IPCH contre profil de ménage), pour comprendre pourquoi les courbes
   divergent autant sur ce poste précis.
2. En tant que visiteur, je veux une explication en une ou deux phrases de
   la raison de cet écart (exclusion des loyers imputés du champ IPCH),
   pour ne pas le lire comme une anomalie ou un biais du projet.
3. En tant que visiteur, je veux que cette explication cite sa source
   (ADR 0005, `prc_hicp_iw`), pour vérifier moi-même l'affirmation si je le
   souhaite.
4. En tant que visiteur curieux d'un autre poste que le logement, je veux
   que ce mécanisme d'encart soit générique (pas câblé en dur sur `CP04`),
   pour qu'un futur écart notable sur un autre poste (ex. `CP12` assurance,
   déjà documenté en limite 4) puisse être affiché de la même façon sans
   reconstruire la fonctionnalité.
5. En tant qu'Alexandre, je veux que les chiffres affichés dans l'encart
   soient recalculés à chaque run du pipeline depuis les données
   versionnées, pour ne jamais avoir un chiffre en dur qui se périme
   silencieusement (cohérent avec ADR 0008).
6. En tant que développeur, je veux une fonction pure dans
   `traitement/poids.py` qui agrège les poids par division COICOP (2
   premiers chiffres du code poste) pour n'importe quelle table de poids en
   entrée, pour la réutiliser aussi bien sur les poids de profil HBS que sur
   les poids officiels IPCH.
7. En tant que testeur, je veux un test qui vérifie que l'agrégation par
   division somme bien à la valeur totale de la table en entrée, pour
   détecter immédiatement une régression de couverture (garde-fou déjà en
   place ailleurs dans le projet, ex. `TOLERANCE_POUR_MILLE`).
8. En tant que visiteur du dashboard sur mobile ou petit écran, je veux que
   l'encart reste lisible sans écraser le graphe principal, pour ne pas
   dégrader l'expérience de lecture du reste de la page.
9. En tant que recruteur qui regarde le dashboard en démo, je veux que ce
   type d'écart soit présenté comme un résultat méthodologique documenté
   plutôt que comme un chiffre choc, pour que le projet garde sa posture
   "outil d'analyse rigoureux, pas militant" (CLAUDE.md).

## Implementation Decisions

- Nouveau processed artifact : `data/processed/poids_ipch_officiels.csv`
  (poste, pm), produit dans `scripts/run_pipeline.py` à partir de
  `collecte.eurostat.fetch_eurostat_ipch_poids_articles` (déjà collecté,
  `data/raw/eurostat_ipch_poids_articles_2020.json`) — jusqu'ici utilisé
  seulement comme clé de répartition interne (ADR 0018), jamais persisté
  comme table de poids affichable.
- Nouvelle fonction pure dans `traitement/poids.py`, ex.
  `agreger_poids_par_division(poids: pd.DataFrame) -> pd.DataFrame`, qui
  prend une table `poste, pm` (ou `modalite, poste, pm`) et retourne
  `division, pm` en sommant sur les 2 premiers chiffres du code COICOP.
- Composant `viz/` : un encart texte + éventuellement un petit graphique
  barres comparant les deux sources de poids sur une division, positionné
  sur la page de comparaison des postes existante (`src/observatoire/pages`
  — confirmer le fichier exact en explorant le dossier en session dédiée).
- Vocabulaire : respecter `CONTEXT.md` — jamais nommer "poids officiels
  IPCH" et "poids de profil" sous une étiquette commune ambiguë comme
  "poids".
- Portée initiale : `CP04` uniquement pour la première version de l'encart
  (l'écart le plus net et déjà documenté) ; la fonction d'agrégation reste
  générique pour une extension future (`CP12` assurance, limite 4) sans
  nouveau spec pour la mécanique, juste pour le contenu.

## Testing Decisions

- `agreger_poids_par_division` : test avec table factice, plusieurs postes
  par division, vérifie la somme et l'arrondi (prior art : tests existants
  sur `traitement/poids.py`).
- Pas de test réseau : la source `prc_hicp_iw` est déjà collectée et cachée
  en `data/raw/`.
- Test de non-régression sur le total : la somme des poids par division doit
  égaler la somme totale de la table d'entrée, à `TOLERANCE_POUR_MILLE`
  près si la table d'entrée est elle-même un vecteur de profil (garde déjà
  en place ailleurs).

## Out of Scope

- L'extension de l'encart à d'autres postes que `CP04` dans cette première
  session (mécanique générique oui, contenu éditorial sur `CP12` etc. non).
- La collecte du panier national INSEE (indice 0) — spec séparé.
- Tout changement de calcul des cinq indices eux-mêmes : cette
  fonctionnalité est purement informative/pédagogique, elle ne modifie
  aucune formule de `docs/METHODOLOGIE.md`.

## Further Notes

Chiffres de référence déjà vérifiés cette session (à revalider si
`poids.csv` ou les poids IPCH sont regénérés) : CP04 = 15,9 % (IPCH
officiel) contre 26,7-35,3 % (profil HBS selon quintile) ; écart porté
quasi entièrement par `CP042` (loyers imputés), absent de l'IPCH.
