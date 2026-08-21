# Équivalent-loyer pour les loyers imputés (CP042)

Le poste `CP042` (loyers imputés des propriétaires occupants) pèse jusqu'à 169 ‰
dans les poids Eurostat HBS, mais n'existe pas dans l'IPCH : un indice de prix ne
mesure que des transactions observées, et aucun euro ne circule pour un loyer
qu'un propriétaire se verse à lui-même. Six des 47 groupes COICOP ne joignent pas
entre HBS et l'IPCH ; `CP042` est le seul qui pèse lourd.

Nous appliquons à `CP042` l'indice des loyers réels `CP041`. C'est l'approche
équivalent-loyer, celle du *owners' equivalent rent* du BLS américain, où elle
pèse environ un quart du CPI. Elle est cohérente par construction : le loyer
imputé est *défini* comme le loyer que le logement rapporterait sur le marché
locatif, donc son prix est le prix du marché locatif.

## Alternatives écartées

- **OOHPI Eurostat (`prc_hpi_ooq`) appliqué tel quel** : incohérent. `DW_OWN`
  couvre l'entretien, l'assurance et les services de possession, pas le service
  de logement. Y coller un poids de 169 ‰ qui représente le service complet
  gonfle artificiellement l'effet.
- **OOHPI avec poids recomposés (`prc_hpi_ooinw`)** : rigoureux, mais impose de
  reconstruire tout le vecteur de poids avant la première courbe. Reste la voie
  propre si nous voulons un jour l'approche acquisition nette.
- **Exclure et renormaliser** : ce que fait implicitement l'IPC, mais alors
  propriétaire et locataire subissent le même logement et le cas d'usage central
  du projet disparaît.

## Conséquence à documenter

De décembre 2019 à mars 2026, `CP041` fait +10,2 % contre +19,3 % pour l'ensemble
— effet des loyers encadrés. Tout propriétaire ressortira donc mécaniquement
protégé de l'inflation. C'est un résultat de la régulation du marché locatif, pas
une mesure du vécu des propriétaires. À écrire noir sur blanc dans
`docs/METHODOLOGIE.md` et à afficher en note dans l'interface.
