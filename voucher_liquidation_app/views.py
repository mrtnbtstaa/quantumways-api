from .models import VoucherLiquidation
from django.db.models import When, Case, Value, CharField
from datetime import date, datetime
from quantumways.base_feature_view import BaseFeatureView
from quantumways.base_import_view import BaseImportView
from quantumways.base_export_view import BaseExportView
from quantumways.base_comment_view import BaseCommentView
from comment_app.serializers import AddCommentSerializer, ListCommentSerializer, UpdateCommentSerializer
from quantumways.constants import Features
from django.db.models import Q
from .serializers import (
    AddVoucherLiquidationSerializer,
    ViewVoucherLiquidationSerializer,
    ViewVoucherLiquidationDetailsSerializer,
    UpdateVoucherLiquidationSerializer,
    ImportXlsxInVoucherLiquidationSerializer,
    SearchVoucherLiquidationSerializer
)

class VoucherLiquidationView(BaseFeatureView):

    model = VoucherLiquidation
    lookup_no_field = 'voucher_no'

    create_serializer_class = AddVoucherLiquidationSerializer
    list_serializer_class = ViewVoucherLiquidationSerializer
    detail_serializer_class = ViewVoucherLiquidationDetailsSerializer
    update_serializer_class = UpdateVoucherLiquidationSerializer
    search_serializer_class = SearchVoucherLiquidationSerializer

    success_create_message = "Successfully added voucher"
    success_list_message = "List of vouchers"
    success_detail_message = "Successfully found voucher"
    success_update_message = "Successfully update the vouchers"
    success_bulk_delete_message = "Successfully delete the vouchers"
    success_single_delete_message = "Successfully delete the voucher"
    not_found_message = "No ids_or_no found from the voucher"
    not_found_search = "No voucher liquidation found"

    prefetch_related_model = 'expenses'

    created_activity_type_message = "Record Created"
    created_activity_changes_message = "Created Voucher Liquidation"

    update_activity_type_message = "Record Updated"
    update_activity_changes_message = "Created Voucher Liquidation"

    delete_activity_type_message = "Record Deleted"
    delete_activity_changes_message = "Deleted Voucher Liquidation"

    unique_control_no = "voucher_no"

    item_to_search = "voucher_no__icontains"


class VoucherLiquidationImportView(BaseImportView):

    feature_name = Features.VOUCHER_LIQUIDATION

    serializer_class = ImportXlsxInVoucherLiquidationSerializer

    queryset = VoucherLiquidation.objects.select_related(
        'expenses'
    ).all()


class VoucherLiquidationExportView(BaseExportView):

    feature_name = Features.VOUCHER_LIQUIDATION
   
    model = VoucherLiquidation 

    ids_or_no = 'ids_or_no'

    unique_no = 'voucher_no'

    file_name = 'voucher_liquidation_export_'

    formatters = {
        2: lambda d: d.strftime('%m/%d/%Y') if isinstance(d, (datetime, date)) else '',
        11: lambda d: d.strftime('%Y/%m/%d') if isinstance(d, (datetime, date)) else '' 
    }

    title_export = 'Voucher Liquidation'

    use_values_list = True

    def get_queryset(self, valid_uuids, valid_slugs):
        return (
            VoucherLiquidation.objects
            .select_related(
                'expenses'
            )
            .annotate(
                new_excess_cash_advance=Case(
                    When(excess_cash_advance=True, then=Value('Yes')),
                    When(excess_cash_advance=False, then=Value('No')),
                    output_field=CharField()
                ),
                new_excess_actual_expense=Case(
                    When(excess_actual_expense=True, then=Value('Yes')),
                    When(excess_actual_expense=False, then=Value('No')),
                    output_field=CharField()
                )
            )
            .filter(
                Q(id__in=valid_uuids) |
                Q(voucher_no__in=valid_slugs)
            ).values_list(
                "voucher_no",
                "document_revisions",
                "voucher_date",
                "voucher_amount",
                "prepared_by",
                "reviewed_and_received_by",
                "net_settlement",
                "new_excess_cash_advance",
                "new_excess_actual_expense",
                "excess_actual_expense_amount",
                "remarks",
                "expenses__date",
                "expenses__particulars",
                "expenses__amount",
            )
        )

    def get_headers(self):
        return [
            "Voucher No",
            "Document Revisions",
            "Voucher Date",
            "Voucher Amount",
            "Prepared By/Date",
            "Reviewed and Received By/Date",
            "Net Settlement",
            "Excess Cash Advance",
            "Excess Actual Expense",
            "Excess Actual Expense Amount",
            "Remarks",
            "Date",
            "Particulars",
            "Amount",
        ]



class CommentView(BaseCommentView):

    model = VoucherLiquidation

    create_serializer_class = AddCommentSerializer

    list_serializer_class = ListCommentSerializer

    update_serializer_class = UpdateCommentSerializer

    
