# Raccord de sources : IPCH avant la première capture, série propre après

Session du 23/08/2026. L'ADR 0019 (source `CP01`) et l'ADR 0020 (candidat
`CP071`) rencontrent toutes deux le même trou : une source de prix propre sans
profondeur d'historique jusqu'à la référence `2019-12`. L'ADR 0019 tranche pour
`CP01` (édition la plus ancienne comme point de départ, ancrage direct) mais
renvoie explicitement le cas général — une source qui ne démarre qu'après la
référence, sans aucune archive rétroactive possible — à « une v2 qui
accepterait cette méthode ». Cette ADR est cette v2 : elle formalise le
raccord pour `CP071` (ADEME Car Labelling, ADR 0020) et pour tout futur
candidat dans la même situation.

## Le problème

`CP071` n'a aucune archive antérieure à la première capture du pipeline
(`data.ademe.fr` répond `"history": null`, ADR 0020). Sans raccord, deux
options dégradées :

- Exclure `CP071` du panier — mais `CLAUDE.md` interdit d'exclure un poste
  pondéré autrement que par absence de source, et l'ADR 0020 documente une
  source réelle, ouverte, avec un prix effectif.
- Ancrer l'indice sur la première capture — reproduirait exactement l'erreur
  déjà écartée pour « Point conso » (ADR 0019) : un indice ancré en 2026 serait
  vide de sens comparé à une référence `2019-12`.

## Décision

**Avant la première capture `t₁` : IPCH pur.** C'est déjà le repli par défaut
de tout poste sans source propre (section 4.2 de `docs/METHODOLOGIE.md`,
ADR 0014). Aucun changement de comportement pour la période antérieure à
l'adoption.

**À partir de `t₁` : le niveau continue depuis `IPCH(t₁)`, puis chaîne sur le
ratio de la source propre entre captures successives** :

```
I(t₁)  =  I_IPCH(t₁)

I(t_k) =  I(t_{k-1})  ×  P_source(t_k) / P_source(t_{k-1})     pour k ≥ 2
```

**Entre deux captures, interpolation linéaire**, même règle que `CP01` et
`CP041` (ADR 0015) : les points intermédiaires sont marqués `interpole`,
tracés en pointillé, jamais indiscernables d'un point publié.

## Pourquoi le ratio, pas le niveau brut

La valeur absolue de la source propre (ici : moyenne non pondérée sur 3604
versions commercialisées, ADR 0020) n'est **pas comparable** au niveau IPCH —
champs différents, pondération différente, univers différent. Chaîner sur le
niveau brut introduirait un saut discontinu à `t₁` qui ne mesurerait rien
(section 5.2, `docs/METHODOLOGIE.md`, exige `I_p(t) = 100 × P_p(t) / P_p(t₀)`
sur une **même** série de prix).

Le ratio période à période de la source propre, en revanche, mesure la même
chose d'une capture à l'autre — même méthode, même univers de 3604 versions
(à composition près, cf. limite ci-dessous). C'est ce ratio, et lui seul, qui
est chaîné sur le niveau hérité de l'IPCH.

## Conséquence mécanique, pas une clause de prudence

Un ratio suppose deux points. **`CP071` ne peut donc entrer dans
`poids.csv`/`prix.csv` qu'à partir de la deuxième capture** — la première
(23/08/2026) fixe seulement `I(t₁)`, aucun ratio n'est calculable avant la
suivante. Ce n'est pas une décision distincte, c'est une conséquence directe
de la formule ci-dessus.

## Non testé chiffre par chiffre

À la différence des décisions de `docs/METHODOLOGIE.md` §3.3 (méthode du
ratio contre prorata) et §3.6, cette règle n'a **pas** été comparée sur des
données réelles avant validation — une seule capture existe, aucun ratio n'est
calculable pour la vérifier. Validée sur la forme de la formule, pas sur son
résultat. `# TODO: à confronter aux chiffres dès la deuxième capture ; si le
ratio produit un résultat aberrant (saut brutal, signe inattendu), le signaler
plutôt que corriger silencieusement — CLAUDE.md, règle anti-hallucination 4.`

## Limite héritée, à ajouter à `docs/METHODOLOGIE.md` §8 au moment de l'adoption effective

Le ratio suppose une composition stable de l'échantillon sous-jacent d'une
capture à l'autre. Pour `CP071` : les 3604 versions commercialisées à `t_k`
ne sont pas les 3604 versions de `t_{k-1}` — gammes qui sortent, gammes qui
entrent. Le ratio capture donc en partie un effet de composition, pas
seulement un effet prix pur — même famille de limite que la limite 10 déjà
documentée (carburants non pondérés par les volumes).

## Portée

Ce raccord s'applique à toute source candidate dans la même situation
structurelle : prix réel, ouvert, mais sans historique rétroactif accessible.
Ne s'applique pas à `CP01` (ADR 0019, historique rétroactif partiel existant,
raccord non nécessaire) ni à une source qui aurait une archive datée
exploitable.
