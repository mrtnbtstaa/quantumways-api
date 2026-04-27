from django.contrib import admin
from .models import PurchaseItem, PurchaseRequest

@admin.register(PurchaseRequest)
class AdminPurchaseRequest(admin.ModelAdmin):
    pass

@admin.register(PurchaseItem)
class AdminPurchaseItem(admin.ModelAdmin):
    pass