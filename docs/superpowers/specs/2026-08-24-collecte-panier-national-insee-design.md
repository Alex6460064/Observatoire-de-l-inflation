# Spec — Collecte du panier national INSEE (poids indice 0, 263 postes)

## Problem Statement

`docs/SOURCES.md` documente un unique IDBANK vérifié pour le panier national
INSEE (263 postes/groupes, poids sur 10 000, revu chaque année) — la
collecte complète n'a jamais été faite (`# TODO: collecte complète non
faite`). Conséquence directe vécue cette session : impossible de répondre à
une demande simple et légitime ("donne-moi le tableau des poids de l'indice
IPC officiel") avec de vraies données ; seul un indice voisin (IPCH
Eurostat, indice 1) a pu servir de substitut, ce qui n'est pas la même
chose (CONTEXT.md distingue explicitement les deux). La page "panier INSEE"
pédagogique déjà nommée dans `CONTEXT.md` ("poids national INSEE... affiché
uniquement à des fins pédagogiques") ne peut pas exister tant que cette
donnée n'est pas collectée.

## Solution

Compléter la collecte des 263 poids nationaux INSEE (indice 0), les
normaliser, les persister en `data/processed/`, et construire la page
pédagogique "panier INSEE" prévue par `CONTEXT.md`, strictement séparée des
poids de profil utilisés dans les calculs des cinq indices.

## User Stories

1. En tant que visiteur curieux, je veux voir le vrai panier national INSEE
   (poids par poste/groupe, base 10 000), pour comprendre ce que "l'IPC
   officiel" pèse réellement, indépendamment du profil de ménage.
2. En tant que visiteur, je veux que cette page soit clairement étiquetée
   comme pédagogique et non mêlée aux poids de profil utilisés par les
   indices 2/3/4, pour ne jamais confondre les deux notions de "panier"
   (CONTEXT.md l'interdit explicitement).
3. En tant qu'Alexandre, je veux que la collecte respecte la limite
   documentée de 30 appels/minute/IP de l'API INSEE, pour ne pas se faire
   bannir ou dégrader le service en pleine collecte de 263 séries.
4. En tant qu'Alexandre, je veux savoir avant de lancer 263 appels un par un
   s'il existe un catalogue ou une recherche en masse côté INSEE, pour
   éviter un travail inutilement long si un raccourci existe (question
   ouverte explicitement laissée par `docs/SOURCES.md`).
5. En tant que développeur, je veux que chaque appel réussi sauvegarde son
   brut dans `data/raw/` avant toute transformation, pour garder une trace
   reproductible (règle collecte du projet, CLAUDE.md).
6. En tant que développeur, je veux que la collecte gère explicitement les
   erreurs réseau et les codes HTTP inattendus sans laisser une exception
   brute remonter, pour ne pas casser une collecte de 263 appels sur un seul
   échec transitoire.
7. En tant que testeur, je veux que la fonction de normalisation
   (SDMX/XML -> `poste, pm`) soit testée avec une réponse mockée, sans
   dépendre du réseau, pour suivre la convention déjà en place sur
   `collecte/insee.py` et `collecte/eurostat.py`.
8. En tant qu'Alexandre, je veux que `docs/SOURCES.md` soit mis à jour avec
   le résultat réel de la collecte complète (nombre de postes trouvés,
   éventuels manquants, licence confirmée), pour que la documentation
   reflète l'état réel des données et non plus un TODO.
9. En tant que visiteur, je veux voir le millésime de ce panier national
   (revu chaque année par l'INSEE) affiché à côté des poids, comme le
   millésime 2017 est déjà affiché pour les poids de profil, pour ne jamais
   lire un poids sans savoir de quelle année il vient.
10. En tant que recruteur regardant le dépôt, je veux que cette page
    pédagogique illustre la rigueur du projet (distinction panier national
    vs panier de profil) plutôt que de créer une nouvelle source de
    confusion, pour que l'ajout serve l'objectif de démonstration du
    projet.
11. En tant que mainteneur futur, je veux que le module de collecte soit
    réutilisable pour les collectes annuelles suivantes (le panier national
    est revu chaque année), pour ne pas devoir réécrire le mécanisme dans un
    an.

## Implementation Decisions

- Étape préalable, à faire avant tout code de collecte en masse : identifier
  comment obtenir les 263 IDBANK sans deviner — chercher un
  catalogue/nomenclature INSEE (ex. une fiche liste, ou l'endpoint de
  structure du dataflow `IPC-2025` avec la dimension `MENAGES_IPC`/poste) ;
  documenter le résultat dans `docs/SOURCES.md` avant de lancer les appels.
- Collecte : nouvelle fonction dans `collecte/insee.py` (ou nouveau module
  `collecte/insee_panier_national.py` si la logique diverge trop de
  l'existant), un appel par IDBANK sur `SERIES_BDM/<IDBANK>` (endpoint déjà
  validé), espacement explicite pour respecter 30 appels/minute/IP — pas de
  parallélisation agressive.
- Traitement : fonction pure de normalisation SDMX -> table
  `poste, pm, millesime`, unité `P10000` confirmée par le test déjà fait sur
  l'IDBANK `011818239`.
- Persistance : nouvel artefact `data/processed/poids_national_insee.csv`,
  distinct de `poids.csv` (poids de profil) — jamais fusionné dans le même
  fichier ni sous la même colonne `pm` sans distinction de source,
  conformément à `CONTEXT.md`.
- Dashboard : nouvelle page pédagogique (`src/observatoire/pages`), lecture
  seule, aucun calcul d'indice ne doit lire ce fichier (ADR 0008 : le
  dashboard ne fait aucun appel réseau, et cette donnée n'entre dans aucun
  des cinq indices par construction, cf. CONTEXT.md "Poids national INSEE").
- Documentation : `docs/SOURCES.md` (résultat de la collecte complète,
  remplace le TODO), `docs/METHODOLOGIE.md` si une section dédiée est jugée
  nécessaire, `CONTEXT.md` reste la référence de vocabulaire déjà correcte à
  ce sujet.

## Testing Decisions

- Fonction de normalisation SDMX -> `poste, pm` : test avec une réponse
  XML/SDMX factice couvrant quelques postes, prior art le pattern déjà
  utilisé pour l'IPC officiel dans `collecte/insee.py`.
- Pas de test réseau réel dans la suite (`uv run pytest`) — la collecte
  complète reste un script one-off (`scripts/`), testée sur des cas mockés
  uniquement.
- Test de la persistance : vérifier que le fichier
  `data/processed/poids_national_insee.csv` produit somme à 10 000 (±
  tolérance à définir, cohérent avec `TOLERANCE_POUR_MILLE` existant côté
  profil).

## Out of Scope

- Toute utilisation de ce panier national dans le calcul des cinq indices —
  interdit par construction (CONTEXT.md).
- La collecte annuelle automatisée future (cron, etc.) — hors scope, projet
  sans infrastructure de ce type à ce stade (CLAUDE.md : pas de framework
  web, pas d'infra lourde sans discussion).
- Le graphe historique du panier national dans le temps — v1 se limite au
  millésime courant, sauf si la collecte donne l'historique sans coût
  supplémentaire (à observer, pas à garantir).

## Further Notes

Risque principal identifié dans `docs/SOURCES.md` : l'absence de wildcard
connue sur `SERIES_BDM` peut rendre la collecte des 263 IDBANK nettement
plus longue qu'un simple appel groupé. La session dédiée doit budgéter du
temps pour cette recherche de raccourci avant de s'engager sur 263 appels un
par un.
