from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.models import User
from contacts.models import Contact
from listings.models import MaintenanceRequest, SavedListing
from django.core.mail import send_mail
from .models import EmailVerification, User
from django.conf import settings
import uuid
import random
import string
from django.contrib.auth.decorators import login_required
from listings.models import Listing
from listings.forms import ListingForm
from django.http import HttpResponse



# دالة لتحويل العملة
def convert_currency(amount, from_currency, to_currency, conversion_rates):
    if from_currency not in conversion_rates or to_currency not in conversion_rates:
        raise ValueError("Unsupported currency")
    
    # تحويل المبلغ إلى الدولار أولاً
    amount_in_usd = amount / conversion_rates[from_currency]
    
    # تحويل المبلغ من الدولار إلى العملة المطلوبة
    converted_amount = amount_in_usd * conversion_rates[to_currency]
    return round(converted_amount, 2)

# Create verification code
def generate_verification_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def register(request):
    if request.method == 'POST':
        if 'verification_code' in request.POST:  # حالة إدخال كود التحقق
            verification_code = request.POST['verification_code']
            user_id = request.session.get('user_id')  # الحصول على معرف المستخدم من الجلسة
            if not user_id:
                messages.error(request, 'User ID not found in session. Please register again.')
                return redirect('register')
            
            try:
                user = User.objects.get(id=user_id)
                email_verification = EmailVerification.objects.get(user=user)
                if email_verification.verification_code == verification_code:
                    email_verification.is_verified = True
                    email_verification.save()
                    messages.success(request, 'Account verified successfully.')
                    return redirect('login')  # بعد التحقق الناجح
                else:
                    messages.error(request, 'Invalid verification code. Please try again.')
                    return render(request, 'accounts/register.html', {'show_verification': True})
            except User.DoesNotExist:
                messages.error(request, 'User does not exist.')
                return redirect('register')
            except EmailVerification.DoesNotExist:
                messages.error(request, 'Verification code does not exist.')
                return render(request, 'accounts/register.html', {'show_verification': True})

        else:  # حالة تسجيل حساب جديد
            # Get form values
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            password2 = request.POST['password2']

            if password == password2:
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'That username is taken')
                    return redirect('register')
                elif User.objects.filter(email=email).exists():
                    messages.error(request, 'That email is being used')
                    return redirect('register')
                else:
                    user = User.objects.create_user(username=username, password=password, email=email,
                                                    first_name=first_name, last_name=last_name)
                    user.save()

                    # Create a 6-character verification code
                    verification_code = generate_verification_code()

                    # Save the verification code in the database
                    EmailVerification.objects.create(user=user, verification_code=verification_code)

                    # Save user ID in session for verification later
                    request.session['user_id'] = user.id

                    # Send the verification code via email
                    send_mail(
                        'Welcome To Real Estate',
                        f'Your verification code is: {verification_code}',
                        'your_email@example.com',
                        [email],
                        fail_silently=False,
                    )

                    messages.success(request, 'You are now registered. A verification code has been sent to your email.')
                    return render(request, 'accounts/register.html', {'show_verification': True})

            else:
                messages.error(request, 'Passwords do not match')
                return redirect('register')

    else:
        return render(request, 'accounts/register.html')
    
def resend_code(request):
    if request.method == 'GET':
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Session expired. Please register again.')
            return redirect('register')
        
        try:
            user = User.objects.get(id=user_id)
            email_verification = EmailVerification.objects.get(user=user)
            
            # إنشاء كود جديد
            new_code = generate_verification_code()
            email_verification.verification_code = new_code
            email_verification.save()
            
            # إعادة إرسال البريد
            send_mail(
                'New Verification Code',
                f'Your new verification code is: {new_code}',
                settings.EMAIL_HOST_USER,  # استخدام settings هنا
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'New verification code has been sent.')
            return render(request, 'accounts/register.html', {'show_verification': True})
        
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('register')
        
        
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    else:
        return render(request, 'accounts/login.html')


def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        messages.success(request, 'You are now logged out')
        return redirect('index')
    return redirect('index')


def verify_email(request, user_id):
    if request.method == 'POST':
        code = request.POST['verification_code']
        user = User.objects.get(id=user_id)
        verification = EmailVerification.objects.get(user=user)

        if str(verification.verification_code) == code:
            verification.is_verified = True
            verification.save()
            user.is_active = True  # Activate user
            user.save()

            messages.success(request, 'Your email is verified, you can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid verification code')
            return redirect('verify_email', user_id=user_id)
    else:
        return render(request, 'accounts/register.html', {'user_id': user_id})

def dashboard(request):
    user = request.user  # المستخدم الحالي
    currency = request.session.get('currency', 'USD')  # العملة المختارة من الجلسة

    # أسعار الصرف - يجب تحديثها بشكل دوري
    conversion_rates = {
        'USD': 1.0,
        'SYP': 13000.0  
    }

    # العقارات المحفوظة وتحويل الأسعار للعملة المختارة
    saved_listings = SavedListing.objects.filter(user=user)
    for saved_listing in saved_listings:
        saved_listing.listing.converted_price = convert_currency(
            saved_listing.listing.price, 'USD', currency, conversion_rates
        )

    # بيانات العقارات والوكلاء
    my_listings = None
    realtor_contacts = None
    user_maintenance_requests = MaintenanceRequest.objects.filter(user=user)
    realtor_maintenance_requests = None

    # إذا كان المستخدم وكيل عقارات، اجلب العقارات التي يملكها والطلبات المتعلقة بها
    if user.is_authenticated and hasattr(user, 'realtor'):
        my_listings = Listing.objects.filter(realtor=user.realtor)
        realtor_contacts = Contact.objects.filter(listing_id__in=my_listings)
        realtor_maintenance_requests = MaintenanceRequest.objects.filter(listing__realtor=user.realtor)

    context = {
        'contacts': Contact.objects.filter(user_id=user.id).order_by('-contact_date'),
        'realtor_contacts': realtor_contacts,  # الطلبات الخاصة بالوكيل العقاري
        'maintenance_requests': user_maintenance_requests,  # طلبات الصيانة الخاصة بالمستخدم
        'realtor_maintenance_requests': realtor_maintenance_requests,  # طلبات الصيانة الخاصة بعقارات الوكيل
        'saved_listings': saved_listings,
        'currency': currency,
        'my_listings': my_listings,  # عقارات الوكيل العقاري
    }

    return render(request, 'accounts/dashboard.html', context)

@login_required
def delete_saved_listing(request, listing_id):
    saved_listing = get_object_or_404(SavedListing, user=request.user, listing_id=listing_id)
    saved_listing.delete()
    messages.success(request, 'Listing removed from saved listings.')
    return redirect('dashboard')

@login_required
def delete_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    # ✅ تأكد أن العقار يخص الـ Realtor المسجل فقط
    if hasattr(request.user, 'realtor') and request.user.realtor != listing.realtor:
        messages.error(request, "You are not authorized to delete this listing.")
        return redirect('dashboard')

    listing.delete()
    messages.success(request, "Listing deleted successfully!")
    return redirect('dashboard')

@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    # ✅ تأكد أن العقار يخص الـ Realtor المسجل فقط
    if hasattr(request.user, 'realtor') and request.user.realtor != listing.realtor:
        messages.error(request, "You are not authorized to edit this listing.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, "Listing updated successfully!")
            return redirect('dashboard')
    else:
        form = ListingForm(instance=listing)

    context = {
        'form': form,
        'listing': listing
    }
    return render(request, 'listings/edit_listing.html', context)

def create_admin(request):
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser('admin', 'lavi@gmail.com', '123')
        user.save()
        return HttpResponse("Admin user created successfully.")
    else:
        return HttpResponse("Admin already exists.")
