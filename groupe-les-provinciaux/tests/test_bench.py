import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import numpy as np
import pytest

from tvbench.frames import Frame, adaptive_indices, uniform_indices
from tvbench.metrics import wilson
from tvbench.models import ModelConfig, OpenAICompatModel
from tvbench.prompts import build_prompt, parse_answer


@pytest.mark.parametrize("text,exp", [
    ("B", "B"), ("B.", "B"), ("(C) le carré", "C"), ("La réponse est D", "D"),
    ("Answer: a", "A"), ("C'est B", "B"), ("", None), ("je ne sais pas", None), ("E", None),
])
def test_parse_answer(text, exp):
    assert parse_answer(text, 4) == exp


def test_uniform_indices():
    assert uniform_indices(100, 4) == [12, 37, 62, 87]
    assert uniform_indices(3, 8) == [0, 1, 2]


def test_adaptive_catches_brief_event():
    frames = np.zeros((100, 32, 32, 3), np.uint8)
    frames[53:56] = 255  # flash de 3 frames, raté par 8 frames uniformes
    uni = uniform_indices(100, 8)
    assert not any(53 <= i < 56 for i in uni)
    ada = adaptive_indices(frames, 8)
    assert len(ada) == 8 and any(53 <= i < 56 for i in ada)


def test_wilson():
    lo, hi = wilson(40, 80)
    assert lo < 0.5 < hi and abs((lo + hi) / 2 - 0.5) < 1e-9


def test_prompt_lists_options():
    p = build_prompt("Q ?", ["x", "y", "z", "w"], [0.5, 1.5], 10.0)
    assert "A. x" in p and "D. w" in p and "1.5s" in p


def test_openai_adapter_against_fake_server(tmp_path, monkeypatch):
    seen = {}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"] = self.path
            seen["auth"] = self.headers["Authorization"]
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            out = json.dumps({"choices": [{"message": {"content": "C"}}],
                              "usage": {"prompt_tokens": 1000, "completion_tokens": 2}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    img = tmp_path / "f.jpg"
    from PIL import Image
    Image.new("RGB", (8, 8)).save(img)
    monkeypatch.setenv("FAKE_KEY", "sk-test")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    cfg = ModelConfig(name="fake", kind="openai_compat", model="gpt-5-mini",
                      base_url=f"http://127.0.0.1:{srv.server_port}/v1", api_key_env="FAKE_KEY",
                      price_in_eur_per_mtok=1.0, price_out_eur_per_mtok=10.0, extra={"reasoning_effort": "minimal"})
    rep = OpenAICompatModel(cfg).ask([Frame(0.5, img), Frame(2.0, img)], "prompt")
    srv.shutdown()
    assert rep.text == "C" and rep.error is None
    assert seen["path"] == "/v1/chat/completions" and seen["auth"] == "Bearer sk-test"
    body = seen["body"]
    assert body["max_completion_tokens"] == 16 and body["reasoning_effort"] == "minimal"
    parts = body["messages"][1]["content"]
    assert [p["type"] for p in parts] == ["text", "image_url", "text", "image_url", "text"]
    assert parts[2]["text"] == "[t=2.0s]"
    assert abs(cfg.cost_eur(rep) - (1000 * 1.0 + 2 * 10.0) / 1e6) < 1e-12


def test_synthetic_questions_well_formed():
    p = Path("data/synthetic/questions.jsonl")
    if not p.exists():
        pytest.skip("lancer python -m tvbench.synth d'abord")
    qs = [json.loads(l) for l in p.read_text().splitlines()]
    assert len(qs) == 80
    for q in qs:
        assert len(q["options"]) == 4 and len(set(q["options"])) == 4
        assert q["answer"] in "ABCD" and len(q["variants"]) == 3
    cats = {c: sum(q["category"] == c for q in qs) for c in ["order", "counting", "causality", "fleeting"]}
    assert set(cats.values()) == {20}


def test_load_dotenv(tmp_path, monkeypatch):
    from tvbench.run import load_dotenv
    f = tmp_path / ".env"
    f.write_text("# commentaire\nTVB_A=abc\nTVB_B=\nTVB_C=\"x y\"\nTVB_D=deja\n")
    monkeypatch.delenv("TVB_A", raising=False)
    monkeypatch.delenv("TVB_B", raising=False)
    monkeypatch.delenv("TVB_C", raising=False)
    monkeypatch.setenv("TVB_D", "env")
    load_dotenv(f)
    import os
    assert os.environ["TVB_A"] == "abc" and "TVB_B" not in os.environ
    assert os.environ["TVB_C"] == "x y" and os.environ["TVB_D"] == "env"


def test_cost_prefers_billed_cost():
    from tvbench.models import Reply
    cfg = ModelConfig(name="x", kind="openai_compat", price_in_eur_per_mtok=1000.0)
    assert cfg.cost_eur(Reply("A", 1.0, input_tokens=10, cost_usd=0.01)) == 0.01 * cfg.eur_per_usd
    assert cfg.cost_eur(Reply("A", 1.0, input_tokens=10)) == 10 * 1000.0 / 1e6


def test_evidence_seen_uses_frame_span():
    from tvbench.metrics import evidence_seen
    assert evidence_seen({"evidence": [7.45, 7.73], "frame_times": [7.4]})      # frame [7,40 ; 7,50) chevauche
    assert not evidence_seen({"evidence": [7.45, 7.73], "frame_times": [7.3, 7.8]})
    assert evidence_seen({"evidence": None, "frame_times": []})
