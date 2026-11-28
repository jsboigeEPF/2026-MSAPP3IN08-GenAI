# Les Provinciaux — tvbench, benchmark de compréhension temporelle vidéo

## Groupe

| Membre | Contribution principale |
|---|---|
| @Leo-Bnvl | À compléter par l'intéressé |
| @rouautu | À compléter par l'intéressé |
| Troisième membre (compte GitHub à créer) | À compléter par l'intéressé |

**Contribution d'un agent de code (déclarée).** Claude Code a écrit le harnais (échantillonnage, adaptateurs,
métriques, tests), le corpus contrôlé, la récupération des clips Commons, une **première version des annotations du
corpus réel**, les campagnes, le notebook et le générateur de slides. Tout cela doit être relu et compris par le groupe
(voir [`docs/TACHES-MEMBRES.md`](docs/TACHES-MEMBRES.md)) ; les annotations réelles doivent être vérifiées par des
humains ([`docs/VERIFICATION-ANNOTATIONS.md`](docs/VERIFICATION-ANNOTATIONS.md)).

## Sujet

- **Identifiant du catalogue :** E2 — Benchmark de compréhension temporelle vidéo
- **Problématique :** les modèles vision-langage reçoivent une vidéo sous forme de quelques frames.
  Comprennent-ils vraiment le *temps* (ordre, comptage, causalité, événements brefs) ? Leurs réponses
  restent-elles stables quand on reformule la question ? À quel coût et avec quelle latence ?
- **MVP :** corpus libre de 20 clips Wikimedia Commons et 80 questions annotées à choix multiples, plus un corpus
  contrôlé de 20 clips scriptés et 80 questions ; deux modèles via l'espace OpenRouter du cours (Gemini 3.5 Flash-Lite
  et Qwen 3.8-27B), un troisième plus petit (Qwen 3.5-9B, taille exécutable en local) et une baseline aléatoire.
- **Extensions réalisées :** sélection adaptative de frames ; troisième modèle de petite taille ; baseline « aveugle »
  (questions posées sans image) ; test du comptage à 32 frames.
- **Notebook d'analyse** : [`notebooks/analyse_resultats.ipynb`](notebooks/analyse_resultats.ipynb) · **slides** : [`slides/soutenance.pdf`](slides/soutenance.pdf).

## Architecture

```text
clips vidéo ──► frames.py ───────────────► run.py ──────────────► results/*.jsonl ──► metrics.py ──► report.md / .csv
               (uniforme | adaptatif,      (prompt QCM horodaté,                     (accuracy/catégorie + IC Wilson,
                cache JPEG = plan B)        appel modèle, parsing,                    stabilité, couverture des frames,
                                            coût, latence, reprise,                   coût, latence p50/p95)
questions.jsonl ─────────────────────────►  plafond budgétaire)
                                                │
                                   models.py ───┘  openai_compat (OpenRouter, OpenAI, DashScope, Ollama, vLLM)
                                                   qwen_local (transformers) · random (baseline)
```

| Module | Rôle |
|---|---|
| `tvbench/frames.py` | Décodage ffmpeg, sélection **uniforme** (centre de k segments, comme Video-MME/MVBench) ou **adaptative** (couverture uniforme pour moitié + pics de différence inter-frames), cache JPEG |
| `tvbench/models.py` | Adaptateurs de modèles ; les frames sont envoyées en JPEG base64, chacune précédée de `[t=…s]` |
| `tvbench/prompts.py` | Prompt QCM et extraction robuste de la lettre de réponse |
| `tvbench/run.py` | Boucle modèles × questions × formulations, reprise, `--budget-eur`, `--dry-run` |
| `tvbench/metrics.py` | Agrégation et rapport |
| `tvbench/synth.py` | Corpus **contrôlé** de 20 clips scriptés à vérité terrain exacte |
| `scripts/fetch_commons.py` | Corpus **réel** : clips libres Wikimedia Commons, avec licence et auteur dans `manifest.csv` |
| `scripts/annotate_helper.py` | Planches-contact horodatées et validation du fichier d'annotations |
| `notebooks/analyse_resultats.ipynb` | Analyse complète et figures, rejouable hors-ligne (généré par `notebooks/build_notebook.py`) |
| `slides/build_slides.py` | Slides de soutenance générées depuis les résultats (`slides/soutenance.pdf`) |

Les 4 catégories :

| Catégorie | Exemple (corpus contrôlé) |
|---|---|
| `order` | Quel objet est apparu juste après le triangle orange ? |
| `counting` | Combien de fois la lampe s'est-elle allumée ? |
| `causality` | Pourquoi la boîte s'est-elle déplacée ? (percutée par quelle balle, ou partie seule *avant* le contact) |
| `fleeting` | Quel nombre est apparu pendant 0,28 s ? |

Chaque question existe en **3 formulations** pour mesurer la stabilité.

## Installation

```bash
pip install -r requirements.txt      # Python ≥ 3.11 ; ffmpeg/ffprobe doivent être dans le PATH
cp .env.example .env                 # puis renseigner OPENROUTER_API_KEY (clé du cours) dans .env
# .env est lu automatiquement par tvbench.run (et ignoré par git)
```

## Utilisation

```bash
# 1. Corpus contrôlé (20 clips, 80 questions, déterministe)
python -m tvbench.synth

# 2. Estimation du coût, puis campagne
python -m tvbench.run --questions data/synthetic/questions.jsonl --clips data/synthetic/clips \
    --models random gemini-flash-lite-or qwen-27b-or qwen-9b-or --dry-run
for s in uniform adaptive; do
  python -m tvbench.run --questions data/synthetic/questions.jsonl --clips data/synthetic/clips \
      --models random gemini-flash-lite-or qwen-27b-or qwen-9b-or --frames 16 --strategy $s --out results/syn.jsonl
done
python -m tvbench.metrics results/syn.jsonl --out results/report_synthetic.md

# 3. Corpus réel : reconstituer exactement les 20 clips retenus (licences dans data/real/manifest.csv)
python scripts/fetch_commons.py --from-manifest data/real/manifest.csv
python scripts/annotate_helper.py validate data/real/questions.jsonl
for s in uniform adaptive; do
  python -m tvbench.run --questions data/real/questions.jsonl --clips data/real/clips \
      --models random gemini-flash-lite-or qwen-27b-or qwen-9b-or --frames 16 --strategy $s --out results/real.jsonl
done

# 4. Baseline aveugle (aucune image) et analyse
python -m tvbench.run --questions data/real/questions.jsonl --clips data/real/clips \
    --models gemini-flash-lite-or qwen-27b-or --frames 0 --variants first --out results/blind_real.jsonl
jupyter nbconvert --to notebook --execute --inplace notebooks/analyse_resultats.ipynb
python slides/build_slides.py
```

Les modèles disponibles sont listés dans `configs/models.toml` (OpenRouter, OpenAI, DashScope, Ollama, transformers).

> **Garde-fou de l'espace OpenRouter du cours.** Seule une liste de modèles est autorisée : GPT-5-mini et
> Qwen2.5/Qwen3-VL y sont refusés (HTTP 404 « Model blocked by guardrail »). Les modèles vision autorisés
> au 27/11/2026 sont Gemini 3.5 Flash-Lite et la famille Qwen 3.5/3.8. Les modèles Qwen sont appelés avec
> `reasoning.enabled = false`, sinon ils épuisent leur budget de tokens à raisonner et renvoient une réponse vide.

## Tests

```bash
python -m tvbench.synth && python -m pytest -q
```

Résultat actuel : **18 tests passés**. Ils couvrent :

- le parsing des réponses, y compris les sorties vides, hors options et ambiguës (« C'est B ») ;
- l'échantillonnage uniforme et adaptatif (un flash de 3 frames est raté en uniforme et capturé en adaptatif) ;
- l'intervalle de Wilson ;
- l'adaptateur OpenAI-compatible, testé contre un faux serveur HTTP local (format de requête, en-tête d'authentification, calcul du coût) ;
- la validité du corpus (80 questions, 20 par catégorie, options uniques) ;
- le calcul du coût réel facturé, la lecture du `.env`, la couverture de la fenêtre de preuve.

Modes d'échec gérés :

- réponse non parsable : comptée fausse et mesurée dans `unparsed` ;
- erreurs HTTP 429/5xx : 3 essais avec back-off, puis erreur journalisée dans `errors` ; la ligne est rejouée à la relance ;
- dépassement de budget : arrêt propre, reprise possible.

## Résultats et évaluation

**Protocole.** QCM à 4 options, bonnes réponses équilibrées sur A/B/C/D ; 3 formulations par question ; 16 frames
par question, uniformes ou adaptatives ; baseline hasard (0,25). Résultats bruts dans `results/*.jsonl`, rapports
dans `results/report_*.md`, analyse et figures dans le notebook. Avec 80 questions × 3 formulations, l'IC 95 % fait
environ ±6 points par modèle et ±12 points par catégorie.

**Exactitude, 16 frames** (uniforme → adaptatif) :

| Modèle | Corpus contrôlé | Corpus réel |
|---|---|---|
| Hasard | 0,25 | 0,24 |
| Gemini 3.5 Flash-Lite | 0,54 → **0,73** | 0,89 → 0,92 |
| Qwen 3.8-27B | 0,64 → **0,72** | 0,88 → 0,89 |
| Qwen 3.5-9B | 0,62 → **0,73** | 0,83 → 0,90 |

**Par catégorie, corpus contrôlé, uniforme :** ordre 0,80–0,83 · causalité 0,52–0,80 · détail fugitif 0,57–0,73 ·
**comptage 0,18–0,37** (à peine au-dessus du hasard).

**Constats principaux**

1. **La sélection adaptative paie sur les détails fugitifs.** Sur le corpus contrôlé, une frame contient le nombre
   affiché 0,28 s dans 60 % des cas en uniforme contre 100 % en adaptatif ; l'exactitude « détail fugitif » passe de
   0,57–0,73 à **1,00** pour les trois modèles (+8 à +19 points au global). Sur le corpus réel, le gain est plus
   faible (+1 à +7 points) : les événements y sont moins brefs et les questions plus faciles (point 3).
2. **Le comptage est la faiblesse commune.** Les clignotements durent 0,35–0,6 s alors que 16 frames sur 10 s sont
   espacées de 0,625 s : une partie des événements n'est jamais vue. Avec **32 frames**, le comptage passe à **0,35–0,48** et le
   sous-comptage moyen diminue (Gemini : écart moyen prédit − vrai de −0,54 à −0,09). Le problème est donc en partie
   de **perception**, mais pas seulement : même à 32 frames, plus de la moitié des comptes restent faux.
3. **Le corpus réel est trop facile, et en partie devinable sans la vidéo.** Posées **sans aucune image**, les
   questions réelles obtiennent 0,48 (Gemini) et 0,60 (Qwen-27B), contre 0,29–0,30 sur le corpus contrôlé.
   28 questions sur 80 sont réussies à l'aveugle par les deux modèles (liste dans
   `docs/VERIFICATION-ANNOTATIONS.md`) : surtout des questions de causalité et de détail fugitif dont les distracteurs
   sont peu plausibles. Même sans elles, l'exactitude réelle reste de 0,78–0,87. Le corpus contrôlé est donc le
   plus discriminant ; le corpus réel doit être **réécrit** (distracteurs plausibles, questions qui exigent la vidéo).
4. **Stabilité aux reformulations.** Corpus contrôlé : les modèles donnent la même réponse sur les 3 formulations
   dans 51–70 % des questions seulement (uniforme) ; les 3 formulations ne sont toutes justes que pour 41–53 % des
   questions, contre 54–64 % d'exactitude moyenne. Corpus réel : 80–94 % de cohérence.
5. **Biais de lettre.** Sur le comptage contrôlé, Qwen 3.5-9B répond « D » dans 52–57 % des cas ; Gemini évite « A ».
   La lettre la plus prédite représente 0,27–0,43 des réponses selon les configurations (0,25 sans biais).
6. **Coût et latence.** Ensemble des campagnes (≈ 3 400 appels API) : **1,74 €** au total, bien sous le budget de 12 €.
   Pour 100 questions : Gemini 0,12 €, Qwen-27B 0,015 €, Qwen-9B 0,025 €. Latence médiane 1,0–1,4 s, p95 1,9–2,7 s.
   Qwen 3.8-27B offre le meilleur rapport exactitude/coût (8 fois moins cher que Gemini pour une exactitude
   comparable).

## Limites et plan B

- **Annotations du corpus réel non vérifiées.** Elles ont été rédigées par l'agent à partir de planches-contact,
  sans visionner les vidéos ; 28 questions sont devinables sans image. À vérifier et réécrire par le groupe.
- **Équilibre des catégories (corpus réel)** : 20 ordre, 23 comptage, 20 causalité, 17 détail fugitif ; plusieurs
  questions de comptage ont pour réponse « 1 » (questions de contrôle faciles).
- **Sélection des clips** : 20 retenus sur 36 téléchargés ; exclusion des enfants, des personnes filmées en gros plan
  et des clips sans événement net (motifs dans `data/real/manifest.csv`).
- **Taille** : 80 questions par corpus ; les écarts de moins de 10 points entre modèles ne sont pas significatifs.
- **Modèles imposés** par le garde-fou de l'espace OpenRouter du cours (pas de GPT-5 ni de Qwen-VL).
- **Accès aux frames** : 16 images seulement, sans audio ni vidéo native.
- **Couverture de la preuve** : calculée en considérant qu'une frame décodée à 10 images/s couvre 0,1 s.
- **Plan B pour la démo** :
  - résultats bruts versionnés : le notebook et les slides se rejouent sans réseau ;
  - baseline `random` : démontre la chaîne complète sans clé ;
  - modèle local `qwen-local-ollama` : configuré, sans API.

## Répartition du travail

À compléter par le groupe. Une répartition est **proposée** dans [`docs/TACHES-MEMBRES.md`](docs/TACHES-MEMBRES.md) :
vérification des annotations par tous (clips répartis), campagne et analyse (@Leo-Bnvl), échantillonnage et modèle
local (@rouautu), corpus et slides (troisième membre). Chacun commite son propre travail depuis son compte.

## Licence et références

- Code : MIT (comme le dépôt du cours).
- Clips réels : CC0 / CC BY / CC BY-SA de Wikimedia Commons, avec auteur et licence par clip dans `data/real/manifest.csv`. Les clips ne sont pas commités et se retéléchargent avec le script.
- Modèles : conditions d'utilisation de Google (Gemini), de Qwen (licence Qwen / Apache-2.0 selon la taille) et d'OpenRouter.
- Références :
  - Fu et al., *Video-MME*, arXiv:2405.21075 ;
  - Li et al., *MVBench*, arXiv:2311.17005 ;
  - [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) ;
  - notebooks CoursIA `GenAI/Video` (01-2 compréhension vidéo par API, 01-3 compréhension locale avec Qwen-VL, 03-1 comparaison multi-modèles).
