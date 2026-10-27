# Analyse des premiers résultats

Les chiffres sont des mesures de la campagne enregistrée. Les évaluations de style et de fidélité restent **provisoires**, en attente de revue humaine.

## Comparaison sur les 32 textes de test

| Attribut | Simple : succès conjoint estimé | Structurée : succès conjoint estimé | Dérive estimée simple / structurée |
|---|---:|---:|---:|
| longueur | 16/32 | 0/32 | 9/32 / 2/32 |
| lisibilite | 15/32 | 23/32 | 16/32 / 4/32 |
| registre | 5/32 | 3/32 | 22/32 / 8/32 |
| ton | 12/32 | 14/32 | 20/32 / 13/32 |

## Ce que ces résultats suggèrent

La consigne structurée réussit mieux la simplification dans cet échantillon et le juge estime moins de dérives factuelles pour les quatre objectifs. Elle ne domine pas toutes les mesures : pour la longueur, elle produit des sorties trop courtes par rapport à la cible de 65 % ± 15 %. La consigne qui demande de retirer les introductions sans information encourage probablement une compression excessive. Cette explication est une hypothèse à vérifier, pas un mécanisme démontré.

Le registre reste difficile à faire progresser, car les sources ont déjà un registre professionnel. Le gain minimum d’un point rend la cible exigeante. Le ton chaleureux peut aussi provoquer une promesse ou une précision nouvelle. La formule de politesse seule n’est pas comptée comme un fait ajouté.

La comparaison porte sur une consigne structurée **avec faits listés** : il ne faut pas attribuer les différences uniquement aux titres ou à l’ordre des instructions.

## Cas utiles à discuter à l’oral

- T15, structurée, ton : la réécriture maintient la date et le programme, mais ne rappelle pas explicitement que la durée ne change pas. Le juge signale cette perte. C’est un exemple de tension entre chaleur et fidélité.
- T02, simple, lisibilité : « pièce justificative » devient « preuve d’identité », ce qui ajoute une restriction non justifiée par la source.
- T20, simple, ton : le juge signale une omission de l’ouverture à 8 heures alors que « de 8h à 19h » figure dans la sortie. Cette observation de revue assistée révèle un **faux signal possible du juge** et doit être examinée dans la revue humaine. On ne corrige pas silencieusement le score pour améliorer le résultat.

## Contrôle du juge

Huit cas synthétiques à perturbations connues (identité, omission, négation inversée, quantité et date modifiées, promesse ajoutée, faits seuls, instruction parasite) donnent 8/8 verdicts de fidélité attendus dans `controle_juge_synthetique.json`. Ce test de contrôle ne remplace pas une validation sur de vraies réécritures annotées par les membres du groupe.

## Ce qui empêche encore une conclusion définitive

La revue humaine des 16 cas n’est pas faite. Le corpus est synthétique, avec des introductions proches et seulement trois faits par texte. Une génération par condition ne mesure pas la variabilité. La similarité est notée par un juge, sans embeddings dans cette campagne. Les intervalles bootstrap sont descriptifs et n’intègrent pas l’erreur du juge.

Une amélioration future consisterait à donner une plage de mots explicite, puis à tester une itération de correction sur les huit textes de développement avant une nouvelle évaluation identifiée comme telle. La campagne actuelle n’a pas été remplacée après observation des échecs.
