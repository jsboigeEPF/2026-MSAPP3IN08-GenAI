# Vérification humaine des annotations du corpus réel

Les 80 questions de `data/real/questions.jsonl` portent le champ `"annotation": "claude-code, à vérifier par le groupe"`.
Elles ont été rédigées par l'agent à partir de planches-contact (1 et 2 images/s, fenêtres à 5 images/s), **sans
visionnage de la vidéo**. Chaque question doit être vérifiée par un membre du groupe dans un lecteur vidéo.

Procédure pour chaque question :

1. Lire les 3 formulations : demandent-elles bien la même chose ?
2. Vérifier la bonne réponse et que les 3 distracteurs sont faux.
3. Vérifier la fenêtre `evidence` (en secondes).
4. Si besoin, corriger `questions.jsonl`, puis passer le champ `annotation` à `"vérifiée par @pseudo"`.

Pour mesurer l'accord entre annotateurs, faire vérifier 20 questions par **deux** membres, sans se concerter,
et noter les désaccords.

| Clip | Vérifié par | Questions corrigées | Désaccords / remarques |
|---|---|---|---|
| real02 | | | |
| real03 | | | |
| real06 | | | |
| real09 | | | |
| real11 | | | |
| real12 | | | |
| real13 | | | |
| real15 | | | |
| real16 | | | |
| real17 | | | |
| real18 | | | |
| real21 | | | |
| real22 | | | |
| real23 | | | |
| real24 | | | |
| real25 | | | |
| real26 | | | |
| real28 | | | |
| real30 | | | |
| real33 | | | |

Questions jugées les plus incertaines par l'agent (à vérifier en priorité) :

- `real13_counting` : nombre de pressions sur la bouteille (une 3e approche commence à 29 s) ;
- `real21_counting` : nombre de passages à gauche (période estimée à 6 s) ;
- `real28_counting` : nombre de poissons travaillés ;
- `real16_fleeting` et `real16_causality` : « masse sombre » et mouvement de caméra vers 4–5 s ;
- `real22_causality` : caméra embarquée derrière le tramway (« phantom ride ») ;
- `real26_causality` : raison de la présence de la foule.
