from django.contrib import admin
from .models import User, UserRole, UserProfile, UserInformation, UserEmergencyInformation
# Register your models here.

@admin.register(User)
class AdminUser(admin.ModelAdmin):
    pass

@admin.register(UserRole)
class AdminUserRole(admin.ModelAdmin):
    pass

@admin.register(UserProfile)
class AdminUserProfile(admin.ModelAdmin):
    pass

@admin.register(UserInformation)
class AdminUserInformation(admin.ModelAdmin):
    pass

@admin.register(UserEmergencyInformation)
class AdminUserEmergencyInformation(admin.ModelAdmin):
    pass
