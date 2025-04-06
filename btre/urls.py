from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from listings import views
from accounts import views as accounts_views  # استيراد الفيوز الخاصة بحسابات المستخدمين

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('listings/', include('listings.urls')),
    path('accounts/', include('accounts.urls')),
    path('contacts/', include('contacts.urls')),
    path('listing/<int:listing_id>/request-maintenance/', views.request_maintenance, name='request_maintenance'),
    path('chatbot/', include('chatbot.urls')),
    path('predict-price/', views.predict_price_view, name='predict_price'),
    
    
    # مسار التحقق من البريد الإلكتروني
    path('accounts/verify_email/<int:user_id>/', accounts_views.verify_email, name='verify_email'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
