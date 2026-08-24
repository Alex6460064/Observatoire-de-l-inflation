# Spec — Débloquer `CP01` (alimentation) comme poste actif de l'indice Observatoire

## Problem Statement

Le poste `CP01` (alimentation), 13 à 16 % du panier selon le quintile, est en
repli IPCH temporaire dans l'indice Observatoire (ADR 0023) alors qu'une
source propre existe (Familles Rurales, `docs/SOURCES.md`). Résultat : la
couverture affichée de l'indice Observatoire est de 19 à 31 % du panier au
lieu des 24 à 46 % qu'elle atteindrait avec `CP01` actif — et le visiteur du
dashboard ne voit, sur le poste le plus discutable historiquement (prix
alimentaires), que le repli IPCH générique, sans jamais bénéficier de la
source indépendante que le projet a pourtant identifiée et documentée.

Deux blocages précis empêchent l'activation (ADR 0019) :
1. Cinq éditions de l'Observatoire des prix Familles Rurales (2019, 2020,
   2023, 2024, 2026) n'ont jamais été récupérées — seules 2021, 2022, 2025
   sont lues.
2. La règle de conversion des périodes hétérogènes publiées par
   l'association (édition 2021 sur deux ans, éditions suivantes sur un an)
   en points datés utilisables par le pipeline n'est pas tranchée.

## Solution

Depuis le point de vue du visiteur du dashboard : le poste alimentation de
l'indice Observatoire doit refléter une source de prix indépendante des
instituts statistiques (comme les quatre autres postes actifs), avec son
badge `qualite = etude_publiee`, au lieu de retomber silencieusement sur
l'IPCH.

Concrètement, la session dédiée doit :
- Récupérer (ou confirmer l'absence de) les 5 éditions manquantes.
- Faire trancher par Alexandre, via un nouvel ADR, la règle de conversion
  des périodes — ce n'est pas une décision qu'un agent peut prendre seul
  (CLAUDE.md : aucune formule non validée ne se code).
- Implémenter la chaîne : évolutions publiées -> série de points datés ->
  injection dans `data/manual/releves.csv` -> assemblage dans l'indice
  Observatoire via `CP011`/`CP012` (pas `CP01`, cf. METHODOLOGIE §4.2 bis).
- Optionnellement, si Alexandre le valide, chaîner vers Point conso
  (FranceAgriMer, mensuel dès 2024) après la première capture Familles
  Rurales exploitable, en réutilisant le mécanisme de raccord déjà en
  production pour `CP071` (ADR 0021).

## User Stories

1. En tant que visiteur du dashboard, je veux que le poste alimentation de
   l'indice Observatoire vienne d'une source indépendante des instituts
   statistiques, pour que l'indice tienne sa promesse de mesurer autrement
   quand une source alternative crédible existe.
2. En tant que visiteur du dashboard, je veux voir le badge
   `qualite = etude_publiee` sur `CP01` une fois actif, pour savoir que ce
   chiffre n'est ni rejouable par API ni invérifiable, mais qu'il vient d'un
   protocole publié et critiquable.
3. En tant que visiteur consultant le graphe indice Observatoire, je veux que
   les segments de `CP01` construits par interpolation soient visuellement
   distincts (pointillés, ADR 0015) des points publiés, pour ne jamais
   confondre une valeur mesurée et une valeur calculée.
4. En tant que visiteur, je veux que la courbe indice Observatoire affiche sa
   couverture réelle du panier (24-46 % au lieu de 19-31 %) une fois `CP01`
   actif, pour comprendre l'ampleur de ce que l'indice mesure réellement.
5. En tant qu'Alexandre (mainteneur), je veux qu'un nouvel ADR documente la
   règle de conversion des périodes hétérogènes Familles Rurales avant tout
   code, pour que la méthode soit tracée et défendable comme le reste du
   projet.
6. En tant qu'Alexandre, je veux que la collecte des 5 éditions manquantes
   soit tentée et son résultat documenté dans `docs/SOURCES.md` (trouvées et
   lues, ou confirmées introuvables), pour ne pas coder une conversion
   partielle sans savoir ce qui manque réellement.
7. En tant que développeur reprenant le module plus tard, je veux que la
   fonction de conversion évolutions -> points datés soit une fonction pure
   testable indépendamment de la collecte (séparation `traitement/` imposée
   par CLAUDE.md), pour pouvoir la valider sur des cas synthétiques avant de
   la brancher sur les vraies données.
8. En tant que développeur, je veux que le raccord optionnel vers Point
   conso réutilise explicitement le mécanisme déjà validé pour `CP071`
   (`traitement/aaa_data.py::raccorder_serie_cp071`, ADR 0021), pour éviter
   une deuxième implémentation divergente du même patron.
9. En tant que visiteur consultant `docs/METHODOLOGIE.md`, je veux que la
   section 4.4 (aujourd'hui un `# TODO: donnée manquante`) soit remplacée
   par la règle effectivement retenue, pour que la documentation
   contraignante du projet reste à jour.
10. En tant que testeur du pipeline (`uv run pytest`), je veux un test qui
    vérifie que `CP011` et `CP012` reçoivent bien la série attendue lors de
    l'assemblage, pour éviter la régression documentée dans METHODOLOGIE
    §4.2 bis (clé `CP01` inexistante en COICOP 1999).
11. En tant qu'Alexandre, je veux que le coût des postes exclus du panier
    commun (ADR ticket 02) soit revérifié une fois `CP01` actif, au cas où
    son activation change les trous d'historique à `2019-12`.
12. En tant que recruteur/lecteur du dépôt, je veux que le commit qui active
    `CP01` référence explicitement l'ADR de la règle de conversion, pour que
    l'historique git reste lisible comme documentation du raisonnement.

## Implementation Decisions

- **Décision préalable bloquante, hors périmètre de code** : la règle de
  conversion des périodes (2021 sur 2 ans vs 1 an ensuite) doit être
  tranchée par un nouvel ADR avant toute implémentation — ce spec ne la
  décide pas, conformément à la règle anti-hallucination de `CLAUDE.md`. La
  session dédiée commence par cette décision, pas par le code.
- Collecte : reste manuelle (`docs/SOURCES.md` : "prévoir que la collecte
  CP01 restera manuelle... ne pas budgéter de parseur automatique"). Pas de
  nouveau module `collecte/familles_rurales.py` prévu pour du parsing PDF
  automatique. Les valeurs lues entrent dans `data/manual/releves.csv`,
  schéma existant (`source_url`, `periode`, `qualite`, ADR 0004).
- Traitement : nouveau module (ou fonction ajoutée à un module existant)
  `traitement/familles_rurales.py`, fonction pure qui prend les évolutions
  publiées + leurs dates de référence et produit une série de points datés
  chaînée depuis `2019-12`, avec marquage `interpole` entre points publiés
  (ADR 0015). Distinct du module `traitement/aaa_data.py` mais suit le même
  patron de raccord si l'option Point conso est retenue.
- Assemblage : `scripts/run_pipeline.py::construire_prix_indice_observatoire`
  doit passer la série sous les clés `CP011` et `CP012` (pas `CP01`), comme
  documenté en METHODOLOGIE §4.2 bis.
- Panier commun : `traitement.poids.exclure_postes_du_panier` (ticket 02) à
  revérifier une fois `CP011`/`CP012` actifs — leur historique à `2019-12`
  doit être confirmé complet, sinon ils rejoignent l'exclusion existante.
- Documentation : `docs/METHODOLOGIE.md` §4.4 et §4.2 (tableau "poids
  couverts"), `docs/SOURCES.md` (éditions retrouvées ou confirmées
  absentes), `docs/INDICES.md` (retirer le repli IPCH temporaire une fois
  actif) à mettre à jour dans le même travail.

## Testing Decisions

- Fonction de conversion évolutions -> points datés : tests avec données
  factices (pas d'appel réseau, cohérent avec
  `tests/test_traitement_observatoire.py` existant) — cas nominal, cas bord
  (une seule édition disponible, évolution négative, période chevauchant
  `2019-12`).
- `assembler_prix_indice_observatoire` : réutilise les tests existants
  (`tests/test_traitement_observatoire.py`), ajouter un cas `CP011`/`CP012`
  simultanés depuis le même groupe HBS.
- Si raccord Point conso retenu : test du raccord sur le même patron que le
  raccord `CP071` existant (chercher les tests d'`aaa_data` comme prior
  art).
- Pas de test d'intégration réseau — `docs/SOURCES.md` documente déjà que la
  collecte reste manuelle.

## Out of Scope

- Le parsing automatique des PDF Familles Rurales (explicitement écarté par
  `docs/SOURCES.md`).
- L'extension à d'autres postes (`CP08`, `CP11`, etc.) — traité par un spec
  séparé si retenu.
- La décision elle-même de la règle de conversion — ce spec prépare le
  terrain, ne la prend pas.

## Further Notes

Ce spec ne peut pas être exécuté de bout en bout par un agent sans
intervention humaine : la première étape (choix de la règle de conversion)
est une décision méthodologique qui doit être validée par Alexandre,
conformément à la priorité absolue du projet ("Exactitude des données >
Rigueur méthodologique"). L'agent qui reprend ce spec doit s'arrêter et
proposer 2-3 règles candidates plutôt que d'en coder une.
