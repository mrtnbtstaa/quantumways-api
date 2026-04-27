from django.contrib import admin
from .models import (
    PurchaseAdditionalInformation,
    PurchaseItem,
    PurchaseOrder,
    PurchaseProject,
    PurchaseVendee
)

@admin.register(PurchaseOrder)
class AdminPurchaseOrder(admin.ModelAdmin):
    pass

@admin.register(PurchaseVendee)
class AdminPurchaseVendee(admin.ModelAdmin):
    pass

@admin.register(PurchaseProject)
class AdminPurchaseProject(admin.ModelAdmin):
    pass

@admin.register(PurchaseAdditionalInformation)
class AdminPurchaseAdditionalInformation(admin.ModelAdmin):
    pass

@admin.register(PurchaseItem)
class AdminPurchaseItem(admin.ModelAdmin):
    pass