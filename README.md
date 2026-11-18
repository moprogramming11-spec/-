# Sokar w Laban Backend

واجهة خلفية لمشروع Sokar w Laban باستخدام FastAPI وSQLite.

## المتطلبات

- Python 3.10 أو أحدث
- pip
- حساب Cloudinary لرفع الصور

## التثبيت والتشغيل على Windows

افتح PowerShell داخل مجلد `backend`، ثم نفّذ:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

إذا كان اسم ملف الكود مختلفًا عن `main.py`، غيّر `main` في أمر التشغيل إلى اسم الملف بدون `.py`.

بعد التشغيل، افتح `http://127.0.0.1:8000/docs` لتجربة الـAPI من Swagger UI.

## المكتبات

- **FastAPI**: إنشاء مسارات الـAPI.
- **Uvicorn**: تشغيل تطبيق FastAPI.
- **python-multipart**: استقبال الملفات المرفوعة عبر `UploadFile` و`File`.
- **Cloudinary**: رفع الصور إلى Cloudinary.
- **pwdlib[argon2]**: تشفير كلمات المرور والتحقق منها باستخدام Argon2.
- **PyJWT**: إنشاء والتحقق من JWT tokens.

`sqlite3` و`os` و`asyncio` مكتبات مدمجة مع Python ولا تحتاج إلى تثبيت منفصل. `asyncio` مستوردة في الكود الحالي لكنها غير مستخدمة.

## ملاحظات الإعداد

الكود الحالي يحتوي بيانات Cloudinary ومفتاح JWT مباشرةً داخله. لا ترفع هذا الملف إلى مستودع عام. قبل تشغيله في بيئة مشتركة، انقل القيم إلى إعدادات محلية أو متغيرات بيئة، وغيّر المفاتيح التي سبق مشاركتها.

قاعدة البيانات `database.db` تُنشأ تلقائيًا عند تشغيل التطبيق، في مجلد التشغيل الحالي.