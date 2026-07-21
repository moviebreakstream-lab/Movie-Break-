# ملخص الأبحاث الخارجية لمشروع Movie Break

## مصادر استخراج الروابط (Extractors):
- **Vidsrc.to**: يعتمد على `data-id` وجلب المصادر عبر `/ajax/embed/episode/{id}/sources`. يتطلب فك تشفير الروابط المشفرة (AES/Base64).
- **GogoAnime**: يستخدم مشغلات مثل Vidstreaming/GogoPlay. يتطلب فك تشفير AJAX باستخدام مفاتيح AES (Secret Keys).
- **TMDB**: يستخدم لجلب البيانات الوصفية عبر API Key.

## تقنيات فك التشفير:
- استخدام `cryptography` في Python للتعامل مع AES.
- تحليل ملفات JS (مثل `cpt.js`) لاستخراج مفاتيح التشفير الديناميكية.

## إعدادات Render:
- يتطلب `TMDB_API_KEY` كمتغير بيئة.
- يحتاج إلى `buildCommand` و `startCommand` صحيحة.
- لتجنب "Application exited early"، يفضل تشغيله كخدمة ويب (Web Service) بدلاً من Worker إذا كان سينتهي بسرعة.
