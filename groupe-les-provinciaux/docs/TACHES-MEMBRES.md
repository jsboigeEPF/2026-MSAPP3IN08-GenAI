# Tâches à réaliser par chaque membre

L'historique Git est noté : chaque membre doit **faire lui-même** des commits depuis son propre compte.
Les tâches ci-dessous sont de vraies contributions au projet, pas des commits de façade. Elles servent aussi
à préparer la soutenance, où chacun sera interrogé sur l'architecture, les choix et les limites.

Mode opératoire (une fois par membre) :

```bash
git clone https://github.com/Leo-Bnvl/2026-MSAPP3IN08-GenAI.git
cd 2026-MSAPP3IN08-GenAI
git checkout e2-benchmark-video-temporelle
cd groupe-les-provinciaux
pip install -r requirements.txt
python -m tvbench.synth && python -m pytest -q     # doit afficher « passed »
```

@rouautu doit être ajouté comme collaborateur du fork (Settings → Collaborators) pour pouvoir pousser.
Le membre sans compte GitHub doit **créer un compte** : la PR identifie les membres par leur pseudo.

## Tâche commune (tout le groupe) : vérifier les annotations du corpus réel

Les 80 questions de `data/real/questions.jsonl` ont été rédigées avec l'aide de Claude Code à partir de
planches-contact. **Elles doivent être vérifiées par des humains** avant d'être présentées comme vérité terrain.

1. `python scripts/annotate_helper.py sheets data/real/clips` génère une planche par clip.
2. Pour chaque question : regarder le clip dans un lecteur vidéo, vérifier la bonne réponse, la fenêtre
   `evidence` et que les 3 formulations demandent bien la même chose. Corriger si besoin.
3. Noter dans `docs/VERIFICATION-ANNOTATIONS.md` : qui a vérifié quel clip, les questions corrigées, et les
   désaccords entre vous. L'accord entre annotateurs est un bon résultat à présenter.
4. Relancer la campagne réelle sur les questions corrigées et le notebook (commandes dans le README).

Répartition proposée : clips `real00`–`real06` → @Leo-Bnvl, `real07`–`real13` → @rouautu,
`real14`–`real19` → troisième membre.

## @Leo-Bnvl — campagne et analyse

- Relire `tvbench/run.py` et `tvbench/metrics.py` ; savoir expliquer l'IC de Wilson et `robust_acc`.
- Lancer la campagne à 8 et 32 frames (en plus de 16) et ajouter au notebook la courbe exactitude/nombre de frames.
- Compléter la section « Conclusions » du notebook avec vos propres mots.

## @rouautu — échantillonnage et modèle local

- Relire `tvbench/frames.py` ; savoir expliquer la sélection adaptative et ses limites (mouvements de caméra).
- Faire tourner le 3e modèle **réellement en local** avec Ollama (`ollama pull qwen2.5vl:7b`, modèle
  `qwen-local-ollama`) sur le corpus réel, et comparer au Qwen 3.5-9B appelé par API.
- Ajouter un test pour un cas d'échec non couvert (ex. vidéo corrompue, clip introuvable).

## Troisième membre — corpus et slides

- Relire `scripts/fetch_commons.py` et `data/real/clips/manifest.csv` ; vérifier licences et attributions.
- Ajouter 2–3 questions « pièges » par catégorie si certaines sont trop faciles.
- Finaliser `slides/` : relire, adapter le discours, préparer la démo (plan B : résultats déjà calculés).

Chaque membre complète ensuite sa ligne du tableau « Groupe » et la section « Répartition du travail » du README.
