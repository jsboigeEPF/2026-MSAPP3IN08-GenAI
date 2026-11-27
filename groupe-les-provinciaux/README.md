# Les Provinciaux — tvbench, benchmark de compréhension temporelle vidéo

## Groupe

| Membre | Contribution principale |
|---|---|
| @Leo-Bnvl | À compléter |
| @rouautu | À compléter |
| Troisième membre (sans compte GitHub) | À compléter |

Contribution d'un agent de code déclarée : le squelette du harnais (échantillonnage, adaptateurs, métriques,
corpus contrôlé, tests) a été écrit avec l'assistance de Claude Code, puis relu par le groupe.

## Sujet

- **Identifiant du catalogue :** E2 — Benchmark de compréhension temporelle vidéo
- **Problématique :** les modèles vision-langage reçoivent une vidéo sous forme de quelques frames.
  Comprennent-ils vraiment le *temps* (ordre, comptage, causalité, événements brefs) ? Leurs réponses
  restent-elles stables quand on reformule la question ? À quel coût et avec quelle latence ?
- **MVP :** corpus libre de 20 clips, 80 questions annotées à choix multiples (4 catégories × 20),
  deux modèles (GPT-5-mini et Qwen-VL), plus une baseline aléatoire.

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
cp .env.example .env                 # renseigner OPENROUTER_API_KEY (clé du cours)
set -a; . ./.env; set +a             # charger les variables dans le shell
```

## Utilisation

```bash
# 1. Corpus contrôlé (20 clips, 80 questions, déterministe)
python -m tvbench.synth

# 2. Estimation du coût, puis campagne
python -m tvbench.run --questions data/synthetic/questions.jsonl --clips data/synthetic/clips \
    --models random gpt5-mini-or qwen-vl-openrouter --dry-run
for s in uniform adaptive; do
  python -m tvbench.run --questions data/synthetic/questions.jsonl --clips data/synthetic/clips \
      --models random gpt5-mini-or qwen-vl-openrouter --frames 16 --strategy $s --out results/syn.jsonl
done
python -m tvbench.metrics results/syn.jsonl --out results/report_synthetic.md

# 3. Corpus réel
python scripts/fetch_commons.py --per-category 2 --max-seconds 30
python scripts/annotate_helper.py sheets data/real/clips
#    -> annoter data/real/questions.jsonl (format : data/real/questions.example.jsonl)
python scripts/annotate_helper.py validate data/real/questions.jsonl
python -m tvbench.run --questions data/real/questions.jsonl --clips data/real/clips \
    --models random gpt5-mini-or qwen-vl-openrouter --out results/real.jsonl
```

Les modèles disponibles sont listés dans `configs/models.toml` (OpenRouter, OpenAI, DashScope, Ollama, transformers).

## Tests

```bash
python -m tvbench.synth && python -m pytest -q
```

Résultat actuel : **15 tests passés**. Ils couvrent :

- le parsing des réponses, y compris les sorties vides, hors options et ambiguës (« C'est B ») ;
- l'échantillonnage uniforme et adaptatif (un flash de 3 frames est raté en uniforme et capturé en adaptatif) ;
- l'intervalle de Wilson ;
- l'adaptateur OpenAI-compatible, testé contre un faux serveur HTTP local (format de requête, en-tête d'authentification, calcul du coût) ;
- la validité du corpus (80 questions, 20 par catégorie, options uniques).

Modes d'échec gérés :

- réponse non parsable : comptée fausse et mesurée dans `unparsed` ;
- erreurs HTTP 429/5xx : 3 essais avec back-off, puis erreur journalisée dans `errors` ; la ligne est rejouée à la relance ;
- dépassement de budget : arrêt propre, reprise possible.

## Résultats et évaluation

**Protocole.** QCM à 4 options et bonnes réponses équilibrées (A/B/C/D : 19/15/24/22). On fait varier 8 ou 16 frames et
deux stratégies d'échantillonnage, uniforme ou adaptative. Toutes les formulations sont posées. La baseline est le
tirage aléatoire, qui donne 0,25 en théorie.

**Contrôle du pipeline** avec la baseline aléatoire (`results/smoke_report.md`) : accuracy de 0,25,
avec un IC 95 % de [0,20 ; 0,31]. C'est conforme à l'attendu.

**Premier constat mesuré, indépendant du modèle :** la part des questions « fugitives » dont la fenêtre de preuve
contient au moins une frame envoyée (`fleeting_coverage`).

| Échantillonnage | 8 frames | 16 frames |
|---|---|---|
| uniforme | 0,05 | 0,35 |
| adaptatif | 0,90 | 0,85 |

Avec un échantillonnage uniforme, aucun modèle ne *peut* répondre à la plupart des questions fugitives :
l'information n'est pas dans les frames. La métrique sépare donc les erreurs de **perception** (rien vu)
des erreurs de **compréhension** (vu, mais mal interprété).

**Résultats des modèles :** à compléter après la campagne. Le coût estimé est d'environ 0,7 € pour les deux modèles
sur 80 × 3 questions à 16 frames, soit moins de 12 € même en couvrant toutes les configurations.
Avec 80 questions, l'IC 95 % fait environ ±10 points : les écarts inférieurs ne sont pas interprétables.

## Limites et plan B

- **Corpus contrôlé :** ses scènes simples et synthétiques valident les mesures, mais ne remplacent pas le corpus réel annoté. Les deux sont rapportés séparément.
- **Annotation :** elle est faite par le groupe. Chaque question doit être vérifiée par un deuxième membre, et l'accord entre annotateurs doit être noté.
- **Prix :** ceux de `configs/models.toml` sont indicatifs et doivent être vérifiés. Le coût rapporté est calculé à partir des tokens réellement facturés (champ `usage`).
- **Accès aux frames :** les modèles ne voient que des frames, sans audio ni vidéo native. Les adaptateurs « vidéo native » (Gemini, Qwen avec fps) sont une extension possible.
- **Plan B :**
  - frames pré-extraites et mises en cache dans `data/frames/` : on peut les rejouer sans décodage et sans réseau ;
  - baseline `random` : démontre la chaîne complète sans clé ;
  - modèle local `qwen-local-ollama` : fonctionne sans API.

## Répartition du travail

À compléter : qui a fait l'annotation, les adaptateurs, la campagne, l'analyse et les slides ; mode de relecture.

## Licence et références

- Code : MIT (comme le dépôt du cours).
- Clips réels : CC0 / CC BY / CC BY-SA de Wikimedia Commons, avec auteur et licence par clip dans `data/real/clips/manifest.csv`. Les clips ne sont pas commités et se retéléchargent avec le script.
- Modèles : conditions d'utilisation d'OpenAI, de Qwen (licence Qwen / Apache-2.0 selon la taille) et d'OpenRouter.
- Références :
  - Fu et al., *Video-MME*, arXiv:2405.21075 ;
  - Li et al., *MVBench*, arXiv:2311.17005 ;
  - [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) ;
  - notebooks CoursIA `GenAI/Video` (01-2 compréhension vidéo par API, 01-3 compréhension locale avec Qwen-VL, 03-1 comparaison multi-modèles).
