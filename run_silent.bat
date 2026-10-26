@echo off
rem تشغيل التطبيق من المصدر بدون نافذة سوداء
cd /d "%~dp0"
start "" pyw -3.14 "%~dp0app.py"
