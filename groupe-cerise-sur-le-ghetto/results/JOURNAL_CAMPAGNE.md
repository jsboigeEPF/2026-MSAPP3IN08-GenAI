# Journal de campagne

Tous les essais ci-dessous utilisent uniquement des textes synthétiques. Aucun secret n’est stocké dans ces fichiers. Les erreurs ne sont pas remplacées par des sorties simulées.

| Étape | État | Coût mesuré ou réservé (USD) |
|---|---|---:|
| Pilote initial : deux générations tronquées avec raisonnement par défaut ; sorties rejetées. | 8 variantes prévues | 0.100000 |
| Pilote avec raisonnement désactivé : génération réussie, juge GLM rejetant cette option ; erreur conservée. | 8 variantes prévues | 0.050355 |
| Pilote final sur T01 : générateur Qwen et juge DeepSeek, sorties conformes. | 8 variantes prévues | 0.000575 |
| Campagne 40 textes, après reprise ciblée T13 | 320 sorties évaluées | 0.039855 |
| Contrôle synthétique du juge | 8/8 cas attendus | 0.000276 |

Les deux premiers pilotes incluent une réserve conservatrice pour des appels en échec dont le coût exact n’a pas été sauvegardé. La somme prudente de toutes les lignes reste inférieure à 0,20 USD ; ce n’est pas une facture exacte. Les requêtes réussies uniques de la campagne (y compris celles réutilisées du pilote) totalisent 0,0408 USD selon le fournisseur, dans reproductibilite.json. Les montants des lignes ne doivent pas être additionnés à ce dernier total, ce qui compterait certains appels deux fois.

La campagne a reçu une réponse de juge non exploitable au format JSON sur T13. Une seule nouvelle tentative du même jugement a été faite, en réutilisant les deux générations du cache ; les huit échecs initiaux restent dans retry_log.json. Les prompts n’ont pas changé entre la campagne et cette reprise.

Aucune optimisation n’a été effectuée sur les 32 textes de test après observation du résultat. Les échecs de longueur de la méthode structurée et les faux signaux possibles du juge restent visibles.

Le budget cible du catalogue est inférieur à 8 EUR. Le logiciel impose ici un plafond local en USD et ne fait aucune conversion monétaire implicite. Aucun budget futur n’est engagé par les résultats enregistrés.
