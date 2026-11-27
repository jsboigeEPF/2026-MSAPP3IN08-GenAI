"""Génère les slides de soutenance (HTML puis PDF) à partir des résultats et des figures.

  python slides/build_slides.py            # -> slides/soutenance.html et slides/soutenance.pdf

Les chiffres sont recalculés depuis results/*.jsonl : relancer après chaque campagne.
Le PDF nécessite Playwright + Chromium (pip install playwright && playwright install chromium).
Les messages clés (KEY_POINTS) sont à relire et reformuler par le groupe.
"""
from __future__ import annotations

import base64
import html
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tvbench.metrics import evidence_seen  # noqa: E402

FIG = ROOT / "results" / "figures"
OUT = ROOT / "slides"
LABEL = {"random": "Hasard", "gemini-flash-lite-or": "Gemini 3.5 Flash-Lite",
         "qwen-27b-or": "Qwen 3.8-27B", "qwen-9b-or": "Qwen 3.5-9B"}
CAT = {"order": "Ordre", "counting": "Comptage", "causality": "Causalité", "fleeting": "Détail fugitif"}
KEY_POINTS = json.loads((OUT / "key_points.json").read_text(encoding="utf-8")) if (OUT / "key_points.json").exists() else {}


def load() -> pd.DataFrame:
    frames = []
    for name, corpus in [("synthetic.jsonl", "contrôlé"), ("real.jsonl", "réel")]:
        p = ROOT / "results" / name
        if p.exists():
            d = pd.read_json(p, lines=True)
            d["corpus"] = corpus
            frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df = df[df["error"].isna()].copy()
    df["seen"] = df.apply(evidence_seen, axis=1)
    return df


def img(name: str) -> str:
    p = FIG / name
    if not p.exists():
        return f"<p class='missing'>figure manquante : {name}</p>"
    return f"<img src='data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}'>"


def table(df: pd.DataFrame) -> str:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r) + "</tr>" for r in df.itertuples(index=False))
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def acc_table(df: pd.DataFrame, corpus: str) -> pd.DataFrame:
    d = df[(df.corpus == corpus) & (df.strategy == "uniform")]
    rows = []
    for m in LABEL:
        g = d[d.model == m]
        if not len(g):
            continue
        r = {"Modèle": LABEL[m], "Global": f"{g.correct.mean():.2f}"}
        for c, lab in CAT.items():
            gc = g[g.category == c]
            r[lab] = f"{gc.correct.mean():.2f}" if len(gc) else "—"
        q = g.groupby("qid")
        r["Correct ×3 formulations"] = f"{q.correct.all().mean():.2f}"
        rows.append(r)
    return pd.DataFrame(rows)


def cost_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for m in LABEL:
        g = df[df.model == m]
        if m == "random" or not len(g):
            continue
        rows.append({"Modèle": LABEL[m], "Appels": len(g), "Coût total (€)": f"{g.cost_eur.sum():.3f}",
                     "€ / 100 questions": f"{100 * g.cost_eur.mean():.3f}",
                     "Latence médiane (s)": f"{g.latency_s.median():.2f}",
                     "Latence p95 (s)": f"{g.latency_s.quantile(0.95):.2f}"})
    return pd.DataFrame(rows)


def bullets(items) -> str:
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def slide(title: str, body: str, cls: str = "") -> str:
    return f"<section class='slide {cls}'><h2>{title}</h2><div class='body'>{body}</div></section>"


def build():
    df = load()
    n_calls = len(df[df.model != "random"])
    total = df.cost_eur.sum()
    cov = df[(df.category == "fleeting") & (df.model != "random")].groupby(["corpus", "strategy"]).seen.mean()
    cov_txt = ", ".join(f"{c} / {s} : {v:.0%}" for (c, s), v in cov.items())
    kp = lambda k, default: bullets(KEY_POINTS.get(k, default))  # noqa: E731

    S = []
    S.append("<section class='slide title'><h1>Comprendre le temps dans une vidéo</h1>"
             "<p class='sub'>Benchmark de compréhension temporelle pour modèles vision-langage — sujet E2</p>"
             "<p class='who'>Groupe <b>Les Provinciaux</b> · @Leo-Bnvl · @rouautu · 3<sup>e</sup> membre</p>"
             "<p class='who small'>MSAPP3IN08 — IA générative et chatbots · EPF 2026-2027</p></section>")
    S.append(slide("Le problème", bullets([
        "Un modèle vision-langage ne « voit » pas une vidéo : il reçoit <b>quelques images</b> (frames) horodatées.",
        "Sait-il retrouver l'<b>ordre</b> des événements, <b>compter</b>, expliquer une <b>cause</b>, repérer un <b>détail bref</b> ?",
        "Sa réponse change-t-elle si l'on <b>reformule</b> la question ?",
        "À quel <b>coût</b> et avec quelle <b>latence</b> ?",
        "Inspiré de Video-MME (Fu et al., 2024) et MVBench (Li et al., 2024), à petite échelle et avec un budget &lt; 12 €."])))
    S.append(slide("Protocole", bullets([
        "<b>QCM à 4 options</b>, bonnes réponses réparties A/B/C/D, baseline <b>hasard</b> = 0,25.",
        "<b>Corpus contrôlé</b> : 20 clips scriptés (formes, lampe, balle/boîte, nombre flash) — vérité terrain exacte, 80 questions.",
        "<b>Corpus réel</b> : 20 clips libres Wikimedia Commons (licences dans le manifeste), 80 questions ; "
        "sélection sans enfants ni personnes en gros plan.",
        "Chaque question en <b>3 formulations</b> → stabilité ; fenêtre de preuve <code>evidence</code> annotée.",
        "16 frames par question, échantillonnage <b>uniforme</b> ou <b>adaptatif</b>."])))
    S.append(slide("Architecture", "<div class='pipe'>"
                   "<div>clips vidéo<br><small>ffmpeg</small></div><span>→</span>"
                   "<div>frames.py<br><small>uniforme | adaptatif<br>cache JPEG = plan B</small></div><span>→</span>"
                   "<div>run.py<br><small>prompt QCM horodaté<br>reprise, budget</small></div><span>→</span>"
                   "<div>models.py<br><small>OpenRouter · Ollama<br>transformers · hasard</small></div><span>→</span>"
                   "<div>metrics.py<br><small>IC Wilson, stabilité<br>coût, latence</small></div></div>"
                   + bullets(["Adaptatif : moitié des frames uniformes + pics de différence entre images consécutives.",
                              "17 tests automatisés (parsing, échantillonnage, adaptateur API contre un faux serveur, coûts, .env).",
                              "Tout est rejouable sans réseau : résultats bruts versionnés, notebook hors-ligne."])))
    S.append(slide("Modèles", bullets([
        "<b>Gemini 3.5 Flash-Lite</b> (API propriétaire) · <b>Qwen 3.8-27B</b> (poids ouverts) · "
        "<b>Qwen 3.5-9B</b> (taille exécutable en local) · <b>hasard</b>.",
        "Imposé par l'espace OpenRouter du cours : GPT-5 et Qwen-VL y sont <b>bloqués</b> (garde-fou, HTTP 404).",
        "Qwen appelé <b>sans raisonnement</b> : sinon il épuise ses tokens et renvoie une réponse vide.",
        f"Campagne : <b>{n_calls} appels</b>, coût réel facturé <b>{total:.2f} €</b>."])))
    S.append(slide("Exactitude par catégorie", img("accuracy_by_category.png") + kp("accuracy", [])))
    for corpus in ["contrôlé", "réel"]:
        t = acc_table(df, corpus)
        if len(t):
            S.append(slide(f"Tableau — corpus {corpus} (16 frames uniformes)", table(t)
                           + "<p class='note'>Avec 80 questions, l'IC 95 % fait environ ±10 points.</p>"))
    S.append(slide("Uniforme ou adaptatif ?", img("adaptive_gain.png") + kp("adaptive", [])))
    S.append(slide("Perception ou compréhension ?", img("perception_vs_comprehension.png")
                   + bullets([f"Part des questions fugitives où une frame contient la preuve — {cov_txt}."] + KEY_POINTS.get("perception", []))))
    S.append(slide("Stabilité aux reformulations", img("stability.png") + kp("stability", [])))
    S.append(slide("Coût et latence", table(cost_table(df)) + img("cost_vs_accuracy.png")))
    S.append(slide("Limites", kp("limits", [
        "Annotations du corpus réel rédigées avec l'aide d'un agent, à <b>vérifier par le groupe</b> (accord inter-annotateurs).",
        "80 questions par corpus : écarts &lt; 10 points non significatifs.",
        "Catégories non parfaitement équilibrées sur le corpus réel (17 questions « détail fugitif »).",
        "Les modèles ne voient que 16 images : pas d'audio, pas de vidéo native.",
        "Modèles limités par le garde-fou du cours (pas de GPT-5)."])))
    S.append(slide("Démo et plan B", bullets([
        "<code>python -m tvbench.run … --models random</code> : chaîne complète sans clé ni réseau.",
        "Frames en cache et résultats bruts versionnés : le notebook se rejoue hors-ligne.",
        "3<sup>e</sup> modèle réellement local : Ollama <code>qwen2.5vl:7b</code> (configuré, à lancer sur un PC).",
        "Suite : vérification humaine des annotations, courbe exactitude / nombre de frames (8-16-32)."])))
    css = """
    @page { size: 1280px 720px; margin: 0 }
    body { margin: 0; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1d2433; }
    .slide { width: 1280px; height: 720px; box-sizing: border-box; padding: 48px 64px; page-break-after: always;
             position: relative; background: #fff; overflow: hidden; border-bottom: 1px solid #eee; }
    .slide h2 { margin: 0 0 22px; font-size: 34px; color: #1a3e72; border-bottom: 3px solid #e3ebf6; padding-bottom: 10px; }
    .slide .body { font-size: 22px; line-height: 1.45; }
    .slide img { max-width: 100%; max-height: 430px; display: block; margin: 0 auto 10px; }
    .title { display: flex; flex-direction: column; justify-content: center; background: #1a3e72; color: #fff; }
    .title h1 { font-size: 56px; margin: 0 0 16px; } .title .sub { font-size: 26px; opacity: .9; margin: 0 0 40px; }
    .title .who { font-size: 22px; margin: 4px 0; } .title .small { font-size: 18px; opacity: .8; }
    table { border-collapse: collapse; margin: 0 auto 12px; font-size: 19px; }
    th, td { border: 1px solid #d5dce8; padding: 6px 12px; text-align: center; } th { background: #eef3fa; }
    .note { font-size: 16px; color: #666; text-align: center; }
    .pipe { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 10px 0 30px; }
    .pipe div { border: 2px solid #1a3e72; border-radius: 10px; padding: 12px 14px; text-align: center; font-weight: 600; font-size: 19px; }
    .pipe small { font-weight: 400; font-size: 14px; color: #555; } .pipe span { font-size: 28px; color: #1a3e72; }
    code { background: #f2f4f8; padding: 1px 5px; border-radius: 4px; font-size: .9em; }
    ul { margin: 6px 0; } li { margin: 4px 0; } .missing { color: #b00; }
    """
    doc = f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Soutenance E2 — Les Provinciaux</title><style>{css}</style></head><body>{''.join(S)}</body></html>"
    (OUT / "soutenance.html").write_text(doc, encoding="utf-8")
    pdf = OUT / "soutenance.pdf"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_content(doc, wait_until="load")
            pg.pdf(path=str(pdf), width="1280px", height="720px", print_background=True)
            b.close()
    except Exception:
        # repli : Chrome/Chromium en ligne de commande (headless)
        import shutil
        import subprocess
        exe = next((x for x in [os.environ.get("CHROME"), "/opt/pw-browsers/chromium", shutil.which("google-chrome"),
                                shutil.which("chromium"), shutil.which("chromium-browser")] if x and Path(x).exists()), None)
        if exe is None:
            print("PDF non généré (ni Playwright ni Chrome) ; ouvrir slides/soutenance.html")
            return
        subprocess.run([exe, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", (OUT / "soutenance.html").resolve().as_uri()],
                       check=True, capture_output=True, timeout=120)
    print(f"{len(S)} slides -> slides/soutenance.pdf")

if __name__ == "__main__":
    build()
