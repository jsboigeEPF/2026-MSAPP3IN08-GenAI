# Projets 2026 — IA générative et chatbots

Dépôt de projets du cours **MSAPP3IN08 — IA générative et chatbots**, filière **apprentissage** (Paris-Cachan), EPF, année 2026-2027.

## Calendrier

La promotion apprentissage est répartie en deux groupes de TD — **TD AP3A** et **TD AP3B** — qui suivent le même programme. Le cours comporte **onze séances par groupe**, en alternance de cours magistraux et de séances de TPs préparés et présentés par les élèves, sous forme d'exercices résolus dans [CoursIA](https://github.com/jsboige/CoursIA/tree/main/MyIA.AI.Notebooks/GenAI) et soumis par Pull Request avant leur présentation.

| Séance | TD AP3A | TD AP3B |
|---:|---|---|
| 1 | lun. 12 oct. 2026, 15:45–17:45 — P916 C | lun. 12 oct. 2026, 13:30–15:30 — P916 C |
| 2 | ven. 16 oct. 2026, 08:00–10:00 — P916 C | ven. 16 oct. 2026, 10:15–12:15 — P916 C |
| 3 | lun. 26 oct. 2026, 15:45–17:45 — P911 C | lun. 26 oct. 2026, 13:30–15:30 — P911 C |
| 4 | jeu. 29 oct. 2026, 08:00–12:15 — P911 C | ven. 30 oct. 2026, 08:00–12:15 — P912 C |
| 5 | ven. 27 nov. 2026, 08:00–10:00 — P916 C | ven. 27 nov. 2026, 10:15–12:15 — P916 C |
| 6 | ven. 11 déc. 2026, 08:00–12:15 — P913 C | jeu. 10 déc. 2026, 08:00–12:15 — GA102 C |
| 7 | mar. 26 janv. 2027, 10:15–12:15 — P911 C | mar. 26 janv. 2027, 08:00–10:00 — P912 C |
| 8 | ven. 29 janv. 2027, 08:00–12:15 — P911 C | mer. 27 janv. 2027, 08:00–12:15 — P913 C |
| 9 à 11 | à programmer | à programmer |

| Étape | Échéance |
|---|---|
| Dépôt de la Pull Request finale | au plus tard **deux jours avant la soutenance** |
| Soutenance et démonstration | à la **dernière séance programmée du groupe** |

> Les dates de séances ci-dessus proviennent du calendrier EPF de l'enseignant ; un écart éventuel est signalé en séance. Les séances 9 à 11 seront programmées en fin de trimestre : pour chaque groupe, la soutenance a lieu à la dernière d'entre elles, et la Pull Request finale est attendue deux jours plus tôt.

Le projet est réalisé progressivement et doit rester démontrable tout au long du module.

## Démarrage rapide

1. Constituez un groupe — **3 personnes est le format standard**.
2. Choisissez un sujet dans le [catalogue 2026](docs/CATALOGUE.md), puis [réservez-le par une issue](https://github.com/jsboigeEPF/2026-MSAPP3IN08-GenAI/issues/new?template=inscription-groupe.yml). Un sujet ne peut être réservé que par un groupe.
3. Forkez ce dépôt sur le compte d'un membre du groupe.
4. Créez un dossier unique à la racine, nommé `groupe-<nom-court>`.
5. Copiez le contenu de [`template-groupe/`](template-groupe/) dans ce dossier.
6. Travaillez par commits réguliers sans modifier les fichiers des autres groupes.
7. Si le groupe est bloqué, ouvrez tôt une [demande d'accompagnement](https://github.com/jsboigeEPF/2026-MSAPP3IN08-GenAI/issues/new?template=demande-accompagnement.yml).
8. Ouvrez une Pull Request vers ce dépôt avant la date limite.

Les sujets libres sont possibles, mais doivent être proposés avec le [formulaire dédié](https://github.com/jsboigeEPF/2026-MSAPP3IN08-GenAI/issues/new?template=proposition-sujet.yml) et validés avant développement.

## Deux circuits de contribution distincts

- **Projet fil rouge** : le groupe développe son démonstrateur dans son fork de **ce dépôt**, puis ouvre une PR vers [`jsboigeEPF/2026-MSAPP3IN08-GenAI:main`](https://github.com/jsboigeEPF/2026-MSAPP3IN08-GenAI/pulls). Cette PR collective porte le projet évalué en soutenance.
- **TPs par groupe** : le groupe corrige des exercices dans un notebook du dépôt [`jsboige/CoursIA`](https://github.com/jsboige/CoursIA), puis ouvre une PR distincte vers `jsboige/CoursIA:main`. Ces contributions ne vont ni dans le dossier du groupe ni dans la PR du projet ; leur barème est décrit dans [TPs dans CoursIA et bonus](docs/TPS-ET-BONUS.md).

## Documents de référence

- [Catalogue des sujets 2026](docs/CATALOGUE.md)
- [Guide de réalisation et de soumission](docs/GUIDE-SOUMISSION.md)
- [Modalités d'évaluation](docs/EVALUATION.md)
- [TPs dans CoursIA et bonus](docs/TPS-ET-BONUS.md)
- [Tutoriel GitHub pour les TPs](https://github.com/jsboige/CoursIA/blob/main/docs/TUTORIEL-GITHUB-TP.md) — pas à pas pour les groupes qui découvrent GitHub (page du dépôt CoursIA, où se font les TPs)
- [Sujets réalisés lors des promotions précédentes](docs/HISTORIQUE-SUJETS.md)
- [Gabarit de dossier de groupe](template-groupe/README.md)

## Catégories du catalogue

| Code | Catégorie |
|---|---|
| A | Texte structuré, RAG et mémoire sémantique |
| B | Agents, orchestration et MCP |
| C | Génération et édition d'images |
| D | Audio et voix |
| E | Vidéo et médias composés |
| F | Plateformes conversationnelles et mise en production |
| G | Ingénierie logicielle assistée par IA |
| H | Évaluation, sécurité et fiabilité |
| I | Adaptation de modèles et inférence locale |
| J | Données, science et aide à la décision |
| K | IA responsable, gouvernance et sobriété |
| L | Applications sectorielles évaluables |

## Livrables attendus

Chaque groupe fournit au minimum :

- le code source et des instructions reproductibles ;
- un `README.md` complet ;
- un notebook explicatif avec analyses et visualisations **ou** une interface/démonstration fonctionnelle ;
- des tests adaptés au projet ;
- les slides de soutenance ;
- un fichier `.env.example` sans valeur secrète ;
- un historique Git montrant la participation des membres.

Les données volumineuses, poids de modèles, environnements virtuels, fichiers `.env` et clés API ne doivent jamais être commités.

## Ressources du cours

Les fiches renvoient aux notebooks du dépôt public [CoursIA](https://github.com/jsboige/CoursIA/tree/main/MyIA.AI.Notebooks/GenAI). Ils servent de points de départ : un projet attendu ne se limite pas à recopier un notebook, mais construit un démonstrateur, mesure ses résultats et documente ses choix.

Les accès aux services du module — assistant conversationnel en ligne, clé d'API OpenRouter, base vectorielle, transcription audio — sont regroupés dans le **document de référence du cours**, distribué en séance et publié sur la page Moodle dès sa création. Ils ne figurent pas dans ce dépôt. Les clés restent réservées au cours et ne se diffusent pas en dehors.

## Licence

Le contenu pédagogique de ce dépôt est distribué sous [licence MIT](LICENSE). Chaque groupe reste responsable des licences des modèles, données, bibliothèques et médias qu'il utilise.
