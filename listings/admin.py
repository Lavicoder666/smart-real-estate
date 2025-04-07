from django.contrib import admin
from .models import Listing
from .models import MaintenanceRequest
# Register your models here.

class ListingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_published', 'price', 'list_date', 'realtor')
    list_display_links = ('id', 'title')
    list_filter = ('realtor',)
    list_editable = ('is_published',)
    search_fields = ('title', 'description', 'address', 'city', 'state', 'zipcode', 'price')
    list_per_page = 25

admin.site.register(Listing, ListingsAdmin)


class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'request_type', 'status', 'request_date')
    list_filter = ('status', 'request_type')
    search_fields = ('user__username', 'listing__title')

admin.site.register(MaintenanceRequest, MaintenanceRequestAdmin)
