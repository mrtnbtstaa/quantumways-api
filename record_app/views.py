from rest_framework import generics, status
from quantumways.utils import response_message_utils
from quantumways.permissions import AllRoles
from rest_framework.permissions import IsAuthenticated
from quantumways.export_to_excel import export_to_excel
from .models import Record
from quantumways.base_feature_view import BaseFeatureView
from datetime import datetime, date
from .serializers import (
    AddRecordSerializer,
    ViewRecordSerializer,
    ViewRecordDetailsSerializer,
    UpdateRecordsSerializer,
    SearchRecordSerializer
)


class RecordView(BaseFeatureView):

    model = Record

    lookup_no_field = 'id'

    create_serializer_class = AddRecordSerializer
    list_serializer_class = ViewRecordSerializer
    detail_serializer_class = ViewRecordDetailsSerializer
    update_serializer_class = UpdateRecordsSerializer
    search_serializer_class = SearchRecordSerializer

    success_create_message = "Successfully created records"
    success_list_message = "List of records"
    success_detail_message = "Successfully found record details"
    success_update_message = "Successfully update the record"
    success_bulk_delete_message = "Succesfully delete the records"
    success_single_delete_message = "Succesfully delete the record"
    not_found_message = "no id found from the record"
    not_found_search = "No records found"

    prefetch_related_model = 'items'

    item_to_search = "items__pr_no__icontains"
    

class RecordsExportView(generics.CreateAPIView):

    permission_classes = [IsAuthenticated, AllRoles]

    def post(self, request, *args, **kwargs):

        try:

            ids = self.request.data.get('ids')


            if not Record.objects.filter(
                id__in=ids
            ).exists():
                return response_message_utils(
                    message="No ids_or_no found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Define the header row
            headers = [
                "DATE".ljust(200),
                "PR NO".ljust(200),
                "PCV NO".ljust(200),
                "DR NO".ljust(200),
                "VL".ljust(200),
                "PO NO".ljust(200),
                "PROJECT SITE".ljust(200),
                "PERSON IN CHARGE".ljust(200),
                "EQUIPMENT".ljust(200),
                "SUPPLIER".ljust(200),
                "TYPE OF RECEIPT".ljust(200),
                "INVOICE/RECEIPT NO".ljust(200),
                "RECEIPT ISSUED TO".ljust(200),
                "QTY".ljust(200),
                "UNIT".ljust(200),
                "PRODUCT NAME".ljust(200),
                "ITEM PRICE".ljust(200),
                "ITEM UNIT".ljust(200),
                "TOTAL AMOUNT".ljust(200),
                "SUPPLIER RECEIPT AMOUNT".ljust(200),
                "AMOUNT/SITE. PER person".ljust(200),
                "PETTY CASH GIVEN".ljust(200),
                "AMOUNT REFUNDED".ljust(200),
            ]

            rows = []

            # Get data
            queryset = (
                Record.objects.prefetch_related('items')
                .filter(
                    id__in=ids
                )
            )

            for obj in queryset:
                items = obj.items.all()
                
                if items.exists():
                    first = True
                    for item in items:
                        row = [
                        obj.date if first else '',
                        item.pr_no if item.pr_no else '',
                        item.pcv_no if item.pcv_no else '',
                        item.dr_no if item.dr_no else '',
                        item.vl if item.vl else '',
                        item.po_no if item.po_no else '',
                        item.project_site if item.project_site else '',
                        item.person_in_charge if item.person_in_charge else '',
                        item.equipment if item.equipment else '',
                        item.supplier if item.supplier else 'NO MERCHANT NAME',
                        item.type_of_receipt if item.type_of_receipt else '',
                        item.invoice_receipt_no if item.invoice_receipt_no else '',
                        item.receipt_issued_to if item.receipt_issued_to else '',
                        item.qty if item.qty else '',
                        item.unit if item.unit else '',
                        item.product_name if item.product_name else '',
                        item.item_price if item.item_price else '',
                        item.item_unit if item.item_unit else '',
                        item.total_amount if item.total_amount else '',
                        item.supplier_receipt_amount if item.supplier_receipt_amount else '',
                        obj.amount_site_per_person if first else '',
                        obj.petty_cash_given if first else '',
                        obj.amount_refunded if first else ''
                    ]

                        rows.append(row)
                        first = False

            formatters = {
                0: lambda d: d.strftime('%m/%d/%Y') if isinstance(d, (datetime, date)) else ''
            }

            return export_to_excel(
                headers=headers,
                file_name=f"records_",
                queryset=rows,
                title="Records",
                formatters=formatters

            )

        except Exception as e:
            return response_message_utils(
                message=f"Something went wrong while exporting your excel {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    