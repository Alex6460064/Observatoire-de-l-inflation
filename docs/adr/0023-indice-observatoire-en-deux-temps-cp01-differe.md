# Indice Observatoire livré en deux temps, `CP01` différé

L'ADR 0014 annonce l'indice Observatoire avec ses quatre postes (`CP01`,
`CP041`, `CP045`, `CP072`) ensemble en v1. `CP01` reste bloqué par deux
manques non résolus (ADR 0019) : la règle de conversion des périodes
hétérogènes de Familles Rurales (édition 2021 sur deux ans, éditions
suivantes sur un an) en points datés n'est pas tranchée, et cinq éditions
(2019, 2020, 2023, 2024, 2026) n'ont pas été récupérées. `CLAUDE.md` interdit
de coder une méthodologie non validée.

**Décision** : livrer l'indice Observatoire avec `CP041`, `CP045` et `CP072`
d'abord ; `CP01` retombe sur l'IPCH comme n'importe quel poste sans source
propre (§4.2 METHODOLOGIE), exactement le comportement par défaut déjà en
place — aucun code de raccord spécial n'est nécessaire pour ce report.
`CP01` rejoindra l'indice une fois la règle de conversion validée et les
éditions manquantes récupérées, dans une session dédiée.

## Conséquence

Tant que `CP01` n'est pas intégré, l'indice Observatoire couvre une part
plus faible du panier que les 24-43 % annoncés par l'ADR 0014 (`CP01` pèse
128 à 154 ‰ selon le quintile). À corriger dans `docs/METHODOLOGIE.md` et
`docs/INDICES.md` tant que `CP01` reste en repli IPCH.
