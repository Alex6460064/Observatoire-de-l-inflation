# Clé de répartition de la transposition HBS → COICOP 2018

L'ADR 0010 a décidé de transposer les poids HBS en COICOP 2018. Il ne disait pas
**comment**, parce que la table de correspondance n'avait pas encore été lue.
Elle l'est maintenant (`docs/SOURCES.md`), et elle **ne porte aucune colonne de
part** : elle dit où va un poste, jamais combien. La clé doit donc venir
d'ailleurs, et le choix de cette clé déplace un huitième du panier.

## Ce qui est en jeu, mesuré

HBS FR 2020 est renseigné au niveau groupe : 47 groupes, somme 1000 ‰. Face à la
correspondance, **48 à 49 % du panier repose sur des groupes qui éclatent** vers
plusieurs postes 2018, selon le quintile. Ce n'est pas un cas marginal.

Une partition fermée sous la correspondance — qui n'exigerait aucun découpage — a
été cherchée et n'existe pas : 34 groupes 1999 s'agglomèrent en un unique bloc de
576 ‰. Il faut donc trancher.

## Décision

Le poids HBS de chaque groupe 1999 est **découpé au prorata des poids d'articles
de l'IPCH ECOICOP ver. 2 France** (`prc_hicp_iw`, année 2020) des sous-classes
2018 issues de ce groupe. La masse de chaque groupe est conservée.

Les poids IPCH servent **uniquement de clé de répartition à l'intérieur d'un
groupe, jamais de niveau**. C'est la propriété qui borne l'erreur : une clé
inexacte redistribue à l'intérieur du groupe et ne peut pas déformer son total.

Cas particuliers :

- **41 sous-classes 2018 ont plusieurs sources 1999** (148 ‰ du poids IPCH
  France). Aucune source ne dit dans quelle proportion. Leur poids IPCH est
  réparti **à parts égales** entre leurs sources. C'est le seul nombre inventé de
  la méthode ; il est borné à ces 148 ‰ et doit figurer dans les limites.
- **`CP042` loyers imputés** n'a aucune contrepartie dans l'IPCH. Son poids
  traverse sans découpage : `04.2` est bijectif dans la correspondance. Le prix
  qu'on lui applique est traité par l'ADR 0005.

## L'alternative écartée, et pourquoi

**Méthode du ratio** : ne pas découper les poids HBS, mais partir des poids IPCH
et les déformer par le ratio quintile / national (`hbs_str_t223` sur
`hbs_str_t211`). Elle a un avantage réel — les poids restent cohérents avec les
indices de prix qu'ils pondèrent, puisqu'ils viennent du même producteur — et les
sous-classes multi-sources n'y affectent qu'un ratio borné, pas une masse.

Les deux méthodes ont été codées et comparées sur les données réelles. Écart
total : **248 ‰ en valeur absolue, soit 124 ‰ de panier qui atterrit ailleurs.**

Poids QU3, en pour mille :

| poste | ratio | prorata | HBS brut |
|---|---|---|---|
| `01.1` alimentation | 135 | 145 | 143 |
| `04.1` loyers réels | 65 | 71 | 71 |
| `04.5` énergie logement | 48 | 46 | 46 |
| `07.2` carburants | **94** | 59 | 58 |
| `12.1` assurances | **34** | 82 | 82 |
| `07.1` achat de véhicules | 29 | 49 | 49 |

L'écart vient de deux différences de périmètre, qui disent la même chose :

- **Assurances** : HBS enregistre la prime brute, l'IPCH le seul service
  d'assurance (prime moins indemnités). 82 ‰ contre 34 ‰.
- **Carburants** : HBS compte les loyers imputés dans son total, l'IPCH ne les
  compte pas. Tous les poids IPCH sont donc gonflés par construction, et la
  méthode du ratio hérite de ce gonflement.

La méthode du ratio exprime le budget dans le périmètre de l'IPCH ; le prorata
l'exprime dans celui de l'enquête. Annoncer 94 ‰ de carburant à un ménage dont
l'enquête dit 58 ‰ est indéfendable sur une interface qui promet « ton panier ».
S'y ajoutent l'injection manuelle de `CP042` puis une renormalisation, exactement
le traitement spécial que l'ADR 0005 cherchait à éviter.

La recommandation initiale était la méthode du ratio. Les chiffres l'ont
renversée : c'est elle qui éloigne le plus le panier affiché de ce que l'enquête
a mesuré, et elle exige davantage de rustines non sourcées.

## Le coût assumé, à écrire dans les limites

Le prorata laisse une **incohérence de périmètre entre poids et prix** : appliquer
82 ‰ mesurés en primes brutes à un indice de prix qui suit le coût du service
surpondère une série qui n'évolue pas comme la dépense. Le défaut est réel,
unique, et écrivable — c'est ce qui l'a fait préférer.

Deux entrées pour la section « Limites » de `docs/METHODOLOGIE.md` :

1. incohérence de périmètre poids HBS / prix IPCH, cas le plus lourd : les
   assurances ;
2. parts égales sur les 41 sous-classes multi-sources, 148 ‰ du poids IPCH.
