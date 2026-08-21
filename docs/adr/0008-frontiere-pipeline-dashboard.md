# Frontière entre le pipeline et le dashboard

Le dashboard ne fait aucun appel réseau. Le pipeline écrit deux tables longues
dans `data/processed/`, versionnées en CSV ; le dashboard les charge et calcule.

La ligne de partage n'est pas « collecte contre affichage » mais :

> **Tout ce qui ne dépend pas des choix de l'utilisateur est pré-calculé et
> versionné. Tout ce qui en dépend est calculé en direct, par fonction pure.**

Conséquence non évidente : **l'indice Observatoire est assemblé dans le
pipeline**, pas dans l'application. Son arbitrage poste par poste — carburant,
`CP042` traité par `CP041` (ADR 0005), relevés manuels, repli sur l'IPCH — ne
dépend d'aucun choix de l'utilisateur. Il produit donc une série de prix comme
les autres, avec sa colonne `qualite`, et reste testable hors application. Seule
la repondération par les poids de profil est dynamique, ce qui réduit `analyse/`
à une seule fonction pure `(prix, poids) → indice`.

## Pourquoi les curseurs ne forcent pas le pré-calcul

L'ADR 0006 impose des curseurs d'ajustement, donc les indices ne peuvent pas être
pré-calculés pour toutes les combinaisons de poids. Mais le recalcul est un
produit scalaire sur 47 postes × ~366 mois, soit environ 17 000 opérations
vectorisées : de l'ordre de la milliseconde. Le budget de 100 ms n'exclut que le
fetch réseau.

## Format et versionnement

Volume estimé à partir des couvertures relevées dans `docs/SOURCES.md` (IPC
rétropolé à `1996-01`, IPCH v2 jusqu'à `2026-06`) : ~60 séries × ~366 mois × 3
sources de prix ≈ 45 000 lignes, soit **~1,5 Mo en CSV long**. Les poids pèsent
~940 lignes.

CSV commité plutôt que Parquet : à cette échelle, Parquet économiserait ~1,3 Mo,
ajouterait la dépendance `pyarrow` et rendrait les diffs binaires. Le CSV rend
visible en revue git qu'une valeur publiée a changé — ce qui est précisément ce
que ce projet doit pouvoir tracer.

```
data/processed/prix.csv    source, poste, periode, valeur, qualite
data/processed/poids.csv   axe, modalite, poste, pm
data/processed/META.json   date_collecte
```

## Conséquence à ne pas oublier

La donnée est figée au dernier run du pipeline. `META.json` porte la date de
collecte et **l'interface doit l'afficher** : sans elle, le dashboard présente
des chiffres périmés sans le dire.

## Alternatives écartées

- **Indices pré-calculés et commités** : tue les curseurs, contredit l'ADR 0006.
- **Fetch réseau depuis le dashboard avec `@st.cache_data`** : donnée toujours
  fraîche, mais démo suspendue à la disponibilité des APIs, tests non
  déterministes, et la limite INSEE de 30 appels/minute/IP devient un risque en
  démo publique.
- **Parquet non commité** : casse le `clone && streamlit run`.
- **Assembler l'indice Observatoire côté dashboard** : rendrait l'arbitrage de
  sources visible dans l'interface, mais ferait de la logique la plus fragile du
  projet du code d'application non testé hors Streamlit.
