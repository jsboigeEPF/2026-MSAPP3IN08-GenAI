# Rapport — compréhension temporelle vidéo

Sources : results/synthetic.jsonl

## Accuracy (par formulation, IC 95 % Wilson)

| model | strategy | k | n | acc | acc_ci | acc_order | acc_counting | acc_causality | acc_fleeting |
|---|---|---|---|---|---|---|---|---|---|
| gemini-flash-lite-or | adaptive | 16 | 240 | 0.73 | [0.67, 0.78] | 0.88 | 0.35 | 0.68 | 1.00 |
| gemini-flash-lite-or | uniform | 16 | 240 | 0.54 | [0.48, 0.60] | 0.83 | 0.25 | 0.52 | 0.57 |
| qwen-27b-or | adaptive | 16 | 240 | 0.72 | [0.66, 0.77] | 0.75 | 0.32 | 0.80 | 1.00 |
| qwen-27b-or | uniform | 16 | 240 | 0.64 | [0.58, 0.70] | 0.82 | 0.37 | 0.80 | 0.58 |
| qwen-9b-or | adaptive | 16 | 240 | 0.73 | [0.67, 0.78] | 0.85 | 0.30 | 0.77 | 1.00 |
| qwen-9b-or | uniform | 16 | 240 | 0.62 | [0.56, 0.68] | 0.80 | 0.18 | 0.77 | 0.73 |
| random | adaptive | 16 | 240 | 0.25 | [0.20, 0.31] | 0.32 | 0.22 | 0.23 | 0.25 |
| random | uniform | 16 | 240 | 0.25 | [0.20, 0.31] | 0.32 | 0.22 | 0.23 | 0.25 |

## Stabilité aux reformulations

`consistency` = même réponse sur toutes les formulations ; `robust_acc` = toutes correctes ; `top_letter_share` = part de la lettre la plus souvent prédite (0,25 attendu sans biais) ; `fleeting_coverage` = part des questions « fugitives » où au moins une frame tombe dans la fenêtre de preuve.

| model | strategy | k | consistency | robust_acc | unparsed | errors | top_letter_share | fleeting_coverage |
|---|---|---|---|---|---|---|---|---|
| gemini-flash-lite-or | adaptive | 16 | 0.66 | 0.61 | 0.03 | 0.00 | 0.36 | 1.00 |
| gemini-flash-lite-or | uniform | 16 | 0.56 | 0.41 | 0.02 | 0.00 | 0.43 | 0.60 |
| qwen-27b-or | adaptive | 16 | 0.65 | 0.60 | 0.00 | 0.00 | 0.30 | 1.00 |
| qwen-27b-or | uniform | 16 | 0.51 | 0.46 | 0.00 | 0.00 | 0.32 | 0.60 |
| qwen-9b-or | adaptive | 16 | 0.79 | 0.68 | 0.00 | 0.00 | 0.34 | 1.00 |
| qwen-9b-or | uniform | 16 | 0.70 | 0.53 | 0.00 | 0.00 | 0.37 | 0.60 |
| random | adaptive | 16 | 0.06 | 0.00 | 0.00 | 0.00 | 0.30 | 1.00 |
| random | uniform | 16 | 0.06 | 0.00 | 0.00 | 0.00 | 0.30 | 0.60 |

## Coût et latence

| model | strategy | k | cost_eur | eur_per_100q | lat_p50_s | lat_p95_s |
|---|---|---|---|---|---|---|
| gemini-flash-lite-or | adaptive | 16 | 0.291 | 0.121 | 1.296 | 1.923 |
| gemini-flash-lite-or | uniform | 16 | 0.291 | 0.121 | 1.337 | 1.907 |
| qwen-27b-or | adaptive | 16 | 0.038 | 0.016 | 1.004 | 1.939 |
| qwen-27b-or | uniform | 16 | 0.038 | 0.016 | 1.011 | 1.960 |
| qwen-9b-or | adaptive | 16 | 0.060 | 0.025 | 1.075 | 1.868 |
| qwen-9b-or | uniform | 16 | 0.055 | 0.023 | 1.012 | 1.995 |
| random | adaptive | 16 | 0.000 | 0.000 | 0.000 | 0.000 |
| random | uniform | 16 | 0.000 | 0.000 | 0.000 | 0.000 |
