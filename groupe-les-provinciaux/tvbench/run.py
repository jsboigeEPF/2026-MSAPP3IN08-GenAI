"""Exécution du benchmark : modèles × questions × formulations, avec reprise et plafond budgétaire.

Exemple :
  python -m tvbench.run --questions data/synthetic/questions.jsonl --clips data/synthetic/clips \\
      --models random gpt5-mini qwen-vl --frames 16 --strategy uniform --budget-eur 12
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path

from .frames import probe, select_frames
from .models import ModelConfig, build
from .prompts import build_prompt, parse_answer


def load_dotenv(path: Path = Path(".env")) -> None:
    """Charge un fichier .env (CLE=valeur) sans écraser les variables déjà définies."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.strip().strip('"').strip("'")
        if val:
            os.environ.setdefault(key.strip(), val)


def load_models(path: Path) -> dict[str, ModelConfig]:
    raw = tomllib.loads(path.read_text())
    out = {}
    for name, d in raw.items():
        out[name] = ModelConfig(name=name, **d)
    return out


def load_questions(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def find_clip(clips: Path, clip: str) -> Path:
    for ext in (".mp4", ".webm", ".mkv", ".mov", ".ogv"):
        p = clips / f"{clip}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"clip introuvable : {clip} dans {clips}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--questions", type=Path, required=True)
    ap.add_argument("--clips", type=Path, required=True)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--config", type=Path, default=Path("configs/models.toml"))
    ap.add_argument("--frames", type=int, default=16)
    ap.add_argument("--strategy", choices=["uniform", "adaptive"], default="uniform")
    ap.add_argument("--variants", choices=["all", "first"], default="all",
                    help="'first' = formulation d'origine seulement (moins cher)")
    ap.add_argument("--budget-eur", type=float, default=12.0, help="arrêt si le coût cumulé dépasse ce montant")
    ap.add_argument("--out", type=Path, default=Path("results/results.jsonl"))
    ap.add_argument("--cache", type=Path, default=Path("data/frames"))
    ap.add_argument("--limit", type=int, default=0, help="n'évaluer que les N premières questions (test)")
    ap.add_argument("--dry-run", action="store_true", help="estime le nombre d'appels et le coût, sans appeler")
    a = ap.parse_args(argv)
    load_dotenv()

    cfgs = load_models(a.config)
    unknown = [m for m in a.models if m not in cfgs]
    if unknown:
        sys.exit(f"modèles inconnus dans {a.config} : {unknown}")
    qs = load_questions(a.questions)[: a.limit or None]
    n_var = lambda q: len(q["variants"]) if a.variants == "all" else 1
    n_calls = sum(n_var(q) for q in qs)

    if a.dry_run:
        print(f"{len(qs)} questions, {n_calls} appels par modèle, {a.frames} frames/appel")
        total = 0.0
        for m in a.models:
            c = cfgs[m]
            tin = n_calls * (a.frames * c.est_input_tokens_per_frame + 250)
            tout = n_calls * c.max_output_tokens
            eur = (tin * c.price_in_eur_per_mtok + tout * c.price_out_eur_per_mtok) / 1e6
            total += eur
            print(f"  {m:14s} ~{tin/1e6:.2f} M tok entrée, ~{eur:.2f} €")
        print(f"  total estimé : {total:.2f} € (budget {a.budget_eur} €)")
        return

    a.out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if a.out.exists():
        for l in a.out.read_text().splitlines():
            r = json.loads(l)
            if not r.get("error"):
                done.add((r["model"], r["qid"], r["variant"], r["strategy"], r["k"]))
    spent = 0.0
    if a.out.exists():
        spent = sum(json.loads(l).get("cost_eur", 0) for l in a.out.read_text().splitlines())
    models = {m: build(cfgs[m]) for m in a.models}
    frames_cache: dict[str, tuple] = {}

    with open(a.out, "a") as fout:
        for qi, q in enumerate(qs):
            if q["clip"] not in frames_cache:
                video = find_clip(a.clips, q["clip"])
                frames_cache[q["clip"]] = (select_frames(video, a.frames, a.strategy, a.cache), probe(video)[3])
            frames, duration = frames_cache[q["clip"]]
            for vi, text in enumerate(q["variants"][: n_var(q)]):
                prompt = build_prompt(text, q["options"], [f.t for f in frames], duration)
                for m, model in models.items():
                    key = (m, q["qid"], vi, a.strategy, a.frames)
                    if key in done:
                        continue
                    if spent >= a.budget_eur:
                        sys.exit(f"budget atteint ({spent:.2f} €) — arrêt, relancer pour reprendre.")
                    rep = model.ask(frames, prompt)
                    pred = parse_answer(rep.text, len(q["options"]))
                    cost = cfgs[m].cost_eur(rep)
                    spent += cost
                    fout.write(json.dumps({
                        "model": m, "qid": q["qid"], "clip": q["clip"], "category": q["category"],
                        "variant": vi, "strategy": a.strategy, "k": a.frames, "answer": q["answer"],
                        "pred": pred, "correct": pred == q["answer"], "raw": rep.text[:200],
                        "latency_s": round(rep.latency_s, 3), "input_tokens": rep.input_tokens,
                        "output_tokens": rep.output_tokens, "cost_eur": cost, "error": rep.error,
                        "frame_times": [f.t for f in frames], "evidence": q.get("evidence"),
                    }, ensure_ascii=False) + "\n")
                    fout.flush()
            print(f"\r{qi + 1}/{len(qs)} questions — {spent:.3f} €", end="", flush=True)
    print(f"\nterminé -> {a.out}")


if __name__ == "__main__":
    main()
