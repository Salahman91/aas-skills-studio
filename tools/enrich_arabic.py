#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""يحسّن الوصف العربي ويستخرج المصطلحات الإنجليزية لكل مهارة.

- يعالج الأوصاف القالبية الغامضة (Curated upstream guidance …) بصياغة عربية واضحة.
- يضيف سياق القسم للمهارات ذات الوصف القصير جداً.
- يستخرج المصطلحات الإنجليزية لعرضها في سطر مستقل داخل التطبيق.
"""

import json
import re
import sys
from pathlib import Path

TECH_TERMS = {
    # لغات وأطر وأدوات شائعة تظهر بحرف كبير أول فقط
    "React", "Flutter", "Android", "Docker", "Kubernetes", "Python", "JavaScript",
    "TypeScript", "Node", "Expo", "SwiftUI", "Compose", "Semgrep", "OWASP", "Cursor",
    "Claude", "Codex", "Gemini", "Figma", "Stitch", "Makepad", "Avalonia", "Electron",
    "Tauri", "Unity", "Unreal", "Godot", "Phoenix", "Rails", "Django", "FastAPI", "Next",
    "Vue", "Angular", "Svelte", "Tailwind", "Kotlin", "Swift", "Java", "Go", "Rust", "PHP",
    "Ruby", "Scala", "Elixir", "Haskell", "Julia", "Terraform", "Ansible", "Jenkins",
    "Postgres", "PostgreSQL", "MySQL", "SQLite", "Redis", "MongoDB", "Supabase", "Stripe",
    "Figma", "Playwright", "Selenium", "Appium", "Pytest", "Jest", "Vitest", "Cypress",
    "Next.js", "Node.js", "Express", "NestJS", "Laravel", "Spring", "Flask", "Pandas",
    "PyTorch", "TensorFlow", "OpenAI", "Anthropic", "LangChain", "LlamaIndex", "Chroma",
    "Vercel", "Netlify", "Cloudflare", "Azure", "GCP", "Nginx", "Linux", "Windows", "macOS",
    "iOS", "iPadOS", "VisionOS", "Airflow", "Kafka", "Spark", "dbt", "Snowflake",
}

STOPWORDS = {
    "the", "and", "for", "use", "when", "with", "this", "that", "you", "your", "are", "can",
    "will", "from", "into", "its", "all", "not", "but", "they", "them", "has", "have", "was",
    "were", "our", "out", "any", "per", "who", "how", "why", "what", "which", "their", "there",
    "then", "than", "also", "each", "other", "such", "may", "must", "should", "would", "could",
    "does", "did", "has", "had", "been", "being", "about", "across", "after", "before", "while",
    "where", "under", "over", "between", "within", "without", "through", "these", "those",
    "more", "most", "some", "only", "just", "like", "make", "makes", "made", "get", "gets",
    "run", "runs", "new", "one", "two", "own", "same", "very", "well", "back", "even", "still",
    "help", "helps", "using", "used", "true", "false", "none", "null", "yes", "via", "etc",
    "curated", "authorized", "main", "design", "review", "build", "create", "write", "apply",
    "expert", "specializing", "guidance", "upstream", "workflow", "matches", "user", "goal",
    "production", "senior", "modern", "advanced", "complete", "guide", "includes", "including",
}

PAT_CURATED = re.compile(r"^Curated upstream guidance for (?P<x>.+?);?\s*use when", re.I)
PAT_USE_WHEN = re.compile(r"^Use when working with (?P<x>.+?)\.?$", re.I)


def looks_technical(token):
    if token in TECH_TERMS or token.lower() in {t.lower() for t in TECH_TERMS}:
        return True
    if len(token) < 2:
        return False
    if token.isupper() and 2 <= len(token) <= 8:
        return True
    if re.search(r"[A-Z]", token[1:]):
        return True
    if re.search(r"[0-9+#]", token):
        return True
    return False


def terms_from(text):
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}", text or "")
    out = []
    seen = set()
    for token in tokens:
        clean = token.strip(".-")
        if not clean or len(clean) < 2:
            continue
        if clean.lower() in STOPWORDS:
            continue
        if not looks_technical(clean):
            continue
        if clean.lower() in seen:
            continue
        seen.add(clean.lower())
        out.append(clean)
        if len(out) >= 8:
            break
    return out


def main():
    root = Path(__file__).resolve().parent.parent
    catalog_path = root / "data" / "catalog.json"
    groups = json.loads((root / "data" / "groups.json").read_text(encoding="utf-8"))["groups"]

    sub_of_cat = {}
    for group in groups:
        for sub in group["subs"]:
            for cat in sub["cats"]:
                sub_of_cat[cat] = (group, sub)

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    improved = 0

    for skill in catalog["skills"]:
        arabic = (skill.get("ar") or skill.get("ar_desc") or "").strip()
        desc = (skill.get("desc") or "").strip()
        group, sub = sub_of_cat.get(skill["category"], (None, None))
        sub_title = sub["ar"] if sub else skill["category"]

        match = PAT_CURATED.match(desc) or PAT_USE_WHEN.match(desc)
        if match:
            topic = match.group("x").strip()
            arabic = ("مهارة جاهزة حول «%s» مأخوذة من مصدر خارجي. "
                      "استخدمها عندما تكون مهمتك متعلقة بهذا الموضوع." % topic)
            improved += 1
        elif len(arabic) < 45 and not re.search(r"[A-Za-z]{4,}", arabic):
            arabic = "مهارة في قسم «%s»: %s" % (sub_title, arabic)
            improved += 1

        if not arabic:
            arabic = ("مهارة في قسم «%s». لا يوجد وصف نصي في فهرس المستودع؛ "
                      "افتح SKILL.md لمعرفة التفاصيل." % sub_title)

        skill["ar_clear"] = arabic
        skill["terms"] = terms_from(desc)

    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("ENRICH OK improved=%d skills=%d" % (improved, len(catalog["skills"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
