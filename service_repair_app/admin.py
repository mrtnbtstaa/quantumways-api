from django.contrib import admin
from .models import EquipmentLog, Material, ServiceRepair

@admin.register(ServiceRepair)
class AdminServiceRepair(admin.ModelAdmin):
    pass

@admin.register(Material)
class AdminMaterial(admin.ModelAdmin):
    pass

@admin.register(EquipmentLog)
class AdminEquipmentLog(admin.ModelAdmin):
    pass

