# Rapport — compréhension temporelle vidéo

Sources : results/essai.jsonl

## Accuracy (par formulation, IC 95 % Wilson)

| model | strategy | k | n | acc | acc_ci | acc_order | acc_counting | acc_causality | acc_fleeting |
|---|---|---|---|---|---|---|---|---|---|
| gemini-flash-lite-or | uniform | 16 | 12 | 0.50 | [0.25, 0.75] | 1.00 | 0.00 | 0.00 | 1.00 |
| qwen-27b-or | uniform | 16 | 12 | 0.58 | [0.32, 0.81] | 1.00 | 0.00 | 1.00 | 0.33 |
| qwen-9b-or | uniform | 16 | 12 | 0.58 | [0.32, 0.81] | 1.00 | 0.33 | 1.00 | 0.00 |
| random | uniform | 16 | 12 | 0.25 | [0.09, 0.53] | 0.00 | 0.67 | 0.00 | 0.33 |

## Stabilité aux reformulations

`consistency` = même réponse sur toutes les formulations ; `robust_acc` = toutes correctes ; `fleeting_coverage` = part des questions « fugitives » où au moins une frame tombe dans la fenêtre de preuve.

| model | strategy | k | consistency | robust_acc | unparsed | errors | fleeting_coverage |
|---|---|---|---|---|---|---|---|
| gemini-flash-lite-or | uniform | 16 | 1.00 | 0.50 | 0.00 | 0.00 | 0.00 |
| qwen-27b-or | uniform | 16 | 0.50 | 0.50 | 0.00 | 0.00 | 0.00 |
| qwen-9b-or | uniform | 16 | 0.50 | 0.50 | 0.00 | 0.00 | 0.00 |
| random | uniform | 16 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Coût et latence

| model | strategy | k | cost_eur | eur_per_100q | lat_p50_s | lat_p95_s |
|---|---|---|---|---|---|---|
| gemini-flash-lite-or | uniform | 16 | 0.006 | 0.049 | 1.231 | 1.621 |
| qwen-27b-or | uniform | 16 | 0.002 | 0.013 | 1.011 | 1.566 |
| qwen-9b-or | uniform | 16 | 0.002 | 0.019 | 0.945 | 1.575 |
| random | uniform | 16 | 0.000 | 0.000 | 0.000 | 0.000 |
