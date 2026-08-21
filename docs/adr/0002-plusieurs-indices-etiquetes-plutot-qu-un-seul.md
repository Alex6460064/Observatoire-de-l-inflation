# Publier plusieurs indices étiquetés plutôt qu'un indice unique

Un seul « meilleur » chiffre obligerait à arbitrer en silence entre source de
prix et source de poids, et à mélanger des sources hétérogènes dans un même
calcul — ce qui rend l'indice irreproductible. Nous publions donc cinq indices
distincts, chacun défini par un couple explicite (source de prix, source de
poids) : IPC officiel, IPCH, IPCH repondéré, IPC repondéré, indice Observatoire.

La règle qui rend ce choix tenable : **on ne mélange jamais deux sources de prix
à l'intérieur d'un même indice.** Croiser les sources se fait en juxtaposant des
courbes, pas en les additionnant. L'indice Observatoire fait exception assumée —
il agrège des sources hétérogènes poste par poste — et c'est précisément pour ça
que chacun de ses postes porte un badge de qualité de source dans l'interface.

## Conséquences

- Le dashboard doit rester lisible avec cinq courbes ; c'est une contrainte de
  conception, pas un détail.
- Tout nouvel indice exige une entrée dans `docs/METHODOLOGIE.md` avant d'être
  codé.
