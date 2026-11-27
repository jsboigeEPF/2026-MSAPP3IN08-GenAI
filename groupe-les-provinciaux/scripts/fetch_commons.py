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
# Critère de sélection : de préférence objets, animaux, véhicules ou mains (pas d'enfants ni de personnes
# filmées en gros plan) — scènes riches en événements temporels et sans donnée personnelle de tiers.
DEFAULT_CATS = [
    "Videos of billiards", "Videos of chemical reactions", "Videos of pendulums", "Videos of trams",
    "Videos of cats", "Videos of horses", "Videos of fish", "Videos of airplanes", "Videos of chess",
    "Videos of table tennis", "Videos of cooking", "Videos of trains", "Videos of birds", "Videos of dogs",
]
OK_LICENSES = re.compile(r"^(CC0|CC BY|CC BY-SA|Public domain)", re.I)


def api(session, **params):
    params |= {"action": "query", "format": "json", "formatversion": 2, "maxlag": 5}
    for attempt in range(8):
        r = session.get(API, params=params, timeout=60)
        if r.status_code == 429 or "maxlag" in r.text[:200]:
            wait = 30 * (attempt + 1)
            print(f"  API limitée (429), nouvel essai dans {wait} s", flush=True)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Commons API indisponible (429 répétés) — relancer plus tard")


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


WIKI = "https://commons.wikimedia.org/wiki/"


def _get_html(session, url):
    for attempt in range(6):
        r = session.get(url, timeout=60)
        if r.status_code == 429:
            time.sleep(20 * (attempt + 1))
            continue
        r.raise_for_status()
        return html.unescape(r.text)
    raise RuntimeError(f"page indisponible (429 répétés) : {url}")


def videos_in_category_html(session, cat: str, limit: int):
    """Repli sans API : lit la page HTML de la catégorie puis chaque page de fichier.

    L'API Commons limite fortement certaines adresses IP partagées (HTTP 429) ;
    les pages web restent accessibles et contiennent licence, auteur, durée et transcodages.
    """
    page = _get_html(session, WIKI + "Category:" + cat.replace(" ", "_"))
    files = list(dict.fromkeys(re.findall(r'href="/wiki/(File:[^"]+\.(?:webm|ogv))"', page)))
    out = []
    for f in files:
        time.sleep(2)
        try:
            fp = _get_html(session, WIKI + f)
        except Exception as e:
            print(f"  ! {f}: {e}", flush=True)
            continue
        lic = re.search(r'class="licensetpl_short"[^>]*>([^<]+)', fp)
        lic = lic.group(1).strip() if lic else ""
        dur = re.search(r'data-durationhint="(\d+)"', fp)
        dur = float(dur.group(1)) if dur else 0.0
        if not OK_LICENSES.match(lic) or not (5 <= dur <= 300):
            continue
        srcs = re.findall(r'<source src="([^"]+)"[^>]*data-transcodekey="([^"]+)"', fp)
        files_only = [(u, k) for u, k in srcs if not u.endswith((".mpd", ".m3u8"))]  # pas de flux segmentés
        pick = ([u for u, k in files_only if k.startswith(("480p", "360p")) and k.endswith("webm")]
                or [u for u, k in files_only if k.endswith(("webm", "mov", "mp4"))])
        if not pick:
            continue
        aut = re.search(r'id="fileinfotpl_aut".*?</td>\s*<td[^>]*>(.*?)</td>', fp, re.S)
        artist = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", aut.group(1))).strip()[:200] if aut else ""
        link = re.search(r'class="licensetpl_link"[^>]*>([^<]+)', fp)
        out.append(dict(title=f.replace("_", " "), url=pick[0], page=WIKI + f, duration=dur, license=lic,
                        license_url=link.group(1).strip() if link else "", author=artist))
        if len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("data/real/clips"))
    ap.add_argument("--categories", nargs="+", default=DEFAULT_CATS)
    ap.add_argument("--per-category", type=int, default=2)
    ap.add_argument("--max-seconds", type=float, default=30)
    ap.add_argument("--html", action="store_true", help="lire les pages web au lieu de l'API (si l'API renvoie 429)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = UA
    man = a.out / "manifest.csv"
    fields = ["clip", "category", "title", "url", "page", "duration", "license", "license_url", "author"]
    if not man.exists():
        with open(man, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=fields).writeheader()
    seen = {r["title"] for r in csv.DictReader(open(man))}
    n = len(seen)
    added = 0
    for cat in a.categories:
        print(f"catégorie : {cat}", flush=True)
        time.sleep(5)  # politesse envers l'API
        try:
            vids = (videos_in_category_html if a.html else videos_in_category)(s, cat, a.per_category)
        except Exception as e:
            print(f"! {cat}: {e}", flush=True)
            continue
        for v in vids:
            if v["title"] in seen:
                continue
            clip = f"real{n:02d}"
            tmp = a.out / f"{clip}.src"
            try:
                for attempt in range(5):
                    with s.get(v["url"], stream=True, timeout=300) as r:
                        if r.status_code == 429 and attempt < 4:
                            print(f"  téléchargement refusé (429), nouvel essai dans {30 * (attempt + 1)} s", flush=True)
                            time.sleep(30 * (attempt + 1))
                            continue
                        r.raise_for_status()
                        with open(tmp, "wb") as f:
                            for chunk in r.iter_content(1 << 16):
                                f.write(chunk)
                        break
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-t", str(a.max_seconds), "-an",
                                "-vf", "scale='min(640,iw)':-2", "-c:v", "libx264", "-crf", "23",
                                str(a.out / f"{clip}.mp4")], check=True)
            except Exception as e:
                print(f"! {v['title']}: {e}", flush=True)
                continue
            finally:
                tmp.unlink(missing_ok=True)
            with open(man, "a", newline="") as f:  # écrit au fil de l'eau : rien n'est perdu si on interrompt
                csv.DictWriter(f, fieldnames=fields).writerow({"clip": clip, "category": cat, **v})
            seen.add(v["title"])
            print(f"{clip}  {v['license']:10s}  {v['title']}", flush=True)
            n += 1
            added += 1
            time.sleep(1)
    print(f"{added} clips ajoutés -> {man}")


if __name__ == "__main__":
    main()
