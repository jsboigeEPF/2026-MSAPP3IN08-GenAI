# Rapport — compréhension temporelle vidéo

Sources : results/smoke.jsonl

## Accuracy (par formulation, IC 95 % Wilson)

| model | strategy | k | n | acc | acc_ci | acc_order | acc_counting | acc_causality | acc_fleeting |
|---|---|---|---|---|---|---|---|---|---|
| random | adaptive | 8 | 240 | 0.25 | [0.20, 0.31] | 0.32 | 0.22 | 0.23 | 0.25 |
| random | adaptive | 16 | 240 | 0.25 | [0.20, 0.31] | 0.32 | 0.22 | 0.23 | 0.25 |
| random | uniform | 8 | 240 | 0.25 | [0.20, 0.31] | 0.32 | 0.22 | 0.23 | 0.25 |
| random | uniform | 16 | 240 | 0.25 | [0.20, 0.31] | 0.32 | 0.22 | 0.23 | 0.25 |

## Stabilité aux reformulations

`consistency` = même réponse sur toutes les formulations ; `robust_acc` = toutes correctes ; `fleeting_coverage` = part des questions « fugitives » où au moins une frame tombe dans la fenêtre de preuve.

| model | strategy | k | consistency | robust_acc | unparsed | errors | fleeting_coverage |
|---|---|---|---|---|---|---|---|
| random | adaptive | 8 | 0.06 | 0.00 | 0.00 | 0.00 | 0.90 |
| random | adaptive | 16 | 0.06 | 0.00 | 0.00 | 0.00 | 0.85 |
| random | uniform | 8 | 0.06 | 0.00 | 0.00 | 0.00 | 0.05 |
| random | uniform | 16 | 0.06 | 0.00 | 0.00 | 0.00 | 0.35 |

## Coût et latence

| model | strategy | k | cost_eur | eur_per_100q | lat_p50_s | lat_p95_s |
|---|---|---|---|---|---|---|
| random | adaptive | 8 | 0 | 0.000 | 0.000 | 0.000 |
| random | adaptive | 16 | 0 | 0.000 | 0.000 | 0.000 |
| random | uniform | 8 | 0 | 0.000 | 0.000 | 0.000 |
| random | uniform | 16 | 0 | 0.000 | 0.000 | 0.000 |
