"""Aide à l'annotation du corpus réel.

  python scripts/annotate_helper.py sheets data/real/clips      # planches-contact horodatées (1 frame / 0,5 s)
  python scripts/annotate_helper.py validate data/real/questions.jsonl

La planche-contact sert à repérer les instants exacts (champ `evidence`) ; on vérifie
ensuite dans un lecteur vidéo. `validate` contrôle le schéma, l'équilibre des catégories
et la distribution des bonnes réponses (A/B/C/D doivent être à peu près équilibrées).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw  # noqa: E402

from tvbench.frames import decode  # noqa: E402

CATS = {"order", "counting", "causality", "fleeting"}


def sheets(clips: Path, step: float = 0.5, cols: int = 8, width: int = 200):
    for v in sorted(clips.glob("*.mp4")):
        fr, ts = decode(v, fps=1 / step, width=width)
        h, w = fr.shape[1:3]
        rows = -(-len(fr) // cols)
        sheet = Image.new("RGB", (cols * w, rows * (h + 16)), "white")
        d = ImageDraw.Draw(sheet)
        for i, (f, t) in enumerate(zip(fr, ts)):
            x, y = (i % cols) * w, (i // cols) * (h + 16)
            sheet.paste(Image.fromarray(f), (x, y + 16))
            d.text((x + 3, y + 2), f"{t:.1f}s", fill="black")
        out = v.with_suffix(".sheet.jpg")
        sheet.save(out, quality=80)
        print(out)


def validate(path: Path):
    qs = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    errs = []
    ids = Counter(q.get("qid") for q in qs)
    for q in qs:
        qid = q.get("qid", "?")
        for k in ["qid", "clip", "category", "variants", "options", "answer"]:
            if k not in q:
                errs.append(f"{qid}: champ manquant {k}")
        if q.get("category") not in CATS:
            errs.append(f"{qid}: catégorie invalide {q.get('category')}")
        opts = q.get("options", [])
        if len(opts) < 2 or len(set(opts)) != len(opts):
            errs.append(f"{qid}: options invalides")
        if q.get("answer") not in "ABCDEFGH"[: len(opts)]:
            errs.append(f"{qid}: réponse hors options")
        if len(q.get("variants", [])) < 2:
            errs.append(f"{qid}: au moins 2 formulations attendues pour la stabilité")
        if ids[qid] > 1:
            errs.append(f"{qid}: identifiant dupliqué")
    print(f"{len(qs)} questions, {len({q.get('clip') for q in qs})} clips")
    print("catégories :", dict(Counter(q.get("category") for q in qs)))
    print("réponses   :", dict(sorted(Counter(q.get("answer") for q in qs).items())))
    print("\n".join(errs) if errs else "OK")
    return not errs


if __name__ == "__main__":
    cmd, arg = sys.argv[1], Path(sys.argv[2])
    if cmd == "sheets":
        sheets(arg)
    else:
        sys.exit(0 if validate(arg) else 1)
