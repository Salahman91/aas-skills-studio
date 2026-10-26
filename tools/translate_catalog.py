#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""يضيف وصفاً عربياً لكل مهارة في data/catalog.json.

- الوصف اليدوي (39 مهارة) يُترك كما هو.
- بقية المهارات تُترجم من وصف المستودع الإنجليزي عبر خدمة ترجمة عامة،
  مع تخزين مؤقت في data/ar_cache.json حتى لا تتكرر الطلبات.
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl=ar"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
MAX_URL_CHARS = 1700
BATCH_ITEMS = 10
DELAY = 0.35


def has_arabic(text):
    return any("\u0600" <= ch <= "\u06ff" for ch in text or "")


def translate_batch(texts, attempts=5):
    query = "".join("&q=" + urllib.parse.quote(text) for text in texts)
    url = ENDPOINT + query
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, list) and len(payload) == len(texts):
                return payload
            last_error = "unexpected payload shape"
        except urllib.error.HTTPError as exc:
            last_error = "HTTP %s" % exc.code
            if exc.code == 429:
                time.sleep(2.5 * attempt)
                continue
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        time.sleep(1.2 * attempt)
    raise RuntimeError("translate failed: %s" % last_error)


def main():
    root = Path(__file__).resolve().parent.parent
    catalog_path = root / "data" / "catalog.json"
    cache_path = root / "data" / "ar_cache.json"

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    cache = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    pending = []
    for skill in catalog["skills"]:
        if skill.get("ar"):
            continue
        text = (skill.get("desc") or "").strip()
        if not text:
            skill["ar_desc"] = ""
            continue
        if text in cache and has_arabic(cache[text]):
            skill["ar_desc"] = cache[text]
            continue
        if text not in pending:
            pending.append(text)

    print("unique to translate:", len(pending))
    batches, current, size = [], [], 0
    for text in pending:
        cost = len(urllib.parse.quote(text)) + 3
        if current and (size + cost > MAX_URL_CHARS or len(current) >= BATCH_ITEMS):
            batches.append(current)
            current, size = [], 0
        current.append(text)
        size += cost
    if current:
        batches.append(current)

    print("batches:", len(batches))
    done = failures = 0
    for index, batch in enumerate(batches, start=1):
        try:
            results = translate_batch(batch)
        except Exception as exc:  # noqa: BLE001
            failures += len(batch)
            print("  batch %d/%d FAILED: %s" % (index, len(batches), exc))
            continue
        for source, translated in zip(batch, results):
            translated = (translated or "").strip()
            if has_arabic(translated):
                cache[source] = translated
                done += 1
            else:
                failures += 1
        if index % 10 == 0 or index == len(batches):
            print("  %d/%d batches — translated=%d failed=%d" % (index, len(batches), done, failures))
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        time.sleep(DELAY)

    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    missing = 0
    for skill in catalog["skills"]:
        if skill.get("ar"):
            continue
        text = (skill.get("desc") or "").strip()
        skill["ar_desc"] = cache.get(text, "")
        if not skill["ar_desc"]:
            missing += 1

    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")),
                            encoding="utf-8")
    print("ARABIC DONE translated=%d missing=%d cache=%d" % (done, missing, len(cache)))
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
