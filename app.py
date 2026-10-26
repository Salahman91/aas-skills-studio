#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AAS Skills Studio 2
عارض وتنزيل مهارات مستودع sickn33/agentic-awesome-skills:
كل المهارات (2750) مع تصنيفها، اختيار متعدد، تنزيل الكل،
وإضافة المهارة مباشرة إلى مجلد مهارات برنامج مثل AutoClaw أو Antigravity أو OpenCode.

Standard library only (tkinter) so the one-file PyInstaller build stays reliable.
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

import search_engine

APP_NAME = "AAS Skills Studio"
APP_VERSION = "2.0.0"

BG = "#0B0D12"
PANEL = "#12151C"
PANEL_2 = "#171B24"
PANEL_3 = "#1D222D"
BORDER = "#252B36"
ROW_BORDER = "#1B2029"
TEXT = "#E6EAF2"
MUTED = "#8B94A7"
ACCENT = "#5EEAD4"
ACCENT_DIM = "#1F4B45"
VIOLET = "#A78BFA"
DANGER = "#F87171"
OK = "#34D399"
WARN = "#FBBF24"

UI_FONT = "Segoe UI"
MONO_FONT = "Consolas"

USER_AGENT = "AAS-Skills-Studio/2.0 (Windows)"
API_SUBTREE = "https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"
RAW_FILE = "https://raw.githubusercontent.com/{repo}/{branch}/{path}"
HTTP_TIMEOUT = 45

RENDER_CAP = 250

# مسارات موثّقة من docs/users/getting-started.md في المستودع نفسه.
TARGETS = [
    {"id": "custom", "label": "مجلد مخصص…", "en": "Custom folder…", "kind": "custom", "path": ""},
    {"id": "autoclaw", "label": "AutoClaw", "en": "AutoClaw", "kind": "home",
     "path": ".openclaw-autoclaw/skills"},
    {"id": "agents", "label": "OpenClaw / Antigravity", "en": "OpenClaw / Antigravity",
     "kind": "home", "path": ".agents/skills"},
    {"id": "agy", "label": "Antigravity CLI (agy)", "en": "Antigravity CLI (agy)", "kind": "home",
     "path": ".gemini/antigravity-cli/skills"},
    {"id": "claude", "label": "Claude Code", "en": "Claude Code", "kind": "home",
     "path": ".claude/skills"},
    {"id": "codex", "label": "Codex CLI", "en": "Codex CLI", "kind": "home",
     "path": ".codex/skills"},
    {"id": "gemini", "label": "Gemini CLI", "en": "Gemini CLI", "kind": "home",
     "path": ".gemini/skills"},
    {"id": "kiro", "label": "Kiro (CLI/IDE)", "en": "Kiro (CLI/IDE)", "kind": "home",
     "path": ".kiro/skills"},
    {"id": "autohand", "label": "Autohand Code", "en": "Autohand Code", "kind": "home",
     "path": ".autohand/skills"},
    {"id": "cursor", "label": "Cursor (داخل المشروع)", "en": "Cursor (project)",
     "kind": "project", "path": ".cursor/skills"},
    {"id": "opencode", "label": "OpenCode (داخل المشروع)", "en": "OpenCode (project)",
     "kind": "project",
     "path": ".agents/skills"},
    {"id": "adal", "label": "AdaL CLI (داخل المشروع)", "en": "AdaL CLI (project)",
     "kind": "project", "path": ".adal/skills"},
]

TARGET_BY_ID = {target["id"]: target for target in TARGETS}

CATEGORY_EN = {
    "ai-ml": "AI & Machine Learning",
    "devops": "DevOps",
    "seo": "SEO",
    "mcp": "MCP",
    "api-integration": "API Integration",
    "code-quality": "Code Quality",
    "web-development": "Web Development",
    "game-development": "Game Development",
    "project-management": "Project Management",
    "agent-orchestration": "Agent Orchestration",
    "ai-agents": "AI Agents",
    "data-science": "Data Science",
    "ml-ops": "MLOps",
    "design-it": "Visual Design Styles",
    "front-end": "Front-end",
    "backend": "Backend",
    "uncategorized": "Uncategorized",
    "super-code": "Super Code",
    "meta": "Meta Skills",
    "test-automation": "Test Automation",
    "browser-automation": "Browser Automation",
    "developer-tools": "Developer Tools",
    "legal": "Legal",
    "finance": "Finance",
    "ecommerce": "E-commerce",
    "office-productivity": "Office Productivity",
    "prompt-engineering": "Prompt Engineering",
}


def category_en(cat_id):
    if cat_id in CATEGORY_EN:
        return CATEGORY_EN[cat_id]
    return cat_id.replace("-", " ").replace("_", " ").title()


# --------------------------------------------------------------------------- #
# data / settings
# --------------------------------------------------------------------------- #
def resource_path(*parts):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
        bundled = base.joinpath("data", *parts)
        if bundled.exists():
            return bundled
        return base.joinpath(*parts)
    base = Path(__file__).resolve().parent
    base = base / "data" if (base / "data").is_dir() else base
    return base.joinpath(*parts)


def load_catalog():
    with open(resource_path("catalog.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_groups():
    with open(resource_path("groups.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)["groups"]


def settings_path():
    root = os.environ.get("APPDATA") or str(Path.home())
    return Path(root) / "AAS-Skills-Studio" / "settings.json"


def load_settings():
    try:
        with open(settings_path(), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_settings(data):
    try:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# github access
# --------------------------------------------------------------------------- #
class Repo:
    def __init__(self, repo, branch, token=None):
        self.repo = repo
        self.branch = branch
        self.token = (token or "").strip()
        self._files_cache = {}

    # -- low level ---------------------------------------------------------
    def _headers(self, accept=None):
        headers = {"User-Agent": USER_AGENT}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if accept:
            headers["Accept"] = accept
        return headers

    def _read(self, response):
        data = bytearray()
        while True:
            chunk = response.read(65536)
            if not chunk:
                break
            data.extend(chunk)
        return bytes(data)

    def _get(self, url, accept=None):
        request = urllib.request.Request(url, headers=self._headers(accept))
        response = urllib.request.urlopen(request, timeout=HTTP_TIMEOUT)
        try:
            return self._read(response)
        finally:
            response.close()

    # -- api ---------------------------------------------------------------
    def files_for(self, skill_path):
        """Return relative file paths inside one skill folder."""
        skill_path = skill_path.strip("/")
        if skill_path in self._files_cache:
            return self._files_cache[skill_path]

        ref = urllib.parse.quote("%s:%s" % (self.branch, skill_path), safe=":/")
        payload = json.loads(self._get(API_SUBTREE.format(repo=self.repo, ref=ref)).decode("utf-8"))
        if "tree" not in payload:
            raise RuntimeError("استجابة GitHub غير متوقعة")
        files = [entry["path"] for entry in payload["tree"] if entry.get("type") == "blob"]
        self._files_cache[skill_path] = files
        return files

    def download_file(self, repo_path, target):
        blob = self._get(RAW_FILE.format(repo=self.repo, branch=self.branch, path=repo_path))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        return len(blob)

    def download_skill(self, skill, dest_root, progress=None, skip_existing=True):
        folder = Path(dest_root) / skill["id"]
        if skip_existing and (folder / "SKILL.md").exists() and (folder / "SKILL.md").stat().st_size > 0:
            return 0, 0, folder, "موجودة"

        skill_path = skill["path"].strip("/")
        try:
            files = self.files_for(skill_path)
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                raise RuntimeError("تجاوز حد طلبات GitHub — أضف رمز وصول من الإعدادات")
            if exc.code == 404:
                raise RuntimeError("المهارة غير موجودة في المستودع")
            raise
        if not files:
            files = ["SKILL.md"]

        ok = fail = 0
        for index, rel in enumerate(files, start=1):
            if progress:
                progress(index, len(files), rel)
            try:
                self.download_file(skill_path + "/" + rel, folder / rel)
                ok += 1
            except Exception:
                fail += 1
        return ok, fail, folder, ""


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def cli_selftest():
    try:
        catalog = load_catalog()
    except Exception as exc:
        print("SELFTEST FAIL cannot load catalog: %s" % exc)
        return 2

    skills = catalog.get("skills") or []
    categories = catalog.get("categories") or []
    if not skills or not categories:
        print("SELFTEST FAIL empty catalog")
        return 3

    cat_ids = {c["id"] for c in categories}
    seen = set()
    problems = []
    for skill in skills:
        for key in ("id", "name", "category", "desc", "risk", "path"):
            if not skill.get(key):
                problems.append("%s: missing %s" % (skill.get("id", "?"), key))
        if skill.get("category") not in cat_ids:
            problems.append("%s: unknown category" % skill.get("id"))
        if skill.get("id") in seen:
            problems.append("%s: duplicate id" % skill.get("id"))
        seen.add(skill.get("id"))

    if problems:
        print("SELFTEST FAIL")
        for item in problems[:20]:
            print("  - " + item)
        return 4

    try:
        groups = load_groups()
    except Exception as exc:
        print("SELFTEST FAIL cannot load groups: %s" % exc)
        return 5
    assigned = {cat for group in groups for sub in group["subs"] for cat in sub["cats"]}
    unmapped = sorted(cat_ids - assigned)
    if unmapped:
        print("SELFTEST FAIL unmapped categories: %s" % ", ".join(unmapped[:10]))
        return 6

    curated = sum(1 for s in skills if s.get("ar"))
    subs = sum(len(group["subs"]) for group in groups)
    print("SELFTEST OK skills=%d categories=%d curated=%d groups=%d subs=%d"
          % (len(skills), len(categories), curated, len(groups), subs))
    return 0


def cli_download_test(skill_id, dest):
    catalog = load_catalog()
    skill = next((s for s in catalog["skills"] if s["id"] == skill_id), None)
    if skill is None:
        print("DOWNLOAD-TEST FAIL unknown skill id: %s" % skill_id)
        return 2

    repo = Repo(catalog["repo"], catalog.get("branch", "main"), load_settings().get("token"))
    dest_root = Path(dest).expanduser().resolve()
    dest_root.mkdir(parents=True, exist_ok=True)
    print("downloading %s -> %s" % (skill_id, dest_root / skill_id))
    try:
        ok, fail, folder, note = repo.download_skill(
            skill, dest_root, skip_existing=False,
            progress=lambda i, n, name: print("  [%d/%d] %s" % (i, n, name)))
    except Exception as exc:
        print("DOWNLOAD-TEST FAIL %s" % exc)
        return 3

    skill_md = folder / "SKILL.md"
    size = skill_md.stat().st_size if skill_md.exists() else 0
    print("files ok=%d failed=%d folder=%s SKILL.md=%d bytes" % (ok, fail, folder, size))
    if size <= 0:
        print("DOWNLOAD-TEST FAIL SKILL.md missing or empty")
        return 4
    print("DOWNLOAD-TEST OK")
    return 0


def cli_bulk_test(count, dest):
    """يتحقق من حلقة التنزيل المتعدد (نفس مسار زر «تنزيل المحدد»)."""
    catalog = load_catalog()
    skills = catalog["skills"][:count]
    dest_root = Path(dest).expanduser().resolve()
    dest_root.mkdir(parents=True, exist_ok=True)
    print("bulk-test: %d skills -> %s" % (len(skills), dest_root))
    repo = Repo(catalog["repo"], catalog.get("branch", "main"), load_settings().get("token"))
    ok_total = fail_total = 0
    for position, skill in enumerate(skills, start=1):
        print("  [%d/%d] %s" % (position, len(skills), skill["id"]))
        try:
            ok, fail, folder, note = repo.download_skill(skill, dest_root, skip_existing=False)
            ok_total += 1 if (ok or note) else 0
            fail_total += 1 if fail else 0
            print("       files=%d fail=%d note=%s" % (ok, fail, note))
        except Exception as exc:  # noqa: BLE001
            fail_total += 1
            print("       FAIL %s" % exc)
    print("skills ok=%d failed=%d" % (ok_total, fail_total))
    if ok_total == 0:
        print("BULK-TEST FAIL nothing downloaded")
        return 4
    print("BULK-TEST OK")
    return 0


# --------------------------------------------------------------------------- #
# GUI
# --------------------------------------------------------------------------- #
def _enable_dpi_awareness():
    scale = 1.0
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
        try:
            scale = ctypes.windll.user32.GetDpiForSystem() / 96.0
        except Exception:
            hdc = ctypes.windll.user32.GetDC(0)
            scale = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88) / 96.0
            ctypes.windll.user32.ReleaseDC(0, hdc)
    except Exception:
        scale = 1.0
    return min(2.0, max(1.0, scale)), (lambda value: int(round(value * scale)))


def build_ui(catalog, settings):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk, font as tkfont

    repo_name = catalog["repo"]
    branch = catalog.get("branch", "main")
    all_skills = catalog["skills"]
    categories = catalog["categories"]
    GROUPS = load_groups()
    skill_by_id = {skill["id"]: skill for skill in all_skills}

    scale, px = _enable_dpi_awareness()
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", scale * 96.0 / 72.0)
    except Exception:
        pass
    root.title(APP_NAME)
    root.configure(bg=BG)

    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    win_w = max(px(900), min(px(1280), screen_w - px(40)))
    win_h = max(px(560), min(px(840), screen_h - px(90)))
    root.geometry("%dx%d+%d+%d" % (win_w, win_h, max(0, (screen_w - win_w) // 2),
                                   max(0, (screen_h - win_h) // 3)))
    root.minsize(min(px(980), win_w), min(px(600), win_h))

    state = {
        "filter": "all",
        "expanded": {GROUPS[0]["id"]} if GROUPS else set(),
        "query": "",
        "selected_id": None,
        "checked": set(),
        "rendered": RENDER_CAP,
        "target": settings.get("target", "autoclaw"),
        "busy": False,
        "smart_ids": None,
        "smart_why": {},
        "smart_busy": False,
        "project_dir": settings.get("project_dir", ""),
        "last_dir": settings.get("last_dir", str(Path.home() / "Documents" / "AAS-Skills")),
    }
    lang = settings.get("lang", "ar")
    RTL = lang == "ar"

    STR = {
        "جاهز": "Ready",
        "إلغاء": "Cancel",
        "%d مهارة من مستودع agentic-awesome-skills":
            "%d skills from the agentic-awesome-skills repository",
        "كل المهارات": "All skills",
        "فتح المستودع على GitHub": "Open repository on GitHub",
        "إعدادات GitHub (رمز اختياري)": "GitHub settings (optional token)",
        "تنزيل كل المهارات (%d)": "Download all skills (%d)",
        "ابحث بالاسم أو بالوصف… (Ctrl+F)": "Search by name or description… (Ctrl+F)",
        "تحديد الكل": "Select all",
        "مسح التحديد": "Clear selection",
        "المحدد: 0": "Selected: 0",
        "المحدد: %d": "Selected: %d",
        "تنزيل المحدد": "Download selected",
        "تنزيل المحدد (%d)": "Download selected (%d)",
        "تنزيل النتائج": "Download results",
        "اختر مهارة من القائمة": "Pick a skill from the list",
        "ستجد هنا وظيفة المهارة، أمر استدعائها، أمر تثبيتها، "
        "وإمكانية تنزيلها إلى مجلد مهارات برنامجك.":
            "You will see what the skill does, how to invoke it, how to install it, "
            "and you can download it straight into your tool's skills folder.",
        "وظيفة المهارة": "What the skill does",
        "نسخ": "Copy",
        "أمر استدعاء المهارة": "Invocation command",
        "اكتب «/» ثم اسم المهارة في محادثة الوكيل ليظهر الاقتراح، أو الصق الأمر كما هو.":
            "Type “/” then the skill name in your agent chat to get the suggestion, "
            "or paste the command as is.",
        "أمر التثبيت عبر npx": "npx install command",
        "بديل عن التنزيل اليدوي. غيّر --claude حسب أداتك: --cursor أو --codex أو --gemini.":
            "Alternative to the manual download. Change --claude to your tool: "
            "--cursor, --codex or --gemini.",
        "أضف إلى برنامج:": "Add to program:",
        "تنزيل وإضافة": "Download & add",
        "تنزيل إلى مجلد…": "Download to folder…",
        "فتح على GitHub": "Open on GitHub",
        "المسار: %s": "Path: %s",
        "%d نتيجة": "%d results",
        "لا نتائج مطابقة.": "No matching results.",
        "عرض المزيد (%d متبقية)": "Show more (%d remaining)",
        "شرح عربي معدّ يدوياً لهذه المهارة.": "Hand-written Arabic explanation for this skill.",
        "الوصف الأصلي: ": "Original description: ",
        "لا يوجد وصف في فهرس المستودع.": "No description in the repository index.",
        "الوصف كما ورد في فهرس المستودع، بلغته الأصلية.":
            "Description as published in the repository index.",
        "تم النسخ: ": "Copied: ",
        "أمر الاستدعاء": "invocation command",
        "أمر التثبيت": "install command",
        "إعدادات GitHub": "GitHub settings",
        "رمز وصول GitHub (اختياري)": "GitHub access token (optional)",
        "بدون رمز: 60 طلباً في الساعة — تنزيل جماعي كبير سيتوقف.\n"
        "مع رمز (fine-grained, read-only): 5000 طلب في الساعة.":
            "Without a token: 60 requests per hour — a large bulk download will stall.\n"
            "With a fine-grained read-only token: 5000 requests per hour.",
        "حفظ": "Save",
        "اختر مجلد حفظ المهارات": "Choose a folder to store the skills",
        "اختر مجلد المشروع الذي يستخدم %s": "Choose the project folder used by %s",
        "انتهى: نجح %d، فشل %d": "Done: %d succeeded, %d failed",
        "عملية تنزيل قيد التنفيذ بالفعل…": "A download is already running…",
        "لم تحدد أي مهارة": "No skill selected",
        "مجلد مخصص": "Custom folder",
        "سيتم تنزيل %d مهارة إلى:\n%s\n\nالمتابعة؟":
            "About to download %d skills to:\n%s\n\nContinue?",
        "تأكيد التنزيل": "Confirm download",
        "تنزيل كبير بدون رمز GitHub": "Large download without a GitHub token",
        "بدون رمز وصول، يسمح GitHub بـ60 طلباً في الساعة فقط.\n"
        "تنزيل %d مهارة سيحتاج %d طلباً وقد يتوقف في المنتصف.\n\n"
        "أضف رمزاً من «إعدادات GitHub» لرفع الحد إلى 5000 طلب/ساعة.\n\n"
        "هل تريد المتابعة الآن على أي حال؟":
            "Without a token GitHub allows only 60 requests per hour.\n"
            "Downloading %d skills needs %d requests and may stop halfway.\n\n"
            "Add a token from “GitHub settings” to raise the limit to 5000/hour.\n\n"
            "Continue anyway?",
        "تعذّر إنشاء المجلد: %s": "Cannot create the folder: %s",
        "جارٍ التنزيل إلى %s": "Downloading to %s",
        "جارٍ الإيقاف…": "Stopping…",
        "أُوقف التنزيل بواسطة المستخدم": "Stopped by the user",
        "تم تحديد %d مهارة من النتائج الحالية": "Selected %d skills from the current results",
        "تم مسح التحديد": "Selection cleared",
        "تم حفظ الرمز": "Token saved",
        "تم مسح الرمز": "Token cleared",
        "الإعدادات": "Settings",
        "مفتاح النموذج الذكي (اختياري)": "Smart model API key (optional)",
        "بدون مفتاح يعمل البحث الذكي محلياً بالكلمات المفتاحية.\n"
        "مع مفتاح النموذج تُرتَّب النتائج حسب فهم الطلب ويظهر سبب الاختيار.":
            "Without a key, smart search works locally with keywords.\n"
            "With a Gemini key, results are ranked by intent and show a reason.",
        "النموذج:": "Model:",
        "تم حفظ الإعدادات": "Settings saved",
        "شرح": "Description",
        "التصنيف": "Category",
        "المصطلحات: ": "Terms: ",
        "اكتب طلبك أولاً، مثال: مهارة لتحليل مشروع":
            "Type your request first, e.g. a skill to audit a project",
        "لم أجد مرشحاً مطابقاً — جرّب كلمات أخرى":
            "No candidate matched — try different words",
        "بحث محلي ذكي: %d نتيجة. أضف مفتاح النموذج من الإعدادات لترتيب أدق.":
            "Smart local search: %d results. Add a Gemini key in settings for better ranking.",
        "بحث محلي بدون نموذج": "Local search without a model",
        "جارٍ فهم طلبك عبر النموذج…": "Understanding your request with the model…",
        "جارٍ البحث الذكي…": "Running smart search…",
        "تعذّر استخدام النموذج — عرض نتائج محلية":
            "Gemini unavailable — showing local results",
        "نتائج البحث الذكي": "Smart search results",
        "نتائج البحث الذكي: %d": "Smart results: %d",
        "بحث ذكي": "Smart search",
    }

    def tr(text):
        if lang == "ar":
            return text
        return STR.get(text, text)

    def target_label(target):
        return target["label"] if lang == "ar" else target.get("en", target["label"])

    def cat_label(cat_id, ar_value):
        return ar_value if lang == "ar" else category_en(cat_id)
    check_flag = {"on": True}

    ui_queue = queue.Queue()
    cancel_event = threading.Event()

    base_font = tkfont.Font(family=UI_FONT, size=11)
    small_font = tkfont.Font(family=UI_FONT, size=9)
    bold_font = tkfont.Font(family=UI_FONT, size=12, weight="bold")
    title_font = tkfont.Font(family=UI_FONT, size=16, weight="bold")
    body_font = tkfont.Font(family=UI_FONT, size=11)
    mono_font = tkfont.Font(family=MONO_FONT, size=9)

    def repo_client():
        return Repo(repo_name, branch, settings.get("token"))

    # ---------------- shell ------------------------------------------------
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True)

    status_bar = tk.Frame(root, bg=PANEL_2, height=px(30))
    status_bar.pack(side="bottom", fill="x")
    status_dot = tk.Label(status_bar, text="●", font=body_font, bg=PANEL_2, fg=OK)
    status_dot.pack(side="right", padx=(0, 6), pady=2)
    status_label = tk.Label(status_bar, text="جاهز", font=small_font, bg=PANEL_2, fg=MUTED,
                            anchor="e", justify="right")
    status_label.pack(side="right", fill="x", expand=True, pady=3)
    cancel_btn = tk.Label(status_bar, text="إلغاء", font=small_font, bg=PANEL_3, fg=DANGER,
                          padx=12, pady=2, cursor="hand2")
    progress_label = tk.Label(status_bar, text="", font=small_font, bg=PANEL_2, fg=ACCENT)

    sidebar_w = px(270)
    middle_w = px(430)
    details = tk.Frame(outer, bg=BG)
    middle = tk.Frame(outer, bg=BG)
    sidebar = tk.Frame(outer, bg=PANEL)

    details.place(x=0, y=0, relheight=1.0, width=win_w - sidebar_w - middle_w)
    if RTL:
        middle.place(relx=1.0, x=-(sidebar_w + middle_w), y=0, width=middle_w, relheight=1.0)
        sidebar.place(relx=1.0, x=-sidebar_w, y=0, width=sidebar_w, relheight=1.0)
    else:
        sidebar.place(x=0, y=0, width=sidebar_w, relheight=1.0)
        middle.place(x=sidebar_w, y=0, width=middle_w, relheight=1.0)
        details.place(x=sidebar_w + middle_w, y=0, relheight=1.0,
                      width=win_w - sidebar_w - middle_w)

    def layout_panels(_event=None):
        width = outer.winfo_width()
        if width < 50:
            return
        if RTL:
            details.place_configure(x=0, width=max(px(300), width - sidebar_w - middle_w))
            middle.place_configure(x=-(sidebar_w + middle_w), width=middle_w)
            sidebar.place_configure(x=-sidebar_w, width=sidebar_w)
        else:
            sidebar.place_configure(x=0, width=sidebar_w)
            middle.place_configure(x=sidebar_w, width=middle_w)
            details.place_configure(x=sidebar_w + middle_w,
                                    width=max(px(300), width - sidebar_w - middle_w))

    outer.bind("<Configure>", layout_panels)

    # ---------------- sidebar ----------------------------------------------
    lang_row = tk.Frame(sidebar, bg=PANEL)
    lang_row.pack(fill="x", padx=px(16), pady=(px(10), 0))
    lang_btn = tk.Label(lang_row, text=("EN" if lang == "ar" else "عربي"), font=small_font,
                        bg=PANEL_2, fg=ACCENT, padx=px(10), pady=px(2), cursor="hand2")
    lang_btn.pack(side="left")

    head = tk.Frame(sidebar, bg=PANEL)
    head.pack(fill="x", padx=px(16), pady=(px(8), px(4)))
    tk.Label(head, text="AAS Skills Studio", font=title_font, bg=PANEL, fg=TEXT,
             anchor="w").pack(anchor="w")
    tk.Label(head, text=tr("%d مهارة من مستودع agentic-awesome-skills") % catalog["total"],
             font=small_font, bg=PANEL, fg=MUTED, anchor="e", justify="right",
             wraplength=px(236)).pack(anchor="e", pady=(2, 0))

    tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=px(14), pady=px(10))

    # يُحجز الشريط السفلي قبل قائمة الفئات حتى لا تبتلعه القائمة المتمددة.
    side_footer = tk.Frame(sidebar, bg=PANEL)
    side_footer.pack(side="bottom", fill="x", padx=px(14), pady=px(10))

    repo_link = tk.Label(side_footer, text="فتح المستودع على GitHub", font=small_font,
                         bg=PANEL_2, fg=ACCENT, cursor="hand2", pady=px(6))
    repo_link.pack(fill="x", pady=(0, px(4)))
    repo_link.bind("<Button-1>", lambda _e: webbrowser.open("https://github.com/" + repo_name))

    settings_link = tk.Label(side_footer, text="إعدادات GitHub (رمز اختياري)", font=small_font,
                             bg=PANEL, fg=MUTED, cursor="hand2", pady=px(4))
    settings_link.pack(fill="x")
    settings_link.bind("<Button-1>", lambda _e: open_token_dialog())

    download_all_btn = tk.Label(side_footer, text=tr("تنزيل كل المهارات (%d)") % catalog["total"],
                                font=small_font, bg=PANEL_3, fg=WARN, cursor="hand2",
                                pady=px(7))
    download_all_btn.pack(fill="x", pady=(px(8), 0))
    download_all_btn.bind("<Button-1>", lambda _e: start_download(all_skills, True))

    cat_canvas = tk.Canvas(sidebar, bg=PANEL, highlightthickness=0, bd=0)
    cat_scroll = ttk.Scrollbar(sidebar, orient="vertical", command=cat_canvas.yview,
                               style="AAS.Vertical.TScrollbar")
    cat_inner = tk.Frame(cat_canvas, bg=PANEL)
    cat_id = cat_canvas.create_window((0, 0), window=cat_inner, anchor="nw")
    cat_canvas.configure(yscrollcommand=cat_scroll.set)
    cat_scroll.pack(side="left", fill="y")
    cat_canvas.pack(side="right", fill="both", expand=True, padx=(0, px(4)))

    cat_inner.bind("<Configure>", lambda _e: cat_canvas.configure(scrollregion=cat_canvas.bbox("all")))
    cat_canvas.bind("<Configure>", lambda e: cat_canvas.itemconfigure(cat_id, width=e.width))

    # ---- شجرة التصنيفات: 9 مجموعات رئيسية يتفرّع منها 23 قسماً --------------
    groups = GROUPS
    cat_group = {}
    cat_sub = {}
    for group in groups:
        for sub in group["subs"]:
            for cat in sub["cats"]:
                cat_group[cat] = group["id"]
                cat_sub[cat] = sub["id"]

    cat_counts = {c["id"]: c["count"] for c in categories}

    def group_count(group):
        return sum(cat_counts.get(c, 0) for sub in group["subs"] for c in sub["cats"])

    def sub_count(sub):
        return sum(cat_counts.get(c, 0) for c in sub["cats"])

    def group_title(group):
        return group["ar"] if lang == "ar" else group["en"]

    def sub_title(sub):
        return sub["ar"] if lang == "ar" else sub["en"]

    tree_rows = {}

    def build_categories():
        tree_rows.clear()
        for child in cat_inner.winfo_children():
            child.destroy()

        def make_row(parent, key, label, count, indent, caret=None, command=None,
                     hover_group=None):
            row = tk.Frame(parent, bg=PANEL)
            row.pack(fill="x", padx=(px(6), px(6)), pady=1)
            bar = tk.Frame(row, bg=PANEL, width=px(3))
            bar.pack(side="right", fill="y")
            count_lbl = tk.Label(row, text=str(count), font=small_font, bg=PANEL, fg=MUTED,
                                 width=4)
            count_lbl.pack(side="left", padx=(px(4), 0))
            text_lbl = tk.Label(row, text=label, font=small_font, bg=PANEL, fg=TEXT,
                                anchor="e", justify="right",
                                wraplength=px(180 - indent))
            text_lbl.pack(side="right", fill="x", expand=True,
                          padx=(px(4), px(2) + px(indent)), pady=px(5))
            # يُنشأ دائماً للحفاظ على اصطفاف العناوين، لكنه فارغ للتصنيفات بلا أقسام.
            caret_lbl = tk.Label(row, text=caret or "", font=small_font, bg=PANEL, fg=MUTED,
                                 width=2, cursor="hand2" if caret else "arrow")
            caret_lbl.pack(side="left", padx=(px(2), 0))
            tree_rows[key] = {"row": row, "bar": bar, "text": text_lbl,
                              "count": count_lbl,
                              "caret": caret_lbl if caret else None,
                              "caret_w": caret_lbl,
                              "hover": hover_group or key}
            widgets = [row, text_lbl, count_lbl] + ([caret_lbl] if caret else [])
            for widget in widgets:
                widget.bind("<Button-1>", lambda _e, c=command: c() if c else None)
                widget.bind("<Enter>", lambda _e, r=row, t=text_lbl, cl=count_lbl:
                            (r.configure(bg=PANEL_2), t.configure(bg=PANEL_2),
                             cl.configure(bg=PANEL_2)))
                widget.bind("<Leave>", lambda _e: paint_categories())
            return row

        make_row(cat_inner, "all", tr("كل المهارات"), catalog["total"], 0,
                 command=lambda: select_node("all"))

        for group in groups:
            key = "g:" + group["id"]
            expanded = group["id"] in state["expanded"]
            has_children = len(group["subs"]) > 1
            caret = None if not has_children else ("▾" if expanded else "▸")
            make_row(cat_inner, key, group_title(group), group_count(group), 0,
                     caret=caret, command=lambda g=group: select_node("g:" + g["id"]))
            if has_children and expanded:
                for sub in group["subs"]:
                    make_row(cat_inner, "s:%s:%s" % (group["id"], sub["id"]),
                             "•  " + sub_title(sub), sub_count(sub), 18,
                             command=lambda g=group, s=sub: select_node(
                                 "s:%s:%s" % (g["id"], s["id"])))

    def paint_categories():
        active = state["filter"]
        for key, parts in tree_rows.items():
            is_active = key == active
            bg = PANEL_3 if is_active else PANEL
            for name in ("row", "text", "count", "caret_w"):
                widget = parts[name]
                if widget is not None:
                    widget.configure(bg=bg)
            parts["bar"].configure(bg=ACCENT if is_active else PANEL)
            parts["text"].configure(fg=TEXT if is_active else MUTED)
            parts["count"].configure(fg=ACCENT if is_active else MUTED)
            if parts["caret"] is not None:
                parts["caret"].configure(fg=ACCENT if is_active else MUTED)

    def select_node(key):
        if state["smart_ids"] is not None or state["smart_why"]:
            state["smart_ids"] = None
            state["smart_why"] = {}
            smart_note.configure(text="")
        if key.startswith("g:"):
            gid = key.split(":", 1)[1]
            if gid in state["expanded"]:
                state["expanded"].discard(gid)
            else:
                state["expanded"].add(gid)
            state["filter"] = key
            build_categories()
        else:
            state["filter"] = key
        state["rendered"] = RENDER_CAP
        paint_categories()
        refresh_list()

    build_categories()
    paint_categories()
    # ---------------- middle: search, selection, list ----------------------
    search_wrap = tk.Frame(middle, bg=BG)
    search_wrap.pack(fill="x", padx=px(12), pady=(px(14), px(6)))
    search_box = tk.Frame(search_wrap, bg=PANEL_2, highlightthickness=1, highlightbackground=BORDER)
    search_box.pack(fill="x")
    search_entry = tk.Entry(search_box, bg=PANEL_2, fg=TEXT, insertbackground=ACCENT,
                            relief="flat", font=base_font, justify="right", highlightthickness=0)
    search_entry.pack(side="right", fill="x", expand=True, padx=px(8), pady=px(6))
    placeholder = "ابحث بالاسم أو بالوصف… (Ctrl+F)"
    placeholder_text = tr(placeholder)
    search_entry.insert(0, placeholder_text)
    search_entry.configure(fg=MUTED)

    smart_row = tk.Frame(search_wrap, bg=BG)
    smart_row.pack(fill="x", pady=(px(6), 0))
    smart_btn = tk.Frame(smart_row, bg=ACCENT_DIM)
    smart_btn.pack(side="right")
    smart_icon = tk.Label(smart_btn, text="✦", font=small_font, bg=ACCENT_DIM, fg=ACCENT,
                          padx=px(6), pady=px(3), cursor="hand2")
    smart_icon.pack(side="right")
    smart_label = tk.Label(smart_btn, text=tr("بحث ذكي"), font=small_font, bg=ACCENT_DIM,
                           fg=ACCENT, padx=px(6), pady=px(3), cursor="hand2")
    smart_label.pack(side="right", padx=(0, px(4)))
    smart_note = tk.Label(smart_row, text="", font=small_font, bg=BG, fg=MUTED,
                          anchor="e", justify="right", wraplength=px(330))
    smart_note.pack(side="right", fill="x", expand=True, padx=(px(8), 0))
    for widget in (smart_btn, smart_icon, smart_label):
        widget.bind("<Button-1>", lambda _e: run_smart_search())
    search_entry.bind("<Return>", lambda _e: run_smart_search())

    toolbar = tk.Frame(middle, bg=BG)
    toolbar.pack(fill="x", padx=px(12), pady=(0, px(4)))

    count_label = tk.Label(toolbar, text="", font=small_font, bg=BG, fg=MUTED, anchor="e")
    count_label.pack(side="right")

    def small_button(parent, text, fg, command):
        btn = tk.Label(parent, text=text, font=small_font, bg=PANEL_2, fg=fg, padx=px(8),
                       pady=px(3), cursor="hand2")
        btn.pack(side="left", padx=(px(4), 0))
        btn.bind("<Button-1>", lambda _e: command())
        return btn

    small_button(toolbar, "تحديد الكل", TEXT, lambda: select_all(True))
    small_button(toolbar, "مسح التحديد", MUTED, lambda: select_all(False))

    action_bar = tk.Frame(middle, bg=BG)
    action_bar.pack(fill="x", padx=px(12), pady=(px(2), px(6)))

    selected_label = tk.Label(action_bar, text="المحدد: 0", font=small_font, bg=BG, fg=ACCENT,
                              anchor="e")
    selected_label.pack(side="right")

    def accent_button(parent, text, command, bg=ACCENT, fg="#06231F"):
        btn = tk.Label(parent, text=text, font=small_font, bg=bg, fg=fg, padx=px(10),
                       pady=px(4), cursor="hand2")
        btn.bind("<Button-1>", lambda _e: command())
        return btn

    dl_selected_btn = accent_button(action_bar, "تنزيل المحدد", lambda: start_selected())
    dl_selected_btn.pack(side="left", padx=(0, px(4)))
    dl_results_btn = accent_button(action_bar, "تنزيل النتائج", lambda: start_download(visible_skills(), False),
                                   bg=PANEL_2, fg=TEXT)
    dl_results_btn.pack(side="left")

    list_wrap = tk.Frame(middle, bg=BG)
    list_wrap.pack(fill="both", expand=True, padx=(px(8), px(10)), pady=(0, px(8)))
    canvas = tk.Canvas(list_wrap, bg=BG, highlightthickness=0, bd=0)
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("AAS.Vertical.TScrollbar", background=PANEL_3, troughcolor=BG,
                    bordercolor=BG, arrowcolor=MUTED, darkcolor=PANEL_3, lightcolor=PANEL_3)
    scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview,
                           style="AAS.Vertical.TScrollbar")
    inner = tk.Frame(canvas, bg=BG)
    inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    scroll.pack(side="left", fill="y")
    canvas.pack(side="right", fill="both", expand=True)
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(inner_id, width=e.width))

    def on_wheel(event):
        node = canvas.winfo_containing(event.x_root, event.y_root)
        while node is not None:
            if node is canvas or node is inner:
                canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")
                return
            node = getattr(node, "master", None)
        node = cat_canvas.winfo_containing(event.x_root, event.y_root)
        while node is not None:
            if node is cat_canvas or node is cat_inner:
                cat_canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")
                return
            node = getattr(node, "master", None)

    canvas.bind_all("<MouseWheel>", on_wheel)

    # ---------------- details ---------------------------------------------
    details_inner = tk.Frame(details, bg=BG, width=px(760))
    details_inner.pack(side="right", fill="y", padx=px(16), pady=px(12))
    details_inner.pack_propagate(False)

    def fit_content(_event=None):
        available = details.winfo_width() - px(32)
        details_inner.configure(width=max(px(300), min(px(820), available)))

    details.bind("<Configure>", fit_content)

    empty_view = tk.Frame(details_inner, bg=BG)
    tk.Label(empty_view, text="اختر مهارة من القائمة", font=title_font, bg=BG,
             fg=TEXT).pack(pady=(px(70), px(6)))
    tk.Label(empty_view, text="ستجد هنا وظيفة المهارة، أمر استدعائها، أمر تثبيتها، "
                              "وإمكانية تنزيلها إلى مجلد مهارات برنامجك.",
             font=base_font, bg=BG, fg=MUTED, wraplength=px(460), justify="center").pack()

    detail_view = tk.Frame(details_inner, bg=BG)
    name_row = tk.Frame(detail_view, bg=BG)
    name_row.pack(fill="x")
    name_label = tk.Label(name_row, text="", font=title_font, bg=BG, fg=TEXT, anchor="w",
                          justify="left")
    name_label.pack(side="right")

    chip_row = tk.Frame(detail_view, bg=BG)
    chip_row.pack(fill="x", pady=(px(6), 0))
    category_chip = tk.Label(chip_row, text="", font=small_font, bg=PANEL_2, fg=VIOLET,
                             padx=px(9), pady=px(2))
    category_chip.pack(side="right", padx=(0, px(6)))
    risk_chip = tk.Label(chip_row, text="", font=small_font, bg=PANEL_2, fg=OK,
                         padx=px(9), pady=px(2))
    risk_chip.pack(side="right")

    tk.Label(detail_view, text="وظيفة المهارة", font=bold_font, bg=BG, fg=MUTED,
             anchor="e").pack(fill="x", pady=(px(14), px(4)))
    func_label = tk.Label(detail_view, text="", font=body_font, bg=PANEL, fg=TEXT,
                          anchor="e", justify="right", wraplength=px(380), padx=px(12),
                          pady=px(10))
    func_label.pack(fill="x")
    source_note = tk.Label(detail_view, text="", font=small_font, bg=BG, fg=MUTED, anchor="e",
                           justify="right", wraplength=px(380))
    source_note.pack(fill="x", pady=(px(3), 0))
    terms_label = tk.Label(detail_view, text="", font=small_font, bg=BG, fg=VIOLET, anchor="e",
                           justify="right", wraplength=px(380))
    terms_label.pack(fill="x", pady=(px(2), 0))
    desc_label = tk.Label(detail_view, text="", font=small_font, bg=BG, fg=MUTED, anchor="e",
                          justify="right", wraplength=px(380))
    desc_label.pack(fill="x", pady=(px(2), 0))

    def command_block(title, note, height=2):
        tk.Label(detail_view, text=title, font=bold_font, bg=BG, fg=MUTED,
                 anchor="e").pack(fill="x", pady=(px(12), px(4)))
        holder = tk.Frame(detail_view, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        holder.pack(fill="x")
        buttons = tk.Frame(holder, bg=PANEL)
        buttons.pack(side="left", fill="y", padx=px(6), pady=px(6))
        copy_btn = tk.Label(buttons, text="نسخ", font=small_font, bg=ACCENT_DIM, fg=ACCENT,
                            padx=px(12), pady=px(4), cursor="hand2")
        copy_btn.pack()
        text = tk.Text(holder, height=height, width=20, bg=PANEL, fg=ACCENT, font=mono_font, bd=0,
                       relief="flat", wrap="word", highlightthickness=0, padx=px(6), pady=px(6),
                       selectbackground=PANEL_3, selectforeground=TEXT)
        text.pack(side="right", fill="both", expand=True)
        tk.Label(detail_view, text=note, font=small_font, bg=BG, fg=MUTED, anchor="e",
                 justify="right", wraplength=px(380)).pack(fill="x", pady=(px(3), 0))
        return text, copy_btn

    invoke_text, invoke_copy = command_block(
        "أمر استدعاء المهارة",
        "اكتب «/» ثم اسم المهارة في محادثة الوكيل ليظهر الاقتراح، أو الصق الأمر كما هو.",
        height=1)
    install_text, install_copy = command_block(
        "أمر التثبيت عبر npx",
        "بديل عن التنزيل اليدوي. غيّر --claude حسب أداتك: --cursor أو --codex أو --gemini.")

    path_label = tk.Label(detail_view, text="", font=small_font, bg=BG, fg=MUTED, anchor="e",
                          justify="right", wraplength=px(380))
    path_label.pack(fill="x", pady=(px(10), 0))

    target_row = tk.Frame(detail_view, bg=BG)
    target_row.pack(fill="x", pady=(px(12), 0))
    tk.Label(target_row, text="أضف إلى برنامج:", font=small_font, bg=BG, fg=MUTED,
             anchor="e").pack(side="right", padx=(0, px(8)))
    target_var = tk.StringVar()
    target_combo = ttk.Combobox(target_row, textvariable=target_var, state="readonly",
                                values=[target_label(t) for t in TARGETS], width=24,
                                font=small_font)
    target_combo.pack(side="right")

    actions = tk.Frame(detail_view, bg=BG)
    actions.pack(fill="x", pady=(px(10), 0))

    def make_button(parent, text, bg, fg, command, side="right", padx=(0, px(6))):
        btn = tk.Label(parent, text=text, font=base_font, bg=bg, fg=fg, padx=px(14), pady=px(8),
                       cursor="hand2")
        btn.pack(side=side, padx=padx)
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(bg=PANEL_3))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=bg))
        return btn

    add_btn = make_button(actions, "تنزيل وإضافة", ACCENT, "#06231F", lambda: start_selected(single=True))
    folder_btn = make_button(actions, "تنزيل إلى مجلد…", PANEL_2, TEXT,
                             lambda: start_selected(single=True, force_folder=True))
    github_btn = make_button(actions, "فتح على GitHub", PANEL_2, TEXT,
                             lambda: open_current_github(), side="left", padx=(0, 0))

    # ---------------- state helpers ---------------------------------------
    def set_status(text, color=None):
        status_label.configure(text=text)
        if color:
            status_dot.configure(fg=color)

    def current_skill():
        return skill_by_id.get(state["selected_id"])

    def open_current_github():
        skill = current_skill()
        if skill:
            full_path = skill["path"]
            webbrowser.open("https://github.com/%s/tree/%s/%s" % (repo_name, branch, full_path))

    def visible_skills():
        query = state["query"].strip().lower()
        if state["smart_ids"] is not None:
            return [skill_by_id[sid] for sid in state["smart_ids"] if sid in skill_by_id]
        allowed = None
        node = state["filter"]
        if node.startswith("g:"):
            gid = node.split(":", 1)[1]
            group = next((g for g in GROUPS if g["id"] == gid), None)
            if group:
                allowed = {cat for sub in group["subs"] for cat in sub["cats"]}
        elif node.startswith("s:"):
            _, gid, sid = node.split(":", 2)
            group = next((g for g in GROUPS if g["id"] == gid), None)
            sub = next((s for s in group["subs"] if s["id"] == sid), None) if group else None
            if sub:
                allowed = set(sub["cats"])

        result = []
        for skill in all_skills:
            if allowed is not None and skill["category"] not in allowed:
                continue
            if query:
                haystack = (skill["name"] + " " + skill["id"] + " " + skill["desc"] + " "
                            + skill["category"]).lower()
                if query not in haystack:
                    continue
            result.append(skill)
        return result

    def update_selected_label():
        selected_label.configure(text=tr("المحدد: %d") % len(state["checked"]))
        dl_selected_btn.configure(text=tr("تنزيل المحدد (%d)") % len(state["checked"]))

    def toggle_check(skill_id, value=None):
        if skill_id in state["checked"]:
            if value is True:
                return
            state["checked"].discard(skill_id)
        else:
            if value is False:
                return
            state["checked"].add(skill_id)
        update_selected_label()

    def select_all(value):
        targets = visible_skills()
        if value:
            state["checked"].update(skill["id"] for skill in targets)
            set_status(tr("تم تحديد %d مهارة من النتائج الحالية") % len(targets), ACCENT)
        else:
            state["checked"].clear()
            set_status(tr("تم مسح التحديد"), MUTED)
        update_selected_label()
        paint_rows()

    # ---------------- list -------------------------------------------------
    row_widgets = {}

    def paint_rows():
        for sid, widgets in row_widgets.items():
            active = sid == state["selected_id"]
            checked = sid in state["checked"]
            bg = PANEL_3 if active else PANEL
            for widget in widgets:
                widget.configure(bg=bg)
            widgets[1].configure(fg=ACCENT if active else TEXT)
            if sid in row_widgets:
                box = row_widgets[sid][-1]
                box.configure(text="☑" if checked else "☐",
                              fg=ACCENT if checked else MUTED)

    def select_skill(skill_id):
        state["selected_id"] = skill_id
        paint_rows()
        show_detail()

    def clear_children():
        for child in inner.winfo_children():
            child.destroy()
        row_widgets.clear()

    def refresh_list():
        clear_children()
        items = visible_skills()
        count_label.configure(text=tr("%d نتيجة") % len(items))

        if not items:
            tk.Label(inner, text=tr("لا نتائج مطابقة."), font=base_font, bg=BG, fg=MUTED,
                     pady=px(30)).pack(fill="x")
            update_selected_label()
            show_detail()
            return

        shown = items[: state["rendered"]]
        for skill in shown:
            row = tk.Frame(inner, bg=PANEL, highlightthickness=1, highlightbackground=ROW_BORDER)
            row.pack(fill="x", pady=px(3), padx=px(2))

            box = tk.Label(row, text="☑" if skill["id"] in state["checked"] else "☐",
                           font=base_font, bg=PANEL, fg=ACCENT if skill["id"] in state["checked"] else MUTED,
                           width=2, cursor="hand2")
            box.pack(side="left", padx=(px(8), 0))

            text_wrap = tk.Frame(row, bg=PANEL)
            text_wrap.pack(side="right", fill="x", expand=True, padx=px(8), pady=px(5))

            name = tk.Label(text_wrap, text=skill["name"], font=base_font, bg=PANEL, fg=TEXT,
                            anchor="w", justify="left")
            name.pack(fill="x")

            if lang == "ar":
                desc_text = (skill.get("ar_clear") or skill.get("ar")
                             or skill.get("ar_desc") or skill["desc"])
            else:
                desc_text = skill["desc"]
            desc = tk.Label(text_wrap, text=desc_text, font=small_font, bg=PANEL, fg=MUTED,
                            anchor="e" if RTL else "w", justify="right" if RTL else "left",
                            wraplength=px(300))
            desc.pack(fill="x")

            why_text = state["smart_why"].get(skill["id"])
            why_lbl = None
            if why_text:
                why_lbl = tk.Label(text_wrap, text="✦ " + why_text, font=small_font, bg=PANEL,
                                   fg=ACCENT, anchor="e" if RTL else "w",
                                   justify="right" if RTL else "left", wraplength=px(300))
                why_lbl.pack(fill="x")

            cat_ar = next((c["ar"] for c in categories if c["id"] == skill["category"]),
                          skill["category"])
            meta = tk.Label(text_wrap, text=cat_label(skill["category"], cat_ar)
                            + ("  ·  critical" if skill["risk"] == "critical" else ""),
                            font=small_font, bg=PANEL,
                            fg=DANGER if skill["risk"] == "critical" else VIOLET,
                            anchor="e" if RTL else "w")
            meta.pack(fill="x")

            widgets = [row, name, desc, meta, box] + ([why_lbl] if why_lbl else [])
            row_widgets[skill["id"]] = widgets

            for widget in (row, name, desc, meta):
                widget.bind("<Button-1>", lambda _e, s=skill["id"]: select_skill(s))
            box.bind("<Button-1>", lambda _e, s=skill["id"]: (toggle_check(s), paint_rows(),
                                                              select_skill(s)))

        if len(items) > len(shown):
            more = tk.Label(inner, text=tr("عرض المزيد (%d متبقية)") % (len(items) - len(shown)),
                            font=small_font, bg=PANEL_2, fg=ACCENT, pady=px(8), cursor="hand2")
            more.pack(fill="x", pady=px(6))
            more.bind("<Button-1>", lambda _e: (state.__setitem__("rendered",
                                                                  state["rendered"] + RENDER_CAP),
                                                refresh_list()))

        paint_rows()
        update_selected_label()
        show_detail()

    # ---------------- detail -------------------------------------------------
    def show_detail():
        skill = current_skill()
        if not skill:
            detail_view.pack_forget()
            empty_view.pack(fill="both", expand=True)
            return
        empty_view.pack_forget()
        detail_view.pack(fill="both", expand=True)

        name_label.configure(text=skill["name"])
        cat_ar = next((c["ar"] for c in categories if c["id"] == skill["category"]),
                      skill["category"])
        category_chip.configure(text=cat_label(skill["category"], cat_ar))
        risk_chip.configure(text="critical" if skill["risk"] == "critical" else skill["risk"],
                            fg=DANGER if skill["risk"] == "critical" else OK)

        original = skill.get("desc") or ""
        arabic = (skill.get("ar_clear") or skill.get("ar")
                  or skill.get("ar_desc") or "")
        if lang == "ar":
            func_label.configure(text=arabic or original or tr("لا يوجد وصف في فهرس المستودع."))
            if skill.get("ar"):
                source_note.configure(text=tr("شرح عربي معدّ يدوياً لهذه المهارة."))
            else:
                source_note.configure(text="ترجمة عربية لوصف المستودع.")
            desc_label.configure(text=(tr("الوصف الأصلي: ") + original) if original else "")
        else:
            func_label.configure(text=original or "No description in the repository index.")
            source_note.configure(text=tr("الوصف كما ورد في فهرس المستودع، بلغته الأصلية."))
            desc_label.configure(text=arabic, anchor="e", justify="right")

        terms = skill.get("terms") or []
        terms_label.configure(text=(tr("المصطلحات: ") + "  ·  ".join(terms)) if terms else "")

        invocation = "/" + skill["id"]
        install_cli = skill.get("install_cli") or (
            "npx agentic-awesome-skills --claude --skills %s" % skill["id"])

        for widget, value in ((invoke_text, invocation), (install_text, install_cli)):
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", value)
            widget.configure(state="disabled")

        invoke_copy.bind("<Button-1>",
                         lambda _e: copy_value(invocation, "أمر الاستدعاء"))
        install_copy.bind("<Button-1>",
                          lambda _e: copy_value(install_cli, "أمر التثبيت"))

        path_label.configure(text=tr("المسار: %s") % skill["path"])
        target_combo.set(next((target_label(t) for t in TARGETS if t["id"] == state["target"]),
                              target_label(TARGETS[0])))

    def copy_value(value, label):
        root.clipboard_clear()
        root.clipboard_append(value)
        root.update()
        set_status(tr("تم النسخ: ") + tr(label), ACCENT)

    def on_target_change(_event=None):
        label = target_var.get()
        target = next((t for t in TARGETS if target_label(t) == label), TARGETS[0])
        state["target"] = target["id"]
        settings["target"] = target["id"]
        save_settings(settings)

    target_combo.bind("<<ComboboxSelected>>", on_target_change)

    # ---------------- search --------------------------------------------------
    def on_search(_event=None):
        value = search_entry.get()
        new_query = "" if value == placeholder_text else value
        if new_query != state["query"]:
            if state["smart_ids"] is not None or state["smart_why"]:
                state["smart_ids"] = None
                state["smart_why"] = {}
                smart_note.configure(text="")
        state["query"] = new_query
        state["rendered"] = RENDER_CAP
        refresh_list()

    def focus_search(_event=None):
        if search_entry.get() == placeholder_text:
            search_entry.delete(0, "end")
            search_entry.configure(fg=TEXT)
        search_entry.focus_set()
        return "break"

    def blur_search(_event=None):
        if not search_entry.get().strip():
            search_entry.delete(0, "end")
            search_entry.insert(0, placeholder_text)
            search_entry.configure(fg=MUTED)

    search_entry.bind("<FocusIn>", focus_search)
    search_entry.bind("<FocusOut>", blur_search)
    search_entry.bind("<KeyRelease>", on_search)

    def clear_search():
        search_entry.delete(0, "end")
        state["query"] = ""
        state["smart_ids"] = None
        state["smart_why"] = {}
        smart_note.configure(text="")
        state["rendered"] = RENDER_CAP
        refresh_list()

    root.bind("<Control-f>", focus_search)
    root.bind("<Escape>", lambda _e: clear_search())

    # ---------------- البحث الذكي -------------------------------------------
    def run_smart_search():
        if state.get("smart_busy"):
            return
        value = search_entry.get().strip()
        if not value or value == placeholder_text:
            set_status(tr("اكتب طلبك أولاً، مثال: مهارة لتحليل مشروع"), WARN)
            return

        candidates = search_engine.score_skills(all_skills, value, limit=60)
        if not candidates:
            state["smart_ids"] = []
            state["smart_why"] = {}
            smart_note.configure(text=tr("لم أجد مرشحاً مطابقاً — جرّب كلمات أخرى"), fg=WARN)
            refresh_list()
            return

        api_key = settings.get("gemini_key", "").strip()
        model = settings.get("gemini_model") or search_engine.GEMINI_MODELS[0]

        if not api_key:
            ids = [skill["id"] for skill in candidates[:30]]
            state["smart_ids"] = ids
            state["smart_why"] = {}
            smart_note.configure(
                text=tr("بحث محلي ذكي: %d نتيجة. أضف مفتاح النموذج من الإعدادات لترتيب أدق.")
                     % len(ids), fg=MUTED)
            state["rendered"] = RENDER_CAP
            refresh_list()
            set_status(tr("بحث محلي بدون نموذج"), ACCENT)
            return

        state["smart_busy"] = True
        state["smart_ids"] = None
        smart_note.configure(text=tr("جارٍ فهم طلبك عبر النموذج…"), fg=ACCENT)
        set_status(tr("جارٍ البحث الذكي…"), ACCENT)

        def worker():
            understanding, results, error = search_engine.gemini_rerank(
                api_key, model, value, candidates)
            ui_queue.put(("smart", (understanding, results, error, value)))

        threading.Thread(target=worker, daemon=True).start()

    # ---------------- token dialog --------------------------------------------
    def open_token_dialog():
        dialog = tk.Toplevel(root)
        dialog.title(tr("الإعدادات"))
        dialog.configure(bg=BG)
        dialog.geometry("%dx%d" % (px(560), px(430)))
        dialog.transient(root)

        def field_label(text):
            tk.Label(dialog, text=tr(text), font=bold_font, bg=BG, fg=TEXT).pack(
                anchor="e", padx=px(16), pady=(px(12), px(2)))

        def field_entry(value, mono=True):
            widget = tk.Entry(dialog, bg=PANEL_2, fg=TEXT, insertbackground=ACCENT,
                              relief="flat", font=mono_font if mono else base_font,
                              justify="left", highlightthickness=1,
                              highlightbackground=BORDER)
            widget.pack(fill="x", padx=px(16), pady=(0, px(2)))
            widget.insert(0, value)
            return widget

        field_label("رمز وصول GitHub (اختياري)")
        tk.Label(dialog,
                 text=tr("بدون رمز: 60 طلباً في الساعة — تنزيل جماعي كبير سيتوقف.\n"
                         "مع رمز (fine-grained, read-only): 5000 طلب في الساعة."),
                 font=small_font, bg=BG, fg=MUTED, justify="right").pack(anchor="e", padx=px(16))
        token_entry = field_entry(settings.get("token", ""))

        field_label("مفتاح النموذج الذكي (اختياري)")
        tk.Label(dialog, text="Google Gemini API key", font=small_font, bg=BG, fg=MUTED,
                 anchor="e").pack(anchor="e", padx=px(16))
        tk.Label(dialog,
                 text=tr("بدون مفتاح يعمل البحث الذكي محلياً بالكلمات المفتاحية.\n"
                         "مع مفتاح النموذج تُرتَّب النتائج حسب فهم الطلب ويظهر سبب الاختيار."),
                 font=small_font, bg=BG, fg=MUTED, justify="right").pack(anchor="e", padx=px(16))
        key_entry = field_entry(settings.get("gemini_key", ""))

        model_row = tk.Frame(dialog, bg=BG)
        model_row.pack(fill="x", padx=px(16), pady=(px(8), 0))
        tk.Label(model_row, text=tr("النموذج:"), font=small_font, bg=BG, fg=MUTED).pack(
            side="right", padx=(0, px(8)))
        model_var = tk.StringVar(value=settings.get("gemini_model")
                                 or search_engine.GEMINI_MODELS[0])
        model_combo = ttk.Combobox(model_row, textvariable=model_var,
                                   values=search_engine.GEMINI_MODELS, width=24,
                                   font=small_font)
        model_combo.pack(side="right")

        row = tk.Frame(dialog, bg=BG)
        row.pack(fill="x", padx=px(16), pady=(px(14), 0))

        def save():
            settings["token"] = token_entry.get().strip()
            settings["gemini_key"] = key_entry.get().strip()
            settings["gemini_model"] = model_var.get().strip() or search_engine.GEMINI_MODELS[0]
            save_settings(settings)
            dialog.destroy()
            set_status(tr("تم حفظ الإعدادات"), ACCENT)

        tk.Label(row, text=tr("حفظ"), font=base_font, bg=ACCENT, fg="#06231F", padx=px(16),
                 pady=px(5), cursor="hand2").pack(side="right")
        row.winfo_children()[-1].bind("<Button-1>", lambda _e: save())
        tk.Label(row, text=tr("إلغاء"), font=base_font, bg=PANEL_2, fg=TEXT, padx=px(16),
                 pady=px(5), cursor="hand2").pack(side="right", padx=(0, px(8)))
        row.winfo_children()[-1].bind("<Button-1>", lambda _e: dialog.destroy())

    # ---------------- download -------------------------------------------------
    def resolve_target_dir(target, ask_folder=False):
        if target["kind"] == "custom" or ask_folder:
            start = state["last_dir"] if Path(state["last_dir"]).exists() else str(Path.home())
            chosen = filedialog.askdirectory(title=tr("اختر مجلد حفظ المهارات"), initialdir=start)
            if not chosen:
                return None
            state["last_dir"] = chosen
            settings["last_dir"] = chosen
            save_settings(settings)
            return Path(chosen)

        if target["kind"] == "home":
            return Path.home() / target["path"]

        project = state.get("project_dir") or ""
        if not project or not Path(project).is_dir():
            chosen = filedialog.askdirectory(
                title=tr("اختر مجلد المشروع الذي يستخدم %s") % target_label(target))
            if not chosen:
                return None
            state["project_dir"] = chosen
            settings["project_dir"] = chosen
            save_settings(settings)
            project = chosen
        return Path(project) / target["path"]

    def set_busy(busy, text=""):
        state["busy"] = busy
        if busy:
            progress_label.configure(text=text)
            progress_label.pack(side="left", padx=px(8))
            cancel_btn.pack(side="left", padx=(0, px(8)))
        else:
            progress_label.pack_forget()
            cancel_btn.pack_forget()

    def drain_queue():
        try:
            while True:
                kind, payload = ui_queue.get_nowait()
                if kind == "progress":
                    done, total, label = payload
                    progress_label.configure(text="%d/%d — %s" % (done, total, label))
                elif kind == "status":
                    set_status(payload, ACCENT)
                elif kind == "done":
                    ok_count, fail_count, folder, notes = payload
                    set_busy(False)
                    message = tr("انتهى: نجح %d، فشل %d") % (ok_count, fail_count)
                    set_status(message + "  →  " + str(folder), OK if not fail_count else WARN)
                    if notes:
                        progress_label.configure(text=notes[0])
                    paint_rows()
                elif kind == "error":
                    set_busy(False)
                    set_status(payload, DANGER)
                elif kind == "smart":
                    understanding, results, error, query = payload
                    state["smart_busy"] = False
                    if error:
                        smart_note.configure(text=tr(error) if error in STR else error, fg=DANGER)
                        ids = [skill["id"] for skill in
                               search_engine.score_skills(all_skills, query, limit=30)]
                        state["smart_ids"] = ids
                        state["smart_why"] = {}
                        set_status(tr("تعذّر استخدام النموذج — عرض نتائج محلية"), WARN)
                    else:
                        state["smart_ids"] = [sid for sid, _why in results]
                        state["smart_why"] = dict(results)
                        smart_note.configure(text=understanding or tr("نتائج البحث الذكي"),
                                             fg=ACCENT)
                        set_status(tr("نتائج البحث الذكي: %d") % len(results), ACCENT)
                    state["rendered"] = RENDER_CAP
                    refresh_list()
        except queue.Empty:
            pass
        root.after(120, drain_queue)

    def start_selected(single=False, force_folder=False):
        if state["busy"]:
            set_status(tr("عملية تنزيل قيد التنفيذ بالفعل…"), WARN)
            return
        if single:
            skill = current_skill()
            if not skill:
                return
            skills = [skill]
        else:
            skills = [skill_by_id[sid] for sid in state["checked"] if sid in skill_by_id]
        if not skills:
            set_status(tr("لم تحدد أي مهارة"), WARN)
            return

        target = TARGET_BY_ID.get(state["target"], TARGETS[0])
        dest = resolve_target_dir(target, ask_folder=force_folder)
        if dest is None:
            return

        label = target_label(target) if not force_folder else tr("مجلد مخصص")
        start_download(skills, False, dest, label)

    def start_download(skills, is_all, dest=None, target_label=""):
        if state["busy"]:
            set_status(tr("عملية تنزيل قيد التنفيذ بالفعل…"), WARN)
            return
        if not skills:
            return
        if dest is None:
            target = TARGET_BY_ID.get(state["target"], TARGETS[0])
            dest = resolve_target_dir(target)
            if dest is None:
                return
            target_label = target["label"]

        if len(skills) > 1:
            question = tr("سيتم تنزيل %d مهارة إلى:\n%s\n\nالمتابعة؟") % (len(skills), dest)
            if not messagebox.askyesno(tr("تأكيد التنزيل"), question):
                return
        if len(skills) > 25 and not settings.get("token"):
            if not messagebox.askyesno(
                    tr("تنزيل كبير بدون رمز GitHub"),
                    tr("بدون رمز وصول، يسمح GitHub بـ60 طلباً في الساعة فقط.\n"
                       "تنزيل %d مهارة سيحتاج %d طلباً وقد يتوقف في المنتصف.\n\n"
                       "أضف رمزاً من «إعدادات GitHub» لرفع الحد إلى 5000 طلب/ساعة.\n\n"
                       "هل تريد المتابعة الآن على أي حال؟") % (len(skills), len(skills))):
                return

        try:
            dest.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            set_status(tr("تعذّر إنشاء المجلد: %s") % exc, DANGER)
            return

        cancel_event.clear()
        set_busy(True, "0/%d" % len(skills))
        set_status(tr("جارٍ التنزيل إلى %s") % dest, ACCENT)

        def worker():
            client = repo_client()
            ok_total = fail_total = 0
            notes = []
            log_lines = []
            started = time.strftime("%Y-%m-%d %H:%M:%S")

            try:
                for position, skill in enumerate(skills, start=1):
                    if cancel_event.is_set():
                        notes.append(tr("أُوقف التنزيل بواسطة المستخدم"))
                        break
                    ui_queue.put(("progress", (position, len(skills), skill["id"])))
                    try:
                        ok, fail, _folder, note = client.download_skill(skill, dest)
                        if note == "موجودة":
                            ok_total += 1
                            status = "SKIP"
                        else:
                            ok_total += 1 if ok and not fail else 0
                            fail_total += 1 if fail or not ok else 0
                            status = "OK" if not fail else "PARTIAL"
                    except Exception as exc:  # noqa: BLE001
                        fail_total += 1
                        status = "FAIL"
                        notes.append("%s: %s" % (skill["id"], exc))
                    log_lines.append("[%s] %s" % (status, skill["id"]))
            except Exception as exc:  # noqa: BLE001
                ui_queue.put(("error", "فشل التنزيل: %s" % exc))
                return

            try:
                with open(Path(dest) / "aas-download-log.txt", "a", encoding="utf-8") as fh:
                    fh.write("\n# %s — target=%s\n" % (started, target_label))
                    fh.write("\n".join(log_lines))
                    fh.write("\n")
            except Exception:
                pass

            ui_queue.put(("done", (ok_total, fail_total, dest, notes)))

        threading.Thread(target=worker, daemon=True).start()

    cancel_btn.bind("<Button-1>", lambda _e: (cancel_event.set(),
                                              set_status(tr("جارٍ الإيقاف…"), WARN)))

    # ---------------- boot ------------------------------------------------------
    def switch_language():
        settings["lang"] = "en" if lang == "ar" else "ar"
        save_settings(settings)
        os.environ.pop("AAS_TOGGLE_TEST", None)  # لا تُمرّر علم الاختبار للعملية الجديدة
        try:
            if getattr(sys, "frozen", False):
                args = [sys.executable]
            else:
                args = [sys.executable, str(Path(__file__).resolve())]
            subprocess.Popen(args)
        except Exception:
            pass
        root.destroy()

    lang_btn.bind("<Button-1>", lambda _e: switch_language())

    def apply_language_walk(widget):
        for child in widget.winfo_children():
            apply_language_walk(child)
        try:
            if widget.winfo_class() in ("Label", "Button", "Checkbutton", "Radiobutton"):
                value = widget.cget("text")
            else:
                return
        except Exception:
            return
        if not value:
            return
        translated = tr(value)
        if translated != value:
            try:
                widget.configure(text=translated)
            except Exception:
                pass
        if not RTL:
            try:
                if widget.cget("anchor") == "e":
                    widget.configure(anchor="w")
                if widget.cget("justify") == "right":
                    widget.configure(justify="left")
            except Exception:
                pass

    def on_close():
        settings["target"] = state["target"]
        save_settings(settings)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    update_selected_label()
    refresh_list()
    drain_queue()
    if lang != "ar":
        apply_language_walk(root)

    first = visible_skills()
    if first:
        select_skill(first[0]["id"])

    if os.environ.get("AAS_LAYOUT_PROBE"):
        def probe():
            print("scale=%.3f screen=%dx%d win=%dx%d sidebar=%d middle=%d details=%d rows=%d"
                  % (scale, screen_w, screen_h, root.winfo_width(), root.winfo_height(),
                     sidebar.winfo_width(), middle.winfo_width(), details.winfo_width(),
                     len(row_widgets)))
            print("smart_btn w=%d reqw=%d label_w=%d"
                  % (smart_btn.winfo_width(), smart_btn.winfo_reqwidth(),
                     smart_label.winfo_width()))
            root.destroy()

        root.after(1500, probe)

    if os.environ.get("AAS_UI_TEST"):
        def ui_probe():
            select_all(True)
            print("selected_all=%d" % len(state["checked"]))
            first_id = visible_skills()[0]["id"]
            toggle_check(first_id, False)
            print("after_uncheck=%d label=%s" % (len(state["checked"]),
                                                 selected_label.cget("text")))
            state["filter"] = "s:mobile:mobile"
            state["rendered"] = RENDER_CAP
            paint_categories()
            refresh_list()
            print("mobile_results=%d rendered_rows=%d groups=%d"
                  % (len(visible_skills()), len(row_widgets), len(GROUPS)))
            print("caret_rows=" + ",".join(
                key for key, parts in tree_rows.items() if parts["caret"] is not None))
            print("targets=%s" % ",".join(t["id"] for t in TARGETS))
            root.destroy()

        root.after(1400, ui_probe)

    if os.environ.get("AAS_TOGGLE_TEST"):
        root.after(1200, switch_language)

    if os.environ.get("AAS_SMART_TEST"):
        def smart_probe():
            search_entry.delete(0, "end")
            search_entry.configure(fg=TEXT)
            search_entry.insert(0, "ادارة محتوى فيسبوك")
            state["query"] = "ادارة محتوى فيسبوك"
            run_smart_search()
            ids = state["smart_ids"] or []
            print("smart_ids=%d first=%s" % (len(ids), ids[0] if ids else "-"))
            print("smart_note=%s" % smart_note.cget("text")[:80])
            if not os.environ.get("AAS_SMART_SHOW"):
                root.after(300, root.destroy)

        root.after(1200, smart_probe)

    root.mainloop()
    return 0


def main(argv):
    if "--selftest" in argv:
        return cli_selftest()
    if "--bulk-test" in argv:
        index = argv.index("--bulk-test")
        try:
            count, dest = int(argv[index + 1]), argv[index + 2]
        except (IndexError, ValueError):
            print("usage: app.py --bulk-test <count> <dest-dir>")
            return 2
        return cli_bulk_test(count, dest)
    if "--download-test" in argv:
        index = argv.index("--download-test")
        try:
            skill_id, dest = argv[index + 1], argv[index + 2]
        except IndexError:
            print("usage: app.py --download-test <skill-id> <dest-dir>")
            return 2
        return cli_download_test(skill_id, dest)

    catalog = load_catalog()
    return build_ui(catalog, load_settings())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
