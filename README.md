# Alking-Pro Trading Server

سيرفر تداول آلي لمنصة Quotex مع تحليل 4 استراتيجيات متزامنة

## المميزات

✅ تسجيل دخول تلقائي إلى Quotex  
✅ تحليل 4 استراتيجيات معاً (SMA، RSI، Bollinger، Volume)  
✅ تنفيذ صفقات حقيقية على المنصة  
✅ إيقاف تلقائي بعد 5 صفقات ربح متتالية  
✅ إيقاف تلقائي بعد صفقتين خسارة متتالية  
✅ سحب تلقائي لقائمة العملات من المنصة  

## كيفية التشغيل على Render

1. انسخ هذا المستودع إلى GitHub  
2. اذهب إلى [render.com](https://render.com)  
3. اضغط "New +" → "Web Service"  
4. اختر مستودع Alking-Pro-Trading-Server  
5. سيتم قراءة render.yaml تلقائياً  
6. اضغط "Apply"  

## نقاط API

| المسار | الطريقة | الوظيفة |
|--------|---------|---------|
| `/api/login` | POST | تسجيل الدخول |
| `/api/symbols` | GET | جلب العملات |
| `/api/trade/execute` | POST | تنفيذ صفقة |
| `/api/status` | GET | حالة النظام |
| `/health` | GET | فحص الصحة |

## المتطلبات

- Python 3.11+
- Chrome Browser (يتم تثبيته تلقائياً)
