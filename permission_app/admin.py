from django.contrib import admin
from .models import Feature, UserFeaturePermission


@admin.register(Feature)
class AdminFeature(admin.ModelAdmin):
    pass

@admin.register(UserFeaturePermission)
class AdminUserFeaturePermission(admin.ModelAdmin):
    pass