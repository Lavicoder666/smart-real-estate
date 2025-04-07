import os
import pickle
import joblib
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, models
from PIL import Image
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Listing, MaintenanceRequest, SavedListing
from .forms import ListingForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import EmptyPage, Paginator
from .choices import price_choices, bedroom_choices, state_choices, listing_type_choices, rent_schedule_choices
import pandas as pd
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.utils import timezone

# تحميل النموذج المدرب
model_path = os.path.join(settings.BASE_DIR, 'ml_models/model.pth')
model = models.resnet18(pretrained=True)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, 4)  # 4 فئات: kitchen, living_room, bathroom, bedroom
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
model.eval()

# تعريف التحولات
data_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# دالة لتصنيف الصور
def classify_image(image_path, threshold=0.7):
    try:
        image = Image.open(image_path)
    except FileNotFoundError:
        return "file_not_found"
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image = data_transforms(image).unsqueeze(0)
    outputs = model(image)
    _, preds = torch.max(outputs, 1)
    probabilities = torch.nn.functional.softmax(outputs, dim=1)
    max_prob = probabilities[0][preds[0]].item()
    class_names = ['bathroom', 'bedroom', 'kitchen', 'living_room']
    if max_prob < threshold:
        return "others"
    return class_names[preds[0]]

def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def index(request):
    print(settings.CURRENCY_CONVERSION_RATES)  # طباعة الإعدادات للتأكد من تحميلها بشكل صحيح
    listings = Listing.objects.order_by('-list_date').filter(is_published=True)
    currency = request.session.get('currency', 'USD')

    for listing in listings:
        listing.converted_price = convert_currency(listing.price, 'USD', currency)
        # Debugging statement to print the converted price
        print(f"Listing ID: {listing.id}, Converted Price: {listing.converted_price}")

    paginator = Paginator(listings, 6)
    page = request.GET.get('page')
    paged_listings = paginator.get_page(page)

    context = {
        'listings': paged_listings,
        'state_choices': state_choices,
        'bedroom_choices': bedroom_choices,
        'price_choices': price_choices,
        'listing_type_choices': listing_type_choices,
        'rent_schedule_choices': rent_schedule_choices,
        'values': request.GET if request.GET else {},
        'currency': currency
    }
    return render(request, 'listings/listings.html', context)

def listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    currency = request.session.get('currency', 'USD')
    listing.converted_price = convert_currency(listing.price, 'USD', currency)
    # Debugging statement to print the converted price
    print(f"Listing ID: {listing.id}, Converted Price: {listing.converted_price}")

    # تصنيف الصور
    if listing.photo_main:
        ensure_directory_exists(listing.photo_main.path)
        listing.photo_main_category = classify_image(listing.photo_main.path)
    if listing.photo_1:
        ensure_directory_exists(listing.photo_1.path)
        listing.photo_1_category = classify_image(listing.photo_1.path)
    if listing.photo_2:
        ensure_directory_exists(listing.photo_2.path)
        listing.photo_2_category = classify_image(listing.photo_2.path)
    if listing.photo_3:
        ensure_directory_exists(listing.photo_3.path)
        listing.photo_3_category = classify_image(listing.photo_3.path)
    if listing.photo_4:
        ensure_directory_exists(listing.photo_4.path)
        listing.photo_4_category = classify_image(listing.photo_4.path)
    if listing.photo_5:
        ensure_directory_exists(listing.photo_5.path)
        listing.photo_5_category = classify_image(listing.photo_5.path)
    listing.save()

    # الحصول على توصيات للعقارات المشابهة
    recommendations = get_recommendations(listing_id)

    # تحويل أسعار التوصيات
    for recommendation in recommendations:
        recommendation.converted_price = convert_currency(recommendation.price, 'USD', currency)
        # Debugging statement to print the converted price
        print(f"Recommendation ID: {recommendation.id}, Converted Price: {recommendation.converted_price}")

    # إضافة رابط VR إلى السياق إذا كان موجودًا
    context = {
        'listing': listing,
        'recommendations': recommendations,
        'vr_embed_code': listing.vr_embed_code if hasattr(listing, 'vr_embed_code') and listing.vr_embed_code else None,
        'currency': currency
    }
    return render(request, 'listings/listing.html', context)


def search(request):
    queryset_list = Listing.objects.order_by('-list_date')
    currency = request.session.get('currency', 'USD')

    # Keywords
    if 'keywords' in request.GET:
        keywords = request.GET['keywords']
        if keywords:
            queryset_list = queryset_list.filter(description__icontains=keywords)

    # City
    if 'city' in request.GET:
        city = request.GET['city']
        if city:
            queryset_list = queryset_list.filter(city__iexact=city)

    # State
    if 'state' in request.GET:
        state = request.GET['state']
        if state:
            queryset_list = queryset_list.filter(state__iexact=state)

    # Bedrooms
    if 'bedrooms' in request.GET:
        bedrooms = request.GET['bedrooms']
        if bedrooms:
            queryset_list = queryset_list.filter(bedrooms__gte=bedrooms)

    # Price (Min and Max)
    if 'price_min' in request.GET or 'price_max' in request.GET:
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        if price_min:
            # Convert the min price to USD for filtering
            converted_price_min = convert_currency(float(price_min), currency, 'USD')
            queryset_list = queryset_list.filter(price__gte=converted_price_min)
        if price_max:
            # Convert the max price to USD for filtering
            converted_price_max = convert_currency(float(price_max), currency, 'USD')
            queryset_list = queryset_list.filter(price__lte=converted_price_max)

    # Listing Type
    if 'listing_type' in request.GET:
        listing_type = request.GET['listing_type']
        if listing_type:
            queryset_list = queryset_list.filter(listing_type=listing_type)

    # Rent Payment Schedule
    if 'rent_payment_schedule' in request.GET:
        rent_payment_schedule = request.GET['rent_payment_schedule']
        if rent_payment_schedule:
            queryset_list = queryset_list.filter(rent_payment_schedule=rent_payment_schedule)

    # Convert prices after filtering
    for listing in queryset_list:
        listing.converted_price = convert_currency(listing.price, 'USD', currency)

    context = {
        'state_choices': state_choices,
        'bedroom_choices': bedroom_choices,
        'price_choices': price_choices,
        'listing_type_choices': listing_type_choices,
        'rent_schedule_choices': rent_schedule_choices,
        'listings': queryset_list,
        'values': request.GET if request.GET else {},
        'currency': currency
    }
    return render(request, 'listings/search.html', context)

@login_required
def request_maintenance(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        description = request.POST.get('description')

        maintenance_request = MaintenanceRequest.objects.create(
            listing=listing,
            user=request.user,
            request_type=request_type,
            description=description
        )

        # Get realtor email
        realtor_email = listing.realtor.email

        # Send mail
        send_mail(
            'Maintenance Request',
            f'There has been a maintenance request for {listing.title}. Sign into the admin panel for more info:\n\n'
            f'Request Type: {request_type}\nDescription: {description}\n\n'
            f'User: {request.user.username} ({request.user.email})',
            'laethdeeb66@gmail.com',  # ضع عنوان بريدك الإلكتروني هنا (المرسل)
            [realtor_email],  # عنوان بريد وكيل العقار (المستقبل)
            fail_silently=False
        )

        messages.success(request, 'Request sent successfully!')
        return redirect('listing', listing_id=listing_id)

    return render(request, 'listing.html', {'listing': listing})

def predict_price(size, bedrooms, bathrooms, furnished):
    # تحميل النموذج المدرب
    model_path = os.path.join(settings.BASE_DIR, 'ml_models/real_estate_model.pkl')
    model = joblib.load(model_path)

    # تحويل "furnished" إلى قيمة رقمية (1 لـ Yes، و 0 لـ No)
    furnished_value = 1 if furnished.lower() == 'yes' else 0

    # تجهيز البيانات المدخلة للنموذج
    input_data = np.array([size, bedrooms, bathrooms, furnished_value]).reshape(1, -1)

    # التنبؤ بالسعر
    predicted_price = model.predict(input_data)[0]
    return round(predicted_price, 2)

# تحديث وظيفة عرض التنبؤ بالسعر
def predict_price_view(request):
    if request.method == 'POST':
        size = int(request.POST['size'])
        bedrooms = int(request.POST['bedrooms'])
        bathrooms = int(request.POST['bathrooms'])
        furnished = request.POST['furnished']  # تأخذ "Yes" أو "No"

        # استدعاء وظيفة التنبؤ
        try:
            predicted_price = predict_price(size, bedrooms, bathrooms, furnished)
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'listings/predict_price.html', {
                'size': size,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'furnished': furnished,
            })

        return render(request, 'listings/predict_price.html', {
            'predicted_price': predicted_price,
            'size': size,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'furnished': furnished,
        })

    return render(request, 'listings/predict_price.html')
# تحميل النموذج المدرب
model_path = os.path.join(settings.BASE_DIR, 'ml_models/property_recommender.pkl')
with open(model_path, 'rb') as file:
    df, cosine_sim = pickle.load(file)

def get_recommendations(listing_id, num_recommendations=5):
    # جلب العقار الحالي من قاعدة البيانات
    current_listing = Listing.objects.get(pk=listing_id)
    
    # تحويل الحقول النصية إلى أرقام
    current_sqft = float(current_listing.sqft)
    current_bedrooms = int(current_listing.bedrooms)
    
    # الحصول على العقارات في نفس الموقع
    similar_listings = Listing.objects.filter(city=current_listing.city)
    
    # فرز العقارات بناءً على المساحة وعدد غرف النوم
    similar_listings = sorted(
        similar_listings,
        key=lambda x: (abs(float(x.sqft) - current_sqft), abs(int(x.bedrooms) - current_bedrooms))
    )

    # إرجاع عدد معين من التوصيات
    return similar_listings[:num_recommendations]

def recommend_properties(request, listing_id):
    recommendations = get_recommendations(listing_id)
    currency = request.session.get('currency', 'USD')
    
    # تحويل أسعار التوصيات
    for recommendation in recommendations:
        recommendation.converted_price = convert_currency(recommendation.price, 'USD', currency)

    return render(request, 'listings/recommendations.html', {'recommendations': recommendations, 'currency': currency})

def admin_required(login_url=None):
    return user_passes_test(lambda u: u.is_superuser, login_url=login_url)

@login_required
def save_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    saved_listing, created = SavedListing.objects.get_or_create(user=request.user, listing=listing)
    if created:
        messages.success(request, 'Listing saved successfully!')
    else:
        messages.info(request, 'Listing is already in your saved list.')
    return redirect('listing', listing_id=listing_id)

@login_required(login_url='/login/')
def add_listing(request):
    # التأكد من أن المستخدم إما أدمن أو Realtor مسجل
    if not request.user.is_superuser and not hasattr(request.user, 'realtor'):
        messages.error(request, 'You are not authorized to add a listing.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.realtor = request.user.realtor  # تعيين السمسار بناءً على المستخدم الحالي
            listing.save()
            messages.success(request, 'Listing added successfully!')
            return redirect('dashboard')
    else:
        form = ListingForm()

    context = {
        'form': form
    }
    return render(request, 'listings/add_listing.html', context)

# دالة لتغيير العملة
def change_currency(request, currency):
    if currency in settings.CURRENCY_CHOICES:
        request.session['currency'] = currency
    return redirect(request.META.get('HTTP_REFERER', '/'))

# دالة لتحويل العملة
def convert_currency(amount, from_currency, to_currency):
    if from_currency not in settings.CURRENCY_CONVERSION_RATES or to_currency not in settings.CURRENCY_CONVERSION_RATES:
        raise ValueError("Unsupported currency")
    
    # تحويل المبلغ إلى الدولار أولاً
    amount_in_usd = amount / settings.CURRENCY_CONVERSION_RATES[from_currency]
    
    # تحويل المبلغ من الدولار إلى العملة المطلوبة
    converted_amount = amount_in_usd * settings.CURRENCY_CONVERSION_RATES[to_currency]
    return round(converted_amount, 2)
