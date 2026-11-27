"""Corpus contrôlé : 20 clips rendus de façon procédurale (PIL + ffmpeg) avec vérité terrain exacte.

Ce n'est pas de la génération par IA : chaque clip est une scène scriptée simple
(formes, lampe, balle/boîte, nombre flash) qui permet de valider le pipeline et de
mesurer précisément les 4 compétences temporelles, à côté du corpus réel annoté.

Chaque clip donne 4 questions (une par catégorie) × 3 formulations :
  order     – ordre d'apparition de 3 formes
  counting  – nombre de clignotements d'une lampe
  causality – pourquoi la boîte a bougé (percutée par quelle balle / toute seule)
  fleeting  – nombre affiché pendant ~0,3 s
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 480, 360, 25, 10.0
COLORS = {"rouge": (220, 40, 40), "bleu": (40, 90, 230), "vert": (30, 170, 60),
          "jaune": (235, 200, 20), "violet": (150, 60, 200), "orange": (245, 130, 20)}
SHAPES = {"cercle": "circle", "carré": "square", "triangle": "triangle"}
BG = (235, 235, 228)


def _font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def _shape(d, kind, cx, cy, r, color):
    if kind == "circle":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    elif kind == "square":
        d.rectangle([cx - r, cy - r, cx + r, cy + r], fill=color)
    else:
        d.polygon([(cx, cy - r), (cx - r, cy + r), (cx + r, cy + r)], fill=color)


def make_script(rng: random.Random) -> dict:
    # Ordre : 3 objets (forme, couleur) distincts, apparitions à des instants espacés
    combos = [(s, c) for s in SHAPES for c in COLORS]
    rng.shuffle(combos)
    objs = combos[:3]
    distractor = combos[3]
    t_app = sorted(rng.sample([0.8, 2.0, 3.2, 4.4, 5.6, 6.8, 8.0], 3))
    # Comptage : n clignotements de la lampe
    n_blink = rng.randint(2, 7)
    slots = sorted(rng.sample([round(0.5 + 1.2 * i, 2) for i in range(8)], n_blink))
    blinks = [(t, t + rng.uniform(0.35, 0.6)) for t in slots]
    # Causalité : balle A frappe la boîte à t_hit ; balle B passe sans contact.
    a, b = rng.sample(["rouge", "bleu", "vert", "violet"], 2)
    t_hit = rng.uniform(4.0, 7.0)
    self_move = rng.random() < 0.25  # la boîte part toute seule AVANT le contact
    t_box = t_hit - 1.5 if self_move else t_hit
    # Fugitif : nombre à 2 chiffres affiché 0,28 s
    num = rng.randint(10, 99)
    t_flash = rng.uniform(1.0, 9.0)
    return dict(objs=objs, distractor=distractor, t_app=t_app, blinks=blinks, ball_hit=a, ball_other=b,
                t_hit=t_hit, t_box=t_box, self_move=self_move, num=num, t_flash=t_flash, flash_dur=0.28)


def render_frame(s: dict, t: float, font) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.line([(0, 300), (W, 300)], fill=(120, 120, 120), width=3)  # sol
    # objets d'ordre (zone haut-gauche)
    for i, ((shape, color), ta) in enumerate(zip(s["objs"], s["t_app"])):
        if t >= ta:
            _shape(d, SHAPES[shape], 50 + i * 80, 60, 26, COLORS[color])
    # lampe (haut-droite)
    on = any(t0 <= t < t1 for t0, t1 in s["blinks"])
    d.rectangle([415, 20, 465, 30], fill=(90, 90, 90))
    d.ellipse([415, 30, 465, 80], fill=(255, 230, 40) if on else (90, 90, 80), outline=(40, 40, 40), width=2)
    # balle A : vient de la gauche, touche la boîte (bord gauche x=300) à t_hit, puis s'arrête
    box_x0 = 300
    v = 100.0  # px/s ; la balle arrive au bord gauche initial de la boîte à t_hit puis s'arrête
    ax = max(-30.0, box_x0 - 18 - v * max(0.0, s["t_hit"] - t))
    # la boîte part à t_box (= t_hit si percutée, t_hit - 1,5 s si elle part toute seule)
    dx = min(120.0, max(0.0, t - s["t_box"]) * 150)
    d.ellipse([ax - 18, 262, ax + 18, 298], fill=COLORS[s["ball_hit"]])
    # balle B : traverse en hauteur de droite à gauche, loin de la boîte
    bx = W + 30 - (t / DUR) * (W + 60)
    d.ellipse([bx - 14, 160, bx + 14, 188], fill=COLORS[s["ball_other"]])
    # boîte
    bx0 = box_x0 + dx
    d.rectangle([bx0, 240, bx0 + 60, 298], fill=(150, 110, 70), outline=(80, 55, 30), width=3)
    # nombre fugitif
    if s["t_flash"] <= t < s["t_flash"] + s["flash_dur"]:
        d.rectangle([180, 120, 300, 200], fill=(20, 20, 20))
        d.text((240, 160), str(s["num"]), fill=(255, 255, 255), font=font, anchor="mm")
    return img


def render(s: dict, out: Path):
    font = _font(56)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                          "-pix_fmt", "yuv420p", "-crf", "20", str(out)], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(render_frame(s, i / FPS, font).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg a échoué")


def _mcq(rng, correct: str, distractors: list[str]):
    opts = [correct] + [x for x in distractors if x != correct][:3]
    rng.shuffle(opts)
    return opts, "ABCD"[opts.index(correct)]


def make_questions(clip: str, s: dict, rng: random.Random) -> list[dict]:
    name = lambda o: f"le {o[0]} {o[1]}"
    qs = []
    # ordre
    order = [name(o) for o in s["objs"]]
    kind = rng.choice(["first", "last", "after"])
    if kind == "first":
        correct = order[0]
        variants = ["Quel objet est apparu en premier ?",
                    "Parmi les formes en haut à gauche, laquelle s'est affichée la première ?",
                    "Quelle forme apparaît avant toutes les autres dans la vidéo ?"]
    elif kind == "last":
        correct = order[2]
        variants = ["Quel objet est apparu en dernier ?",
                    "Parmi les formes en haut à gauche, laquelle s'est affichée la dernière ?",
                    "Quelle forme apparaît après toutes les autres dans la vidéo ?"]
    else:
        correct = order[1]
        variants = [f"Quel objet est apparu juste après {order[0]} ?",
                    f"Quelle forme s'est affichée immédiatement après l'apparition du {order[0][3:]} ?",
                    f"Une fois {order[0]} apparu, quelle est la forme suivante à apparaître ?"]
    pool = [o for o in order if o != correct] + [name(s["distractor"])]
    if kind == "after":
        pool = [order[2], name(s["distractor"]), order[0]]
    opts, ans = _mcq(rng, correct, pool)
    qs.append(dict(category="order", variants=variants, options=opts, answer=ans,
                   evidence=[s["t_app"][0], s["t_app"][2]], meta={"kind": kind}))
    # comptage
    n = len(s["blinks"])
    cands = [x for x in range(1, 10) if x != n]
    rng.shuffle(cands)
    near = sorted(cands, key=lambda x: abs(x - n))[:3]
    opts, ans = _mcq(rng, str(n), [str(x) for x in near])
    qs.append(dict(category="counting", options=opts, answer=ans,
                   variants=["Combien de fois la lampe en haut à droite s'est-elle allumée ?",
                             "Quel est le nombre de clignotements de la lampe jaune pendant la vidéo ?",
                             "La lampe s'allume puis s'éteint plusieurs fois : combien de fois au total ?"],
                   evidence=[s["blinks"][0][0], s["blinks"][-1][1]], meta={"n": n}))
    # causalité
    A, B = s["ball_hit"], s["ball_other"]
    o_a = f"Elle a été poussée par la balle {A}"
    o_b = f"Elle a été poussée par la balle {B}"
    o_self = "Elle s'est mise en mouvement toute seule, avant tout contact"
    o_none = "Elle n'a pas bougé"
    correct = o_self if s["self_move"] else o_a
    opts, ans = _mcq(rng, correct, [o_a, o_b, o_self, o_none])
    qs.append(dict(category="causality", options=opts, answer=ans,
                   variants=["Pourquoi la boîte marron s'est-elle déplacée ?",
                             "Qu'est-ce qui a provoqué le mouvement de la boîte posée au sol ?",
                             "Quelle est la cause du déplacement de la boîte ?"],
                   evidence=[s["t_box"] - 1, s["t_box"] + 1], meta={"self_move": s["self_move"]}))
    # fugitif
    num = s["num"]
    rev = int(str(num)[::-1])
    d = {num + 1, num - 1, num + 10, num - 10, rev if num % 10 else num + 2}
    d = [str(x) for x in d if 10 <= x <= 99 and x != num]
    rng.shuffle(d)
    opts, ans = _mcq(rng, str(num), d)
    qs.append(dict(category="fleeting", options=opts, answer=ans,
                   variants=["Quel nombre est brièvement apparu au centre de l'écran ?",
                             "Un nombre s'affiche un court instant dans un cadre noir : lequel ?",
                             "Quel nombre à deux chiffres a flashé pendant la vidéo ?"],
                   evidence=[s["t_flash"], s["t_flash"] + s["flash_dur"]], meta={}))
    for q in qs:
        q.update(qid=f"{clip}_{q['category']}", clip=clip, source="synthetic")
        q["evidence"] = [round(x, 2) for x in q["evidence"]]
    return qs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("data/synthetic"))
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args(argv)
    (a.out / "clips").mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(a.n):
        rng = random.Random(a.seed * 1000 + i)
        clip = f"syn{i:02d}"
        s = make_script(rng)
        render(s, a.out / "clips" / f"{clip}.mp4")
        rows += make_questions(clip, s, rng)
        (a.out / "clips" / f"{clip}.script.json").write_text(json.dumps(s, ensure_ascii=False, indent=1))
    with open(a.out / "questions.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{a.n} clips, {len(rows)} questions -> {a.out}")


if __name__ == "__main__":
    main()
