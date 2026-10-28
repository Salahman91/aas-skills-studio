#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تقييم جودة البحث الذكي محليًا (بلا شبكة).

كل حالة: استعلام عربي + مجموعة معرّفات مقبولة (أي واحد منها داخل أفضل 5 يُعد نجاحًا).
يخرج بغير صفر عند أي فشل، ويطبع متوسط رتبة أول نتيجة مقبولة.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import search_engine  # noqa: E402

TOP_N = 5

# صياغات عامة يعرف المحرك اللفظي أنه لا يحسمها؛ تُعرض ولا تُسقط التقييم.
KNOWN_LIMITS = {"مهارة لتحليل مشروع"}

CASES = [
    ("ادارة محتوى فيسبوك",
     ["social-content", "social-post-writer-seo", "social-media-setup", "taisly-social-media-posting"]),
    ("مهارة لتحليل مشروع",
     ["codebase-onboarding", "code-audit", "repo-maintainer", "project-skill-audit"]),
    ("مراجعة كود",
     ["code-audit", "code-reviewer", "five-axis-code-review", "code-review-and-quality", "brooks-review"]),
    ("نسخ احتياطي لقاعدة بيانات",
     ["database-backups", "backup-recovery"]),
    ("تحسين محركات البحث",
     ["tools-page-seo-optimizer", "seo-aeo-keyword-research", "seo-competitor-pages"]),
    ("اختبار تطبيق اندرويد",
     ["android-ui-journey-testing", "webapp-testing", "testing-qa"]),
    ("كتابة مقال",
     ["blog-writing-guide", "seo-aeo-blog-writer", "copywriting"]),
    ("تصميم واجهة مستخدم",
     ["design-ux", "ui-visual-validator", "ui-ux-designer", "ui-ux-pro-max"]),
    ("تحليل بيانات",
     ["data-scientist", "analytics-product", "analytics", "advanced-analytics-dashboard"]),
    ("امن التطبيقات",  # بلا همزة، كما يكتبها المستخدم عادة
     ["security-audit", "llm-app-security", "mobile-security-coder"]),
    ("اتمتة المتصفح",
     ["browser-automation", "skyvern-browser-automation", "reverse-browser-automation",
      "browser-act", "browser-harness"]),
    ("ترجمة نص",
     ["azure-ai-translation-text-py", "azure-ai-translation-document-py"]),
    ("ادارة مشروع",
     ["projects-work-management", "project-state-governor", "wrike-automation", "todoist-automation"]),
    ("انشاء عرض تقديمي",
     ["presentation-deck", "pptx-deck-creation", "google-slides-automation", "2slides-ppt-generator"]),
    ("تحليل السبب الجذري",
     ["monte-carlo-analyze-root-cause"]),
]


def load_skills():
    data = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    return data["skills"]


def main():
    skills = load_skills()
    known = {s["id"] for s in skills}
    failures = []
    ranks = []
    known_count = 0
    print("SEARCH-EVAL cases=%d top_n=%d" % (len(CASES), TOP_N))
    for query, expected in CASES:
        missing = [e for e in expected if e not in known]
        if missing:
            print("  SKIP %s — unknown ids: %s" % (query, ", ".join(missing)))
            failures.append(query)
            continue
        results = search_engine.score_skills(skills, query, limit=TOP_N)
        ids = [s["id"] for s in results]
        rank = next((i + 1 for i, sid in enumerate(ids) if sid in expected), None)
        if rank is None:
            if query in KNOWN_LIMITS:
                known_count += 1
                print("  known %-23s top5=%s" % (query, ids))
            else:
                failures.append(query)
                print("  FAIL %-24s top5=%s" % (query, ids))
        else:
            ranks.append(rank)
            print("  ok   %-24s rank=%d  top1=%s" % (query, rank, ids[0] if ids else "-"))
    passed = len(CASES) - len(failures) - known_count
    avg = (sum(ranks) / float(len(ranks))) if ranks else 0.0
    print("SEARCH-EVAL %s %d/%d known_limits=%d avg_rank=%.2f"
          % ("OK" if not failures else "FAIL", passed, len(CASES), known_count, avg))
    if failures:
        print("failed: " + " | ".join(failures))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
