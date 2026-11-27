# Commencer par ici

## Voir ce qui a été fait, sans coder

Ouvrir `results/rapport.html` dans un navigateur. Les résultats sont enregistrés : aucune clé ni connexion nécessaire. Le tableau compare les deux méthodes. Déplier un cas pour voir la source, les trois faits, la réécriture réelle et les contrôles.

Ouvrir `results/review.html` pour la revue humaine. Lire les 16 cas, compléter les quatre notes puis exporter le CSV. Ne pas remplir au hasard : cette revue est la vérification indépendante demandée par le professeur. Envoyer le CSV à l’assistant permettra de calculer l’accord avec le juge. Aucune validation humaine n’est déjà revendiquée.

## Lancer la démo locale sur Mac

Depuis le Terminal, ouvrir le dossier `groupe-cerise-sur-le-ghetto`, puis :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONPATH=src python -m a6 serve
```

Ouvrir `http://127.0.0.1:8765`. Choisir un texte et un objectif, puis « Afficher l’essai enregistré ». Ce bouton ne facture aucun appel.

Pour une nouvelle génération, renseigner la clé du cours dans le fichier local `.env` (jamais dans GitHub). Copier `.env.example` comme base. Le fournisseur et les modèles utilisés pour la campagne sont documentés dans le README. La clé ne doit être envoyée ni dans un message public, ni dans une capture.

## Ce qu’il reste à faire à deux

1. Relire le fonctionnement et les résultats, puis annoter les 16 cas de revue. Le second membre peut faire une revue indépendante.
2. Vérifier l’inscription d’Igor et son compte GitHub dans le classeur du cours. Aucun compte ni contribution n’a été inventé pour lui.
3. Choisir une vraie répartition des prochaines tâches et réaliser chacun ses propres commits. La préparation de ce dossier utilise l’assistance déclarée de ChatGPT/Codex.
4. Répéter la présentation avec le texte oral fourni. Les slides sont une version de travail tant que la validation humaine et les éventuels retours du prof ne sont pas intégrés.

## Pour montrer le projet au professeur

« Nous comparons deux consignes sur les mêmes textes. Nous mesurons le changement demandé, puis nous vérifions les faits. Si la réécriture devient plus courte mais retire une condition, elle compte comme un échec. Les premières mesures sont calculées ; nous devons encore vérifier le juge sur notre échantillon annoté. »

Les trois nouveaux exercices ajoutés à CoursIA par l’équipe concernent les prochains étudiants. Ils ne sont pas à résoudre pour terminer A6.
