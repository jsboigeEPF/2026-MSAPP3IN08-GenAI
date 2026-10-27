# A6 - Réécriture contrôlée par attributs

Projet G15, « Cerise sur le ghetto ». **Sujet A6 confirmé par l’enseignant sur [l’issue #7](https://github.com/jsboigeEPF/2026-MSAPP3IN08-GenAI/issues/7).** Le classeur du cours reste la référence d’inscription.

## Voir le projet

- [Prise en main sans jargon](docs/PRISE_EN_MAIN.md)
- [Rapport des 320 réécritures](results/rapport.html) : télécharger le fichier et l’ouvrir dans un navigateur ; il fonctionne sans connexion.
- [Grille interactive des 16 cas de revue humaine](results/review.html) : télécharger et ouvrir dans un navigateur.
- [Présentation PDF](slides/A6_Presentation.pdf), [PowerPoint modifiable](slides/A6_Presentation.pptx) et [texte oral](slides/Notes_orales.md).
- [Protocole détaillé](docs/PROTOCOLE.md), [analyse des résultats](docs/ANALYSE_RESULTATS.md), [données complètes](results/benchmark.json).

**État : prototype et campagne fonctionnels ; validation humaine du juge en attente. Ce n’est pas encore une remise finale de soutenance.**

## Groupe et contributions

| Compte public | État de la contribution |
|---|---|
| @cliph94 | Porteur du fork ; préparation du corpus, du code, de la campagne et des documents avec l’assistance déclarée ci-dessous |
| Second compte GitHub à confirmer | Membre du binôme G15 dans le classeur ; aucune contribution ni annotation humaine n’est attribuée artificiellement |

Chaque membre doit relire et comprendre le projet, réaliser sa propre contribution et la rendre visible dans Git. Le compte du second membre ne peut pas être deviné. Les noms civils et les adresses e-mail ne sont pas publiés dans ce dossier.

## Problématique

Une IA peut-elle raccourcir, simplifier, rendre plus formel ou plus chaleureux un message sans perdre une information ? Un résultat qui réussit le changement de style mais supprime une condition doit compter comme un échec.

## Architecture

`corpus + faits préétablis` → `consigne simple / structurée` → `générateur` → `contrôles locaux + juge distinct` → `évaluation conjointe` → `rapport + revue humaine`.

Le corpus comprend 40 textes synthétiques, huit domaines, trois faits par texte. Chaque méthode génère quatre variantes indépendantes du même texte. Le générateur est `qwen/qwen3.8-flash` ; le juge est `deepseek/deepseek-v4.1-flash`, tous deux autorisés par le compte du cours au moment de l’essai. L’ordre des variantes envoyé au juge est mélangé ; le juge ne voit pas les noms de méthodes.

Le registre et le ton sont des jugements, la longueur est un comptage, la lisibilité est un indice Flesch configuré pour le français. La similarité sémantique publiée est **estimée par le juge**, et non calculée avec des embeddings. Les nombres font l’objet d’un contrôle conservateur supplémentaire.

## Installation et démonstration

Python 3.10+ recommandé ; campagne et tests exécutés avec Python 3.12.

```bash
cd groupe-cerise-sur-le-ghetto
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONPATH=src python -m a6 serve
```

Ouvrir `http://127.0.0.1:8765`. Le bouton « Afficher l’essai enregistré » ne lance aucun appel API. Le serveur écoute uniquement sur l’ordinateur local. Les fichiers privés ne sont pas servis ; les appels live nécessitent un jeton de session et une clé configurée côté serveur.

### Appels live et configuration

Copier `.env.example` vers `.env` et renseigner localement :

- `MODEL_API_KEY` : clé du cours, jamais dans le code ou dans GitHub ;
- `MODEL_BASE_URL` : `https://openrouter.ai/api/v1` pour cette campagne ;
- `GENERATOR_MODEL` : `qwen/qwen3.8-flash` ;
- `JUDGE_MODEL` : `deepseek/deepseek-v4.1-flash`.

Les valeurs sont à compléter : les lignes vides du fichier d’exemple ne sont pas une configuration active. Le client emploie les valeurs par défaut quand ces variables sont absentes. Le modèle d’embeddings est optionnel et non utilisé dans la campagne.

```bash
PYTHONPATH=src python -m a6 benchmark --limit 40 --workers 4 --budget 3
PYTHONPATH=src python -m a6 report
```

La limite `--budget` est exprimée en USD, avec une réserve conservatrice de 0,05 USD par appel lorsque le coût réel n’est pas encore connu. Le cache `.cache/` reste local et n’est pas versionné. Les appels identiques sont réutilisés ; supprimer le cache entraîne de nouveaux appels payants. Aucun repli silencieux vers des réponses inventées n’est effectué en cas d’erreur API.

## Résultats mesurés

320 réécritures générées, 320 évaluées après une reprise ciblée du juge sur un texte. Huit textes sont marqués développement et 32 test. Les seuils et prompts sont figés dans `docs/PROTOCOLE.md`. Les pilotes techniques utilisaient uniquement T01, un texte de développement.

| Attribut | Simple : succès conjoint estimé sur test | Structurée : succès conjoint estimé sur test |
|---|---:|---:|
| Longueur | 16/32 | 0/32 |
| Lisibilité | 15/32 | 23/32 |
| Registre | 5/32 | 3/32 |
| Ton | 12/32 | 14/32 |

**Ces taux ne sont pas encore validés par annotation humaine.** La consigne structurée réduit la dérive factuelle estimée dans les quatre catégories, mais ne satisfait pas toujours l’attribut : elle raccourcit notamment trop les textes. Une méthode n’est donc pas déclarée gagnante sur tous les critères. Un cas de faux signal du juge est conservé et discuté dans l’analyse.

Les 120 requêtes réussies uniques sauvegardées (80 génération, 40 jugement) totalisent environ **0,0408 USD** de coût renvoyé par le fournisseur. Les essais préalables et une reprise sont détaillés dans `results/JOURNAL_CAMPAGNE.md`, avec séparation des montants mesurés et des réserves. Un contrôle supplémentaire du juge sur huit perturbations synthétiques donne 8/8 réponses attendues, **sans remplacer la revue humaine demandée**.

Le rapport affiche les écarts aux cibles, le taux de dérive avec son dénominateur, la similarité estimée et les intervalles bootstrap appariés par texte. Les données et métadonnées suffisent à retrouver chaque variante, chaque référence et la provenance de chaque appel.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

20 tests au stade de cette version : corpus, références, omission malgré style correct, négation inversée, nombre modifié, gain de registre insuffisant, sortie inconnue, schéma invalide, budget nul, cache sans réseau, texte vide, rapport sans injection HTML et refus d’annotations humaines manquantes. Résultat exécuté : [results/tests.txt](results/tests.txt).

La démo HTTP a aussi été vérifiée : chargement des 40 textes, chemins privés refusés et POST sans jeton refusé. Les tests ne remplacent pas la campagne live ; celle-ci a été exécutée séparément et ses sorties sont conservées.

## Revue humaine à terminer

Ouvrir `results/review.html`, lire les 16 cas et exporter les notes en CSV. Aucune case n’est préremplie avec les jugements IA. La méthode est masquée dans l’interface et les verdicts du juge ne sont pas affichés.

```bash
PYTHONPATH=src python -m a6 validate-human chemin/annotations_humaines.csv
```

Le calcul refuse les champs vides et donne MAE sur les échelles et accord sur la fidélité. Examiner les désaccords avant toute conclusion. Le second membre peut annoter indépendamment le même échantillon. Le CSV n’a pas à contenir de nom personnel.

## Limites et plan B

Corpus synthétique assez homogène, une génération par condition, juge faillible, échantillon limité et similarité évaluée par jugement. Flesch ne mesure pas directement la compréhension. Le contrôle de nombres peut rejeter une reformulation exacte en lettres. La méthode structurée reçoit la liste de faits : le gain ne peut pas être attribué à la structure du prompt seule. Les contraintes combinées ou contradictoires et la réécriture itérative sont des extensions non mesurées dans ce MVP.

**Plan B :** ouvrir `results/rapport.html`, `slides/A6_Presentation.pdf` et les résultats JSON enregistrés, sans réseau ni clé. Ces sorties sont clairement identifiées comme enregistrées et ne sont pas présentées comme une génération en direct.

## Assistance IA, licences et références

Code, corpus synthétique, contrôles, campagnes et documents préparés avec assistance ChatGPT/Codex. Les résultats live et les erreurs sont réels ; aucune annotation humaine ni contribution du second membre n’est inventée. Le groupe doit relire le travail et être capable de l’expliquer à l’oral.

Code et corpus synthétique original : MIT, voir `LICENSE`. textstat : MIT ; pytest (développement) : MIT. Les modèles sont utilisés via une API, aucun poids ni licence de poids n’est redistribué. Les conditions du fournisseur et les modèles autorisés doivent être revérifiés avant une nouvelle campagne.

Ressources du cours : [fiche A6](https://github.com/jsboigeEPF/2026-MSAPP3IN08-GenAI/blob/main/docs/CATALOGUE.md#a6--réécriture-contrôlée-par-attributs), CoursIA [Prompt Engineering](https://github.com/jsboige/CoursIA/blob/main/MyIA.AI.Notebooks/GenAI/Texte/02_PromptEngineering.ipynb), [Structured Outputs](https://github.com/jsboige/CoursIA/blob/main/MyIA.AI.Notebooks/GenAI/Texte/03_Structured_Outputs.ipynb), [Evaluating Generated Text](https://github.com/jsboige/CoursIA/blob/main/MyIA.AI.Notebooks/GenAI/Texte/22_Evaluating_Generated_Text.ipynb). Références externes détaillées dans le protocole : CTRL, Sentence-BERT, QAGS, textstat et documentation officielle OpenRouter.
