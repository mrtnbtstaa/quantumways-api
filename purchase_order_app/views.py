from .models import PurchaseOrder
from django.db.models import When, Case, Value, CharField, Q
from datetime import date
from quantumways.base_feature_view import BaseFeatureView
from quantumways.base_import_view import BaseImportView
from quantumways.base_export_view import BaseExportView
from quantumways.base_comment_view import BaseCommentView
from comment_app.serializers import AddCommentSerializer, ListCommentSerializer, UpdateCommentSerializer
from quantumways.constants import Features
from .serializers import (
    AddPurchaseOrderInTopManagementSerializer,
    ViewPurchaseOrderInTopManagementSerializer,
    ImportXlxsInPurchaseOrdersSerializer,
    ViewPurchaseOrderDetailsInTopManagementSerializer,
    UpdatePurchaseOrderSerializer,
    SearchPurchaseOrderInTopManagementSerializer
)

class PurchaseOrderInTopManagementView(BaseFeatureView):

    feature_name = Features.PURCHASE_ORDER
    
    model = PurchaseOrder
    lookup_no_field = 'po_control_no'
    create_serializer_class = AddPurchaseOrderInTopManagementSerializer
    list_serializer_class = ViewPurchaseOrderInTopManagementSerializer
    detail_serializer_class = ViewPurchaseOrderDetailsInTopManagementSerializer
    update_serializer_class = UpdatePurchaseOrderSerializer
    search_serializer_class = SearchPurchaseOrderInTopManagementSerializer

    success_create_message = "Successfully added purchase order"
    success_list_message = "List of purchase orders"
    success_detail_message = "Successfully found purchase order"
    success_update_message = "Successfully update the purchase orders"
    success_bulk_delete_message = "Successfully delete the purchase orders"
    success_single_delete_message = "Successfully delete the purchase order"
    not_found_message = "No ids_or_no found from the purchase order"
    not_found_search = "No purchase order found"

    prefetch_related_model = 'items'

    select_related_model = ('vendee', 'project', 'additional_information')

    created_activity_type_message = "Record Created"
    created_activity_changes_message = "Created Purchase Order"

    update_activity_type_message = "Record Updated"
    update_activity_changes_message = "Updated Purchase Order"

    delete_activity_type_message = "Record Deleted"
    delete_activity_changes_message = "Deleted Purchase Order"

    unique_control_no = "po_control_no"

    item_to_search = "po_control_no__icontains"


class PurchaseOrderImportView(BaseImportView):

    feature_name = Features.PURCHASE_ORDER

    serializer_class = ImportXlxsInPurchaseOrdersSerializer

    queryset = PurchaseOrder.objects.select_related(
        'purchase_vendee',
        'purchase_project',
        'purchase_additonal_information',
        'purchase_items'
    ).all()


class PurchaseOrderExportView(BaseExportView):

    feature_name = Features.PURCHASE_ORDER
   
    model = PurchaseOrder

    ids_or_no = 'ids_or_no'

    unique_no = 'po_control_no' 

    prefetch_related_model = None

    items_attr = None 

    file_name = 'purchase_order_export_'

    formatters = {
        5: lambda d: d.strftime('%m/%d/%y') if isinstance(d, date) else '' 
    } 

    title_export = 'Purchase Orders'

    use_values_list = True # When True use the `get_queryset()` otherwise the `format_row()`

    def get_queryset(self, valid_uuids, valid_slugs):
        return (
            PurchaseOrder.objects
            .select_related(
                'purchase_vendee',
                'purchase_project',
                'purchase_additonal_information',
                'purchase_items'
            )
            .annotate(
                new_cash_payment=Case(
                    When(cash_payment=True, then=Value('Yes')),
                    When(cash_payment=False, then=Value('No')),
                    output_field=CharField()
                ),
                new_cheque_payment=Case(
                    When(cheque_payment=True, then=Value('Yes')),
                    When(cheque_payment=False, then=Value('No')),
                    output_field=CharField()
                ),
                new_for_delivery=Case(
                    When(additional_information__for_delivery=True, then=Value('Yes')),
                    When(additional_information__for_delivery=False, then=Value('No')),
                ),
                new_for_pick_up_by=Case(
                    When(additional_information__for_pick_up_by=True, then=Value('Yes')),
                    When(additional_information__for_pick_up_by=False, then=Value('No')),
                )
            )
            .filter(
                Q(id__in=valid_uuids) |
                Q(po_control_no__in=valid_slugs)
            ).values_list(
                "po_control_no",
                "document_revisions",
                "pr_no",
                "new_cash_payment",
                "new_cheque_payment",
                "po_date",
                "vendee__company_name",
                "vendee__address",
                "vendee__contact_person",
                "vendee__phone_email",
                "project__project_name",
                "project__address",
                "project__contact_person",
                "project__phone_email",
                "new_for_delivery",
                "new_for_pick_up_by",
                "additional_information__for_pick_up_by_text",
                "additional_information__remarks",
                "items__quantity",
                "items__description",
                "items__unit_price",
                "items__unit",
                "items__amount"
            )
        )

    def get_headers(self):
        return [
            "PO Control No",
            "Document Revisions",
            "PR Number",
            "Cash Payment",
            "Cheque Payment",
            "PO Date",
            "Company Name",
            "Address",
            "Contact Person",
            "Phone/Email",
            "Project Name",
            "Address",
            "Contact Person",
            "Phone/Email",
            "For Delivery",
            "For Pick up by",
            "For Pick up by text",
            "Remarks",
            "Qty",
            "Description",
            "Unit Price",
            "Unit",
            "Amount"
        ]


class CommentView(BaseCommentView):

    model = PurchaseOrder

    create_serializer_class = AddCommentSerializer

    list_serializer_class = ListCommentSerializer

    update_serializer_class = UpdateCommentSerializer