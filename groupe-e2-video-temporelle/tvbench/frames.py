"""Extraction et sélection de frames (uniforme ou adaptative).

Les frames sont décodées via ffmpeg (pipe rawvideo), puis mises en cache en JPEG
dans data/frames/<clip>/<strategie>_<k>/ : c'est le « plan B » (frames pré-extraites)
réutilisable par n'importe quel modèle, y compris hors-ligne.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class Frame:
    t: float          # timestamp en secondes
    path: Path        # JPEG en cache


def probe(video: Path) -> tuple[int, int, float, float]:
    """Retourne (largeur, hauteur, fps, durée)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate:format=duration",
         "-of", "json", str(video)],
        check=True, capture_output=True, text=True).stdout
    d = json.loads(out)
    s = d["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den), float(d["format"]["duration"])


def decode(video: Path, fps: float | None = None, width: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Décode toute la vidéo -> (frames uint8 [N,H,W,3], timestamps [N])."""
    w, h, src_fps, _ = probe(video)
    vf = []
    if fps:
        vf.append(f"fps={fps}")
    if width and width < w:
        h = int(round(h * width / w / 2) * 2)
        w = width
        vf.append(f"scale={w}:{h}")
    cmd = ["ffmpeg", "-v", "error", "-i", str(video)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    rate = fps or src_fps
    return arr, np.arange(len(arr)) / rate


def uniform_indices(n: int, k: int) -> list[int]:
    """k indices au centre de k segments égaux (comme Video-MME / MVBench)."""
    if k >= n:
        return list(range(n))
    return [int((i + 0.5) * n / k) for i in range(k)]


def adaptive_indices(frames: np.ndarray, k: int, uniform_share: float = 0.5) -> list[int]:
    """Sélection adaptative : une part uniforme (couverture) + les pics de changement visuel.

    Le score de changement est la différence absolue moyenne entre frames
    consécutives (niveaux de gris sous-échantillonnés). Les pics capturent
    les événements brefs (« détails fugitifs ») que l'échantillonnage uniforme rate.
    """
    n = len(frames)
    if k >= n:
        return list(range(n))
    g = frames[:, ::4, ::4].mean(axis=3).astype(np.float32)
    diff = np.zeros(n, np.float32)
    diff[1:] = np.abs(g[1:] - g[:-1]).mean(axis=(1, 2))
    n_uni = max(1, int(round(k * uniform_share)))
    chosen = set(uniform_indices(n, n_uni))
    min_gap = max(1, n // (4 * k))  # évite de prendre plusieurs frames du même événement
    for i in np.argsort(-diff):
        if len(chosen) >= k:
            break
        if diff[i] <= 0:
            break
        if all(abs(int(i) - c) >= min_gap for c in chosen):
            chosen.add(int(i))
    for i in uniform_indices(n, k):  # complète si pas assez de pics
        if len(chosen) >= k:
            break
        chosen.add(i)
    return sorted(chosen)


def select_frames(video: Path, k: int = 16, strategy: str = "uniform",
                  cache_dir: Path = Path("data/frames"), max_side: int = 512,
                  decode_fps: float = 10.0) -> list[Frame]:
    """Retourne k frames (avec timestamps), en utilisant/alimentant le cache disque."""
    out_dir = cache_dir / video.stem / f"{strategy}_{k}"
    index = out_dir / "index.json"
    if index.exists():
        return [Frame(f["t"], out_dir / f["file"]) for f in json.loads(index.read_text())]
    frames, ts = decode(video, fps=decode_fps, width=max_side)
    if strategy == "uniform":
        idx = uniform_indices(len(frames), k)
    elif strategy == "adaptive":
        idx = adaptive_indices(frames, k)
    else:
        raise ValueError(f"stratégie inconnue : {strategy}")
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = []
    for j, i in enumerate(idx):
        name = f"{j:02d}_{ts[i]:07.2f}s.jpg"
        Image.fromarray(frames[i]).save(out_dir / name, quality=85)
        meta.append({"t": round(float(ts[i]), 2), "file": name})
    index.write_text(json.dumps(meta, indent=1))
    return [Frame(m["t"], out_dir / m["file"]) for m in meta]
