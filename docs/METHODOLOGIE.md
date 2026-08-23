# Méthodologie — Observatoire de l'Inflation

Ce document dit **ce que l'Observatoire calcule, comment, et avec quoi**. Il est
contraignant : `CLAUDE.md` interdit de coder une formule qui n'y figure pas, et
interdit d'y écrire un chiffre sans source dans `docs/SOURCES.md`.

Il consolide les **dix-neuf décisions** de `docs/adr/`. Chaque section renvoie à
l'ADR qui l'a tranchée ; l'ADR porte les alternatives écartées et le
raisonnement, ce document porte le résultat.

Le vocabulaire employé ici est celui de `CONTEXT.md`, qui fait foi. Deux termes
y sont **bannis** — « inflation réelle » et « inflation ressentie » employée
comme taux — et ne doivent apparaître nulle part, sauf pour dire qu'ils sont
bannis.

---

## 1. Ce que l'Observatoire mesure

Une seule question : **le panier moyen national n'est pas votre panier ; quelle
différence cela fait-il sur la hausse des prix que vous subissez ?**

L'outil recombine des indices de prix par poste avec des structures de budget
différentes. Il compare le résultat à l'indice officiel.

### Ce qu'il ne mesure pas

Il ne mesure **pas** l'écart entre les prix publiés et les prix « vrais ». Cet
écart — shrinkflation, ajustement hédonique — exigerait de suivre chaque produit,
son grammage et sa qualité, sur plusieurs années. Aucune source du projet ne le
fait, y compris les siennes propres (ADR 0001, amendé ; ADR 0003).

Formulé autrement : le projet change **la source des prix** et **les poids**, il
ne change jamais **le traitement qualité**. C'est la seule raison, mais elle
suffit, du bannissement d'« inflation réelle ».

Ce que le projet peut légitimement affirmer : que les sources propres de l'indice
Observatoire couvrent **24 à 43 % du panier** selon le quintile, et que
repondérer déplace le résultat. Cela se dit sans le terme banni.

---

## 2. Les cinq indices publiés

Jamais un chiffre unique. Cinq indices étiquetés, chacun défini par un couple
explicite **(source de prix, source de poids)** — ADR 0002.

| # | nom | prix | poids |
|---|---|---|---|
| 0 | **IPC officiel** | INSEE | panier moyen national INSEE |
| 1 | **IPCH** | Eurostat | poids officiels Eurostat |
| 2 | **IPCH repondéré** | Eurostat | poids de profil (HBS transposés) |
| 3 | **IPC repondéré** | INSEE | poids de profil (HBS transposés) |
| 4 | **Indice Observatoire** | sources propres poste par poste | poids de profil |

**Règle intangible : on ne mélange jamais deux sources de prix à l'intérieur d'un
même indice.** Croiser des sources se fait en juxtaposant des courbes, pas en les
additionnant.

L'indice 4 est l'exception assumée : il agrège des sources hétérogènes poste par
poste. C'est précisément pourquoi **chacun de ses postes porte un badge de qualité
de source** dans l'interface, et pourquoi lui seul en porte.

Les indices 2 et 3 diffèrent uniquement par la source de prix — c'est ce qui rend
lisible la part de l'écart due à la méthode INSEE contre méthode Eurostat, et non
à la personnalisation.

---

## 3. Les poids

### 3.1 Origine et millésime

Les poids de profil viennent de l'enquête **Eurostat HBS**, table
`hbs_str_t223`, dimension `quant_inc`, modalités `QU1` à `QU5`. Jamais saisis,
jamais estimés.

Le **millésime est 2017**, et non 2020 comme l'étiquette européenne le laisse
croire (ADR 0007, amendé). La « vague 2020 » d'Eurostat n'est pas une collecte
2020 pour la France : les données françaises de 2020 sont celles de 2015,
converties aux prix 2020 par un coefficient IPCH. Vérification : les 47 poids de
groupe français sont **identiques au pour mille près** entre 2015 et 2020, écart
maximum 0.

Et la vague Eurostat 2015 correspond à l'enquête **Budget de famille 2017 de
l'INSEE**, collectée d'**octobre 2016 à octobre 2017**.

Deux conséquences directes :

- **La collecte n'a pas subi les confinements.** Elle s'achève deux ans et demi
  avant le premier. La question est close.
- **Le décalage jusqu'à la date de référence est de deux ans et deux mois**
  (octobre 2017 → décembre 2019). Ordinaire pour un Laspeyres, et non aggravé.

L'interface affiche « enquête Budget de famille 2017 » **à côté de chaque
panier**. C'est de la traçabilité, pas un aveu.

La prochaine vague est annoncée pour 2026 des deux côtés ; sa publication n'est
pas attendue avant 2028. Les poids du projet sont figés jusque-là.

### 3.2 Transposition de nomenclature

Les poids et les prix ne parlent pas la même langue : HBS est publié en **ECOICOP
v1**, l'IPCH courant en **COICOP 2018**. Joindre par le code produirait des
correspondances fausses et silencieuses, pas des valeurs manquantes (ADR 0010).

Mesuré sur les 47 groupes HBS à trois chiffres, poids QU1 FR : 21 groupes ont un
libellé identique (526 ‰), 20 divergent (199 ‰), 6 sont absents de la v2 (268 ‰).
Environ **111 ‰ changent réellement de contenu**. Les pires :

```
CP121  37 ‰   HBS = Personal care          COICOP 2018 = Insurance
CP083  22 ‰   HBS = Téléphone, services    COICOP 2018 = Information and communication services
CP093  18 ‰   HBS = Loisirs, jardin        COICOP 2018 = Garden products and pets
CP022  14 ‰   HBS = Tobacco                COICOP 2018 = Alcohol production services
```

**Les prix restent en COICOP 2018 ; les poids sont transposés une fois pour
toutes vers cette nomenclature.** La transposition vit dans
`data/manual/correspondance_coicop.csv`, versionnée, vérifiée à la main contre la
table officielle UNSD/Eurostat.

Les six groupes réputés non joignants ne manquaient pas : COICOP 2018 les a
renumérotés dans la division `CP13`. `CP042` reste le seul trou réel, traité en
3.4.

Rester en ECOICOP v1 aurait été plus simple et **a été écarté** : les datasets
correspondants sont **arrêtés à `2025-12`**. Le dashboard aurait été figé le jour
de sa publication. Confirmé indépendamment sur l'API OCDE (`docs/SOURCES.md`).
Passer en COICOP 2018 ne coûte aucune profondeur d'historique : `prc_hicp_minr`
France `TOTAL` couvre `1996-01` → `2026-07`.

### 3.3 Clé de répartition

La table de correspondance dit **où va** un poste, jamais **combien** : elle ne
porte aucune part. Or **48 à 49 % du panier** repose sur des groupes qui éclatent
vers plusieurs postes 2018. Une partition fermée n'existe pas — 34 groupes 1999
s'agglomèrent en un bloc unique de 576 ‰ (ADR 0018).

**Décision : prorata direct.** Le poids HBS de chaque groupe est découpé au
prorata des poids d'articles de l'IPCH ECOICOP v2 France (`prc_hicp_iw`, 2020) des
sous-classes 2018 issues de ce groupe.

Pour un groupe HBS `g` de poids `w_g`, et une sous-classe 2018 `c` issue de `g` :

```
w_c  =  w_g  ×  iw_c  /  Σ  iw_c'
                       c' issue de g
```

**La masse de chaque groupe est conservée** : `Σ_c w_c = w_g`. C'est la propriété
qui borne l'erreur — une clé inexacte redistribue à l'intérieur du groupe et ne
peut pas déformer son total. Les poids IPCH servent de clé, **jamais de niveau**.
La contrainte `Σ part = 1` par groupe est vérifiée au chargement, et une ligne qui
la viole est rejetée, pas ignorée.

L'alternative — partir des poids IPCH et les déformer par le ratio quintile /
national — **a été codée et comparée sur les vraies données**. Écart total : 248 ‰
en valeur absolue, soit **124 ‰ de panier qui atterrit ailleurs**.

Poids QU3, en pour mille :

| poste | méthode du ratio | prorata (retenu) | HBS brut |
|---|---|---|---|
| `01.1` alimentation | 135 | 145 | 143 |
| `04.1` loyers réels | 65 | 71 | 71 |
| `07.2` carburants | **94** | 59 | 58 |
| `12.1` assurances | **34** | 82 | 82 |
| `07.1` achat de véhicules | 29 | 49 | 49 |

Annoncer 94 ‰ de carburant à un ménage dont l'enquête dit 58 ‰ est indéfendable
sur une interface qui promet « votre panier ». La recommandation initiale était la
méthode du ratio ; les chiffres l'ont renversée.

Cas particuliers :

- **41 sous-classes 2018 ont plusieurs sources 1999** (148 ‰ du poids IPCH
  France). Aucune source ne dit dans quelle proportion. Leur poids IPCH est
  réparti **à parts égales** entre leurs sources. Il est borné à ces 148 ‰ et
  figure dans les limites.
- **Un groupe HBS dont aucune sous-classe cible n'a de poids IPCH** (le
  dénominateur du prorata est nul) transmet son poids intact à ses sous-classes
  cibles, réparties **à parts égales** entre elles — généralisation de la règle
  ci-dessus au cas symétrique. `CP042` (loyers imputés) en est l'exemple :
  vérifié le 22/08/2026 contre la table UNSD, il a **deux** sous-classes cibles
  (`04.2.1` résidence principale, `04.2.2` autres loyers imputés), pas une
  seule comme une lecture rapide de la correspondance le suggérait. Aucune des
  deux n'a de poids IPCH (section 3.4) : chacune reçoit **la moitié** du poids
  de `CP042`. **C'est, avec le cas ci-dessus, le seul nombre inventé de toute
  la méthode** — décidé le 22/08/2026, faute de donnée qui départagerait
  résidence principale et résidences secondaires.

**Renormalisation finale.** Les poids de groupe HBS bruts (`hbs_str_t223`) ne
somment pas exactement à 1000 ‰ par quintile — chaque quintile est un
arrondi indépendant de 47 valeurs entières publiées, pas une erreur de
calcul : QU1 = 993 ‰, QU2 = 992 ‰, QU3 = 993 ‰, QU4 = 988 ‰, QU5 = 981 ‰
(vérifié le 22/08/2026). `analyse.indice` exige une somme à 1000 ‰ ±
`TOLERANCE_POUR_MILLE` (0,5 ‰) pour tout poste absent ne passe pas
inaperçu (section 5.2) ; un écart de plusieurs pour mille par arrondi de
publication déclencherait la même garde qu'une vraie erreur. Le vecteur
transposé de chaque modalité est donc mis à l'échelle pour sommer exactement
à 1000 ‰ après transposition — la transposition étant linéaire et
conservant la masse par groupe, remettre à l'échelle avant ou après ne
change pas les parts relatives. Décidé le 22/08/2026.

**Panier partiel : postes sans historique jusqu'à la référence.**
`rebaser` (section 5.2) exige une valeur de prix à `2019-12` pour chaque
poste pondéré. Une première vérification du 22/08/2026, sur les 234 postes
INSEE alors pondérés de l'indice 3, avait trouvé deux postes concernés
(`CP06310`, `CP10102`, poids perdu sous 1,5 ‰ par quintile). Depuis
l'extension de `poids.csv` à 296 postes et l'introduction de l'indice 2
(Eurostat `prc_hicp_minr`), un contrôle plus large le 23/08/2026 (ticket 01)
donne : **62 postes** sans historique complet côté INSEE, **66** côté
Eurostat — les 62 INSEE forment un sous-ensemble strict des 66 Eurostat
(détail poste par poste : `docs/SOURCES.md`).

**Décision (ticket 02, 23/08/2026) : panier commun.** Les indices 2 et 3 ne
doivent différer que par la source de prix (section 2) — un panier
différent entre eux casserait cette lecture. L'exclusion retenue est donc
l'**union** des deux trous (66 postes), appliquée une seule fois à
`poids.csv`, qui reste un fichier unique partagé entre les deux indices,
renormalisé une seule fois à 1000 ‰
(`traitement.poids.exclure_postes_du_panier`), même logique que la
renormalisation ci-dessus. Coût du panier commun : 4 postes en plus exclus
côté indice 3 par rapport à un panier INSEE isolé (`CP04210`, `CP04220` —
loyers imputés, absents structurellement de l'IPCH, section 3.4 —
`CP06133`, `CP09470`).

### 3.4 Le poste `CP042`, loyers imputés

`CP042` pèse jusqu'à **169 ‰** dans les poids HBS mais **n'existe pas dans
l'IPCH** : un indice de prix ne mesure que des transactions observées, et aucun
euro ne circule pour un loyer qu'un propriétaire se verse à lui-même (ADR 0005).

**`CP042` reçoit l'indice de prix des loyers réels `CP041`.** C'est l'approche
équivalent-loyer, celle du *owners' equivalent rent* du BLS américain, où elle
pèse environ un quart du CPI. Elle est cohérente par construction : le loyer
imputé est *défini* comme le loyer que le logement rapporterait sur le marché,
donc son prix est le prix du marché locatif.

Exclure et renormaliser — ce que fait implicitement l'IPC — a été écarté : alors
propriétaire et locataire subiraient le même logement, et le cas d'usage central
du projet disparaîtrait.

### 3.5 Le profil de ménage

Eurostat HBS ne publie que des **tables marginales**, jamais de croisement :
`t223` par quintile, `t224` par composition, `t225` par âge, `t226` par
urbanisation. Un formulaire à trois menus n'est donc pas lisible dans la donnée
(ADR 0006).

Les combiner par ajustement proportionnel itératif supposerait l'indépendance des
axes, que les données contredisent : `CP041` vaut 175 ‰ au premier quintile et
144 ‰ chez les moins de 30 ans, deux populations qui se recouvrent largement. Le
vecteur croisé serait biaisé dans un sens inconnu et invérifiable.

**L'utilisateur choisit un axe et une modalité, et reçoit le vecteur Eurostat
exact.** Il peut ensuite ajuster quelques postes lourds au curseur, avec
renormalisation à 1000 ‰ et affichage permanent de la valeur officielle de départ.

> **La frontière qui rend le dispositif honnête : le point de départ est une
> donnée sourcée, l'ajustement est une déclaration de l'utilisateur.**

L'interface rend cette distinction visible en permanence, et tout export ou
partage indique si le résultat a été ajusté.

**En v1, un seul axe est exposé : le quintile de revenu** (ADR 0011). C'est le
plus discriminant sur le poste où le projet est le plus parlant — `CP041` va de
175 ‰ au premier quintile à 25 ‰ au cinquième. Les cinq tables sont collectées et
stockées ; exposer un axe de plus est un changement d'interface, pas de pipeline.

### 3.6 Placer le visiteur dans un quintile

Personne ne connaît son quintile, et HBS ne publie aucun seuil (ADR 0012).

Le visiteur saisit **le revenu net de son ménage et sa composition**. Le quintile
est **calculé, jamais deviné**.

Unités de consommation, échelle **OCDE modifiée** (confirmée sur les métadonnées
EU-SILC, voir `docs/SOURCES.md`) :

```
UC  =  1  +  0,5 × (adultes − 1)  +  0,3 × (enfants de moins de 14 ans)
```

Revenu équivalisé = revenu net annuel du ménage ÷ UC, comparé aux seuils Eurostat
`ilc_di01`, `statinfo=TC` (seuils hauts), France 2025 :

| quintile | seuil haut, €/an | €/mois |
|---|---|---|
| `QU1` | 17 304 | 1 442 |
| `QU2` | 23 445 | 1 954 |
| `QU3` | 29 571 | 2 464 |
| `QU4` | 38 723 | 3 227 |
| `QU5` | — | au-delà |

Le résultat s'affiche **avec le seuil qui l'a déterminé**, et **reste forçable** :
l'exploration « et si j'étais au cinquième quintile ? » fait partie de l'intérêt
du projet, à condition d'être un acte délibéré et visible.

Un seuil de quintile ne rentre dans **aucun calcul d'indice**. Il sert uniquement
à placer le visiteur.

---

## 4. Les prix

### 4.1 Indices 0 à 3

Séries publiées telles quelles, sans retraitement autre que le rebasage de la
section 5. IPC INSEE pour 0 et 3, IPCH Eurostat (`prc_hicp_minr`, COICOP 2018)
pour 1 et 2.

### 4.2 L'indice Observatoire, poste par poste

Quatre postes ont une source propre. **Tout le reste du panier retombe sur
l'IPCH** (ADR 0014).

| poste | source propre | fréquence | couverture | qualité |
|---|---|---|---|---|
| `CP01` alimentation | Familles Rurales, Observatoire des prix | annuelle | 2019→2025 | `etude_publiee` |
| `CP041` loyers réels | « Carte des loyers », min. Transition écologique | annuelle | 2018, 2022→2025 | `api_ouverte` |
| `CP045` énergie logement | CRE, tarif réglementé de vente d'électricité | barème daté | 2012→2026 | `api_ouverte` |
| `CP072` utilisation du véhicule | prix-carburants.gouv.fr | quotidienne | 2019→2026 | `api_ouverte` |

Poids HBS couverts par une source propre :

```
              CP01   CP041   CP045   CP072   total
QU1            147     175      55      48    425 ‰
QU3            154      71      46      58    329 ‰
QU5            128      25      36      50    239 ‰
```

Soit **24 à 43 % du panier selon le quintile**. L'indice Observatoire n'est donc
pas une variante cosmétique de l'IPCH repondéré : il en diffère sur les postes qui
ont le plus augmenté depuis 2019.

**`CP042` reçoit `CP041`**, ici comme ailleurs (section 3.4).

### 4.3 `CP01` — ce qui est chaîné

Source retenue : Familles Rurales, Observatoire des prix de grande consommation,
20 éditions, protocole publié — 4 collectes par an (février, avril, juin,
octobre), 135 magasins, 100 relevés bénévoles, 42 départements, 83 produits sur
les 12 groupes du PNNS en 2025 (ADR 0019).

⚠️ **L'objet chaîné est l'évolution que l'association publie elle-même**, calculée
par elle sur produits comparables. **Jamais le coût brut de son panier** : le
panier perd un quart de ses produits entre 2021 (97) et 2025 (83), et comparer
450 € à 539 € ne comparerait pas des prix.

`# TODO: donnée manquante — à vérifier avec Alexandre.` Seules les éditions 2021,
2022 et 2025 ont été lues. Les périodes de référence publiées ne sont pas
homogènes : l'édition 2021 raisonne sur deux ans (sept. 2019 → sept. 2021), les
suivantes sur un an. **La règle de conversion de ces intervalles en points datés
n'est pas tranchée et ne doit pas être codée avant de l'être.**

---

## 5. Base 100, agrégation, lecture

### 5.1 Date de référence

**`2019-12`**, dernier mois avant le choc covid (ADR 0009). Elle couvre le covid
puis le choc énergétique, et les valeurs déjà relevées dans `docs/SOURCES.md`
partent de ce mois — nos courbes sont donc directement vérifiables contre elles :
`TOTAL` +19,3 %, `CP01` +27,4 %, `CP041` +10,2 %, `CP045` +45,6 % entre `2019-12`
et `2026-03`.

C'est un **paramètre de lecture**, pas une propriété de la donnée. Le pipeline
stocke toute la profondeur disponible ; la référence est offerte dans une liste
courte, jamais en saisie libre — avec des poids fixes, une référence 1996
projetterait la structure de budget de 2017 sur trente ans de prix.

### 5.2 Formules

Rebasage d'un poste `p` sur la date de référence `t₀` :

```
I_p(t)  =  100  ×  P_p(t) / P_p(t₀)
```

Agrégation, Laspeyres à poids fixes, `w_p` en pour mille sommant à 1000 :

```
I(t)  =  Σ  w_p × I_p(t)  /  1000
        p
```

Lectures affichées :

```
évolution depuis la référence   =  I(t) / 100  −  1
glissement annuel               =  I(t) / I(t−12)  −  1
```

Les poids `w_p` ne dépendent pas de `t` : c'est ce qui fait de l'indice un
Laspeyres, et c'est la limite 6.

### 5.3 Interpolation

L'ADR 0013 impose un graphe mensuel ; trois des quatre postes à source propre ne
sont pas mensuels. Les valeurs intermédiaires sont obtenues par **interpolation
linéaire entre deux points publiés** (ADR 0015).

Le garde-fou est **indissociable** de la décision. Interpoler produit des valeurs
mensuelles qui n'existent dans aucune publication ; ce n'est acceptable que si
elles restent discernables d'un relevé **à toutes les étapes** :

- `data/processed/prix.csv` porte une colonne `interpole`, vraie sur tout point
  calculé, fausse sur tout point publié ;
- le tooltip du dashboard affiche explicitement qu'une valeur est interpolée ;
- tout export ou partage conserve la colonne ;
- les segments interpolés sont tracés **en pointillé**, pas seulement signalés au
  survol.

Sans ce marquage, une valeur interpolée devient indiscernable d'une valeur
mesurée — ce qui viole directement la règle d'anti-hallucination de `CLAUDE.md`.

**Le tarif réglementé n'est pas concerné** : un barème vaut jusqu'au suivant. C'est
une donnée en escalier par nature, pas une lacune à combler.

**Le trou 2019-2021 des loyers** relève d'une décision distincte (ADR 0016) : les
millésimes 2019, 2020 et 2021 de la Carte des loyers **n'ont jamais été produits**
— le projet a changé de porteur entre-temps. `CP041` est donc interpolé entre 2018
et 2022, soit **47 valeurs mensuelles calculées**.

### 5.4 Le graphe

Cinq indices, **pas mensuel, en niveau**, base `2019-12 = 100` (ADR 0013).

Le niveau plutôt que le glissement annuel parce que cinq courbes partant du même
point s'écartent en éventail : **l'écart entre indices, qui est le sujet du
projet, se lit comme une distance verticale.** En glissement annuel, les courbes
se croisent en permanence et l'écart cumulé disparaît du graphe.

Le glissement annuel est affiché **en valeur, à côté du graphe**, jamais en
courbe :

```
+19,3 % depuis 2019-12       +2,1 % sur un an
```

Les moyennes annuelles ont été écartées : elles écrasent le choc énergétique de
2022, précisément le moment où les profils divergent le plus.

---

## 6. Paramètres de l'Observatoire

Transformer une source brute en indice de poste demande des paramètres absents de
la source (ADR 0017) :

```
CP045  électricité   puissance souscrite, consommation annuelle, option tarifaire
CP072  carburant     mix gazole / SP95-E10 / SP98 / E85
CP041  loyers        pondération des 34 901 communes
CP01   alimentation  correspondance panier PNNS -> CP01
```

Aucun n'est neutre. Le tarif réglementé est `abonnement + kWh × consommation` : un
ménage à 2 500 kWh/an subit surtout la hausse de l'abonnement, un ménage à
12 000 kWh surtout celle du kWh. **Le choix du profil change le taux affiché sur
`CP045`.**

Ces valeurs vivent dans `data/manual/parametres.csv`, versionné, avec une colonne
`origine` et une colonne `source_url`. Ce sont des **choix de l'Observatoire**,
expliqués en prose ici. L'interface ne les expose pas et ne permet pas de les
modifier en v1.

**Conséquence assumée** : un chiffre affiché dépend d'une constante que
l'interface ne mentionne pas. C'est un recul de transparence par rapport au reste
du projet, et le premier candidat à révision.

**La pondération communale de `CP041`** utilise le parc locatif du recensement
INSEE 2022, jointure `CODGEO` ↔ `INSEE_C` vérifiée. Une agrégation rigoureuse
pondérerait par la **surface louée** ; la base ne publie aucune variable de
surface, seulement un nombre de pièces non ventilé par statut d'occupation. Voir
limite 12.

---

## 7. Architecture du calcul

Le dashboard **ne fait aucun appel réseau** (ADR 0008). La ligne de partage n'est
pas « collecte contre affichage » mais :

> **Tout ce qui ne dépend pas des choix de l'utilisateur est pré-calculé et
> versionné. Tout ce qui en dépend est calculé en direct, par fonction pure.**

Conséquence non évidente : **l'indice Observatoire est assemblé dans le
pipeline**, pas dans l'application. Son arbitrage poste par poste — source propre,
`CP042` traité par `CP041`, relevés manuels, repli sur l'IPCH — ne dépend d'aucun
choix de l'utilisateur. Il produit donc une série de prix comme les autres, avec
sa colonne `qualite`, et reste testable hors Streamlit.

Seule la repondération est dynamique, ce qui réduit `analyse/` à **une seule
fonction pure `(prix, poids) → indice`**.

```
data/processed/prix.csv    source, poste, periode, valeur, qualite, interpole
data/processed/poids.csv   axe, modalite, poste, pm
data/processed/META.json   date_collecte
```

CSV commité plutôt que Parquet : à cette échelle (~45 000 lignes, ~1,5 Mo)
Parquet économiserait ~1,3 Mo, ajouterait une dépendance et rendrait les diffs
binaires. **Le CSV rend visible en revue git qu'une valeur publiée a changé** —
exactement ce que ce projet doit pouvoir tracer.

**La donnée est figée au dernier run du pipeline.** `META.json` porte la date de
collecte et **l'interface doit l'afficher** : sans elle, le dashboard présente des
chiffres périmés sans le dire.

`# TODO: à vérifier` — l'ADR 0008 dimensionne le calcul sur « 47 postes », qui est
le nombre de groupes HBS **avant** transposition. Après transposition (section
3.3) le vecteur est au niveau sous-classe, donc plus long. L'estimation de volume
reste du bon ordre mais le chiffre est à recaler.

---

## 8. Limites

Toutes les limites connues, **ordonnées par le poids de panier qu'elles
affectent**. Aucune n'est un défaut caché : chacune est la contrepartie d'une
décision prise en connaissance de cause, et référencée à son ADR.

**1. La base 100 repose en partie sur des valeurs calculées.** La date de
référence `2019-12` tombe dans le trou 2019-2021 de la Carte des loyers (ADR
0016), et trois mois après le point de départ de la série `CP01` (ADR 0019). Au
premier quintile, **322 ‰ du panier — `CP01` 147 ‰ plus `CP041` 175 ‰ — s'ancrent
donc sur une valeur qu'aucune publication ne contient.** Près d'un tiers. C'est la
conséquence la plus lourde de tout le dossier.

**2. `CP041` mesure autre chose que l'IPCH — flux contre stock.** La Carte des
loyers donne des **loyers d'annonce**, le prix demandé pour un logement remis sur
le marché. L'IPCH `CP041` mesure le loyer payé par **l'ensemble du parc**,
locataires en place compris, dont le loyer est plafonné par l'indexation. L'écart
entre les deux est une différence de champ, **pas une erreur de l'INSEE**.
Afficher cet écart sans l'écrire ferait du projet un outil militant (ADR 0014).

**3. Le panier `CP01` est normatif, pas observé.** Familles Rurales relève un
panier **PNNS** — ce qu'il faudrait manger — où les fruits et légumes pèsent près
du tiers du budget, sans alcool, sans restauration, avec peu de transformé. Ce
n'est pas la structure de `CP01`. Conséquence mesurée : leur panier monte
**systématiquement moins** que l'IPC alimentaire — +8,3 % contre +12 % en 2022,
+9,4 % contre +14,7 % de 2023 à 2025, −0,75 % contre +1,7 % de 2024 à 2025. **Sur
`CP01`, l'indice Observatoire dira que l'INSEE surestime la hausse.** Ce résultat
doit toujours être affiché avec la raison, sous peine d'être lu comme une
découverte alors que c'est un effet de champ (ADR 0019).

> Cette limite **remplace** l'ancienne limite « périmètre PGC-FLS », devenue sans
> objet avec l'abandon des panels de presse.

**4. Incohérence de périmètre entre poids et prix — les assurances.** HBS
enregistre la **prime brute**, l'IPCH le seul **service d'assurance** (prime moins
indemnités) : 82 ‰ contre 34 ‰. Le prorata conserve la masse HBS, donc applique
82 ‰ mesurés en primes brutes à un indice qui suit le coût du service. La série
surpondérée n'évolue pas comme la dépense. Défaut réel, unique, écrivable — c'est
ce qui l'a fait préférer à la méthode du ratio (ADR 0018).

**5. Parts égales sur 41 sous-classes multi-sources, 148 ‰ du poids IPCH.** Ces
sous-classes 2018 ont plusieurs sources ECOICOP v1 et aucune source ne dit dans
quelle proportion. La répartition à parts égales est **le seul nombre inventé de
toute la méthode**. Il est borné à ces 148 ‰ (ADR 0018).

**6. Poids de Laspeyres fixes, millésime 2017.** Les poids sont un instantané
appliqué à des prix couvrant 2015 à aujourd'hui. Ils **ignorent la déformation des
budgets** pendant la période, notamment la substitution opérée face au choc
énergétique. L'IPC officiel, lui, révise ses poids chaque année : **une partie de
l'écart affiché vient de cette différence de méthode, pas du changement de
panier.** Ne pas attribuer tout l'écart à la personnalisation (ADR 0007).

**7. `CP042` traité par `CP041` : tout propriétaire ressortira protégé.** De
`2019-12` à `2026-03`, `CP041` fait **+10,2 %** contre **+19,3 %** pour
l'ensemble — effet des loyers encadrés. Comme `CP042` pèse jusqu'à 169 ‰ et reçoit
cet indice, tout profil de propriétaire apparaîtra mécaniquement moins exposé à
l'inflation. **C'est un résultat de la régulation du marché locatif, pas une
mesure du vécu des propriétaires** (ADR 0005).

**8. Les seuils de quintile ne viennent pas de l'enquête des poids.** Les
quintiles HBS sont calculés à l'intérieur de l'échantillon HBS ; les seuils
`ilc_di01` viennent d'**EU-SILC**. Placer quelqu'un dans un quintile HBS avec des
seuils SILC est une approximation acceptée — le projet assume l'imprécision,
jamais l'invention (ADR 0012).

**9. La position dans la distribution est supposée stable dans le temps.** Le
visiteur déclare son revenu d'aujourd'hui ; les poids datent de 2017. Lui demander
son revenu de 2017 serait absurde. On suppose donc que sa place relative n'a pas
changé. C'est une hypothèse, pas une mesure (ADR 0012).

**10. Les carburants ne sont pas pondérés par les volumes vendus.** Aucun volume
n'est publié. Une moyenne sur les stations donne le même poids à une station
d'autoroute et à un hypermarché. **L'INSEE, lui, pondère** (ADR 0014).

**11. Le tarif réglementé est un barème, pas un prix.** `abonnement + kWh ×
consommation` : en faire un indice suppose un profil de consommation, qui est un
choix de l'Observatoire (section 6). Et il **ne couvre que les ménages restés au
tarif réglementé** (ADR 0014, ADR 0017).

**12. L'agrégation communale des loyers est pondérée par le nombre de logements,
pas par la surface louée.** Le recensement ne publie aucune variable de surface,
seulement un nombre de pièces non ventilé par statut d'occupation. La pondération
retenue **sous-pondère les communes à grands logements** (`docs/SOURCES.md`).

**13. `CP01` est annuel : onze valeurs mensuelles sur douze sont calculées.**
Quatre collectes par an, une publication annuelle, interpolation linéaire entre
points publiés. Toutes marquées `interpole` (ADR 0015, ADR 0019).

**14. Le covid est linéarisé sur `CP041`.** Une droite entre 2018 et 2022 suppose
une évolution régulière des loyers d'annonce, alors que la période a connu des
mouvements réels — desserrement urbain, gel dans les zones encadrées. **Le sens de
l'erreur est inconnu** (ADR 0016).

**15. La shrinkflation et l'ajustement hédonique ne sont ni corrigés ni
mesurés.** L'INSEE ne publie aucune série sans ajustement hédonique et n'en publie
pas l'ampleur : **il n'y a rien à soustraire**. Produire un tel indice supposerait
un coefficient arbitraire, ce qui ferait basculer le projet du côté militant.
Réversible si une estimation chiffrée, publiée et citable apparaît (ADR 0003).

**16. Des paramètres non affichés influencent des chiffres affichés.** Le lecteur
qui veut savoir d'où sort un pourcentage doit ouvrir ce document (ADR 0017).

**17. L'indice Observatoire démarrera plus tard que les quatre autres.** Sa
couverture est plafonnée par ses sources les plus courtes. **La courbe sera plus
courte, et l'interface doit le montrer, pas le masquer** (ADR 0009).

**18. L'indice 3 démarre en 2019-01, pas en 1996.** Sur les 234 postes INSEE
pondérés, deux (`CP06310`, `CP10102`, exclus du panier ci-dessus) publient une
série trop récente, mais **d'autres postes réellement inclus dans le panier
ont eux aussi une série qui débute après 1996** sans être exclus (leur poids
est présent à `2019-12`, la référence, donc `rebaser` les accepte). La
première période où les 232 postes restants ont tous une valeur est `2019-01`
— vérifié le 22/08/2026, identique pour les cinq quintiles. La courbe indice 3
n'a donc que 91 points, contre 367 pour l'IPC officiel et l'IPCH. Même
principe que la limite 17 : **la courbe est courte, l'interface le montre**.

---

## 9. Traçabilité et obligations

Toute donnée chiffrée provient d'une source listée dans `docs/SOURCES.md`, avec
URL exacte, date de consultation, format et licence.

Les chiffres publiés sans API vivent dans `data/manual/releves.csv`, versionné,
schéma validé au chargement : **une ligne sans `source_url`, `periode` ou
`qualite` est rejetée, pas silencieusement ignorée**. Aucune valeur numérique de
prix ou d'indice n'est écrite dans le code (ADR 0004).

La colonne `qualite` prend trois valeurs — `api_ouverte`, `etude_publiee`,
`synthese_presse` — définies dans `CONTEXT.md`, et **remonte jusqu'à l'interface
sous forme de badge par poste**.

### Obligations légales, vérifiées le 21/08/2026

Deux sources de l'indice Observatoire portent la licence `notspecified` sur
data.gouv (CRE, et Carte des loyers pour 2024 et 2025). **Ce n'est pas un
blocage** : l'article L322-1 du CRPA s'applique par défaut et fixe des conditions
identiques à la licence ouverte. Trois obligations, **d'interface et pas seulement
de documentation** :

1. **Ne pas altérer** — au sens de ne pas dénaturer. Transformer en indice est
   licite ; présenter un chiffre dérivé comme celui du producteur ne l'est pas.
   C'est déjà la discipline des ADR 0001 et 0002.
2. **Mentionner la source** de chaque poste.
3. **Mentionner la date de dernière mise à jour** de la donnée employée.

⚠️ **Familles Rurales relève d'un régime différent** : c'est une association
privée, pas une administration. Le L322-1 ne s'applique pas et ses dossiers de
presse sont protégés. Les **valeurs chiffrées publiées sont des faits**,
réutilisables avec mention de source ; le PDF lui-même ne doit pas être
redistribué depuis le dépôt (ADR 0019).

---

## 10. Index des décisions

| ADR | objet |
|---|---|
| 0001 | bannir le terme « inflation réelle » |
| 0002 | plusieurs indices étiquetés plutôt qu'un seul |
| 0003 | abandon de l'indice sans ajustement hédonique |
| 0004 | registre CSV pour les sources sans API |
| 0005 | équivalent-loyer pour les loyers imputés |
| 0006 | un axe de profil officiel, puis ajustement déclaré |
| 0007 | poids HBS 2017 fixes |
| 0008 | frontière pipeline / dashboard |
| 0009 | date de référence `2019-12` |
| 0010 | transposer les poids HBS en COICOP 2018 |
| 0011 | un seul axe en v1, le quintile de revenu |
| 0012 | placer le visiteur dans un quintile |
| 0013 | graphe mensuel en niveau |
| 0014 | périmètre de l'indice Observatoire en v1 |
| 0015 | interpolation des sources non mensuelles |
| 0016 | trou 2019-2021 des loyers |
| 0017 | table de paramètres de l'indice Observatoire |
| 0018 | clé de répartition de la transposition |
| 0019 | source `CP01` : Familles Rurales |
