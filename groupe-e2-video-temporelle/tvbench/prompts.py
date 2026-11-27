"""Construction du prompt QCM et extraction de la réponse."""
from __future__ import annotations

import re

LETTERS = "ABCDEFGH"

SYSTEM = ("Tu analyses une vidéo fournie sous forme de frames ordonnées dans le temps, "
          "chacune précédée de son horodatage. Réponds uniquement par la lettre de l'option correcte.")


def build_prompt(question: str, options: list[str], timestamps: list[float], duration: float | None) -> str:
    ts = ", ".join(f"{t:.1f}s" for t in timestamps)
    head = f"Vidéo de {duration:.1f} s. " if duration else ""
    opts = "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(options))
    return (f"{head}{len(timestamps)} frames échantillonnées aux instants : {ts}.\n\n"
            f"Question : {question}\n{opts}\n\n"
            f"Réponds par une seule lettre ({', '.join(LETTERS[:len(options)])}).")


_PATTERNS = [
    re.compile(r"(?:r[ée]ponse|answer)\s*(?:est|is|:)?\s*\(?([A-H])\b", re.I),
    re.compile(r"^\W*\(?([A-H])\)?(?:[.:)\s]|$)"),
    re.compile(r"\b([A-H])\b(?!['’])"),
]


def parse_answer(text: str, n_options: int) -> str | None:
    """Renvoie la lettre choisie, ou None si la sortie est inexploitable."""
    if not text:
        return None
    valid = LETTERS[:n_options]
    t = text.strip()
    for p in _PATTERNS:
        for m in p.finditer(t):
            letter = m.group(1).upper()
            if letter in valid:
                return letter
    return None
