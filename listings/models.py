from django.db import models
from datetime import datetime
from realtors.models import Realtor
from django.contrib.auth.models import User 
from .choices import bedroom_choices, state_choices, listing_type_choices, rent_schedule_choices, maintenance_choices 


class Listing(models.Model):
    realtor = models.ForeignKey(Realtor, on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    price = models.IntegerField()
    bedrooms = models.IntegerField()
    bathrooms = models.DecimalField(max_digits=2, decimal_places=1)
    garage = models.IntegerField(default=0)
    sqft = models.CharField(max_length=20, blank=True)
    lot_size = models.DecimalField(max_digits=5, decimal_places=1)
    photo_main = models.ImageField(upload_to='photos/%Y/%m/%d')
    photo_1 = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True)
    photo_2 = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True)
    photo_3 = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True)
    photo_4 = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True)
    photo_5 = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True)
    is_published = models.BooleanField(default=True)
    list_date = models.DateTimeField(default=datetime.now, blank=True)
    vr_embed_code = models.TextField(blank=True, null=True)
    listing_type = models.CharField(max_length=10, choices=listing_type_choices, default='sale')
    rent_payment_schedule = models.CharField(max_length=10, choices=rent_schedule_choices, blank=True, null=True)  # إضافة حقل جدول الدفع
    photo_main_category = models.CharField(max_length=50, blank=True, null=True)  # إضافة حقل تصنيف الصورة الرئيسية
    photo_1_category = models.CharField(max_length=50, blank=True, null=True)  # إضافة حقل تصنيف الصورة 1
    photo_2_category = models.CharField(max_length=50, blank=True, null=True)  # إضافة حقل تصنيف الصورة 2
    photo_3_category = models.CharField(max_length=50, blank=True, null=True)  # إضافة حقل تصنيف الصورة 3
    photo_4_category = models.CharField(max_length=50, blank=True, null=True)  # إضافة حقل تصنيف الصورة 4
    photo_5_category = models.CharField(max_length=50, blank=True, null=True)  # إضافة حقل تصنيف الصورة 5
    google_maps_embed_link = models.URLField(blank=True)
    
    def __str__(self):
        return self.title

    objects = models.Manager()

class MaintenanceRequest(models.Model):
    REQUEST_TYPES = [(key, value) for key, value in maintenance_choices.items()]  # ✅ تحويل القاموس إلى خيارات

    listing = models.ForeignKey('Listing', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES)  # ✅ تعيين الخيارات هنا
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='Pending')
    request_date = models.DateTimeField(default=datetime.now)

    def __str__(self): 
        return f"{self.listing.title} - {self.get_request_type_display()} - {self.status}"  # ✅ استخدام `get_request_type_display()`
    
class SavedListing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    saved_date = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.user.username} - {self.listing.title}"    