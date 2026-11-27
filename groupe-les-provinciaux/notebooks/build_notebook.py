import nbformat as nbf
from pathlib import Path
md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
cells = [
md("""# Analyse — benchmark de compréhension temporelle vidéo (E2)

Groupe **Les Provinciaux**. Ce notebook relit les résultats bruts (`results/*.jsonl`) produits par `python -m tvbench.run`
et en tire les tableaux et figures de la soutenance. Il ne fait **aucun appel payant** : il peut être ré-exécuté hors-ligne.

**Questions de recherche**
1. Quelle exactitude par catégorie (ordre, comptage, causalité, détail fugitif) pour chaque modèle, comparée au hasard ?
2. Les réponses sont-elles stables quand on reformule la question ?
3. Que change la sélection adaptative des frames, en particulier pour les détails fugitifs ?
4. Les erreurs viennent-elles de la **perception** (l'information n'est pas dans les frames) ou de la **compréhension** ?
5. Quel coût et quelle latence ?"""),
code("""import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))
from tvbench.metrics import summarize, wilson, evidence_seen, CATS

FIG = ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
MODEL_LABEL = {"random": "Hasard", "gemini-flash-lite-or": "Gemini 3.5 Flash-Lite",
               "qwen-27b-or": "Qwen 3.8-27B", "qwen-9b-or": "Qwen 3.5-9B"}
MODEL_ORDER = [m for m in MODEL_LABEL]
COLORS = {"random": "#9e9e9e", "gemini-flash-lite-or": "#1a73e8", "qwen-27b-or": "#7b3fbf", "qwen-9b-or": "#d9822b"}
CAT_LABEL = {"order": "Ordre", "counting": "Comptage", "causality": "Causalité", "fleeting": "Détail fugitif"}

frames = []
for name, corpus in [("synthetic.jsonl", "contrôlé"), ("real.jsonl", "réel")]:
    p = ROOT / "results" / name
    if p.exists():
        d = pd.read_json(p, lines=True); d["corpus"] = corpus; frames.append(d)
df = pd.concat(frames, ignore_index=True)
df = df[df["error"].isna()].copy()
df["seen"] = df.apply(evidence_seen, axis=1)
print(df.groupby(["corpus", "model", "strategy"]).size().unstack())"""),
md("## 1. Vue d'ensemble"),
code("""tables = {c: summarize(g) for c, g in df.groupby("corpus")}
for c, t in tables.items():
    print(f"=== corpus {c}")
    cols = ["model", "strategy", "n", "acc", "acc_ci"] + [f"acc_{k}" for k in CATS] + ["consistency", "robust_acc", "top_letter_share", "eur_per_100q", "lat_p50_s"]
    display(t[cols].round(3))"""),
md("""## 2. Exactitude par catégorie

Échantillonnage uniforme de 16 frames. Les barres d'erreur sont les IC 95 % de Wilson ; la ligne pointillée marque le hasard (0,25)."""),
code("""def acc_by_cat(d):
    out = []
    for (m, c), g in d.groupby(["model", "category"]):
        k, n = int(g["correct"].sum()), len(g)
        lo, hi = wilson(k, n)
        out.append(dict(model=m, category=c, acc=k / n, lo=lo, hi=hi, n=n))
    return pd.DataFrame(out)

corpora = list(df["corpus"].unique())
fig, axes = plt.subplots(1, len(corpora), figsize=(6.5 * len(corpora), 4), squeeze=False)
for ax, corp in zip(axes[0], corpora):
    a = acc_by_cat(df[(df.corpus == corp) & (df.strategy == "uniform")])
    models = [m for m in MODEL_ORDER if m in set(a.model)]
    w = 0.8 / len(models)
    for i, m in enumerate(models):
        s = a[a.model == m].set_index("category").reindex(CATS)
        x = np.arange(len(CATS)) + i * w
        ax.bar(x, s["acc"], w, color=COLORS[m], label=MODEL_LABEL[m])
        err = np.clip(np.nan_to_num(np.vstack([s["acc"] - s["lo"], s["hi"] - s["acc"]])), 0, None)
        ax.errorbar(x, s["acc"].fillna(0), yerr=err, fmt="none", ecolor="#333", lw=0.8, capsize=2)
    ax.axhline(0.25, ls="--", color="#666", lw=1)
    ax.set_xticks(np.arange(len(CATS)) + w * (len(models) - 1) / 2, [CAT_LABEL[c] for c in CATS])
    ax.set_ylim(0, 1.05); ax.set_ylabel("Exactitude"); ax.set_title(f"Corpus {corp} — 16 frames uniformes")
axes[0][0].legend(frameon=False, fontsize=8, loc="upper right")
plt.tight_layout(); plt.savefig(FIG / "accuracy_by_category.png", dpi=160, bbox_inches="tight"); plt.show()"""),
md("""## 3. Uniforme ou adaptatif ?

La sélection adaptative garde la moitié des frames réparties uniformément et choisit les autres aux pics de changement visuel."""),
code("""rows = []
for (corp, m, strat, c), g in df[df.model != "random"].groupby(["corpus", "model", "strategy", "category"]):
    rows.append(dict(corpus=corp, model=m, strategy=strat, category=c, acc=g["correct"].mean()))
t = pd.DataFrame(rows).pivot_table(index=["corpus", "model", "category"], columns="strategy", values="acc")
if {"uniform", "adaptive"} <= set(t.columns):
    t["gain"] = t["adaptive"] - t["uniform"]
display(t.round(2))

if {"uniform", "adaptive"} <= set(df.strategy):
    fig, axes = plt.subplots(1, len(corpora), figsize=(6.5 * len(corpora), 3.8), squeeze=False)
    for ax, corp in zip(axes[0], corpora):
        sub = t.loc[corp].reset_index()
        models = [m for m in MODEL_ORDER if m in set(sub.model)]
        w = 0.8 / len(models)
        for i, m in enumerate(models):
            s = sub[sub.model == m].set_index("category").reindex(CATS)
            ax.bar(np.arange(len(CATS)) + i * w, s["gain"], w, color=COLORS[m], label=MODEL_LABEL[m])
        ax.axhline(0, color="#333", lw=0.8)
        ax.set_xticks(np.arange(len(CATS)) + w * (len(models) - 1) / 2, [CAT_LABEL[c] for c in CATS])
        ax.set_ylabel("Gain d'exactitude (adaptatif − uniforme)"); ax.set_title(f"Corpus {corp}")
    axes[0][0].legend(frameon=False, fontsize=8)
    plt.tight_layout(); plt.savefig(FIG / "adaptive_gain.png", dpi=160, bbox_inches="tight"); plt.show()"""),
md("""## 4. Perception ou compréhension ?

Pour chaque question, on sait si au moins une frame envoyée tombe dans la fenêtre de preuve annotée (`evidence`).
Si le modèle se trompe alors que la preuve **n'était pas** dans les frames, c'est une erreur de perception imposée par
l'échantillonnage ; s'il se trompe alors qu'elle **était** visible, c'est une erreur de compréhension."""),
code("""fl = df[(df.category == "fleeting") & (df.model != "random")]
cov = fl.groupby(["corpus", "strategy"])["seen"].mean().unstack().round(2)
print("Couverture de la preuve (questions fugitives) :"); display(cov)
pc = fl.groupby(["corpus", "model", "seen"])["correct"].agg(["mean", "size"]).round(2)
print("Exactitude selon que la preuve était visible (seen=True) ou non :"); display(pc)

d = fl[fl.corpus == "contrôlé"] if "contrôlé" in set(fl.corpus) else fl
g = d.groupby(["model", "seen"])["correct"].mean().unstack()
models = [m for m in MODEL_ORDER if m in g.index]
fig, ax = plt.subplots(figsize=(6.5, 3.6))
x = np.arange(len(models))
ax.bar(x - 0.2, g.reindex(models).get(False, pd.Series(np.nan, index=models)), 0.4, color="#bdbdbd", label="preuve absente des frames")
ax.bar(x + 0.2, g.reindex(models).get(True, pd.Series(np.nan, index=models)), 0.4, color="#2e7d32", label="preuve visible")
ax.axhline(0.25, ls="--", color="#666", lw=1)
ax.set_xticks(x, [MODEL_LABEL[m] for m in models]); ax.set_ylim(0, 1.05); ax.set_ylabel("Exactitude (détail fugitif)")
ax.set_title("Détail fugitif : perception vs compréhension"); ax.legend(frameon=False, fontsize=8)
plt.tight_layout(); plt.savefig(FIG / "perception_vs_comprehension.png", dpi=160, bbox_inches="tight"); plt.show()"""),
md("""## 5. Stabilité aux reformulations

`consistency` : même lettre choisie pour les 3 formulations. `robust_acc` : les 3 formulations sont correctes.
L'écart entre exactitude moyenne et `robust_acc` mesure ce qu'on perd en exigeant la stabilité."""),
code("""rows = []
for (corp, m, strat), g in df[df.strategy == "uniform"].groupby(["corpus", "model", "strategy"]):
    q = g.groupby("qid")
    rows.append(dict(corpus=corp, model=m, acc=g["correct"].mean(),
                     consistency=q["pred"].agg(lambda s: s.nunique(dropna=False) == 1).mean(),
                     robust_acc=q["correct"].all().mean()))
st = pd.DataFrame(rows); display(st.round(2))
fig, axes = plt.subplots(1, len(corpora), figsize=(6.5 * len(corpora), 3.6), squeeze=False)
for ax, corp in zip(axes[0], corpora):
    s = st[st.corpus == corp].set_index("model").reindex([m for m in MODEL_ORDER if m in set(st.model)])
    x = np.arange(len(s))
    for j, (col, lab, colr) in enumerate([("acc", "exactitude moyenne", "#90caf9"), ("robust_acc", "correcte sur les 3 formulations", "#1565c0"), ("consistency", "même réponse sur les 3", "#ffb74d")]):
        ax.bar(x + (j - 1) * 0.27, s[col], 0.27, label=lab, color=colr)
    ax.set_xticks(x, [MODEL_LABEL[m] for m in s.index], fontsize=8); ax.set_ylim(0, 1.05); ax.set_title(f"Corpus {corp}")
axes[0][0].legend(frameon=False, fontsize=8)
plt.tight_layout(); plt.savefig(FIG / "stability.png", dpi=160, bbox_inches="tight"); plt.show()"""),
md("## 6. Biais de lettre"),
code("""bias = (df[df.strategy == "uniform"].groupby(["corpus", "model"])["pred"].value_counts(normalize=True)
        .unstack(fill_value=0).round(2))
truth = df[(df.strategy == "uniform") & (df.model == "random")].groupby("corpus")["answer"].value_counts(normalize=True).unstack().round(2)
print("Répartition des lettres prédites :"); display(bias)
print("Répartition des bonnes réponses :"); display(truth)"""),
md("## 7. Coût et latence"),
code("""rows = []
for (corp, m), g in df[df.model != "random"].groupby(["corpus", "model"]):
    rows.append(dict(corpus=corp, model=m, n=len(g), cost_eur=g["cost_eur"].sum(), eur_per_100q=100 * g["cost_eur"].mean(),
                     lat_p50=g["latency_s"].median(), lat_p95=g["latency_s"].quantile(0.95), acc=g["correct"].mean()))
cl = pd.DataFrame(rows); display(cl.round(4))
print(f"Coût total de la campagne : {df['cost_eur'].sum():.3f} €")
fig, ax = plt.subplots(figsize=(6, 3.8))
for _, r in cl.iterrows():
    ax.scatter(r["eur_per_100q"], r["acc"], s=70, color=COLORS[r["model"]], marker="o" if r["corpus"] == "contrôlé" else "s")
    ax.annotate(f"{MODEL_LABEL[r['model']]} ({r['corpus']})", (r["eur_per_100q"], r["acc"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
ax.axhline(0.25, ls="--", color="#666", lw=1)
ax.set_xlabel("Coût pour 100 questions (€)"); ax.set_ylabel("Exactitude"); ax.set_title("Coût vs exactitude (toutes stratégies)")
plt.tight_layout(); plt.savefig(FIG / "cost_vs_accuracy.png", dpi=160, bbox_inches="tight"); plt.show()"""),
md("""## 8. Baseline aveugle : les questions se devinent-elles sans la vidéo ?

Les mêmes questions (formulation d'origine) sont posées **sans aucune image**. Une exactitude nettement supérieure
au hasard signifie que la question se devine par le bon sens ou par la forme des options : elle ne mesure alors pas
la compréhension de la vidéo."""),
code("""blind = []
for name, corpus in [("blind_synthetic.jsonl", "contrôlé"), ("blind_real.jsonl", "réel")]:
    p = ROOT / "results" / name
    if p.exists():
        b = pd.read_json(p, lines=True); b["corpus"] = corpus; blind.append(b)
blind = pd.concat(blind, ignore_index=True)
display(blind.pivot_table(index=["corpus", "model"], columns="category", values="correct", aggfunc="mean")
        .assign(global_=blind.groupby(["corpus", "model"]).correct.mean()).round(2))

with_img = df[(df.strategy == "uniform") & (df.variant == 0) & (df.model.isin(blind.model.unique()))]
comp = pd.DataFrame({"sans image": blind.groupby(["corpus", "model"]).correct.mean(),
                     "16 frames": with_img.groupby(["corpus", "model"]).correct.mean()}).reset_index()
fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
for ax, corp in zip(axes, ["contrôlé", "réel"]):
    c = comp[comp.corpus == corp].set_index("model")
    x = np.arange(len(c))
    ax.bar(x - 0.2, c["sans image"], 0.4, color="#bdbdbd", label="sans image")
    ax.bar(x + 0.2, c["16 frames"], 0.4, color=[COLORS[m] for m in c.index], label="16 frames")
    ax.axhline(0.25, ls="--", color="#666", lw=1)
    ax.set_xticks(x, [MODEL_LABEL[m] for m in c.index]); ax.set_ylim(0, 1.05); ax.set_title(f"Corpus {corp}")
axes[0].set_ylabel("Exactitude (formulation d'origine)"); axes[0].legend(frameon=False, fontsize=8)
plt.tight_layout(); plt.savefig(FIG / "blind_baseline.png", dpi=160, bbox_inches="tight"); plt.show()

br = blind[blind.corpus == "réel"]
guessable = set(br.groupby("qid").correct.all().pipe(lambda s: s[s].index))
print(f"Corpus réel : {len(guessable)} questions sur 80 devinées sans image par les deux modèles.")
r = df[df.corpus == "réel"].assign(devinable=lambda d: d.qid.isin(guessable))
display(r.pivot_table(index=["model", "strategy"], columns="devinable", values="correct", aggfunc="mean").round(2))"""),
md("""## 9. Le comptage est-il un problème de perception ?

Sur le corpus contrôlé, la lampe s'allume 0,35 à 0,6 s ; 16 frames sur 10 s sont espacées de 0,625 s, donc une
partie des clignotements tombe entre deux frames. On relance les seules questions de comptage avec **32 frames**."""),
code("""p32 = ROOT / "results" / "synthetic_counting_32.jsonl"
if p32.exists():
    c32 = pd.read_json(p32, lines=True)
    c16 = df[(df.corpus == "contrôlé") & (df.category == "counting") & (df.model != "random")]
    t = pd.concat([c16.assign(cfg=c16.strategy + " 16"), c32.assign(cfg="uniform 32")])
    tab = t.pivot_table(index="model", columns="cfg", values="correct", aggfunc="mean").round(2)
    display(tab)
    ax = tab.reindex([m for m in MODEL_ORDER if m in tab.index]).rename(index=MODEL_LABEL).plot.bar(
        figsize=(7, 3.6), color=["#90caf9", "#1565c0", "#0d2b5e"], rot=0)
    ax.axhline(0.25, ls="--", color="#666", lw=1); ax.set_ylabel("Exactitude (comptage)"); ax.set_ylim(0, 1)
    ax.set_title("Comptage des clignotements selon le nombre de frames"); ax.legend(frameon=False, fontsize=8)
    plt.tight_layout(); plt.savefig(FIG / "counting_frames.png", dpi=160, bbox_inches="tight"); plt.show()
    # erreurs : sous-comptage ou sur-comptage ?
    import json as _j
    qs = {(_q := _j.loads(l))["qid"]: _q for l in open(ROOT / "data/synthetic/questions.jsonl")}
    def signed(row):
        q = qs[row.qid]
        if row.pred is None or pd.isna(row.pred): return np.nan
        return int(q["options"]["ABCD".index(row.pred)]) - int(q["options"]["ABCD".index(q["answer"])])
    t["ecart"] = t.apply(signed, axis=1)
    print("Écart moyen (prédit − vrai) :"); display(t.groupby(["model", "cfg"]).ecart.mean().unstack().round(2))"""),
md("## 10. Conclusions"),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
nbf.write(nb, str(Path(__file__).resolve().parent / "analyse_resultats.ipynb"))
print("ok")
