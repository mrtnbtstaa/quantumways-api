from django.urls import path
from .views import DeliveryRecordView, DeliveryRecordImportView, DeliveryRecordExportView, CommentView

urlpatterns = [

    # Export/Import Actions
    path('v1/delivery-records/import/', DeliveryRecordImportView.as_view(), name='delivery_records_import'),
    path('v1/delivery-records/export/', DeliveryRecordExportView.as_view(), name='delivery_records_export'),

    # List & Create Comments for Delivery Record
    path('v1/delivery-records/<uuid:object_id>/comments/', CommentView.as_view(), name='delivery_record_comment_list_create'),
    # Retrieve, Update, Delete a specific comment
    path('v1/delivery-records/<uuid:object_id>/comments/<uuid:comment_id>/', CommentView.as_view(), name='delivery_record_comment_detail'),

    # Standard Crud for delivery reocrds
    path('v1/delivery-records/', DeliveryRecordView.as_view(), name='list_create_delivery_records'),
    path('v1/delivery-records/<str:slug>/', DeliveryRecordView.as_view(), name='delivery_record_details'),
]