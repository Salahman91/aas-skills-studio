#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""محرك البحث الذكي: توسيع استعلام عربي/إنجليزي + ترتيب محلي اختياري بـGemini."""

import json
import math
import re
import urllib.error
import urllib.request

DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]")

# كلمة عربية -> مفاهيم إنجليزية تُضاف إلى الاستعلام
CONCEPTS = {
    "تحليل": ["analysis", "audit", "review", "inspect"],
    "فحص": ["audit", "review", "inspect", "scan", "lint"],
    "تدقيق": ["audit", "review", "compliance"],
    "مراجعة": ["review", "audit", "code review"],
    "مشروع": ["project", "codebase", "repository", "repo"],
    "مشاريع": ["project", "codebase", "repository"],
    "كود": ["code", "source", "programming"],
    "برمجة": ["programming", "coding", "development"],
    "تطوير": ["development", "build", "engineering"],
    "برنامج": ["software", "app", "application"],
    "تطبيق": ["app", "application", "mobile", "desktop"],
    "تطبيقات": ["app", "application", "mobile"],
    "موبايل": ["mobile", "ios", "android", "react native", "flutter"],
    "جوال": ["mobile", "ios", "android"],
    "اندرويد": ["android", "kotlin", "jetpack compose"],
    "أندرويد": ["android", "kotlin", "jetpack compose"],
    "ايفون": ["ios", "swift", "swiftui", "iphone"],
    "آيفون": ["ios", "swift", "swiftui", "iphone"],
    "سطح": ["desktop", "electron", "windows", "macos"],
    "كمبيوتر": ["desktop", "windows", "macos"],
    "واجهة": ["ui", "interface", "frontend", "design"],
    "واجهات": ["ui", "interface", "design"],
    "تصميم": ["design", "ui", "ux", "visual"],
    "تصميم_واجهات": ["ui design", "ux", "interface design"],
    "تجربة": ["ux", "user experience", "usability"],
    "الوان": ["color", "palette", "theme"],
    "ألوان": ["color", "palette", "theme"],
    "خطوط": ["typography", "font"],
    "محتوى": ["content", "copywriting", "editorial"],
    "كتابة": ["writing", "copy", "draft"],
    "مقال": ["article", "blog", "writing"],
    "فيسبوك": ["facebook", "meta", "social media"],
    "فيس": ["facebook", "meta", "social media"],
    "انستقرام": ["instagram", "social media"],
    "تويتر": ["twitter", "x", "social media"],
    "اكس": ["twitter", "x", "social media"],
    "لينكد": ["linkedin", "social media", "b2b"],
    "تيك": ["tiktok", "video", "social media"],
    "يوتيوب": ["youtube", "video", "seo"],
    "سوشيال": ["social media", "content", "marketing"],
    "تواصل": ["social", "communication", "engagement"],
    "تسويق": ["marketing", "growth", "campaign"],
    "اعلان": ["ads", "advertising", "campaign"],
    "إعلان": ["ads", "advertising", "campaign"],
    "بيع": ["sales", "ecommerce", "conversion"],
    "متجر": ["ecommerce", "shop", "store"],
    "تجارة": ["ecommerce", "commerce"],
    "سيو": ["seo", "search engine", "keywords"],
    "بحث": ["search", "seo", "research"],
    "كتالوج": ["catalog", "product"],
    "منتج": ["product", "pm", "roadmap"],
    "ازرار": ["button", "component", "ui"],
    "نموذج": ["model", "ai", "ml", "template"],
    "ذكاء": ["ai", "artificial intelligence", "llm"],
    "اصطناعي": ["ai", "artificial intelligence", "llm"],
    "وكيل": ["agent", "automation", "assistant"],
    "وكلاء": ["agent", "multi-agent", "automation"],
    "برومبت": ["prompt", "prompt engineering"],
    "امن": ["security", "secure", "hardening"],
    "أمن": ["security", "secure", "hardening"],
    "امان": ["security", "safety", "hardening"],
    "أمان": ["security", "safety", "hardening"],
    "اختراق": ["pentest", "red team", "vulnerability"],
    "ثغرة": ["vulnerability", "cve", "exploit"],
    "بيانات": ["data", "analytics", "dataset"],
    "تحليلات": ["analytics", "metrics", "dashboard"],
    "قاعدة": ["database", "sql", "schema"],
    "قواعد": ["database", "sql", "schema"],
    "تقارير": ["report", "reporting", "dashboard"],
    "اختبار": ["testing", "qa", "test automation"],
    "جودة": ["quality", "lint", "review"],
    "اداء": ["performance", "optimization", "benchmark"],
    "أداء": ["performance", "optimization", "benchmark"],
    "سرعة": ["performance", "latency", "optimization"],
    "نشر": ["deploy", "deployment", "ci/cd", "devops"],
    "سحابة": ["cloud", "aws", "azure", "gcp"],
    "خادم": ["server", "infrastructure", "backend"],
    "شبكة": ["network", "http", "api"],
    "واجهة_برمجة": ["api", "rest", "graphql"],
    "اوتوميشن": ["automation", "workflow", "script"],
    "أتمتة": ["automation", "workflow", "script"],
    "سير": ["workflow", "pipeline"],
    "العمل": ["workflow", "process"],
    "ملف": ["file", "document", "docx", "pdf"],
    "ملفات": ["file", "document", "docx", "pdf"],
    "مستند": ["document", "docx", "pdf"],
    "عرض": ["presentation", "slides", "ppt"],
    "عروض": ["presentation", "slides", "ppt"],
    "جدول": ["spreadsheet", "excel", "xlsx"],
    "اكسل": ["excel", "xlsx", "spreadsheet"],
    "صورة": ["image", "graphics", "visual"],
    "صور": ["image", "graphics", "visual"],
    "فيديو": ["video", "animation", "media"],
    "صوت": ["audio", "voice", "speech"],
    "العاب": ["game", "gamedev", "unity"],
    "ألعاب": ["game", "gamedev", "unity"],
    "توثيق": ["documentation", "docs", "readme"],
    "تعليم": ["education", "tutorial", "learning"],
    "مالية": ["finance", "accounting", "budget"],
    "قانون": ["legal", "compliance", "contract"],
    "موارد": ["hr", "resources", "hiring"],
    "توظيف": ["hiring", "recruiting", "career"],
    "مشرف": ["maintainer", "review", "admin"],
    "ادارة": ["management", "manage", "admin"],
    "إدارة": ["management", "manage", "admin"],
    "خطة": ["planning", "plan", "roadmap"],
    "تخطيط": ["planning", "roadmap", "strategy"],
    "استراتيجية": ["strategy", "planning"],
    "هيكلة": ["architecture", "refactor", "structure"],
    "معمارية": ["architecture", "design system", "structure"],
    "اعادة": ["refactor", "rewrite", "restructure"],
    "إعادة": ["refactor", "rewrite", "restructure"],
    "تحسين": ["improve", "optimize", "refactor"],
    "ترقية": ["upgrade", "migration", "modernize"],
    "ترحيل": ["migration", "migrate"],
    "اصلاح": ["fix", "debug", "repair"],
    "إصلاح": ["fix", "debug", "repair"],
    "خطأ": ["bug", "error", "debug"],
    "اخطاء": ["bugs", "errors", "debug"],
    "أخطاء": ["bugs", "errors", "debug"],
    "مراقبة": ["monitoring", "observability", "logs"],
    "لوج": ["logs", "logging", "observability"],
    "نسخ": ["backup", "copy", "clone"],
    "احتياطي": ["backup", "disaster recovery"],
    "صلاحيات": ["permissions", "rbac", "auth"],
    "دخول": ["login", "auth", "authentication"],
    "مصادقة": ["authentication", "oauth", "jwt"],
    "دفع": ["payment", "billing", "stripe"],
    "اشتراك": ["subscription", "billing", "paywall"],
}

STOPWORDS_AR = {
    "أريد", "اريد", "أحتاج", "احتاج", "مهارة", "مهارات", "مهاره", "عمل", "يعمل", "تعمل",
    "ممكن", "من", "في", "على", "عن", "الى", "إلى", "مع", "او", "أو", "و", "ثم", "اي", "أي",
    "شي", "شيء", "افضل", "أفضل", "جيد", "جيدة", "كيف", "ماذا", "هل", "لي", "لدى", "عندي",
    "ابحث", "بحث", "عن", "هذا", "هذه", "التي", "الذي", "tutorial", "help", "need", "want",
}

GEMINI_ENDPOINT = ("https://generativelanguage.googleapis.com/v1beta/models/"
                   "{model}:generateContent?key={key}")

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite",
                 "gemini-2.0-flash"]


def normalize(text):
    text = (text or "").lower()
    text = DIACRITICS.sub("", text)
    text = re.sub(r"[أإآٱ]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ؤ", "و", text)
    text = re.sub(r"ئ", "ي", text)
    text = re.sub(r"ة", "ه", text)
    return text


def query_tokens(query):
    raw = re.split(r"[\s,،.;؛:!؟?()\[\]\-_/\\]+", query.strip())
    tokens = [t for t in raw if t and len(t) > 1]
    expanded = []
    seen = set()

    def add(token):
        token = token.strip()
        if not token or token in seen:
            return
        seen.add(token)
        expanded.append(token)

    for token in tokens:
        norm = normalize(token)
        if norm in STOPWORDS_AR or token in STOPWORDS_AR:
            continue
        add(norm)
        for key, values in CONCEPTS.items():
            key_norm = normalize(key)
            if key_norm in norm or norm in key_norm:
                for value in values:
                    for piece in value.split():
                        add(normalize(piece))
    return expanded


_DF_CACHE = {}


def _document_frequency(skills):
    """تردد كل كلمة داخل الفهرس — يُحسب مرة واحدة لترجيح الكلمات النادرة."""
    key = id(skills)
    cached = _DF_CACHE.get(key)
    if cached is not None:
        return cached

    df = {}
    for skill in skills:
        text = normalize(" ".join([
            skill["name"],
            skill["desc"],
            skill.get("ar_clear") or "",
            skill["category"].replace("-", " "),
        ]))
        for token in set(re.findall(r"[a-z0-9\u0600-\u06ff]{2,}", text)):
            df[token] = df.get(token, 0) + 1
    _DF_CACHE[key] = df
    return df


def _idf(df, total, token):
    return math.log((total + 1) / (df.get(token, 1) + 1)) + 1.0


def score_skills(skills, query, limit=60):
    tokens = query_tokens(query)
    if not tokens:
        return []

    total = len(skills)
    df = _document_frequency(skills)
    phrase = normalize(query.strip())
    weights = {token: _idf(df, total, token) for token in tokens}

    scored = []
    for skill in skills:
        name = normalize(skill["name"])
        desc = normalize(skill["desc"] + " " + (skill.get("ar_clear") or ""))
        cat = normalize(skill["category"].replace("-", " "))

        score = 0.0
        matched = 0
        for token in tokens:
            weight = weights[token]
            hit = False
            if token in name:
                score += weight * 2.6
                hit = True
            if token in desc:
                score += weight * 1.0
                hit = True
            if token in cat:
                score += weight * 1.3
                hit = True
            if hit:
                matched += 1

        if not matched:
            continue
        score += matched * 0.8
        if len(phrase) > 4 and phrase in name:
            score += 6.0
        elif len(phrase) > 4 and phrase in desc:
            score += 2.0
        scored.append((score, skill))

    scored.sort(key=lambda item: (-item[0], item[1]["name"].lower()))
    return [skill for _score, skill in scored[:limit]]


def gemini_rerank(api_key, model, query, candidates, timeout=45):
    """يعيد (فهم الطلب، [(id, سبب)], خطأ)."""
    if not api_key:
        return None, [], "لا يوجد مفتاح Gemini"

    lines = []
    for skill in candidates:
        desc = (skill.get("ar_clear") or skill["desc"] or "")[:220].replace("\n", " ")
        lines.append("- %s | %s | %s" % (skill["id"], skill.get("category"), desc))

    prompt = (
        "أنت مساعد يختار مهارات برمجية من مكتبة لمهمة المستخدم.\n"
        "طلب المستخدم: \"%s\"\n\n"
        "المهارات المرشحة (id | التصنيف | الوصف):\n%s\n\n"
        "اختر أفضل 8 مهارات فقط، مرتبة من الأنسب للأقل. "
        "لكل مهارة اكتب سبباً عربياً قصيراً (حتى 15 كلمة) يوضح لماذا تناسب طلبه. "
        "وأضف حقلاً \"understanding\" بجملة عربية واحدة تلخّص ما فهمته من الطلب.\n"
        "أعد JSON فقط بالشكل: "
        "{\"understanding\":\"...\",\"results\":[{\"id\":\"...\",\"why\":\"...\"}]}"
        % (query, "\n".join(lines))
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    request = urllib.request.Request(
        GEMINI_ENDPOINT.format(model=model, key=api_key),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "AAS-Skills-Studio/2.4"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = json.loads(exc.read().decode("utf-8"))["error"]["message"]
        except Exception:
            pass
        return None, [], "فشل النموذج (%s)\n%s" % (exc.code, detail or "تحقق من المفتاح")
    except urllib.error.URLError:
        return None, [], "تعذّر الوصول إلى النموذج — تحقّق من الشبكة"
    except Exception as exc:  # noqa: BLE001
        return None, [], "خطأ غير متوقع: %s" % exc

    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None, [], "استجابة غير متوقعة من النموذج"

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"```$", "", text).strip()
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None, [], "تعذّر قراءة استجابة النموذج"
        try:
            data = json.loads(match.group(0))
        except Exception:
            return None, [], "تعذّر قراءة استجابة النموذج"

    valid_ids = {skill["id"] for skill in candidates}
    results = []
    for item in data.get("results", []):
        if isinstance(item, dict) and item.get("id") in valid_ids:
            results.append((item["id"], (item.get("why") or "").strip()))
    understanding = (data.get("understanding") or "").strip()
    if not results:
        return understanding, [], "لم يجد النموذج نتيجة مناسبة"
    return understanding, results, ""
