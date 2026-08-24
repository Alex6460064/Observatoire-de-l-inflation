# `CP071` : application du raccord ADR 0021 à AAA Data, adoption comme poste actif

Session du 24/08/2026, suite de l'ADR 0024 (source retenue, collecte
différée). Décisions d'Alexandre, prises en séance : trancher seul la règle
de conversion, retenir la valeur la plus haute en cas de doublon, adopter
`CP071` maintenant plutôt que d'attendre une couverture complète.

## Le problème que l'ADR 0021 ne couvre pas telle quelle

AAA Data ne publie jamais un prix moyen « un mois donné, toutes
motorisations ». Deux formats seulement (`docs/SOURCES.md`) :

- **annuel**, par motorisation (essence, électrique...) — aucun total toutes
  motorisations trouvé pour 2025 ;
- **cumul depuis le 1er janvier**, avec un chiffre **toutes motorisations**
  disponible (`globale`).

Un ratio (ADR 0021) exige deux points sur **la même métrique**. Les points
annuels par motorisation (essence 2025 : deux valeurs divergentes selon la
publication, 25 657 € / 25 884 €) ne peuvent pas former une paire cohérente
avec le point `globale` de 2026 : motorisation différente, agrégat
différent.

## Décision 1 — ancrage sur la paire `globale` cumul-YTD

Intelligence Auto n°93 (17/06/2026) cite les deux points dans la même
phrase, même métrique (cumul janvier→mois courant, toutes motorisations) :

```
t1 = 2025-05 (cumul jan-mai 2025, globale) = 35 043 €
t2 = 2026-05 (cumul jan-mai 2026, globale) = 36 319 €
```

Chaque cumul est ancré au **dernier mois de la période couverte** — même
logique éditoriale que l'ancrage des éditions Familles Rurales (ADR 0019).
C'est le seul point non fourni verbatim par la source ; documenté, pas
deviné.

Formule ADR 0021 appliquée telle quelle :

```
I(t1) = I_IPCH_CP071(t1)
I(t2) = I(t1) × 36319 / 35043
```

`I_IPCH_CP071` : Eurostat publie un code groupe `CP071` direct dans
`prc_hicp_minr` (vérifié en direct le 24/08/2026, `unit=I15`, 1996-01 →
2026-07, 2019-12 = 103,14) — même mécanisme que `CP041` pour les loyers
imputés (`collecte.eurostat.fetch_eurostat_prix_par_sous_classe`). Pas
d'agrégation inventée : le groupe existe déjà côté source.

Avant `t1` : IPCH `CP071` pur (repli par défaut, ADR 0014). Entre `t1` et
`t2` : interpolation linéaire (ADR 0015), `interpole = True` sur les mois
intermédiaires.

## Décision 2 — doublon annuel 2025 : valeur la plus haute retenue

Les quatre lignes annuelles par motorisation (`data/manual/releves.csv`)
restent en base pour traçabilité, mais **n'entrent dans aucun calcul
d'indice** — elles ne participent pas au raccord (décision 1). Sur
instruction explicite d'Alexandre, si une future version du calcul les
utilise, c'est la valeur la plus haute des deux publications qui fait foi
(essence 25 884 €, électrique 42 992 €), l'autre conservée en note.

## Décision 3 — après `t2` : valeur maintenue à plat, pas d'extrapolation de tendance

L'ADR 0021 ne dit rien du comportement après la dernière capture. Ne rien
coder laisserait un trou dans `prix.csv` à partir de 2026-06 (l'assemblage,
`traitement.observatoire.assembler_prix_indice_observatoire`, retire les
sous-classes couvertes sur **toute la période**, pas seulement celle de la
série propre). Deux options : extrapoler une tendance (inventerait un
mouvement de prix non observé — interdit par `CLAUDE.md`), ou maintenir la
dernière valeur connue à plat.

**Retenu : valeur maintenue à plat à partir de `t2` jusqu'à la prochaine
capture**, `interpole = True` sur toute cette portion (aucune de ces valeurs
n'est publiée). C'est l'option qui n'invente aucun mouvement de prix.
`# TODO: reevaluer des que l'Intelligence Auto suivant (n°94, deja repere
dans docs/SOURCES.md) est integre a data/manual/releves.csv.`

## Conséquence sur le panier couvert

`CP071` pèse **32 ‰ (QU1) à 80 ‰ (QU5)** (`data/processed/poids.csv`,
somme des sous-classes `CP07111/CP07112/CP07120/CP07130/CP07140`, conforme
à l'ADR 0020). L'indice Observatoire passe de `CP041 + CP045 + CP072` à
`CP041 + CP045 + CP072 + CP071` — à corriger dans `docs/METHODOLOGIE.md`
section 4.2 et `docs/INDICES.md`.

## Ce qui reste ouvert, pas tranché ici

- Nature TTC/HT du prix AAA Data (`docs/SOURCES.md`).
- Backlog des ~90 numéros Intelligence Auto non collectés — seuls deux
  fournissent aujourd'hui une paire `globale` exploitable.
- Pondération par les volumes de vente réels, absente des deux sources
  candidates évaluées pour `CP071` (ADEME comme AAA Data).

Aucun de ces trois points ne bloque l'adoption : ce sont des limites
méthodologiques documentées (`docs/METHODOLOGIE.md` §8), pas des inconnues
qui empêcheraient un calcul.
