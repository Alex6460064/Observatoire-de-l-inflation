# Un seul axe de profil officiel, puis ajustement déclaré

Eurostat HBS ne publie que des tables marginales : `hbs_str_t223` par quintile,
`t224` par composition du ménage, `t225` par âge, `t226` par degré d'urbanisation.
Aucun croisement n'existe. Un formulaire à trois menus déroulants n'est donc pas
lisible dans la donnée.

Les combiner par ajustement proportionnel itératif supposerait l'indépendance des
axes, que les données contredisent : le poids du loyer réel `CP041` vaut 175 ‰ au
premier quintile et 144 ‰ chez les moins de 30 ans, deux populations qui se
recouvrent largement. Le vecteur croisé serait biaisé dans un sens inconnu et
invérifiable.

L'utilisateur choisit donc **un** axe et sa modalité, et reçoit le vecteur
Eurostat exact. Il peut ensuite ajuster quelques postes lourds au curseur, avec
renormalisation à 1000 ‰ et affichage permanent de la valeur officielle de départ.

La frontière est ce qui rend le dispositif honnête : **le point de départ est une
donnée sourcée, l'ajustement est une déclaration de l'utilisateur.** L'interface
doit rendre cette distinction visible en permanence, et l'export ou le partage
d'un résultat doit indiquer s'il a été ajusté.
