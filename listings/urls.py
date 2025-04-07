from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='listings'),
    path('<int:listing_id>', views.listing, name='listing'),
    path('search', views.search, name='search'),
    path('predict-price/', views.predict_price_view, name='predict_price'),
    path('recommend/<int:listing_id>/', views.recommend_properties, name='recommend_properties'),
    path('add/', views.add_listing, name='add_listing'),
    path('save_listing/<int:listing_id>', views.save_listing, name='save_listing'),      
    path('change_currency/<str:currency>/', views.change_currency, name='change_currency'),                                                                                                                                                                 
]