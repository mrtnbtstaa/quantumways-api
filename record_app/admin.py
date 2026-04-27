from django.contrib import admin
from .models import Record, RecordItem

@admin.register(Record)
class AdminRecord(admin.ModelAdmin):
    pass

@admin.register(RecordItem)
class AdminRecordItem(admin.ModelAdmin):
    pass
