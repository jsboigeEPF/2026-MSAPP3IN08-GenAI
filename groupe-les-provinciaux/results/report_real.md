# Rapport — compréhension temporelle vidéo

Sources : results/real.jsonl

## Accuracy (par formulation, IC 95 % Wilson)

| model | strategy | k | n | acc | acc_ci | acc_order | acc_counting | acc_causality | acc_fleeting |
|---|---|---|---|---|---|---|---|---|---|
| gemini-flash-lite-or | adaptive | 16 | 240 | 0.92 | [0.87, 0.95] | 0.90 | 0.81 | 1.00 | 0.98 |
| gemini-flash-lite-or | uniform | 16 | 240 | 0.89 | [0.84, 0.92] | 0.93 | 0.77 | 0.98 | 0.88 |
| qwen-27b-or | adaptive | 16 | 240 | 0.89 | [0.85, 0.92] | 0.98 | 0.68 | 0.98 | 0.96 |
| qwen-27b-or | uniform | 16 | 240 | 0.88 | [0.84, 0.92] | 0.97 | 0.72 | 0.98 | 0.88 |
| qwen-9b-or | adaptive | 16 | 240 | 0.90 | [0.86, 0.93] | 0.97 | 0.74 | 0.98 | 0.94 |
| qwen-9b-or | uniform | 16 | 240 | 0.83 | [0.78, 0.88] | 0.97 | 0.68 | 0.92 | 0.78 |
| random | adaptive | 16 | 240 | 0.24 | [0.19, 0.30] | 0.23 | 0.23 | 0.25 | 0.24 |
| random | uniform | 16 | 240 | 0.24 | [0.19, 0.30] | 0.23 | 0.23 | 0.25 | 0.24 |

## Stabilité aux reformulations

`consistency` = même réponse sur toutes les formulations ; `robust_acc` = toutes correctes ; `top_letter_share` = part de la lettre la plus souvent prédite (0,25 attendu sans biais) ; `fleeting_coverage` = part des questions « fugitives » où au moins une frame tombe dans la fenêtre de preuve.

| model | strategy | k | consistency | robust_acc | unparsed | errors | top_letter_share | fleeting_coverage |
|---|---|---|---|---|---|---|---|---|
| gemini-flash-lite-or | adaptive | 16 | 0.89 | 0.86 | 0.00 | 0.00 | 0.27 | 0.82 |
| gemini-flash-lite-or | uniform | 16 | 0.94 | 0.86 | 0.00 | 0.00 | 0.28 | 0.71 |
| qwen-27b-or | adaptive | 16 | 0.82 | 0.80 | 0.00 | 0.00 | 0.30 | 0.82 |
| qwen-27b-or | uniform | 16 | 0.85 | 0.81 | 0.00 | 0.00 | 0.28 | 0.71 |
| qwen-9b-or | adaptive | 16 | 0.81 | 0.81 | 0.00 | 0.00 | 0.27 | 0.82 |
| qwen-9b-or | uniform | 16 | 0.80 | 0.75 | 0.00 | 0.00 | 0.32 | 0.71 |
| random | adaptive | 16 | 0.06 | 0.01 | 0.00 | 0.00 | 0.30 | 0.82 |
| random | uniform | 16 | 0.06 | 0.01 | 0.00 | 0.00 | 0.30 | 0.71 |

## Coût et latence

| model | strategy | k | cost_eur | eur_per_100q | lat_p50_s | lat_p95_s |
|---|---|---|---|---|---|---|
| gemini-flash-lite-or | adaptive | 16 | 0.287 | 0.120 | 1.410 | 1.940 |
| gemini-flash-lite-or | uniform | 16 | 0.286 | 0.119 | 1.352 | 1.886 |
| qwen-27b-or | adaptive | 16 | 0.033 | 0.014 | 1.292 | 2.677 |
| qwen-27b-or | uniform | 16 | 0.032 | 0.013 | 1.206 | 2.202 |
| qwen-9b-or | adaptive | 16 | 0.060 | 0.025 | 1.333 | 2.249 |
| qwen-9b-or | uniform | 16 | 0.057 | 0.024 | 1.273 | 2.310 |
| random | adaptive | 16 | 0.000 | 0.000 | 0.000 | 0.000 |
| random | uniform | 16 | 0.000 | 0.000 | 0.000 | 0.000 |
