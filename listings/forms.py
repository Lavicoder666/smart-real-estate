from django import forms
from .models import Listing

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'title', 'address', 'city', 'state', 'zipcode', 'description',
            'price', 'bedrooms', 'bathrooms', 'garage', 'sqft', 'lot_size', 'photo_main',
            'photo_1', 'photo_2', 'photo_3', 'photo_4', 'photo_5', 'is_published', 
            'vr_embed_code', 'listing_type', 'rent_payment_schedule', 'google_maps_embed_link'
        ]  # 🚨 تم إزالة 'realtor' من هنا لأنه سيتم تعيينه تلقائيًا في views.py

    def __init__(self, *args, **kwargs):
        super(ListingForm, self).__init__(*args, **kwargs)
        if 'realtor' in self.fields:
            del self.fields['realtor']  # ✅ التأكد من إزالة realtor من الفورم
