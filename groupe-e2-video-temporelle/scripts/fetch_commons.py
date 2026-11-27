"""Constitue le corpus réel : clips sous licence libre depuis Wikimedia Commons.

Pour chaque catégorie, récupère des vidéos courtes, télécharge une version transcodée
(~480p) puis coupe à --max-seconds. Écrit data/real/clips/manifest.csv avec la licence
et l'auteur (attribution obligatoire pour CC BY / BY-SA).

  python scripts/fetch_commons.py --per-category 3 --max-seconds 30

Respecte la politique Wikimedia : User-Agent descriptif, requêtes espacées.
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import subprocess
import time
from pathlib import Path

import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = "temporal-video-bench/0.1 (educational benchmark; python-requests)"
# Catégories choisies pour leur richesse temporelle (ordre, comptage, causalité, détails brefs)
DEFAULT_CATS = [
    "Videos of juggling", "Videos of cooking", "Videos of dominoes", "Videos of billiards",
    "Videos of basketball", "Videos of trains", "Videos of traffic", "Videos of experiments",
    "Videos of dogs", "Videos of birds",
]
OK_LICENSES = re.compile(r"^(CC0|CC BY|CC BY-SA|Public domain)", re.I)


def api(session, **params):
    params |= {"action": "query", "format": "json", "formatversion": 2, "maxlag": 5}
    for attempt in range(5):
        r = session.get(API, params=params, timeout=60)
        if r.status_code == 429 or "maxlag" in r.text[:200]:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Commons API indisponible (429 répétés)")


def videos_in_category(session, cat: str, limit: int):
    d = api(session, generator="categorymembers", gcmtitle=f"Category:{cat}", gcmtype="file",
            gcmlimit=50, prop="videoinfo", viprop="url|mime|size|extmetadata|derivatives",
            viextmetadatafilter="LicenseShortName|Artist|LicenseUrl")
    out = []
    for p in d.get("query", {}).get("pages", []):
        vi = (p.get("videoinfo") or [{}])[0]
        if not str(vi.get("mime", "")).startswith("video/"):
            continue
        dur = float(vi.get("duration") or 0)
        meta = vi.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        if not OK_LICENSES.match(lic) or not (5 <= dur <= 300):
            continue
        derivs = vi.get("derivatives") or []
        small = [x for x in derivs if "480p" in x.get("transcodekey", "") or "360p" in x.get("transcodekey", "")]
        url = (small or derivs or [{"src": vi.get("url")}])[0]["src"]
        artist = re.sub(r"<[^>]+>", "", html.unescape(meta.get("Artist", {}).get("value", ""))).strip()
        out.append(dict(title=p["title"], url=url, page=vi.get("descriptionurl", ""), duration=dur,
                        license=lic, license_url=meta.get("LicenseUrl", {}).get("value", ""), author=artist))
        if len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("data/real/clips"))
    ap.add_argument("--categories", nargs="+", default=DEFAULT_CATS)
    ap.add_argument("--per-category", type=int, default=2)
    ap.add_argument("--max-seconds", type=float, default=30)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = UA
    rows, n = [], len(list(a.out.glob("real*.mp4")))
    for cat in a.categories:
        try:
            vids = videos_in_category(s, cat, a.per_category)
        except Exception as e:
            print(f"! {cat}: {e}")
            continue
        for v in vids:
            clip = f"real{n:02d}"
            tmp = a.out / f"{clip}.src"
            with s.get(v["url"], stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        f.write(chunk)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-t", str(a.max_seconds), "-an",
                            "-vf", "scale='min(640,iw)':-2", "-c:v", "libx264", "-crf", "23",
                            str(a.out / f"{clip}.mp4")], check=True)
            tmp.unlink()
            rows.append({"clip": clip, "category": cat, **v})
            print(f"{clip}  {v['license']:10s}  {v['title']}")
            n += 1
            time.sleep(1)
    man = a.out / "manifest.csv"
    new = not man.exists()
    with open(man, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["clip", "category", "title", "url", "page", "duration",
                                          "license", "license_url", "author"])
        if new:
            w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} clips ajoutés -> {man}")


if __name__ == "__main__":
    main()
