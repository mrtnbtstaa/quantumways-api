from django.contrib import admin
from .models import DeliveryItem, DeliveryRecord

@admin.register(DeliveryRecord)
class AdminDeliveryRecord(admin.ModelAdmin):
    pass

@admin.register(DeliveryItem)
class AdminDeliveryItem(admin.ModelAdmin):
    pass