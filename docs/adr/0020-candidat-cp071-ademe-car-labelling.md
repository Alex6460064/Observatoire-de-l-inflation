# Candidat `CP071` : ADEME Car Labelling — archivage sans adoption

Session du 23/08/2026 : recherche de sources propres pour étendre l'indice
Observatoire au-delà des quatre postes de l'ADR 0014, en priorisant par poids
HBS. `CP071` achat de véhicules (54,3 ‰ moyen, 32 à 80 ‰ selon quintile) est le
plus lourd des postes non couverts après le résiduel de `CP04`.

## Ce qui a été vérifié

Le jeu de données `ademe-car-labelling` (data.gouv.fr / data.ademe.fr) a été
téléchargé et inspecté directement, pas seulement lu sur sa page de
présentation :

- Licence Ouverte (Etalab).
- CSV de 3604 lignes, une version commercialisée par ligne. Colonne
  `Prix véhicule` (51ᵉ colonne) **présente et remplie sur 3604/3604 lignes** —
  un résultat de recherche affirmait ce champ sans que la page primaire
  (glossaire ADEME) le confirme ; vérifié directement sur le fichier, pas pris
  sur parole.
- Encodage réel : UTF-8 avec BOM (confirmé caractère par caractère, `é` =
  U+00E9) — la page `carlabelling.ademe.fr/index/glossaire` et le CSV
  s'accordent.

## Le problème structurel

L'API `data-fair` sous-jacente (`data.ademe.fr`) répond `"history": null` :
le fichier est **écrasé en place** à chaque mise à jour, pas de version
antérieure accessible. Aucune archive datée n'a été trouvée ailleurs
(recherche web infructueuse).

Or la date de référence du projet est `2019-12` (ADR 0009). Une source qui ne
la couvre pas n'est pas une nouvelle limite mineure : c'est exactement le cas
déjà tranché par l'ADR 0019 pour « Point conso » sur `CP01` — *« un indice
ancré en 2019-12 serait en IPCH sur toute la flambée de 2021-2023, c'est-à-dire
vide de sens »*. Et l'ADR 0019 renvoie explicitement le remède — un **raccord
de sources** entre IPCH et série propre à partir d'une date de bascule — à
« une v2 qui accepterait » cette méthode. Elle n'est validée nulle part dans
`docs/METHODOLOGIE.md` aujourd'hui.

`CLAUDE.md` interdit de coder une formule d'indice non validée dans
`docs/METHODOLOGIE.md`. Le raccord de sources n'y est pas. `CP071` ne peut donc
pas devenir un poste `sources propres` de l'indice Observatoire cette session.

## Décision

**Ne pas adopter `CP071` maintenant. Démarrer l'archivage trimestriel dès
aujourd'hui**, pur exercice de collecte (aucun calcul, aucune formule) :

- `collecte.ademe.fetch_ademe_carlabelling()` télécharge le CSV courant et
  écrit un instantané daté dans `data/raw/` (`ademe_carlabelling_AAAA-MM-JJ.csv`).
- Aucune table `processed`, aucun poste `CP071` dans `poids.csv` ou
  `prix.csv` : rien à assembler tant que le raccord n'est pas tranché.
- Sans cette capture, le millésime `2026-Q3` — le seul accessible, faute
  d'archive rétroactive — serait perdu avant même qu'une méthodologie existe
  pour l'utiliser.

C'est la même logique que l'ADR 0016 appliquée à l'envers : là, un trou
passé qu'on ne peut pas combler ; ici, un trou qui s'ouvrirait *dès demain*
si personne ne capture aujourd'hui.

## Pourquoi celle-là plutôt que les autres candidats évalués

| candidat | licence / accès | historique | verdict |
|---|---|---|---|
| **ADEME Car Labelling** | Licence Ouverte, CSV | aucun, écrasé en place | retenu pour archivage seul |
| Institut Mobilités en Transition + C-Ways, baromètre | licence non précisée, rapport PDF | 2 éditions (2024, 2025) | pas de série exploitable |
| Argus, La Centrale, AAA DATA | commercial, pas d'API | — | citation presse au mieux |
| GitHub `ziraax/Car_Labelling_Data_Analysis` | mirror du même ADEME | idem ADEME | n'ajoute rien |

## Réserves, destinées à `docs/METHODOLOGIE.md` le jour où `CP071` sera adopté

**Le prix n'est pas pondéré par les ventes réelles.** Une moyenne simple sur
les 3604 versions commercialisées donne le même poids à une Dacia Sandero
qu'à une Ferrari — aucun volume de vente n'est publié dans ce jeu de données.
Même défaut, déjà documenté pour `CP072` (limite 10 de `docs/METHODOLOGIE.md`,
ADR 0014) : *« L'INSEE, lui, pondère. »*

**La nature exacte de `Prix véhicule` n'est pas confirmée.** Le glossaire
ADEME ne définit pas ce champ ; la seule mention trouvée dit que l'UTAC
fournit un « prix de vente » en amont, sans préciser TTC, bonus-malus déduit,
ou prix catalogue avant remise concessionnaire. `# TODO: à vérifier avant tout
calcul d'indice — à confronter au « lexique des données » (fichier Word) que
la fiche data.gouv.fr référence sans le donner en ligne.`

**Cadence réelle non confirmée.** La fiche annonce une mise à jour « 2 fois
par an » ; le site `carlabelling.ademe.fr` annonce une actualisation
trimestrielle (janvier, avril, juillet, octobre). Les deux ne peuvent pas
être vraies en même temps — à trancher à la deuxième capture, par
comparaison directe des dates de mise à jour observées.

## Ce qui reste à trancher avant tout code d'indice

1. La règle de raccord de sources elle-même (IPCH avant la première capture,
   série propre après) — proposée nulle part encore, à valider dans
   `docs/METHODOLOGIE.md` avant d'être codée.
2. La nature exacte du champ `Prix véhicule`.
3. La cadence réelle de mise à jour de la source.
4. Le retraitement éventuel de l'hétérogénéité de gamme (une moyenne simple
   sur 3604 versions n'est pas un panier).

## Ce qui n'a pas été retenu du tout

Recherche menée en parallèle sur `CP11` (restauration/hôtellerie, 58,7 ‰) et
`CP12`/`CP13` (assurance et services divers, 137 ‰ combiné) — détail dans
`docs/SOURCES.md`. Aucun candidat retenu :

- `CP11` : rien d'indépendant et gratuit trouvé. Les baromètres MKG/STR/UMIH
  sont commerciaux, diffusion PDF sans open data ; la seule série ouverte
  trouvée (Banque de France Webstat) republie l'IPCH officiel, donc
  n'apporte aucune indépendance. Reste sur l'IPCH, aucune action.
- `CP12`/`CP13` : France Assureurs (« données clés ») publie une série
  annuelle réelle (`Prime moyenne HT`, 2020-2024, auto et habitation) mais
  sous un régime de reproduction « strictement interdite sans autorisation
  écrite préalable » — un régime plus restrictif que celui déjà accepté pour
  NielsenIQ/Circana (ADR 0004, ADR 0019). Décision : citable en prose dans
  `docs/METHODOLOGIE.md` avec attribution (droit de courte citation), jamais
  intégrée à `data/manual/releves.csv` comme série redistribuée. Pas un
  cinquième poste de l'indice Observatoire tant qu'un accord écrit n'existe
  pas.
