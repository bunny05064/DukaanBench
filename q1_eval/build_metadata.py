"""Builds per-image metadata (proof of generation) for every image in q1_eval/images.

Reads prompts/prompts.json and the canonical filenames produced by the manual
generation kit, then writes one JSON per image into metadata/.
"""

import datetime as dt
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
META = os.path.join(HERE, "metadata")
SPEC = os.path.join(HERE, "prompts", "prompts.json")

# The three sets were produced in the Gemini consumer app, whose model picker was
# set as follows (candidate's record of the order used):
#   set 1 -> "3.5 Flash Lite"   set 2 -> "3.6 Flash"   set 3 -> "3.1 Pro"
# The consumer app does NOT report which underlying image-generation model it used,
# so the image-model identity for all 30 images is UNVERIFIED.
PICKER = {
    "gemini-3.1-flash-image-preview": "3.5 Flash Lite",
    "gemini-2.5-flash-image": "3.6 Flash",
    "gemini-3-pro-image": "3.1 Pro",
}


def route(model_id):
    return {
        "model_id": model_id,
        "where": "Google Gemini web app (gemini.google.com) - manual generation, "
                 "app model picker set to \"" + PICKER[model_id] + "\"",
        "settings": "app model picker = " + PICKER[model_id]
                    + "; 1:1 carried inside the prompt text (Square 1:1 ...)",
        "model_identity_verified": False,
        "model_identity_note": "The consumer app does not expose the underlying "
                               "image-generation model. Only the picker label is known, "
                               "so this image cannot be attributed to a confirmed API "
                               "model id.",
        "api_attempt": "Programmatic call blocked: HTTP 429, free-tier image quota "
                       "limit = 0 (log in metadata/api_attempt_logs/)",
    }


def slug(s):
    out = "".join(c.lower() if c.isalnum() else "-" for c in s)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def main():
    spec = json.load(open(SPEC, encoding="utf-8"))
    os.makedirs(META, exist_ok=True)
    routes = {}
    for m in spec["models"]:
        routes[slug(m["company"]) + "__" + slug(m["model"])] = m

    written = 0
    for p in spec["prompts"]:
        for m in spec["models"]:
            stem = f"{p['id']}__{slug(m['company'])}__{slug(m['model'])}"
            img = os.path.join(IMG, stem + ".png")
            if not os.path.exists(img):
                print("missing image:", stem)
                continue
            raw = open(img, "rb").read()
            extra = route(m["model_id"])
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
                "image_file": os.path.basename(img),
                "image_size_px": [1024, 1024],
                "image_bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "file_modified_at": dt.datetime.fromtimestamp(
                    os.path.getmtime(img), dt.timezone.utc
                ).isoformat(),
                "where_generated": extra["where"],
                "settings_or_variations": extra["settings"],
                "model_identity_verified": extra["model_identity_verified"],
                "model_identity_note": extra["model_identity_note"],
                "programmatic_attempt": extra["api_attempt"],
                "aspect_handling": "1:1 requested in the prompt text itself, "
                                   "so the wording stays byte-identical across models",
                "status": "ok",
                "app_picker_label": PICKER.get(m["model_id"]),
                "required_model_confirmed": False,
            }
            with open(os.path.join(META, stem + ".json"), "w", encoding="utf-8") as fh:
                json.dump(meta, fh, ensure_ascii=False, indent=2)
            written += 1
    print(f"wrote {written} metadata files")


if __name__ == "__main__":
    main()
