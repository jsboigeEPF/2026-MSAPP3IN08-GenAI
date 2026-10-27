# Protocole A6, version 1.0

## Question

Dans quelle mesure une consigne structurée, qui énumère les faits à conserver, améliore-t-elle le contrôle d’un attribut sans dégrader le sens, par rapport à une consigne simple ? Le traitement expérimental comprend donc **la structure et l’accès explicite aux faits**, pas uniquement une mise en forme.

## Corpus et référence

40 textes synthétiques originaux, huit domaines et trois faits de référence par texte, écrits avant les appels. Les textes contiennent des dates, quantités, négations et conditions. Les introductions volontairement lourdes laissent une possibilité de compression sans retirer les faits. Cela rend aussi le corpus plus homogène qu’un corpus réel.

Un texte sur cinq de chaque domaine est marqué `dev` (8 textes) ; les 32 autres sont marqués `test`. Les essais techniques préalables utilisent uniquement T01 (`dev`). Les objectifs et seuils sont fixés dans le code avant la campagne finale ; aucune optimisation sur les 32 textes de test n’est revendiquée. Les 40 textes sont conservés dans le rapport détaillé.

## Conditions appariées

Chaque texte produit quatre variantes **indépendantes** pour chaque méthode : longueur, lisibilité, registre, ton. Les quatre variantes partagent un appel de génération, ce qui peut créer une dépendance entre elles. Les deux méthodes utilisent le même modèle, la même température (0), les mêmes objectifs et la même limite de sortie.

- Baseline : consigne courte, objectifs et conservation du sens.
- Structurée : mêmes objectifs, faits explicitement listés, priorité aux faits, interdiction d’inventer, attention aux négations et aux conditions.

40 textes × 4 attributs × 2 méthodes = 320 réécritures prévues, 80 appels de génération et 40 appels d’évaluation. Le cache évite de repayer les requêtes identiques. Une température nulle ne garantit pas une sortie identique lors d’une nouvelle requête.

## Mesures et réussite conjointe

| Attribut | Mesure | Objectif prédéfini |
|---|---|---|
| Longueur | Rapport mots sortie / mots source | 0,65 ± 0,15 |
| Lisibilité | Flesch adapté au français, textstat configuré `fr` | Gain d’au moins 10 points |
| Registre | Juge, échelle 1 à 5 | Score ≥ 4 et gain ≥ 1 point par rapport à la source |
| Ton | Juge, chaleur échelle 1 à 5 | Score ≥ 4 et gain ≥ 1 point par rapport à la source |

La similarité sémantique de cette campagne est **une estimation du juge entre 0 et 1**. Aucun score lexical ou indice de lisibilité n’est présenté comme une similarité d’embeddings. Le client contient une option d’embeddings compatible, non utilisée dans cette campagne : le compte de cours ne liste pas de modèle d’embeddings autorisé. Un vrai calcul cosinus pourra compléter l’évaluation si un service autorisé devient disponible.

Un succès conjoint estimé exige : objectif de l’attribut atteint **ET** aucun fait omis **ET** aucune contradiction **ET** aucun ajout factuel **ET** mêmes nombres écrits en chiffres **ET** similarité jugée ≥ 0,85. Une information perdue entraîne donc un échec même si le style est atteint. La comparaison des nombres est conservatrice et peut rejeter un nombre écrit en lettres.

Les taux d’attribut et de succès conjoint incluent les erreurs API dans leur dénominateur prévu. Le taux de dérive factuelle utilise les sorties effectivement évaluées et affiche ce dénominateur. Une réponse manquante n’est jamais évaluée comme fidèle. Les champs inconnus ne sont pas remplacés par des scores favorables.

## Juge et revue humaine

Le juge est un modèle distinct du générateur. Il ne reçoit ni le nom de la méthode ni l’objectif demandé et évalue toutes les propriétés. L’ordre de huit variantes est mélangé avec une graine fixe par texte. Il donne ses scores, les faits manquants et une raison courte.

Cette séparation réduit certains biais, sans constituer une validation. Les échelles de style restent subjectives. Le rapport signale aussi les sources pour lesquelles le juge attribue des scores initiaux différents selon les variantes, ce qui révèle une incohérence du juge.

**La revue humaine n’est pas encore faite.** Seize réécritures sont tirées avec une graine fixe, deux par attribut et méthode sans filtrage sur la réussite. L’interface masque le nom de la méthode et les verdicts du juge. Un membre lit la source, les faits et la sortie, puis note registre, chaleur, fidélité et similarité. Idéalement, le second membre note les mêmes cas indépendamment avant discussion des désaccords.

`validate-human` refuse les champs vides et calcule les erreurs absolues moyennes sur les scores, ainsi que l’accord sur la fidélité. À titre de repères fixés avant annotation : MAE de style ≤ 1 point, MAE de similarité ≤ 0,15 et accord de fidélité ≥ 80 %. Ce sont des critères de diagnostic d’un petit échantillon, pas une preuve de généralisation. En cas de désaccord, examiner les cas puis réviser le juge sur le développement uniquement ; toute nouvelle campagne sera identifiée comme telle. Aucun taux final validé ne doit être revendiqué avant cette étape.

## Analyse et incertitude

Comparaison appariée par texte, pour chaque attribut. L’intervalle descriptif à 95 % utilise 2 000 rééchantillonnages bootstrap des textes de test avec une graine fixe. Il ne tient pas compte des erreurs de mesure du juge ni de la diversité limitée des domaines. Il n’est pas assimilé à une preuve causale sur tous les textes français.

Les échecs sont conservés dans `benchmark.json` et affichés en premier dans `rapport.html`. Les pilotes ayant échoué restent dans le journal séparé et ne sont pas mélangés à la campagne finale.

## Extensions

Les contraintes combinées, contradictoires et la réécriture itérative sont hors du MVP livré. Elles ne doivent pas être annoncées comme mesurées. Le cas contradictoire « conserver tous les faits dans un texte trop court » est abordé comme une limite : la fidélité prime et la contrainte de longueur doit alors compter comme non atteinte.

## Références

- Fiche A6 du catalogue du cours et commentaire de validation : https://github.com/jsboigeEPF/2026-MSAPP3IN08-GenAI/issues/7
- textstat, support du français et limites des indices : https://github.com/textstat/textstat
- CTRL, génération conditionnée : https://arxiv.org/abs/1909.05858
- Sentence-BERT, similarité par représentations : https://arxiv.org/abs/1908.10084 (méthode de référence, non exécutée ici)
- QAGS, vérification factuelle : https://arxiv.org/abs/2004.04228 (inspiration de la séparation sens/faits, pas une réimplémentation)
- API et coût mesuré : https://openrouter.ai/docs/api/reference/overview
