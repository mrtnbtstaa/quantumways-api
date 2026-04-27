from django.urls import path
from .views import (
    PurchaseOrderInTopManagementView, 
    PurchaseOrderExportView,
    PurchaseOrderImportView,
    CommentView
)

urlpatterns = [
    
    # Import/Export Actions
    path('v1/purchase-orders/export/', PurchaseOrderExportView.as_view(), name='purchase_orders_export'),
    path('v1/purchase-orders/import/', PurchaseOrderImportView.as_view(), name='purchase_orders_import'),

    # List & Create Comments for PurchaseRequest
    path('v1/purchase-orders/<uuid:object_id>/comments/', CommentView.as_view(), name='purchase_orders_comment_list_create'),
    # Retrieve, Update, Delete a specific comment
    path('v1/purchase-orders/<uuid:object_id>/comments/<uuid:comment_id>/', CommentView.as_view(), name='purchase_orders_comment_detail'),

    # Standard CRUD for Purchase Orders
    path('v1/purchase-orders/', PurchaseOrderInTopManagementView.as_view(), name='purchase_orders_create_list_delete'),
    path('v1/purchase-orders/<str:slug>/', PurchaseOrderInTopManagementView.as_view(), name='purchase_orders_detail'),

]