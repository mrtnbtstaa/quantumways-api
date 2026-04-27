from django.urls import path
from .views import PurchaseRequestInTopManagementView, PurchaseRequestImportView, PurchaseRequestExportView, CommentView

urlpatterns = [

    # CSV import/export actions
    path('v1/purchase-requests/import/', PurchaseRequestImportView.as_view(), name='purchase_requests_import'),
    path('v1/purchase-requests/export/', PurchaseRequestExportView.as_view(), name='purchase_requests_export'),

    # List & Create Comments for PurchaseRequest
    path('v1/purchase-requests/<uuid:object_id>/comments/', CommentView.as_view(), name='purchase_request_comment_list_create'),
    # Retrieve, Update, Delete a specific comment
    path('v1/purchase-requests/<uuid:object_id>/comments/<uuid:comment_id>/', CommentView.as_view(), name='purchase_request_comment_detail'),
    
    # Standard CRUD for Purchase Requests
    path('v1/purchase-requests/', PurchaseRequestInTopManagementView.as_view(), name='purchase_requests_list_create'),
    path('v1/purchase-requests/<str:slug>/', PurchaseRequestInTopManagementView.as_view(), name='purchase_request_detail'),


]