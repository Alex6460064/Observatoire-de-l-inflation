# Table de paramètres de l'indice Observatoire

Transformer une source brute en indice de poste demande des paramètres qui ne
sont pas dans la source :

```
CP045  électricité   puissance souscrite, consommation annuelle, option tarifaire
CP072  carburant     mix gazole / SP95-E10 / SP98 / E85
CP041  loyers        pondération des 34 901 communes
CP01   alimentation  correspondance PGC-FLS → CP01
```

Aucun n'est neutre. Le tarif réglementé est `abonnement + kWh × consommation` :
un ménage à 2 500 kWh/an subit surtout la hausse de l'abonnement, un ménage à
12 000 kWh surtout celle du kWh. Le choix du profil **change le taux affiché sur
`CP045`**.

## La décision

Ces valeurs vivent dans `data/manual/parametres.csv`, un fichier de configuration
versionné. Ce sont des **choix de l'Observatoire**, expliqués en prose dans
`docs/METHODOLOGIE.md`. L'interface ne les expose pas et ne permet pas de les
modifier.

La règle 2 de `CLAUDE.md` continue de s'appliquer : chaque valeur doit être citée
dans `METHODOLOGIE.md`, soit avec sa source, soit comme une hypothèse assumée et
justifiée. Le fichier porte donc une colonne `origine` et une colonne
`source_url`, même si l'interface n'en montre rien — c'est ce qui rendra le
passage à un régime plus ouvert possible sans rien réécrire.

## Alternatives écartées

- **Curseurs dans l'interface**, avec valeur de référence affichée en permanence,
  sur le modèle de l'ADR 0006. Aurait été le réglage le plus parlant du dashboard
  — voir l'effet de sa propre consommation sur sa propre inflation — au prix
  d'une surface d'interface et de méthodologie nettement plus large.
- **Badge de qualité par paramètre** dans l'interface, sans curseur.
- **Exiger une source pour tout paramètre**, faute de quoi le poste ne sort pas.
  Écarté comme potentiellement bloquant : la pondération du parc locatif par
  commune n'est pas encore identifiée, et `CP041` attendrait.

## Conséquence à assumer

Un chiffre affiché dépendra d'une constante que l'interface ne mentionne pas. Le
lecteur qui veut savoir d'où sort `+48,1 %` doit ouvrir `METHODOLOGIE.md`. C'est
un recul de transparence par rapport au reste du projet, accepté pour la v1 ;
c'est aussi le premier candidat à révision si le dashboard est montré à des tiers.
