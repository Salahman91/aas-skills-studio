# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 2.4.x | ✅ |
| < 2.4 | ❌ |

## Reporting a vulnerability / الإبلاغ عن ثغرة

**لا تفتح قضية عامة.** استخدم تبويب **Security → Report a vulnerability** في
هذا المستودع (Private vulnerability reporting)، أو راسل المشرف عبر GitHub.

سنرد خلال 72 ساعة، وننشر إصلاحاً وإشعاراً بعد التأكد من المشكلة.

## What this app does with your data

- التطبيق يعمل محلياً بالكامل. لا تيليمتري ولا تحليلات.
- يُخزَّن مفتاح GitHub (اختياري) ومفتاح Gemini (اختياري) في
  `%APPDATA%\AAS-Skills-Studio\settings.json` على جهازك فقط.
- لا يُرسل أي مفتاح إلى أي خادم غير الخدمة المقصودة (GitHub API أو Google Gemini).
- التنزيل يقرأ من `github.com` / `raw.githubusercontent.com` فقط.

## Scope notes

- المهارات المُنزَّلة **محتوى طرف ثالث**. راجع `SKILL.md` قبل تشغيل أي مهارة،
  خصوصاً الموسومة `critical` والتي قد تنفّذ أوامر.
- الملف التنفيذي غير موقّع بشهادة تجارية؛ تحقّق من `SHA256SUMS.txt` المرفق
  مع كل إصدار قبل التشغيل.
