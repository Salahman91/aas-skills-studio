#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""يبني data/catalog.json الكامل من skills_index.json الرسمي للمستودع."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fix_arabic_clarity import apply_clarity  # noqa: E402

CATEGORY_AR = {
    "security": "الأمان",
    "development": "التطوير",
    "business": "الأعمال",
    "devops": "DevOps والنشر",
    "cloud": "السحابة",
    "ai-ml": "الذكاء الاصطناعي وتعلّم الآلة",
    "marketing": "التسويق",
    "content": "المحتوى",
    "workflow": "سير العمل",
    "web-development": "تطوير الويب",
    "automation": "الأتمتة",
    "productivity": "الإنتاجية",
    "data": "البيانات",
    "testing": "الاختبار",
    "media": "الوسائط",
    "design-it": "أنماط التصميم البصري",
    "backend": "الواجهة الخلفية",
    "design": "التصميم",
    "code-quality": "جودة الكود",
    "api-integration": "تكامل واجهات API",
    "frontend": "الواجهة الأمامية",
    "mobile": "تطبيقات الموبايل",
    "meta": "مهارات وصفية (Meta)",
    "agent-orchestration": "تنسيق الوكلاء",
    "architecture": "المعمارية",
    "seo": "تحسين محركات البحث",
    "project-management": "إدارة المشاريع",
    "research": "البحث",
    "ai-agents": "وكلاء الذكاء الاصطناعي",
    "finance": "المالية",
    "engineering": "الهندسة",
    "game-development": "تطوير الألعاب",
    "database": "قواعد البيانات",
    "reliability": "الموثوقية",
    "health": "الصحة",
    "code": "لغات البرمجة",
    "super-code": "الكود المكثّف",
    "granular-workflow-bundle": "حزم سير عمل دقيقة",
    "data-ai": "البيانات والذكاء الاصطناعي",
    "front-end": "الواجهة الأمامية",
    "science": "العلوم",
    "blockchain": "البلوكشين",
    "framework": "أطر العمل",
    "planning": "التخطيط",
    "legal": "القانون",
    "uncategorized": "غير مصنّفة",
    "test-automation": "أتمتة الاختبار",
    "workflow-bundle": "حزم سير العمل",
    "mcp": "بروتوكول MCP",
    "agent-squad": "فرق الوكلاء",
    "operations": "العمليات",
    "browser-automation": "أتمتة المتصفح",
    "developer-tools": "أدوات المطوّر",
    "document-verification": "التحقق من المستندات",
    "data-science": "علم البيانات",
    "memory": "الذاكرة",
    "development-and-testing": "التطوير والاختبار",
    "leiloeiro": "المزايدات",
    "database-processing": "معالجة قواعد البيانات",
    "shopping": "التسوّق",
    "agent-behavior": "سلوك الوكيل",
    "writing": "الكتابة",
    "graphics-processing": "معالجة الرسوميات",
    "voice-agents": "الوكلاء الصوتيون",
    "product": "المنتج",
    "agent-persona": "شخصية الوكيل",
    "education": "التعليم",
    "monopoly": "Monopoly",
    "document-processing": "معالجة المستندات",
    "debugging": "التنقيح",
    "presentation-processing": "معالجة العروض",
    "app-builder": "بناء التطبيقات",
    "ecommerce": "التجارة الإلكترونية",
    "business-strategy": "استراتيجية الأعمال",
    "growth": "النمو",
    "databases": "قواعد البيانات",
    "analysis": "التحليل",
    "creative": "الإبداع",
    "andruia": "Andruia",
    "spreadsheet-processing": "معالجة الجداول",
    "agent-tooling": "أدوات الوكيل",
    "knowledge-management": "إدارة المعرفة",
    "skill-authoring": "تأليف المهارات",
    "career-jobs": "الوظائف والمسار المهني",
    "communication": "التواصل",
    "reasoning": "الاستدلال",
    "quality": "الجودة",
    "personal-development": "التطوير الشخصي",
    "agent-evaluation": "تقييم الوكلاء",
    "pentest-tools": "أدوات اختبار الاختراق",
    "media-processing": "معالجة الوسائط",
    "ml-ops": "تشغيل نماذج التعلّم",
    "data-engineering": "هندسة البيانات",
    "ai": "الذكاء الاصطناعي",
    "consulting": "الاستشارات",
    "core-dev": "التطوير الأساسي",
    "collaboration": "التعاون",
    "travel": "السفر",
    "video": "الفيديو",
    "fullstack": "Fullstack",
    "web": "الويب",
    "prompt-engineering": "هندسة الأوامر",
    "ai-research": "أبحاث الذكاء الاصطناعي",
    "tool-quality": "جودة الأدوات",
    "content-writing": "كتابة المحتوى",
    "tools": "الأدوات",
    "general": "عام",
    "ai-testing": "اختبار الذكاء الاصطناعي",
    "reverse-engineering": "الهندسة العكسية",
    "lifestyle": "نمط الحياة",
    "orchestration": "التنسيق",
    "office-productivity": "إنتاجية المكتب",
    "coding": "البرمجة",
    "context-optimization": "تحسين السياق",
    "product-management": "إدارة المنتج",
}


def main():
    root = Path(__file__).resolve().parent.parent
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else root.parent / ".openclaw/tmp/aas/skills_index.json"
    index = json.loads(source.read_text(encoding="utf-8"))

    curated_path = root / "data" / "skills.json"
    curated = {}
    if curated_path.exists():
        old = json.loads(curated_path.read_text(encoding="utf-8"))
        for skill in old.get("skills", []):
            curated[skill["id"]] = skill

    skills = []
    counts = {}
    for entry in index:
        category = entry.get("category") or "uncategorized"
        counts[category] = counts.get(category, 0) + 1
        item = {
            "id": entry["id"],
            "name": entry.get("name") or entry["id"],
            "category": category,
            "desc": (entry.get("description") or "").strip(),
            "risk": entry.get("risk") or "unknown",
            "path": entry.get("path") or ("skills/" + entry["id"]),
        }
        extra = curated.get(entry["id"])
        if extra:
            item["ar"] = extra.get("function_ar", "")
            item["invocation"] = extra.get("invocation", "")
            item["install_cli"] = extra.get("install_cli", "")
            item["group"] = extra.get("group", "")
        skills.append(item)

    categories = [
        {
            "id": cid,
            "ar": CATEGORY_AR.get(cid, cid),
            "count": counts[cid],
        }
        for cid in sorted(counts, key=lambda c: (-counts[c], c))
    ]

    catalog = {
        "repo": "sickn33/agentic-awesome-skills",
        "repo_url": "https://github.com/sickn33/agentic-awesome-skills",
        "branch": "main",
        "total": len(skills),
        "categories": categories,
        "skills": skills,
    }

    clarity = apply_clarity(catalog)

    out = root / "data" / "catalog.json"
    out.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("CATALOG OK skills=%d categories=%d bytes=%d curated=%d clarity=%d"
          % (len(skills), len(categories), out.stat().st_size, len(curated),
             clarity["override"] + clarity["expanded"] + clarity["no_arabic"]))


if __name__ == "__main__":
    main()
