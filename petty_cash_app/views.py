from .models import PettyCash
from datetime import date
from quantumways.base_feature_view import BaseFeatureView
from quantumways.base_import_view import BaseImportView
from quantumways.base_export_view import BaseExportView
from quantumways.base_comment_view import BaseCommentView
from comment_app.serializers import AddCommentSerializer, ListCommentSerializer, UpdateCommentSerializer
from quantumways.constants import Features
from django.db.models import Q
from .serializers import (
    AddPettyCashInTopManagementSerializer,
    ViewPettyCashSerializer,
    ViewPettyCashDetailsSerializer,
    UpdatePettyCashSerializer,
    ImportXlsxInPettyCashSerializer,
    SearchPettyCashSerializer
)

class PettyCashView(BaseFeatureView):

    model = PettyCash
    lookup_no_field = 'control_no'

    create_serializer_class = AddPettyCashInTopManagementSerializer
    list_serializer_class = ViewPettyCashSerializer
    detail_serializer_class = ViewPettyCashDetailsSerializer
    update_serializer_class = UpdatePettyCashSerializer
    search_serializer_class = SearchPettyCashSerializer

    # Custom response message
    success_create_message = "Successfully added petty cash"
    success_list_message = "List of petty cash"
    success_detail_message = "Successfully found petty cash"
    success_update_message = "Successfully update the petty cash"
    success_bulk_delete_message = "Successfully delete the petty cash"
    success_single_delete_message =  "Successfully delete the petty cash"
    not_found_message = "No ids_or_no found from the petty cash"
    not_found_search = "No petty cash found"
    
    prefetch_related_model = 'items'

    created_activity_type_message = "Record Created"
    created_activity_changes_message = "Created Petty Cash"

    update_activity_type_message = "Record Updated"
    update_activity_changes_message = "Updated Petty Cash"

    delete_activity_type_message = "Record Deleted"
    delete_activity_changes_message = "Deleted Petty Cash"

    
    unique_control_no = "control_no"

    item_to_search = "control_no__icontains"
        

class PurchaseOrderImportView(BaseImportView):

    feature_name = Features.PETTY_CASH

    serializer_class = ImportXlsxInPettyCashSerializer

    queryset = PettyCash.objects.select_related(
        'items',
    ).all()


class PettyCashExportView(BaseExportView):

    feature_name = Features.PETTY_CASH 
   
    model = PettyCash 

    ids_or_no = 'ids_or_no' 

    unique_no = 'control_no' 

    prefetch_related_model = None 

    items_attr = None

    file_name = 'petty_cash_export_'

    formatters = {
        2: lambda d: d.strftime('%m/%d/%Y') if isinstance(d, date) else ''
    }

    title_export = 'Petty Cash'

    use_values_list = True

    def get_queryset(self, valid_uuids, valid_slugs):
        return (
            PettyCash.objects
            .select_related(
                'items'
            )
            .filter(
                Q(id__in=valid_uuids) |
                Q(control_no__in=valid_slugs)
            ).values_list(
                "control_no",
                "document_revisions",
                "date",
                "pc_given",
                "requested_and_received_by",
                "location",
                "released_by",
                "remarks",
                "items__no_of_items",
                "items__unit",
                "items__services_purchased",
                "items__unit_cost",
                "items__amount"
            )
        )

    def get_headers(self):
        return [
            "Control No",
            "Document Revisions",
            "Date",
            "PC Given",
            "Requested and Received by",
            "Location",
            "Released by",
            "Remarks",
            "No of Items",
            "Unit",
            "Description of Items/Services Purchased",
            "Unit Cost",
            "Amount"
        ]




    
class CommentView(BaseCommentView):

    model = PettyCash

    create_serializer_class = AddCommentSerializer

    list_serializer_class = ListCommentSerializer

    update_serializer_class = UpdateCommentSerializer