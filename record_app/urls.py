from django.urls import path
from .views import RecordView, RecordsExportView

urlpatterns = [

    # Export Action

    path('v1/records/export/', RecordsExportView.as_view(), name='export_record'),

    path('v1/records/', RecordView.as_view(), name='list_create_records'),
    path('v1/records/<str:slug>/', RecordView.as_view(), name='record_details'),
]