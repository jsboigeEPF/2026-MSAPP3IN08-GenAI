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

## Questions devinables sans voir la vidéo (baseline aveugle)

Ces questions ont été **réussies sans aucune image** par Gemini 3.5 Flash-Lite **et** Qwen 3.8-27B
(`results/blind_real.jsonl`). Elles mesurent surtout le bon sens ou la plausibilité des options, pas la
compréhension de la vidéo : **à réécrire en priorité** (distracteurs plus plausibles, question qui exige d'avoir vu le clip).

| Question | Bonne réponse |
|---|---|
| `real02_causality` — Pourquoi la boule de pâte devient-elle une feuille large et très fine ? | Le cuisinier l'étire et la fait tournoyer à la main |
| `real09_order` — Qu'est-ce qui passe devant la caméra juste après la locomotive verte ? | Des conteneurs jaunes marqués « AMBROGIO » |
| `real11_causality` — Pourquoi le paysage change-t-il complètement vers 13 s ? | La caméra pivote vers un chemin |
| `real11_order` — Que voit-on entre la vue des ruines du début et le chemin bétonné de la fin ? | Un cheval qui broute sous le viaduc |
| `real12_causality` — Pourquoi l'huile jaune s'écarte-t-elle du centre du bol ? | Du savon (gouttes vertes) a été ajouté au centre |
| `real13_causality` — Pourquoi le ludion descend-il dans la bouteille ? | La main serre la bouteille |
| `real13_causality_2` — Pourquoi le ludion remonte-t-il après être descendu ? | La main relâche la bouteille |
| `real13_fleeting` — Pendant un bref instant au début, la caméra montre le haut de la bouteille : de quelle couleur est le bouchon ? | Blanc / gris clair |
| `real15_causality` — Pourquoi la laisse jaune bouge-t-elle au début de la vidéo ? | Le chiot se roule et la tire avec lui |
| `real16_fleeting` — Vers 6 s, que fait brièvement le chien ? | Il baisse la tête vers le sable |
| `real16_order` — Qu'est-ce qui est filmé avant le chien ? | Un coquillage sur le sable |
| `real17_fleeting` — Vers 10–11 s, le chien tourne la tête : de quel côté regarde-t-il ? | Vers la gauche de l'image |
| `real18_fleeting` — Comment apparaît l'image pendant la toute première seconde ? | Assombrie (fondu d'ouverture) |
| `real21_causality` — Pourquoi la ficelle se plie-t-elle quand la balle passe du côté gauche ? | La ficelle bute contre la tige verticale |
| `real21_fleeting` — Vers 6 s, qu'aperçoit-on brièvement en bas à droite de l'image ? | Les doigts de la main qui se retire |
| `real21_order` — Que se passe-t-il juste après que la main lâche la balle ? | Elle part vers la gauche en se balançant |
| `real22_causality` — Pourquoi le tramway reste-t-il à peu près à la même taille dans l'image alors que la rue défile ? | La caméra roule derrière lui à la même vitesse |
| `real22_counting` — Combien de tramways voit-on circuler côte à côte vers 20 s ? | 2 |
| `real22_fleeting` — Vers 23 s, que se passe-t-il brièvement à l'image ? | Un défaut de pellicule (bande parasite) en haut de l'image |
| `real23_fleeting` — Que montre la toute première image, pendant moins d'une seconde ? | Un motif graphique tramé |
| `real23_order` — Quel est le dernier plan de l'extrait ? | Des cyclistes sur des grands-bi devant une foule |
| `real25_causality` — Pourquoi l'image est-elle souvent floue et tremblée ? | La caméra est tenue tout près d'un chat qui bouge |
| `real25_fleeting_2` — Vers 1 s, que voit-on en très gros plan ? | La tête du chat face à la caméra |
| `real25_order` — Vers 19–20 s, quand la caméra s'éloigne du chat, que montre-t-elle ? | Une fenêtre avec des plantes et une lampe allumée |
| `real26_causality` — Pourquoi une foule est-elle rassemblée sur le tarmac ? | Pour assister au débarquement de chevaux transportés par avion |
| `real28_order` — Après avoir écaillé le poisson, que fait le cuisinier ? | Il l'ouvre et le vide |
| `real33_fleeting` — Quel sous-titre s'affiche vers 5–8 s ? | Vorstellung Ponomarjow und Anand |
| `real33_order` — Quel texte apparaît en premier à l'écran ? | Chess Classic in Mainz 14.08.2002 |
