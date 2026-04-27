from .models import DeliveryRecord
from quantumways.base_feature_view import BaseFeatureView
from quantumways.base_import_view import BaseImportView
from quantumways.base_export_view import BaseExportView
from quantumways.base_comment_view import BaseCommentView
from comment_app.serializers import AddCommentSerializer, ListCommentSerializer, UpdateCommentSerializer
from quantumways.constants import Features
from django.db.models import Q
from datetime import date, datetime
from .serializers import (
    AddDeliveryRecordSerializer,
    ViewDeliveryRecordDetailsSerializer,
    ImportXlsxInDeliveryRecordSerializer,
    ViewListDeliveryRecordsSerializer,
    UpdateDeliveryRecordSerializer,
    SearchListDeliveryRecordsSerializer
)

class DeliveryRecordView(BaseFeatureView):

    model = DeliveryRecord
    lookup_no_field = 'dr_no'


    create_serializer_class = AddDeliveryRecordSerializer
    list_serializer_class = ViewListDeliveryRecordsSerializer
    detail_serializer_class = ViewDeliveryRecordDetailsSerializer
    update_serializer_class = UpdateDeliveryRecordSerializer
    search_serializer_class = SearchListDeliveryRecordsSerializer

    # Custom messsages response
    success_create_message = "Successfully added delivery record"
    success_list_message = "List of delivery records"
    success_detail_message = "Successfully found delivery record"
    success_update_message = "Successfully update the delivery record"
    success_bulk_delete_message = "Successfully delete delivery records"
    success_single_delete_message = "Successfully delete delivery record"
    not_found_message = "No id found from delivery record"
    not_found_search = "No delivery records found"

    prefetch_related_model = 'items'

    created_activity_type_message = "Record Created"
    created_activity_changes_message = "Created Delivery Record"

    update_activity_type_message = "Record Updated"
    update_activity_changes_message = "Updated Delivery Record"

    delete_activity_type_message = "Record Deleted"
    delete_activity_changes_message = "Deleted Delivery Record"

    unique_control_no = "dr_no"

    item_to_search = "dr_no__icontains"
        

class DeliveryRecordImportView(BaseImportView):

    feature_name = Features.DELIVERY_RECORD

    serializer_class = ImportXlsxInDeliveryRecordSerializer

    queryset = DeliveryRecord.objects.select_related('items').all()
        

class DeliveryRecordExportView(BaseExportView):

    feature_name = Features.DELIVERY_RECORD 
   
    model = DeliveryRecord 

    ids_or_no = 'ids_or_no' 

    unique_no = 'dr_no'

    prefetch_related_model = 'items'

    items_attr = 'items' 

    file_name = 'delivery_record_export_'

    formatters = {
        2: lambda d: d.strftime('%m/%d/%Y') if isinstance(d, (date, datetime)) else d
    }

    title_export = 'Delivery Record'

    def get_queryset(self, valid_uuids, valid_slugs):
        return (
            DeliveryRecord.objects.prefetch_related('items')
            .filter(
                Q(id__in=valid_uuids) |
                Q(dr_no__in=valid_slugs)
            )
        )

    def get_headers(self):
        return [
            "DR No",
            "Document Revisions",
            "Date",
            "Origin From",
            "Delivered By",
            "Delivered To",
            "Received By",
            "Approved by",
            "Remarks",
            "Item No",
            "Quantity",
            "Unit",
            "Item Description",
        ]


    def format_row(self, obj, item):
        return [
            obj.dr_no,
            obj.document_revisions,
            obj.date,
            obj.origin_from,
            obj.delivered_by,
            obj.delivered_to,
            obj.received_by,
            obj.approved_by.url if obj.approved_by else '',
            obj.remarks,
            item.item_no,
            item.quantity,
            item.unit,
            item.item_description if item.item_description else ''
        ]


class CommentView(BaseCommentView):

    model = DeliveryRecord

    create_serializer_class = AddCommentSerializer

    list_serializer_class = ListCommentSerializer

    update_serializer_class = UpdateCommentSerializer