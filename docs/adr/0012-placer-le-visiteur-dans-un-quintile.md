# Placer le visiteur dans un quintile

L'ADR 0011 retient le quintile de revenu comme seul axe de profil, et laisse
ouvert le problème qu'il crée : personne ne connaît son quintile, et HBS ne
publie aucun seuil.

Le visiteur saisit **le revenu net de son ménage et sa composition**. Le quintile
est calculé, jamais deviné : revenu divisé par les unités de consommation, comparé
aux seuils Eurostat `ilc_di01`. Le résultat s'affiche avec le seuil qui l'a
déterminé, et **reste forçable** — l'exploration « et si j'étais au cinquième
quintile ? » fait partie de l'intérêt du projet, à condition qu'elle soit un acte
délibéré.

Seuils hauts (`statinfo=TC`), France 2025, revenu équivalisé :

| quintile | seuil haut, €/an | €/mois |
|---|---|---|
| `QU1` | 17 304 | 1 442 |
| `QU2` | 23 445 | 1 954 |
| `QU3` | 29 571 | 2 464 |
| `QU4` | 38 723 | 3 227 |
| `QU5` | — | au-delà |

## Deux approximations à déclarer, pas à masquer

**Les seuils et les poids ne viennent pas de la même enquête.** Les quintiles HBS
sont calculés à l'intérieur de l'échantillon HBS ; `ilc_di01` vient d'EU-SILC.
Placer quelqu'un dans un quintile HBS avec des seuils SILC est une approximation.
Elle est acceptable ici — le projet assume l'imprécision, jamais l'invention —
mais elle doit figurer dans `docs/METHODOLOGIE.md` et rester visible dans
l'interface.

**Les seuils sont ceux de la dernière année disponible, les poids ceux de 2020.**
Le visiteur connaît son revenu d'aujourd'hui, pas celui de 2020 ; lui demander
l'autre serait absurde. On suppose donc que sa position dans la distribution est
stable entre les deux dates. C'est une hypothèse, elle est écrite.

## À vérifier avant de coder

L'échelle d'équivalence d'EU-SILC est l'échelle OCDE modifiée — 1 pour le premier
adulte, 0,5 par adulte supplémentaire, 0,3 par enfant. **C'est une connaissance
générale, pas une vérification** : elle doit être confirmée sur la fiche de
métadonnées du dataset et consignée dans `docs/SOURCES.md` avant qu'une seule
ligne de calcul d'unités de consommation soit écrite.
