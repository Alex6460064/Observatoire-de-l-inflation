# Bannir le terme « inflation réelle »

Le projet est né d'une vidéo qui oppose l'inflation officielle à une « inflation
réelle » supposée plus honnête. Distinguer les deux exigerait de corriger
l'ajustement hédonique et la shrinkflation, donc de collecter nos propres prix
produit par produit sur plusieurs années — ce que le projet ne fait pas. Le terme
n'a donc aucune définition opérationnelle ici et promettrait un résultat que le
code ne produit pas. Il est interdit dans le code, la documentation et
l'interface ; les mécanismes qu'il désigne sont décrits en prose dans
`docs/METHODOLOGIE.md`.

Même raisonnement pour « inflation ressentie » employée comme taux : ce que
l'INSEE mesure est un solde d'opinion sans unité, pas un pourcentage.

## Amendement — après l'ADR 0014

L'ADR 0014 a créé l'indice Observatoire, dont les prix ne viennent d'aucun
institut statistique. La phrase « le projet ne collecte pas ses propres prix »
est donc devenue imprécise, et le bannissement mérite d'être rejustifié plutôt
que levé.

L'indice Observatoire change la **source de prix** et les **poids**. Il ne change
pas le **traitement qualité**, qui est ce que le terme « inflation réelle »
promet. Vérification poste par poste :

| source de l'indice 4 | corrige la shrinkflation | corrige l'ajustement hédonique |
|---|---|---|
| CRE, tarif réglementé de vente | sans objet — un kWh est un kWh | sans objet |
| Carte des loyers | non | non |
| prix-carburants.gouv.fr | sans objet — un litre est un litre | sans objet |
| Familles Rurales, panier PNNS | non — produits nommés, aucun suivi de grammage | non |

Aucune de ces sources ne relève de prix produit par produit. Le bannissement
tient donc pour la même raison qu'au départ, formulée plus précisément : le
projet n'a aucun moyen de mesurer l'écart que le mot « réelle » désigne.

Ce que le projet peut légitimement affirmer, et qui est l'intention derrière le
mot : que le panier moyen national n'est pas le panier du visiteur, et que les
sources propres de l'indice 4 couvrent 24 à 43 % de son panier selon le quintile
(ADR 0014). Cela se dit sans le mot banni.
