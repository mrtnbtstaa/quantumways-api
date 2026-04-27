from .models import PurchaseRequest
from quantumways.base_feature_view import BaseFeatureView
from quantumways.base_import_view import BaseImportView
from quantumways.base_export_view import BaseExportView
from quantumways.base_comment_view import BaseCommentView
from quantumways.constants import Features
from django.db.models import Q
from comment_app.serializers import AddCommentSerializer, ListCommentSerializer, UpdateCommentSerializer
from .serializers import (
    AddPurchaseRequestInTopManagementSerializer,
    ViewPurchaseRequestInTopManagementSerializer,
    ViewPurchaseRequestDetailsInTopManagementSerializer,
    ImportXlslInPurchaseRequestSerializer,
    UpdatePurchaseRequestSerializer,
    SearchPurchaseRequestInTopManagementSerializer
)

class PurchaseRequestInTopManagementView(BaseFeatureView):

    feature_name = Features.PURCHASE_REQUEST
    
    model = PurchaseRequest
    lookup_no_field = 'pr_no'

    create_serializer_class = AddPurchaseRequestInTopManagementSerializer
    list_serializer_class = ViewPurchaseRequestInTopManagementSerializer
    detail_serializer_class = ViewPurchaseRequestDetailsInTopManagementSerializer
    update_serializer_class = UpdatePurchaseRequestSerializer
    search_serializer_class = SearchPurchaseRequestInTopManagementSerializer

    success_create_message = "Successfully added purchase request"
    success_list_message = "List of purchase requests"
    success_detail_message = "Successfully found purchase request"
    success_update_message = "Successfully update the purchase requests"
    success_bulk_delete_message = "Successfully delete the purchase requests"
    success_single_delete_message = "Successfully delete the purchase request"
    not_found_message = "No ids_or_no found from purchase requests"
    not_found_search = []

    model_related_prefetch = 'purchase_items'

    created_activity_type_message = "Record Created"
    created_activity_changes_message = "Created Purchase Request"

    update_activity_type_message = "Record Updated"
    update_activity_changes_message = "Updated Purchase Request"

    delete_activity_type_message = "Record Deleted"
    delete_activity_changes_message = "Deleted Purchase Request"

    unique_control_no = "pr_no"

    item_to_search = "pr_no__icontains"


class PurchaseRequestImportView(BaseImportView):

    feature_name = Features.PURCHASE_REQUEST

    serializer_class = ImportXlslInPurchaseRequestSerializer

    queryset = PurchaseRequest.objects.select_related('purchase_items').all()


class PurchaseRequestExportView(BaseExportView):

    feature_name = Features.PURCHASE_REQUEST

    model = PurchaseRequest

    ids_or_no = 'ids_or_no'

    unique_no = 'pr_no'

    prefetch_related_model = 'purchase_items'

    items_attr = 'purchase_items'

    file_name = 'purchase_request_export_'

    title_export = 'purchase_request'

    def get_queryset(self, valid_uuids, valid_slugs):
        filter_unique_no = {f"{self.unique_no}__in": valid_slugs}
        return self.model.objects.prefetch_related(self.prefetch_related_model).filter(Q(id__in=valid_uuids) | Q(**filter_unique_no))

    def get_headers(self):
        return [
            "PR No",
            "Document Revisions",
            "Date Requested",
            "Date Needed",
            "Project Name",
            "Location",
            "Prepared By",
            "Requested Signature",
            "Remarks",
            "Approved By",
            "Approved Signature",
            "Date/Time",
            "Request Status",
            "Remarks",
            "No",
            "Quantity",
            "Unit",
            "Description",
            "Purpose"
        ]

    def format_row(self, obj, item):
        return [
            obj.pr_no,
            obj.document_revisions,
            obj.date_requested or '',
            obj.date_needed or '',
            obj.project_name,
            obj.location,
            str(obj.prepared_by) if obj.prepared_by else '',
            getattr(obj.requested_signature, "url", ""),
            obj.remarks,
            str(obj.approved_by) if obj.approved_by else '',
            getattr(obj.approved_signature, "url", ""),
            obj.date_time.strftime('%m/%d/%Y') if obj.date_time else '',
            obj.request_status,
            obj.final_remarks,
            item.no,
            item.quantity,
            item.unit,
            item.description,
            item.purpose
        ]


class CommentView(BaseCommentView):

    model = PurchaseRequest

    create_serializer_class = AddCommentSerializer

    list_serializer_class = ListCommentSerializer

    update_serializer_class = UpdateCommentSerializer