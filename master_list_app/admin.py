from django.contrib import admin
from .models import Supplier, Product, Equipment, EquipmentSnapshot

@admin.register(Supplier)
class AdminMasterListSupplier(admin.ModelAdmin):
    pass

@admin.register(Product)
class AdminMasterListProduct(admin.ModelAdmin):
    pass

@admin.register(Equipment)
class AdminMasterListEquipment(admin.ModelAdmin):
    pass

@admin.register(EquipmentSnapshot)
class AdminMasterListEquipmentSnapshot(admin.ModelAdmin):
    pass

