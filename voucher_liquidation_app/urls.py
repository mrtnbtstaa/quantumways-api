from django.urls import path

from .views import (
    VoucherLiquidationView,
    VoucherLiquidationImportView,
    VoucherLiquidationExportView,
    CommentView
)

urlpatterns = [

    # Import/Export Actions
    path('v1/vouchers/import/', VoucherLiquidationImportView.as_view(), name='vouchers_import'),
    path('v1/vouchers/export/', VoucherLiquidationExportView.as_view(), name='vouchers_export'),

    # List & Create Comments for Vouchers
    path('v1/vouchers/<uuid:object_id>/comments/', CommentView.as_view(), name='voucher_comment_list_create'),
    # Retrieve, Update, Delete a specific comment
    path('v1/vouchers/<uuid:object_id>/comments/<uuid:comment_id>/', CommentView.as_view(), name='voucher_record_comment_detail'),

    # Standard Crud for vouchers
    path('v1/vouchers/', VoucherLiquidationView.as_view(), name='list_create_vouchers'),
    path('v1/vouchers/<str:slug>/', VoucherLiquidationView.as_view(), name='voucher_details'),
]