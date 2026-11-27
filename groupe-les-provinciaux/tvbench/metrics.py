"""Agrégation des résultats : accuracy par catégorie (IC 95 % de Wilson), stabilité aux
reformulations, couverture des frames, coût et latence. Produit un rapport Markdown + CSV.

  python -m tvbench.metrics results/results.jsonl --out results/report.md
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

CATS = ["order", "counting", "causality", "fleeting"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def evidence_seen(row) -> bool:
    """Au moins une frame échantillonnée tombe-t-elle dans la fenêtre de preuve ?"""
    ev = row.get("evidence")
    if not ev:
        return True
    return any(ev[0] <= t <= ev[1] for t in row["frame_times"])


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, strat, k), g in df.groupby(["model", "strategy", "k"]):
        r = {"model": model, "strategy": strat, "k": k, "n": len(g)}
        acc = g["correct"].mean()
        lo, hi = wilson(int(g["correct"].sum()), len(g))
        r["acc"], r["acc_ci"] = acc, f"[{lo:.2f}, {hi:.2f}]"
        for c in CATS:
            gc = g[g.category == c]
            r[f"acc_{c}"] = gc["correct"].mean() if len(gc) else float("nan")
        per_q = g.groupby("qid")
        multi = per_q.filter(lambda x: len(x) > 1).groupby("qid")
        if len(multi):
            r["consistency"] = multi["pred"].agg(lambda s: s.nunique(dropna=False) == 1).mean()
            r["robust_acc"] = multi["correct"].all().mean()
        else:
            r["consistency"] = r["robust_acc"] = float("nan")
        r["unparsed"] = g["pred"].isna().mean()
        # biais de lettre : part de la lettre la plus prédite (0,25 = aucun biais avec 4 options)
        r["top_letter_share"] = g["pred"].value_counts(normalize=True).max() if g["pred"].notna().any() else float("nan")
        r["errors"] = g["error"].notna().mean()
        r["cost_eur"] = g["cost_eur"].sum()
        r["eur_per_100q"] = 100 * g["cost_eur"].mean()
        lat = g.loc[g["latency_s"] > 0, "latency_s"]
        r["lat_p50_s"] = lat.median() if len(lat) else 0.0
        r["lat_p95_s"] = lat.quantile(0.95) if len(lat) else 0.0
        fl = g[g.category == "fleeting"]
        r["fleeting_coverage"] = fl.apply(evidence_seen, axis=1).mean() if len(fl) else float("nan")
        rows.append(r)
    return pd.DataFrame(rows)


def fmt(df: pd.DataFrame) -> str:
    d = df.copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda x: "—" if pd.isna(x) else (f"{x:.3f}" if "eur" in c or "lat" in c else f"{x:.2f}"))
    cols = list(d.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results", type=Path, nargs="+")
    ap.add_argument("--out", type=Path, default=Path("results/report.md"))
    a = ap.parse_args(argv)
    df = pd.concat([pd.read_json(p, lines=True) for p in a.results], ignore_index=True)
    s = summarize(df)
    main_cols = ["model", "strategy", "k", "n", "acc", "acc_ci"] + [f"acc_{c}" for c in CATS]
    stab_cols = ["model", "strategy", "k", "consistency", "robust_acc", "unparsed", "errors", "top_letter_share",
                 "fleeting_coverage"]
    cost_cols = ["model", "strategy", "k", "cost_eur", "eur_per_100q", "lat_p50_s", "lat_p95_s"]
    md = ["# Rapport — compréhension temporelle vidéo", "",
          f"Sources : {', '.join(map(str, a.results))}", "",
          "## Accuracy (par formulation, IC 95 % Wilson)", "", fmt(s[main_cols]), "",
          "## Stabilité aux reformulations", "",
          "`consistency` = même réponse sur toutes les formulations ; `robust_acc` = toutes correctes ; "
          "`top_letter_share` = part de la lettre la plus souvent prédite (0,25 attendu sans biais) ; "
          "`fleeting_coverage` = part des questions « fugitives » où au moins une frame tombe dans la fenêtre de preuve.",
          "", fmt(s[stab_cols]), "", "## Coût et latence", "", fmt(s[cost_cols]), ""]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(md))
    s.to_csv(a.out.with_suffix(".csv"), index=False)
    print("\n".join(md))


if __name__ == "__main__":
    main()
