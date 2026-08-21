# Poids HBS 2017 fixes sur toute la période

> Cet ADR s'appelait « Poids HBS 2020 fixes ». Le titre était faux et le fichier
> a été renommé le 21/08/2026. Voir l'amendement en fin de document.

L'enquête Eurostat HBS est quinquennale. Les poids de profil sont donc un
instantané appliqué à des prix couvrant 2015 à aujourd'hui : un indice de
Laspeyres à poids fixes.

C'est la méthode standard pour ce type d'exercice, mais elle ignore la
déformation des budgets pendant la période — notamment la substitution qu'ont
opérée les ménages face au choc énergétique. À écrire dans la section « Limites »
de `docs/METHODOLOGIE.md`.

L'IPC officiel, lui, révise ses poids chaque année. Une partie de l'écart que le
projet affichera vient donc de cette différence de méthode et non du seul
changement de panier. Ne pas attribuer tout l'écart à la personnalisation.

## Amendement — le millésime n'est pas 2020

La « vague 2020 » d'Eurostat n'est pas une collecte 2020 pour la France. Les
métadonnées HBS le disent en toutes lettres : les données françaises de 2020 sont
celles de 2015, converties aux prix 2020 par un coefficient IPCH. Mesuré sur les
données : les 47 poids de groupe français sont **identiques au pour mille près**
entre 2015 et 2020, écart maximum 0.

Et la vague Eurostat 2015 correspond à l'enquête **Budget de famille 2017 de
l'INSEE**, collectée d'**octobre 2016 à octobre 2017**. Établi par le nombre de
ménages enquêtés, publié des deux côtés — détail et sources dans
`docs/SOURCES.md`.

Trois conséquences.

**La collecte n'a pas subi les confinements.** Elle s'achève deux ans et demi
avant. La question, ouverte depuis la session précédente, est close.

**Le décalage est de deux ans et deux mois**, entre la fin de collecte
(octobre 2017) et la date de référence de l'ADR 0009 (décembre 2019). C'est un
décalage ordinaire pour un Laspeyres. La limite à écrire reste la même — les
poids ne voient pas la substitution post-2019 — mais elle n'est pas aggravée par
un décalage anormal.

**Le millésime est vérifié, donc affichable.** L'interface affiche « enquête
Budget de famille 2017 » à côté de chaque panier. Ce n'est pas un aveu de
faiblesse : c'est la traçabilité que `CLAUDE.md` exige, rendue visible.

## Ce qui reste vrai

La prochaine vague est annoncée pour 2026 des deux côtés — Eurostat
(« Next reference year is 2026 ») et l'INSEE, qui aligne désormais BdF sur les
vagues européennes. Les poids du projet seront donc figés jusqu'à sa publication,
attendue au plus tôt en 2028 compte tenu des délais habituels de diffusion.
