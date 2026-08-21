# Registre CSV versionné pour les chiffres sans API

L'indice Observatoire s'appuie en partie sur des chiffres publiés sans API
(synthèses d'études, baromètres de presse). Les écrire en constantes Python
rendrait le pipeline irrejouable et les données ni auditables ni diffusables.

Ces chiffres vivent donc dans `data/manual/releves.csv`, versionné, avec un
schéma obligatoire validé au chargement : une ligne sans `source_url`, `periode`
ou `qualite` est rejetée, pas silencieusement ignorée. Aucune valeur numérique de
prix ou d'indice n'est écrite dans le code.

La colonne `qualite` prend trois valeurs — `api_ouverte`, `etude_publiee`,
`synthese_presse` — et remonte jusqu'à l'interface sous forme de badge par poste,
pour que le lecteur voie sur quoi repose chaque morceau de l'indice.
