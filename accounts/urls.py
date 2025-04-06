from django.urls import path
from . import views  # تأكد من أن جميع الدوال مستوردة
from listings.views import add_listing
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('delete_saved_listing/<int:listing_id>', views.delete_saved_listing, name='delete_saved_listing'), 
    path('add-listing/', add_listing, name='add_listing'),  
    path('edit-listing/<int:listing_id>/', views.edit_listing, name='edit_listing'),  
    path('delete-listing/<int:listing_id>/', views.delete_listing, name='delete_listing'),  
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    path('resend_code/', views.resend_code, name='resend_code'),
]
