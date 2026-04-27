from django.contrib import admin

from storage_app.models import File, Folder

# Register your models here.
@admin.register(File)
class AdminFile(admin.ModelAdmin):
    pass
@admin.register(Folder)
class AdminFolder(admin.ModelAdmin):
    pass
