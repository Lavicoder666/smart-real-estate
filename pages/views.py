from django.shortcuts import render
from listings.models import Listing
from realtors.models import Realtor
from listings.choices import price_choices, bedroom_choices, state_choices, listing_type_choices, rent_schedule_choices

# دالة لتحويل العملة
def convert_currency(amount, from_currency, to_currency, conversion_rates):
    if from_currency not in conversion_rates or to_currency not in conversion_rates:
        raise ValueError("Unsupported currency")
    
    # تحويل المبلغ إلى الدولار أولاً
    amount_in_usd = amount / conversion_rates[from_currency]
    
    # تحويل المبلغ من الدولار إلى العملة المطلوبة
    converted_amount = amount_in_usd * conversion_rates[to_currency]
    return round(converted_amount, 2)

# Create your views here.

def index(request):
    listings = Listing.objects.order_by('-list_date').filter(is_published=True)[:3]
    currency = request.session.get('currency', 'USD')
    conversion_rates = {
        'USD': 1.0,
        'SYP': 20000.0  # مثال على سعر الصرف، يجب تعديلها حسب الأسعار الفعلية
    }

    # تحويل الأسعار إلى العملة المطلوبة
    for listing in listings:
        listing.converted_price = convert_currency(listing.price, 'USD', currency, conversion_rates)

    context = {
        'listings': listings,
        'state_choices': state_choices,
        'bedroom_choices': bedroom_choices,
        'price_choices': price_choices,
        'listing_type_choices': listing_type_choices,
        'rent_schedule_choices': rent_schedule_choices,
        'values': request.GET if request.GET else {},  # Ensure values are passed correctly
        'currency': currency
    }
    return render(request, 'pages/index.html', context)

def about(request):
    # Get all realtors
    realtors = Realtor.objects.order_by('-hire_date')

    # Get MVP
    mvp_realtors = Realtor.objects.all().filter(is_mvp=True)

    context = {
        'realtors': realtors,
        'mvp_realtors': mvp_realtors
    }

    return render(request, 'pages/about.html', context)