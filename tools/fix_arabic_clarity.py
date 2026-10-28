#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تحسين وضوح الوصف العربي في data/catalog.json — يعمل محليًا بلا شبكة.

- يطبّق الأوصاف اليدوية من data/ar_overrides.json (مصدرها بشري، موثوق).
- يوسّع أي وصف عربي أقصر من 25 حرفًا أو خالٍ من الحروف العربية بجملة توضّح
  التصنيف وطريقة الاستخدام، دون اختلاق قدرات غير مذكورة في الفهرس.
- عديم الأثر عند التكرار (idempotent): التشغيل الثاني لا يغيّر شيئًا.
"""
import json
import re
from pathlib import Path

VAGUE = re.compile(r"Curated upstream guidance|Curated guidance", re.I)
ARABIC = re.compile(r"[\u0600-\u06FF]")
MIN_LEN = 25
FALLBACK_SUFFIX = " — مهارة ضمن تصنيف «%s»؛ راجع ملف SKILL.md الخاص بها لخطوات التنفيذ."


def project_root():
    return Path(__file__).resolve().parent.parent


def load_overrides(root=None):
    root = root or project_root()
    path = root / "data" / "ar_overrides.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("skills", data)


def category_ar(catalog):
    return {c.get("id"): c.get("ar") or c.get("id") for c in catalog.get("categories", [])}


def _fallback_text(skill, cat_ar):
    name = skill.get("name") or skill.get("id") or ""
    base = (skill.get("ar_clear") or "").strip().rstrip(".")
    if base and ARABIC.search(base):
        return base + (FALLBACK_SUFFIX % cat_ar)
    return "مهارة %s ضمن تصنيف «%s»؛ راجع ملف SKILL.md الخاص بها لمعرفة وظيفتها وخطوات تنفيذها." % (
        name, cat_ar)


def apply_clarity(catalog, overrides=None):
    """يعدّل catalog في الذاكرة ويعيد إحصاءات التغيير."""
    if overrides is None:
        overrides = load_overrides()
    cats = category_ar(catalog)
    stats = {"override": 0, "expanded": 0, "no_arabic": 0}
    for skill in catalog.get("skills", []):
        sid = skill.get("id")
        manual = overrides.get(sid)
        if manual:
            text = manual if isinstance(manual, str) else (manual.get("ar") or "")
            text = text.strip()
            if text and text != (skill.get("ar_clear") or "").strip():
                skill["ar_clear"] = text
                skill["ar_source"] = "manual"
                stats["override"] += 1
            elif text:
                skill.setdefault("ar_source", "manual")
            continue

        current = (skill.get("ar_clear") or "").strip()
        cat = cats.get(skill.get("category"), skill.get("category") or "")
        if not ARABIC.search(current):
            skill["ar_clear"] = _fallback_text(skill, cat)
            skill["ar_source"] = "generated"
            stats["no_arabic"] += 1
        elif len(current) < MIN_LEN:
            skill["ar_clear"] = _fallback_text(skill, cat)
            skill["ar_source"] = "generated"
            stats["expanded"] += 1
    return stats


def clarity_problems(catalog):
    """قائمة بمشكلات الوضوح المتبقية (تستخدمها أداة التحقق)."""
    problems = []
    for skill in catalog.get("skills", []):
        text = (skill.get("ar_clear") or "").strip()
        sid = skill.get("id")
        if not ARABIC.search(text):
            problems.append("%s: لا يحتوي وصفًا عربيًا" % sid)
        elif len(text) < MIN_LEN:
            problems.append("%s: الوصف العربي أقصر من %d حرفًا" % (sid, MIN_LEN))
        if VAGUE.search(skill.get("desc") or "") and skill.get("ar_source") != "manual":
            problems.append("%s: وصف المصدر عام ولم يُستبدل بوصف يدوي" % sid)
    return problems


def main():
    root = project_root()
    path = root / "data" / "catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    stats = apply_clarity(catalog)
    remaining = clarity_problems(catalog)
    path.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8")
    print("CLARITY overrides=%d expanded=%d no_arabic=%d remaining=%d"
          % (stats["override"], stats["expanded"], stats["no_arabic"], len(remaining)))
    for item in remaining[:10]:
        print("  - " + item)
    return 0 if not remaining else 7


if __name__ == "__main__":
    raise SystemExit(main())
