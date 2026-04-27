from django.contrib import admin
from .models import VoucherExpense, VoucherLiquidation


@admin.register(VoucherLiquidation)
class AdminVoucherLiquidation(admin.ModelAdmin):
    pass

@admin.register(VoucherExpense)
class AdminVoucherExpense(admin.ModelAdmin):
    pass