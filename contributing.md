# Contributing / المساهمة

شكراً لاهتمامك. المشروع صغير ومقصده أن يبقى بسيطاً.

## Before you start

- افتح **Issue** أولاً للنقاش قبل أي تغيير كبير.
- للترجمة أو تحسين الوصف العربي: عدّل `data/skills.json` (الأوصاف اليدوية) ثم شغّل الأدوات.
- لا تُضف تبعيات خارجية وقت التشغيل؛ التطبيق يستخدم مكتبة Python القياسية فقط.

## Local checks / فحوصات محلية

```bash
python app.py --selftest
python tools/check_groups.py
python app.py --download-test mobile-design .tmp-download
```

## Pull requests

- فرع واحد لكل تغيير، رسائل كوميت بصيغة `type: summary` (feat, fix, docs, chore).
- أرفق لقطة شاشة لأي تغيير في الواجهة.
- لا ترفع `dist/` أو `build/` أو `data/ar_cache.json` أو أي إعدادات شخصية.

## Commit style

```
feat: add X
fix: correct Y when Z
docs: explain W
chore: bump tooling
```
