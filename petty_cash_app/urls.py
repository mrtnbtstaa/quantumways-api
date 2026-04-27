from django.urls import path
from .views import PettyCashView, PurchaseOrderImportView, PettyCashExportView, CommentView

urlpatterns = [

    # Import/Export actions
    path('v1/petty-cash/import/', PurchaseOrderImportView.as_view(), name='petty_cash_import'),
    path('v1/petty-cash/export/', PettyCashExportView.as_view(), name='petty_cash_export'),

    # List & Create Comments for PurchaseRequest
    path('v1/petty-cash/<uuid:object_id>/comments/', CommentView.as_view(), name='petty_cash_comment_list_create'),
    # Retrieve, Update, Delete a specific comment
    path('v1/petty-cash/<uuid:object_id>/comments/<uuid:comment_id>/', CommentView.as_view(), name='petty_cash_comment_detail'),

    # Standard Crud for Petty cash
    path('v1/petty-cash/', PettyCashView.as_view(), name='list_create_petty_cash'),
    path('v1/petty-cash/<str:slug>/', PettyCashView.as_view(), name='retrieve_destroy_petty_cash_details'),
]