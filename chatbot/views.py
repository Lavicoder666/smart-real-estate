from django.shortcuts import render
from django.http import JsonResponse
import re
import logging
from django.conf import settings
import openai  # استدعاء مكتبة OpenAI
import requests

# إعداد الـ Logger لتتبع الأخطاء
logger = logging.getLogger(__name__)

# تعيين مفتاح API ونقطة النهاية لـ OpenRouter
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = settings.OPENAI_API_KEY  # تأكد من تخزين المفتاح في الإعدادات

# قائمة الأسئلة المخصصة والإجابات
custom_responses = {
    "what is this website about": "This website is about real estate listings and provides information on properties available for sale or rent.",
    "ما هو هذا الموقع": "هذا الموقع مخصص لعرض قوائم العقارات ويوفر معلومات عن العقارات المتاحة للبيع أو الإيجار.",
    
    # أسئلة وأجوبة باللغة الإنجليزية
    "how can i register on the website?": "To register on the website, click on the 'Sign Up' button at the top of the page and follow the instructions.",
    "how can i contact support?": "You can contact support by emailing support@example.com.",
    
    # أسئلة وأجوبة باللغة العربية
    "كيف يمكنني التسجيل على الموقع؟": "للتسجيل على الموقع، انقر على زر 'التسجيل' في أعلى الصفحة واتبع التعليمات.",
    "كيف يمكنني الاتصال بالدعم الفني؟": "يمكنك الاتصال بالدعم الفني عبر البريد الإلكتروني support@example.com."
}

# وظيفة لتنظيف النصوص المدخلة
def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def chatbot_response(request):
    if request.method == "POST":
        user_message = request.POST.get('message')
        cleaned_message = clean_text(user_message)
        
        if cleaned_message in custom_responses:
            bot_response = custom_responses[cleaned_message]
            return JsonResponse({"message": bot_response})

        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": user_message}
                ]
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()  # لو صار خطأ، يرفع استثناء
            result = response.json()
            bot_response = result["choices"][0]["message"]["content"]
            return JsonResponse({"message": bot_response})

        except Exception as e:
            logger.error(f"Error contacting DeepSeek API: {e}")
            return JsonResponse({"message": "Error contacting DeepSeek API."})

    else:
        return JsonResponse({"message": "Invalid request method."})
