from django.contrib import admin
from .models import PettyCash, PettyItem

@admin.register(PettyCash)
class AdminPettyCash(admin.ModelAdmin):
    pass

@admin.register(PettyItem)
class AdminPettyItems(admin.ModelAdmin):
    pass