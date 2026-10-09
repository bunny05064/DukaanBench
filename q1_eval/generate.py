"""DukaanBench image generation.

Generates one image per (prompt, model) using the three required models and
stores proof-of-generation metadata alongside each image.

Usage:
    python3 generate.py --list-models
    python3 generate.py                # generate everything missing
    python3 generate.py --only P1 P3   # generate a subset of prompts

Credentials are read from the environment or from a .env file in the repo root:
    OPENAI_API_KEY=...
    GEMINI_API_KEY=...      (or GOOGLE_API_KEY)
"""

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROMPTS = os.path.join(HERE, "prompts", "prompts.json")
IMG_DIR = os.path.join(HERE, "images")
META_DIR = os.path.join(HERE, "metadata")
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(META_DIR, exist_ok=True)


def load_env():
    for path in (os.path.join(ROOT, ".env"), os.path.join(HERE, ".env")):
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()


# ------------------------------------------------------------------ OpenAI
def gen_openai(prompt, cfg, meta):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    body = {
        "model": cfg["model_id"],
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
    }
    t0 = time.time()
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {key}"},
        json=body,
        timeout=300,
    )
    meta["http_status"] = r.status_code
    meta["latency_s"] = round(time.time() - t0, 2)
    if r.status_code != 200:
        meta["error"] = r.text[:2000]
        raise RuntimeError(f"OpenAI {r.status_code}: {r.text[:300]}")
    data = r.json()
    item = data["data"][0]
    meta["openai_created"] = data.get("created")
    meta["openai_revised_prompt"] = item.get("revised_prompt")
    meta["openai_output_format"] = item.get("output_format")
    meta["sha256"] = hashlib.sha256(base64.b64decode(item["b64_json"])).hexdigest()
    return base64.b64decode(item["b64_json"]), "png"


# ----------------------------------------------------------------- Gemini
def gen_gemini(prompt, cfg, meta):
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY / GOOGLE_API_KEY not set")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{cfg['model_id']}:generateContent"
    )
    variants = [
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {"aspectRatio": "1:1"},
            },
        },
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"imageConfig": {"aspectRatio": "1:1"}},
        },
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        },
        {"contents": [{"parts": [{"text": prompt}]}]},
    ]
    last = None
    t0 = time.time()
    for i, body in enumerate(variants):
        r = requests.post(
            url,
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json=body,
            timeout=300,
        )
        last = (r, body)
        meta.setdefault("request_variants_tried", []).append(
            {"variant": i, "status": r.status_code}
        )
        if r.status_code == 200:
            break
        time.sleep(1)
    r, body = last
    meta["http_status"] = r.status_code
    meta["latency_s"] = round(time.time() - t0, 2)
    meta["request_body_used"] = body
    if r.status_code != 200:
        meta["error"] = r.text[:2000]
        raise RuntimeError(f"{cfg['model_id']} {r.status_code}: {r.text[:300]}")
    data = r.json()
    meta["gemini_finish_reason"] = (
        data.get("candidates", [{}])[0].get("finishReason")
        if data.get("candidates")
        else None
    )
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            raw = base64.b64decode(inline["data"])
            meta["mime_type"] = inline.get("mimeType") or inline.get("mime_type")
            meta["sha256"] = hashlib.sha256(raw).hexdigest()
            ext = "png" if "png" in (meta["mime_type"] or "") else "png"
            return raw, ext
    meta["error"] = json.dumps(data)[:2000]
    raise RuntimeError(f"{cfg['model_id']}: no inline image in response")


GENERATORS = {"OpenAI": gen_openai, "Google": gen_gemini}


def list_gemini_models():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("no GEMINI_API_KEY")
        return
    r = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": key},
        params={"pageSize": 200},
        timeout=60,
    )
    print("HTTP", r.status_code)
    if r.status_code != 200:
        print(r.text[:500])
        return
    for m in r.json().get("models", []):
        name = m.get("name", "")
        if "image" in name.lower() or "imagen" in name.lower():
            print(f"  {name:60s} {m.get('supportedGenerationMethods')}")


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-models", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    if args.list_models:
        list_gemini_models()
        return

    spec = json.load(open(PROMPTS, encoding="utf-8"))
    prompts = [p for p in spec["prompts"] if not args.only or p["id"] in args.only]
    failures = []
    for m in spec["models"]:
        gen = GENERATORS[m["company"]]
        for p in prompts:
            stem = f"{p['id']}__{slug(m['company'])}__{slug(m['model'])}"
            img_path = os.path.join(IMG_DIR, stem + ".png")
            meta_path = os.path.join(META_DIR, stem + ".json")
            if os.path.exists(img_path) and os.path.exists(meta_path):
                print(f"skip {stem} (exists)")
                continue
            meta = {
                "prompt_id": p["id"],
                "prompt_axis": p["axis"],
                "prompt_text": p["text"],
                "must_contain": p["must_contain"],
                "must_show": p["must_show"],
                "company": m["company"],
                "model": m["model"],
                "model_id": m["model_id"],
                "docs": m["docs"],
                "endpoint": (
                    "https://api.openai.com/v1/images/generations"
                    if m["company"] == "OpenAI"
                    else f"generativelanguage.googleapis.com/v1beta/models/{m['model_id']}:generateContent"
                ),
                "settings": spec["shared_settings"],
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "generated_where": "Josh Talks AI hiring challenge, run on candidate machine",
            }
            print(f"generating {stem} ...", flush=True)
            try:
                raw, ext = gen(p["text"], m, meta)
                with open(img_path, "wb") as fh:
                    fh.write(raw)
                meta["image_file"] = os.path.basename(img_path)
                meta["status"] = "ok"
            except Exception as exc:  # noqa: BLE001
                meta["status"] = "failed"
                meta["failure"] = str(exc)[:500]
                failures.append((stem, str(exc)[:200]))
                print(f"  FAILED: {exc}")
            with open(meta_path, "w", encoding="utf-8") as fh:
                json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(f"\ndone. failures: {len(failures)}")
    for s, e in failures:
        print(" -", s, e)


if __name__ == "__main__":
    main()
