"""Adaptateurs de modèles vision-langage.

- `openai_compat` : toute API compatible OpenAI Chat Completions (OpenAI GPT-5/mini,
  Qwen-VL via DashScope / OpenRouter, vLLM ou Ollama en local). Frames envoyées
  en JPEG base64, précédées de leur horodatage.
- `qwen_local`   : Qwen2.5-VL / Qwen3-VL via transformers (GPU), en option.
- `random`       : baseline aléatoire (borne basse, valide le pipeline sans coût).
"""
from __future__ import annotations

import base64
import os
import random
import time
from dataclasses import dataclass, field

import requests

from .frames import Frame
from .prompts import SYSTEM


@dataclass
class Reply:
    text: str
    latency_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
    cost_usd: float | None = None   # coût réel renvoyé par certaines API (OpenRouter : usage.cost)


@dataclass
class ModelConfig:
    name: str
    kind: str
    model: str = ""
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    price_in_eur_per_mtok: float = 0.0
    price_out_eur_per_mtok: float = 0.0
    image_detail: str = "low"
    max_output_tokens: int = 16
    est_input_tokens_per_frame: int = 100       # pour --dry-run uniquement
    eur_per_usd: float = 0.87
    extra: dict = field(default_factory=dict)   # paramètres passés tels quels (ex. reasoning_effort)

    def cost_eur(self, r: Reply) -> float:
        if r.cost_usd is not None:
            return r.cost_usd * self.eur_per_usd
        return (r.input_tokens * self.price_in_eur_per_mtok
                + r.output_tokens * self.price_out_eur_per_mtok) / 1e6


class VLM:
    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg

    def ask(self, frames: list[Frame], prompt: str) -> Reply:  # pragma: no cover
        raise NotImplementedError


class RandomModel(VLM):
    def __init__(self, cfg: ModelConfig):
        super().__init__(cfg)
        self.rng = random.Random(cfg.extra.get("seed", 0))

    def ask(self, frames, prompt):
        n = sum(1 for line in prompt.splitlines() if line[:2] in {f"{c}." for c in "ABCDEFGH"})
        return Reply(text="ABCDEFGH"[self.rng.randrange(max(n, 1))], latency_s=0.0)


def _b64(path) -> str:
    return base64.b64encode(open(path, "rb").read()).decode()


class OpenAICompatModel(VLM):
    def ask(self, frames, prompt, retries: int = 3):
        key = os.environ.get(self.cfg.api_key_env, "")
        content = []
        for f in frames:
            content.append({"type": "text", "text": f"[t={f.t:.1f}s]"})
            content.append({"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{_b64(f.path)}", "detail": self.cfg.image_detail}})
        content.append({"type": "text", "text": prompt})
        body = {"model": self.cfg.model,
                "messages": [{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": content}],
                **self.cfg.extra}
        # GPT-5 / o-series n'acceptent que max_completion_tokens
        tok_key = "max_completion_tokens" if self.cfg.model.startswith(("gpt-5", "o")) else "max_tokens"
        body.setdefault(tok_key, self.cfg.max_output_tokens)
        last = None
        for attempt in range(retries):
            t0 = time.perf_counter()
            try:
                r = requests.post(f"{self.cfg.base_url.rstrip('/')}/chat/completions",
                                  headers={"Authorization": f"Bearer {key}"}, json=body, timeout=180)
                dt = time.perf_counter() - t0
                if r.status_code in (429, 500, 502, 503, 504):
                    last = f"HTTP {r.status_code}: {r.text[:200]}"
                    time.sleep(2 ** attempt * 2)
                    continue
                if r.status_code >= 400:  # erreur définitive : garder le message de l'API
                    return Reply(text="", latency_s=dt, error=f"HTTP {r.status_code}: {r.text[:300]}")
                d = r.json()
                u = d.get("usage") or {}
                return Reply(text=(d["choices"][0]["message"].get("content") or ""), latency_s=dt,
                             input_tokens=u.get("prompt_tokens", 0), output_tokens=u.get("completion_tokens", 0),
                             cost_usd=u.get("cost"))
            except Exception as e:  # erreur réseau / JSON
                last = f"{type(e).__name__}: {e}"
                time.sleep(2 ** attempt)
        return Reply(text="", latency_s=0.0, error=last)


class QwenLocalModel(VLM):
    """Qwen-VL local (transformers + qwen-vl-utils). Chargé paresseusement."""

    def __init__(self, cfg):
        super().__init__(cfg)
        self._model = self._proc = None

    def _load(self):
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor
        mid = self.cfg.model or "Qwen/Qwen2.5-VL-3B-Instruct"
        self._model = AutoModelForImageTextToText.from_pretrained(mid, torch_dtype="auto", device_map="auto")
        self._proc = AutoProcessor.from_pretrained(mid)
        self._torch = torch

    def ask(self, frames, prompt):
        if self._model is None:
            self._load()
        from PIL import Image
        content = []
        for f in frames:
            content += [{"type": "text", "text": f"[t={f.t:.1f}s]"}, {"type": "image"}]
        content.append({"type": "text", "text": prompt})
        msgs = [{"role": "system", "content": [{"type": "text", "text": SYSTEM}]},
                {"role": "user", "content": content}]
        text = self._proc.apply_chat_template(msgs, add_generation_prompt=True)
        imgs = [Image.open(f.path).convert("RGB") for f in frames]
        inputs = self._proc(text=[text], images=imgs, return_tensors="pt").to(self._model.device)
        t0 = time.perf_counter()
        with self._torch.no_grad():
            out = self._model.generate(**inputs, max_new_tokens=self.cfg.max_output_tokens, do_sample=False)
        dt = time.perf_counter() - t0
        gen = out[0, inputs["input_ids"].shape[1]:]
        return Reply(text=self._proc.decode(gen, skip_special_tokens=True), latency_s=dt,
                     input_tokens=int(inputs["input_ids"].shape[1]), output_tokens=int(len(gen)))


KINDS = {"random": RandomModel, "openai_compat": OpenAICompatModel, "qwen_local": QwenLocalModel}


def build(cfg: ModelConfig) -> VLM:
    return KINDS[cfg.kind](cfg)
